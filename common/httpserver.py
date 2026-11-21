

import http.server
from http.server import SimpleHTTPRequestHandler
import urllib.parse, html.entities
import sys, os, time, threading, queue, socket, socketserver
from io import StringIO


class Translator:
    """For use with format strings.
    
    'formatstring % translator' will evaluate all %(xxx)s expressions
    found in the format string in the given globals/locals.

    Multiline expressions are assumed to be one or several complete
    statements; they are executed and whatever they print is inserted back
    into the format string."""
    
    def __init__(self, globals, locals):
        self.globals = globals
        self.locals = locals
    
    def __getitem__(self, expr):
        if '\n' in expr:
            if not expr.endswith('\n'):
                expr += '\n'
            prevstdout = sys.stdout
            try:
                sys.stdout = f = StringIO()
                exec(expr, self.globals, self.locals)
            finally:
                sys.stdout = prevstdout
            return f.getvalue()
        else:
            return eval(expr, self.globals, self.locals)

class TranslatorIO:
    "Lazy version of Translator."
    
    def __init__(self, fmt, d):
        self.gen = self.generate(fmt, d)
        
    def read(self, ignored=None):
        for text in self.gen:
            if text:
                return text
        return ''

    def close(self):
        self.gen = ()

    def generate(self, fmt, d):
        t = Translator(d, d)
        for data in fmt.split('\x0c'):
            yield data % t


# HTML quoting

text_to_html = {}
for key, value in list(html.entities.entitydefs.items()):
    text_to_html[value] = '&' + key + ';'

def htmlquote(s):
    return ''.join([text_to_html.get(c, c) for c in s])


# HTTP Request Handler

pathloaders = {}
publicpaths = {}

def canonicalpath(url):
    if url.startswith('/'):
        url = url[1:]
    return url.lower()

def register(url, loader, public=False):
    # A page is served to this computer only, unless it is registered
    # as 'public': then it is served to everybody.  See MiniHandler.
    url = canonicalpath(url)
    pathloaders[url] = loader
    if public:
        publicpaths[url] = True
    else:
        publicpaths.pop(url, None)

def is_public(url):
    return canonicalpath(url) in publicpaths

def is_registered(url):
    return canonicalpath(url) in pathloaders

def load(filename, mimetype=None, locals=None):
    if mimetype and mimetype.startswith('text/'):
        mode = 'r'
    else:
        mode = 'rb'
    f = open(filename, mode)
    if locals is not None:
        data = f.read()
        f.close()
        #data = data.replace('%"', '%%"')
        d = globals().copy()
        d.update(locals)
        f = TranslatorIO(data, d)
    return f, mimetype

def fileloader(filename, mimetype=None):
    def loader(**options):
        return load(filename, mimetype)
    loader.static = True        # only sends the file: not in the main loop
    return loader

class HTTPRequestError(Exception):
    pass

# Who may see a page is decided when it is registered, see register().
# The control page of the game is only for the player at this computer:
# a web page from elsewhere, open in the same browser, could otherwise
# send requests to it, even read the answers with DNS rebinding.  The
# web client of the game (the Java applet) and the pages of the
# meta-server are public.
LOCAL_HOSTS = ('127.0.0.1', 'localhost', '[::1]')

def is_local_request(client_address, headers):
    if client_address[0] not in ('127.0.0.1', '::1'):
        return False
    host = (headers.get('host') or '').lower()
    if host.startswith('['):
        name = host[:host.find(']') + 1]
    else:
        name = host.split(':')[0]
    return name in LOCAL_HOSTS

