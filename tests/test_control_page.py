"""The game's control page (http2/httppages.py): who may use it and what
it accepts.  No network."""

import os
import stat
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common'), os.path.join(ROOT, 'http2'),
                os.path.join(ROOT, 'display')]

import httpserver
import httppages
from httpserver import HTTPRequestError


class Requests(unittest.TestCase):

    def test_local_requests(self):
        ok = httpserver.is_local_request
        self.assertTrue(ok(('127.0.0.1', 1), {'host': '127.0.0.1:8000'}))
        self.assertTrue(ok(('127.0.0.1', 1), {'host': 'localhost:8000'}))
        self.assertTrue(ok(('::1', 1), {'host': '[::1]:8000'}))

    def test_other_requests(self):
        ok = httpserver.is_local_request
        # from another computer
        self.assertFalse(ok(('192.168.1.5', 1), {'host': '127.0.0.1:8000'}))
        # a web page whose name now points at 127.0.0.1 (DNS rebinding)
        self.assertFalse(ok(('127.0.0.1', 1), {'host': 'evil.example:8000'}))
        self.assertFalse(ok(('127.0.0.1', 1), {}))


class FakeMode:
    def __init__(self, name, options):
        self.name, self.options = name, options
    def unique_id(self):
        return 'dpy_' + self.name
    def getmodule(self):
        return self


class FakePages:
    """What PageServer's loaders use, without sockets."""
    filename = '/tmp/config.txt'
    def __init__(self, options):
        self.localoptions = httppages.Options(options)
        self.globaloptions = httppages.Options(options)
        self.Game = None
    def localmodes(self):
        return (FakeMode('pygame', {'fullscreen': 'no'}),
                FakeMode('off', {}))
    def buildclientoptions(self):
        return httppages.PageServer.buildclientoptions(self)
    def reloadports(self):
        pass


class Launch(unittest.TestCase):

    def test_only_known_driver_options_reach_the_client(self):
        pages = FakePages({'dpy_pygame_fullscreen': 'yes',
                           'dpy_pygame_cfg': '/home/x/other.txt'})
        args = pages.buildclientoptions()
        self.assertIn('--fullscreen=yes', args)
        self.assertFalse([a for a in args if a.startswith('--cfg=/home')])

    def test_join_checks_the_server_address(self):
        pages = FakePages({})
        for host in ('--cfg=/tmp/x', 'a b', 'x;y', ''):
            self.assertRaises(HTTPRequestError, httppages.PageServer.joinloader,
                              pages, {}, host=[host])
        self.assertRaises(HTTPRequestError, httppages.PageServer.joinloader,
                          pages, {}, host=['example.org'], port=['80x'])

    def test_host_names(self):
        for host in ('example.org', '192.168.1.5', 'my-host', '[::1]'):
            self.assertTrue(httppages.HOST_RE.match(host), host)

    def test_only_level_files_of_the_game(self):
        class Game:
            def FnListBoards():
                return [('Levels', 'levels/Levels.bin')]
            FnListBoards = staticmethod(FnListBoards)
        pages = FakePages({'file': '/tmp/anything.py'})
        pages.Game = Game
        self.assertRaises(HTTPRequestError, httppages.PageServer.startgame,
                          pages)


class OneWindow(unittest.TestCase):

    def setUp(self):
        self.launched = []
        self.addCleanup(setattr, httppages, 'schedule_launch',
                        httppages.schedule_launch)
        httppages.schedule_launch = self.launched.append
        self.addCleanup(setattr, httppages, 'client_pid', None)

    def join(self):
        pages = FakePages({})
        pages.metaserverpage = lambda headers: 'http://meta.example/?x=1'
        return httppages.PageServer.joinloader(
            pages, {}, host=['example.org'], port=['1234'], m=['1'])

    def test_second_click_opens_no_second_window(self):
        import subprocess
        # a window that writes 'raised' when asked to come to the front
        window = subprocess.Popen(
            [sys.executable, '-c',
             'import signal, sys, time\n'
             'signal.signal(signal.SIGUSR1, lambda *a: print("raised", flush=True))\n'
             'print("ready", flush=True)\n'
             'time.sleep(30)\n'], stdout=subprocess.PIPE, text=True)
        self.addCleanup(window.wait)
        self.addCleanup(window.kill)
        self.assertEqual(window.stdout.readline(), 'ready\n')
        httppages.client_pid = window.pid
        f, url = self.join()
        self.assertEqual(self.launched, [])
        self.assertIn('already+open', url)
        self.assertEqual(window.stdout.readline(), 'raised\n')
        window.stdout.close()

    def test_closed_window_is_collected(self):
        import subprocess
        window = subprocess.Popen([sys.executable, '-c', 'pass'])
        os.waitid(os.P_PID, window.pid, os.WEXITED | os.WNOWAIT)
        httppages.client_pid = window.pid
        f, url = self.join()
        self.assertEqual(len(self.launched), 1)
        self.assertIsNone(httppages.client_pid)   # no zombie left
        self.assertRaises(ChildProcessError, os.waitpid, window.pid, 0)


class ConfigFile(unittest.TestCase):

    def test_config_file_is_data_not_code(self):
        fd, name = tempfile.mkstemp()
        os.close(fd)
        self.addCleanup(os.unlink, name)
        marker = name + '.ran'
        with open(name, 'w') as f:
            f.write("__import__('os').system('touch %s')" % marker)
        pages = FakePages({})
        pages.filename = name
        self.assertEqual(httppages.PageServer.loadoptionfile(pages), {})
        self.assertFalse(os.path.exists(marker))
        with open(name, 'w') as f:
            f.write(repr({'*': {'lives': '3'}}))
        self.assertEqual(httppages.PageServer.loadoptionfile(pages),
                         {'*': {'lives': '3'}})


class TempFiles(unittest.TestCase):

    def test_private_temp_directory(self):
        import caching
        path = caching.mktemp('.wav')
        mode = stat.S_IMODE(os.stat(os.path.dirname(path)).st_mode)
        self.assertEqual(mode, 0o700)
        self.assertTrue(os.path.basename(os.path.dirname(path))
                        .startswith('bub-n-bros-'))


if __name__ == '__main__':
    unittest.main()
