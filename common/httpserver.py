

import http.server
from http.server import SimpleHTTPRequestHandler
import urllib.parse, html.entities
import sys, os, time
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

def canonicalpath(url):
    if url.startswith('/'):
        url = url[1:]
    return url.lower()

def register(url, loader):
    pathloaders[canonicalpath(url)] = loader

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
    return loader

class HTTPRequestError(Exception):
    pass

class MiniHandler(SimpleHTTPRequestHandler):
    # a connection that sends nothing must not hang the single-threaded
    # server (the game loop, or the meta-server) for ever
    timeout = 10

    def send_head(self, query=''):
        addr, host, path, query1, fragment = urllib.parse.urlsplit(self.path)
        path = canonicalpath(path)
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
            f, ctype = loader(headers=hdr, **kwds)
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
        # but the socket only takes bytes.
        while True:
            data = source.read(16384)
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
        while actions_when_finished:
            actions_when_finished.pop(0)()

actions_when_finished = []

def my_host():
    import gamesrv
    port = gamesrv.socketports[gamesrv.openhttpsocket()]
    return '127.0.0.1:%d' % port
