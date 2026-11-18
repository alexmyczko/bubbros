"""The HTTP server of a game: the web client of the game (the Java
applet) is for everybody, the rest (the control
page) only for the computer the game runs on."""

import http.client
import importlib
import os
import sys
import threading
import unittest
from http.server import HTTPServer
from io import StringIO

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common')]

import httpserver


class SavedPages(unittest.TestCase):

    def setUp(self):
        saved = dict(httpserver.pathloaders), dict(httpserver.publicpaths)
        def restore():
            httpserver.pathloaders.clear()
            httpserver.pathloaders.update(saved[0])
            httpserver.publicpaths.clear()
            httpserver.publicpaths.update(saved[1])
        self.addCleanup(restore)
        httpserver.pathloaders.clear()
        httpserver.publicpaths.clear()


class Access(SavedPages):

    def setUp(self):
        SavedPages.setUp(self)
        self.seen = []
        def loader(headers, **options):
            self.seen.append(headers.get('X-Local-Request'))
            return StringIO('page'), 'text/plain'
        httpserver.register('', loader, public=True)
        httpserver.register('client/', loader, public=True)
        httpserver.register('0xsecret/', loader)
        httpserver.register('0xsecret/run.html', loader)

        class Quiet(httpserver.MiniHandler):
            def log_message(self, *args):
                pass
        self.httpd = HTTPServer(('127.0.0.1', 0), Quiet)
        self.addCleanup(self.httpd.server_close)
        thread = threading.Thread(target=self.httpd.serve_forever,
                                  kwargs={'poll_interval': 0.01})
        thread.daemon = True
        thread.start()
        self.addCleanup(self.httpd.shutdown)

    def get(self, path, host=None):
        # A request with a foreign Host header stands for the other
        # computers: is_local_request() refuses both, see
        # test_control_page.py.
        port = self.httpd.server_address[1]
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        self.addCleanup(conn.close)
        conn.putrequest('GET', path, skip_host=True)
        conn.putheader('Host', host or '127.0.0.1:%d' % port)
        conn.endheaders()
        response = conn.getresponse()
        response.read()
        return response.status

    def test_this_computer_gets_everything(self):
        for path in ('/', '/client/', '/0xsecret/', '/0xsecret/run.html'):
            self.assertEqual(self.get(path), 200, path)
        self.assertEqual(self.get('/nothing'), 404)
        self.assertEqual(self.get('/0xsecret'), 302)

    def test_others_only_get_the_public_pages(self):
        other = 'game.example:8000'
        self.assertEqual(self.get('/', other), 200)
        self.assertEqual(self.get('/client/', other), 200)
        self.assertEqual(self.get('/client', other), 302)
        self.assertEqual(self.get('/0xsecret/', other), 403)
        self.assertEqual(self.get('/0xsecret/run.html', other), 403)

    def test_others_cannot_tell_which_pages_exist(self):
        # same answer as for a page that is not there, and no redirect
        # to a page that is not public
        other = 'game.example:8000'
        self.assertEqual(self.get('/0xsecret', other), 403)
        self.assertEqual(self.get('/nothing', other), 403)

    def test_public_pages_know_who_asks(self):
        self.get('/')
        self.get('/', 'game.example:8000')
        self.assertEqual(self.seen, ['yes', 'no'])

    def test_header_cannot_be_forged(self):
        port = self.httpd.server_address[1]
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        self.addCleanup(conn.close)
        conn.request('GET', '/', headers={'Host': 'game.example',
                                          'X-Local-Request': 'yes'})
        conn.getresponse().read()
        self.assertEqual(self.seen, ['no'])

    def test_pages_are_local_unless_said_otherwise(self):
        loader = httpserver.pathloaders['client/']
        httpserver.register('new.html', loader)
        self.assertFalse(httpserver.is_public('new.html'))
        self.assertEqual(self.get('/new.html', 'game.example'), 403)
        # registering again decides again
        httpserver.register('client/', loader)
        self.assertEqual(self.get('/client/', 'game.example'), 403)
        httpserver.register('new.html', loader, public=True)
        self.assertEqual(self.get('/new.html', 'game.example'), 200)

    def test_meta_server_pages_are_public(self):
        # (it has its own copy of the module, common.httpserver)
        ms = importlib.import_module('metaserver.metaserver')
        for path in ('', 'index.html', 'bub-n-bros.html', 'ico', 'mbub.png',
                     'home.png'):
            self.assertTrue(ms.httpserver.is_public(path), path)

    def test_control_page_is_local(self):
        sys.path.insert(0, os.path.join(ROOT, 'http2'))
        self.addCleanup(sys.path.remove, os.path.join(ROOT, 'http2'))
        import httppages
        pages = httppages.PageServer(None)
        pages.registerpages()
        registered = [path for path in httpserver.pathloaders
                      if path.startswith(pages.seed.lower() + '/')]
        self.assertIn(pages.seed.lower() + '/run.html', registered)
        for path in registered:
            self.assertFalse(httpserver.is_public(path), path)
        url = '/%s/' % pages.seed
        self.assertEqual(self.get(url), 200)
        self.assertEqual(self.get(url, 'game.example:8000'), 403)


class JavaApplet(SavedPages):

    def load_javaserver(self):
        saved = sys.modules.pop('javaserver', None)
        def restore():
            if saved is None:
                sys.modules.pop('javaserver', None)
            else:
                sys.modules['javaserver'] = saved
        self.addCleanup(restore)
        return importlib.import_module('javaserver')

    def test_applet_is_public(self):
        javaserver = self.load_javaserver()
        self.assertIs(httpserver.pathloaders[''], javaserver.indexloader)
        for path in ('', 'index.html', 'name.html', 'pclient.class',
                     'sample.wav'):
            self.assertTrue(httpserver.is_public(path), path)



if __name__ == '__main__':
    unittest.main()
