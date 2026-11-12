"""metaserver/metaserver.py facing peers that misbehave: it must stay up,
drop them, and keep their data out of the list page.  127.0.0.1 only."""

import importlib.util
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from urllib.parse import quote

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common'),
                os.path.join(ROOT, 'metaserver')]

from common.msgstruct import message, decodemessage
from metaserver.metastruct import (MMSG_INFO, MMSG_START, MMSG_LIST,
                                   MMSG_TRACEBACK, RMSG_LIST, encodedict,
                                   decodedict)


def free_port(kind=socket.SOCK_STREAM):
    s = socket.socket(socket.AF_INET, kind)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def closed_by_server(s, timeout=5):
    """True if the server closes s within timeout (reading what it sends)."""
    s.settimeout(timeout)
    try:
        while s.recv(65536):
            pass
    except socket.timeout:
        return False
    except OSError:
        pass
    return True


class MetaServerRobustness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            'metaserver_robust', os.path.join(ROOT, 'metaserver', 'metaserver.py'))
        ms = cls.ms = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ms)
        cls.tbdir = tempfile.mkdtemp()
        ms.TB_DIR = cls.tbdir
        ms.SEND_TIMEOUT = 0.5
        ms.IDLE_TIMEOUT = 1.0
        ms.SWEEP_INTERVAL = 0.2
        cls.port, cls.http = free_port(), free_port()
        ms.metaserver = ms.MetaServer(cls.port, free_port(socket.SOCK_DGRAM))
        ms.openhttpsocket(cls.http)
        threading.Thread(target=ms.mainloop, daemon=True).start()

    def connect(self, rcvbuf=None):
        s = socket.socket()
        if rcvbuf:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
        s.connect(('127.0.0.1', self.port))
        self.addCleanup(s.close)
        return s

    def listing(self):
        s = self.connect()
        s.sendall(message(MMSG_LIST))
        s.settimeout(5)
        buf = b''
        while decodemessage(buf)[0] is None:
            buf += s.recv(65536)
        msg = decodemessage(buf)[0]
        self.assertEqual(msg[0], RMSG_LIST)
        return decodedict(msg[1])

    def page(self, query=''):
        url = 'http://127.0.0.1:%d/bub-n-bros.html%s' % (self.http, query)
        return urllib.request.urlopen(url, timeout=5).read().decode('latin-1')

    def register(self, info, port):
        g = self.connect()
        g.sendall(message(MMSG_INFO, encodedict(info)) + message(MMSG_START, port))
        time.sleep(0.3)
        return g

    def test_page_escapes_what_peers_send(self):
        self.register({'desc': b'Escaping test',
                       'httpport': b'"><script>alert(1)</script>'}, 30001)
        page = self.page('?head=%s&join=%s' % (
            quote('<script>alert(2)</script>'), quote('x"><script>alert(3)</script>/y')))
        self.assertIn('Escaping test', page)
        self.assertNotIn('<script>', page)

    def test_page_keeps_a_valid_join_link(self):
        self.register({'desc': b'Join test', 'httpport': 8000}, 30002)
        page = self.page('?join=%s' % quote('127.0.0.1:8000/0x1234'))
        self.assertIn('http://127.0.0.1:8000/0x1234/join.html?host=127.0.0.1'
                      '&port=30002', page)

    def test_new_description_replaces_the_old_one(self):
        g = self.register({'desc': b'first', 'extra': b'old'}, 30003)
        g.sendall(message(MMSG_INFO, encodedict({'desc': b'second'})))
        time.sleep(0.3)
        info = decodedict([v for k, v in self.listing().items()
                           if k.endswith(':30003')][0])
        self.assertEqual(info['desc'], b'second')
        self.assertNotIn('extra', info)

    def test_malformed_message_is_dropped(self):
        s = self.connect()
        s.sendall(b'\x01\xff' + MMSG_LIST)      # typecode is not ASCII
        self.assertTrue(closed_by_server(s))
        self.listing()                           # still serving

    def test_endless_message_is_dropped(self):
        s = self.connect()
        # announces a 90000-byte value and sends 70000 bytes of it
        s.sendall(b'\x06' + b'90000s' + MMSG_INFO + b'x' * 70000)
        self.assertTrue(closed_by_server(s))
        self.listing()

    def test_peer_that_does_not_read_is_dropped(self):
        self.register({'desc': b'y' * 14000}, 30004)    # a long list
        slow = self.connect(rcvbuf=4096)
        try:
            slow.sendall(message(MMSG_LIST) * 400)
        except OSError:
            pass
        time.sleep(2)
        start = time.time()
        self.listing()                          # others are still served
        self.assertLess(time.time() - start, 2)
        self.assertTrue(closed_by_server(slow))

    def test_idle_connection_without_a_game_is_dropped(self):
        s = self.connect()
        self.assertTrue(closed_by_server(s, timeout=5))

    def test_crash_reports_are_capped(self):
        for f in os.listdir(self.tbdir):
            os.unlink(os.path.join(self.tbdir, f))
        s = self.connect()
        s.sendall(message(MMSG_TRACEBACK, b'z' * 60000))
        time.sleep(0.5)
        name = os.path.join(self.tbdir, 'tb-127.0.0.1.log')
        self.assertLessEqual(os.path.getsize(name),
                             self.ms.MAX_TRACEBACK_SIZE + 1000)
        os.unlink(name)
        for i in range(self.ms.MAX_TRACEBACKS):
            open(os.path.join(self.tbdir, 'tb-10.0.0.%d.log' % i), 'w').close()
        s.sendall(message(MMSG_TRACEBACK, b'one more'))
        time.sleep(0.5)
        self.assertFalse(os.path.exists(name))


if __name__ == '__main__':
    unittest.main()
