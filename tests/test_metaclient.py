"""The meta-server address setting, and a local meta-server end to end.

No network beyond 127.0.0.1."""

import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common'),
                os.path.join(ROOT, 'metaserver')]

from common import configfile
from common.msgstruct import message, decodemessage, HOSTNAME
from metaserver import metaclient
from metaserver.metastruct import (MMSG_INFO, MMSG_START, MMSG_LIST,
                                   RMSG_LIST, encodedict, decodedict)


def free_port(kind=socket.SOCK_STREAM):
    s = socket.socket(socket.AF_INET, kind)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Setting(unittest.TestCase):
    """metaclient.address(): environment first, then the config file."""

    def setUp(self):
        self.saved_env = os.environ.pop(metaclient.ENVIRON_VAR, None)
        self.saved_path = configfile.path
        fd, self.cfg = tempfile.mkstemp()
        os.close(fd)
        configfile.path = lambda sourcedir: self.cfg

    def tearDown(self):
        configfile.path = self.saved_path
        os.unlink(self.cfg)
        os.environ.pop(metaclient.ENVIRON_VAR, None)
        if self.saved_env is not None:
            os.environ[metaclient.ENVIRON_VAR] = self.saved_env

    def write_cfg(self, value):
        with open(self.cfg, 'w') as f:
            f.write(repr({HOSTNAME: {'metaserver': value}}))

    def test_none_by_default(self):
        self.assertIsNone(metaclient.address())

    def test_forms(self):
        p = metaclient.parse_address
        self.assertEqual(p('h'), ('h', 8055, 8050))
        self.assertEqual(p('h:1'), ('h', 1, 8050))
        self.assertEqual(p('h:1:2'), ('h', 1, 2))
        self.assertIsNone(p(''))
        for bad in ('h:x', ':1', 'h:1:2:3'):
            self.assertRaises(ValueError, p, bad)

    def test_config_file(self):
        self.write_cfg('meta.example.org:9000')
        self.assertEqual(metaclient.address(), ('meta.example.org', 9000, 8050))

    def test_environment_wins(self):
        self.write_cfg('meta.example.org:9000')
        os.environ[metaclient.ENVIRON_VAR] = 'other.example.org'
        self.assertEqual(metaclient.address(), ('other.example.org', 8055, 8050))

    def test_empty_field_means_none(self):
        self.write_cfg('')
        self.assertIsNone(metaclient.address())

    def test_bad_value_means_none(self):
        os.environ[metaclient.ENVIRON_VAR] = 'h:notaport'
        self.assertIsNone(metaclient.address())

    def test_unreachable_is_quick(self):
        addr = ('127.0.0.1', free_port(), 1)     # nothing listens there
        start = time.time()
        self.assertIsNotNone(metaclient.reachable(addr))
        self.assertIsNone(metaclient.connect([], addr))
        self.assertLess(time.time() - start, 2 * metaclient.CONNECT_TIMEOUT)


class LocalMetaServer(unittest.TestCase):
    """metaserver/metaserver.py in a thread: a game server registers, and
    both the protocol and the web page list it."""

    @classmethod
    def setUpClass(cls):
        import importlib.util       # metaserver/metaserver.py, not the package
        spec = importlib.util.spec_from_file_location(
            'metaserver_main', os.path.join(ROOT, 'metaserver', 'metaserver.py'))
        ms_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ms_module)
        cls.ms = ms_module
        cls.port, cls.http = free_port(), free_port()
        ms_module.metaserver = ms_module.MetaServer(cls.port, free_port(
            socket.SOCK_DGRAM))
        ms_module.openhttpsocket(cls.http)
        threading.Thread(target=ms_module.mainloop, daemon=True).start()

    def test_register_and_list(self):
        addr = ('127.0.0.1', self.port, self.http)
        self.assertIsNone(metaclient.reachable(addr))
        game = metaclient.connect([], addr)
        game.sendall(message(MMSG_INFO, encodedict({'desc': b'Test game'})) +
                     message(MMSG_START, 12345))
        time.sleep(0.5)
        # the protocol: what Client.py -m lists
        q = metaclient.connect([], addr)
        q.sendall(message(MMSG_LIST))
        buf = b''
        while decodemessage(buf)[0] is None:
            buf += q.recv(8192)
        q.close()
        msg = decodemessage(buf)[0]
        self.assertEqual(msg[0], RMSG_LIST)
        entries = decodedict(msg[1])
        self.assertEqual(len(entries), 1)
        self.assertTrue(list(entries)[0].endswith(':12345'))
        # the web page the "Internet servers page" link leads to
        page = urllib.request.urlopen(metaclient.list_url(addr) + '?join=x',
                                      timeout=5).read().decode('latin-1')
        self.assertIn('Test game', page)
        game.close()


class Page(unittest.TestCase):
    """What the web interface shows, without starting a game server."""

    def setUp(self):
        self.saved_env = os.environ.pop(metaclient.ENVIRON_VAR, None)
        self.saved_path = configfile.path
        configfile.path = lambda sourcedir: os.devnull
        sys.path.insert(0, os.path.join(ROOT, 'http2'))
        import httppages
        self.PageServer = httppages.PageServer

    def tearDown(self):
        configfile.path = self.saved_path
        os.environ.pop(metaclient.ENVIRON_VAR, None)
        if self.saved_env is not None:
            os.environ[metaclient.ENVIRON_VAR] = self.saved_env

    def test_no_link_when_none_is_set(self):
        box = self.PageServer.metaserverbox(None)
        self.assertIn('No Internet server list is set', box)
        self.assertNotIn('http://', box)

    def test_link_to_local_page_when_set(self):
        os.environ[metaclient.ENVIRON_VAR] = 'meta.example.org'
        box = self.PageServer.metaserverbox(None)
        self.assertIn('meta.html', box)
        self.assertIn('meta.example.org:8055', box)

    def test_unreachable_page(self):
        os.environ[metaclient.ENVIRON_VAR] = '127.0.0.1:%d' % free_port()
        f, ctype = self.PageServer.metaloader(None, {})
        self.assertEqual(ctype, 'text/html')
        self.assertIn('Cannot reach the Internet server list', f.read())


if __name__ == '__main__':
    unittest.main()