class MiniHandler(SimpleHTTPRequestHandler):
    # a connection that sends nothing must not keep its thread for ever
    timeout = 10

    def send_head(self, query=''):
        addr, host, path, query1, fragment = urllib.parse.urlsplit(self.path)
        path = canonicalpath(path)
        local = is_local_request(self.client_address, self.headers)
        if not local:
            # For the others, everything that is not public is
            # forbidden, whether there is such a page or not: the
            # answer does not tell which local pages exist.
            if path not in publicpaths:
                if path + '/' in publicpaths:
                    return self.redirect(path + '/')
                self.send_error(403)
                return None
        if path not in pathloaders:
            if path + '/' in pathloaders:
                return self.redirect(path + '/')
            self.send_error(404)
            return None
        kwds = {}
        for q in [query1, query]:
            if q:
                if isinstance(q, bytes):     # the body of a POST
                    q = q.decode('utf-8', 'replace')
                kwds.update(urllib.parse.parse_qs(q))
        loader = pathloaders[path]
        try:
            hdr = self.headers
            # Pass the client address to the loaders with the headers.
            # Python 3 rejects the old name 'remote host' (a space is not
            # valid in a header name, which is also why a client could not
            # forge it). Drop any X-Remote-Host the client sent, so the
            # value is always ours.
            del hdr['X-Remote-Host']
            hdr['X-Remote-Host'] = self.client_address[0]
            # for the public pages: does the request come from this
            # computer?  (also ours, same as above)
            del hdr['X-Local-Request']
            hdr['X-Local-Request'] = local and 'yes' or 'no'
            if getattr(loader, 'static', False):
                f, ctype = loader(headers=hdr, **kwds)
            else:
                f, ctype = self.in_loop(lambda: loader(headers=hdr, **kwds))
        except IOError as e:
            self.send_error(404, "I/O error: " + str(e))
            return None
        except HTTPRequestError as e:
            self.send_error(500, str(e))
            return None
        except Exception:
            # the details go to the log, not to whoever made the request
            import traceback
            traceback.print_exc()
            self.send_error(500)
            return None
        if ctype is None:
            ctype = self.guess_type(self.translate_path(self.path))
        elif f is None:
            return self.redirect(ctype)
        
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.end_headers()
        return f

    def redirect(self, url):
        self.send_response(302)
        self.send_header("Content-type", 'text/html')
        self.send_header("Location", url)
        self.end_headers()
        return StringIO('''<html><head></head><body>
Please <a href="%s">click here</a> to continue.
</body></html>
''' % url)

    def do_POST(self):
        try:
            nbytes = int(self.headers.get('content-length'))
        except:
            nbytes = 0
        query = self.rfile.read(nbytes).strip()
        f = self.send_head(query)
        if f:
            self.copyfile(f, self.wfile)
            f.close()

    def parse_request(self):
        if self.raw_requestline == b'':
            return False
        else:
            return SimpleHTTPRequestHandler.parse_request(self)

    def copyfile(self, source, outputfile):
        # The loaders return text (templates, StringIO) or binary files,
        # but the socket only takes bytes.  A template runs its code part
        # by part as it is read: in the main loop, like the loader.
        if isinstance(source, TranslatorIO):
            read = lambda size: self.in_loop(lambda: source.read(size))
        else:
            read = source.read
        while True:
            data = read(16384)
            if not data:
                break
            if isinstance(data, str):
                data = data.encode('utf-8')
            outputfile.write(data)

    def address_string(self):
        """Override to avoid DNS lookups"""
        return "%s:%d" % self.client_address

    def finish(self):
        SimpleHTTPRequestHandler.finish(self)
        self.connection.close()
        self.in_loop(run_actions_when_finished)

    def in_loop(self, fn):
        caller = getattr(self.server, 'loop_caller', None)
        if caller is None:
            return fn()
        return caller.call(fn)

actions_when_finished = []

def run_actions_when_finished():
    while actions_when_finished:
        actions_when_finished.pop(0)()

# ____________________________________________________________
# The HTTP server runs in threads of its own (see serve_in_threads()), so
# that a slow or idle browser does not hold up the game or the
# meta-server; the page loaders still run in the main loop, which owns
# the state that they read and change, except the ones that only send a
# file (see fileloader()).

class LoopCaller:
    """Runs functions for other threads in a select() loop: the loop
    selects 'wakesock' for reading, and then calls run_pending()."""

    def __init__(self):
        self.wakesock, self.waker = socket.socketpair()
        self.wakesock.setblocking(False)
        self.pending = queue.Queue()
        self.loop_thread = threading.current_thread()

    def call(self, fn):
        if threading.current_thread() is self.loop_thread:
            return fn()
        done = threading.Event()
        result = []
        self.pending.put((fn, done, result))
        try:
            self.waker.send(b'x')
        except OSError:
            pass
        done.wait()
        ok, value = result[0]
        if ok:
            return value
        raise value

    def run_pending(self):
        try:
            while self.wakesock.recv(4096):
                pass
        except OSError:
            pass
        while True:
            try:
                fn, done, result = self.pending.get_nowait()
            except queue.Empty:
                return
            try:
                result.append((True, fn()))
            except BaseException as e:
                result.append((False, e))
            done.set()

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    MAX_THREADS = 128

    def process_request(self, request, client_address):
        if threading.active_count() > self.MAX_THREADS:
            self.shutdown_request(request)       # too many connections
        else:
            socketserver.ThreadingMixIn.process_request(
                self, request, client_address)

def serve_in_threads(httpd):
    """Serve 'httpd' (a ThreadedServer) from now on, with the page
    loaders in the calling thread's loop: it must select the returned
    LoopCaller's wakesock, and call its run_pending()."""
    httpd.loop_caller = LoopCaller()
    t = threading.Thread(target=httpd.serve_forever, name='HTTP server')
    t.daemon = True
    t.start()
    return httpd.loop_caller

def my_host():
    import gamesrv
    port = gamesrv.socketports[gamesrv.openhttpsocket()]
    return '127.0.0.1:%d' % port
