from socket import *
import os, sys, time, random, re
from select import select
from io import StringIO, BytesIO
from weakref import WeakValueDictionary

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from metastruct import *
from common import httpserver, stdlog

if __name__ == '__main__':
    os.chdir(HERE)

META_SERVER_HTTP_PORT = 8050
META_SERVER_PORT = 8055
META_SERVER_UDP_PORT = 8055
# the icon shown next to each game: the bonus images made by
# ../bubbob/doc/bonus-doc.py if they exist, else the dragon of this page
IMAGE_DIR = os.path.join(HERE, os.pardir, 'bubbob', 'doc', 'images')
ICONS = [open(os.path.join(IMAGE_DIR, s), 'rb').read()
         for s in sorted(os.listdir(IMAGE_DIR)) if s.endswith('.png')] \
        if os.path.isdir(IMAGE_DIR) else []
if not ICONS:
    ICONS = [open(os.path.join(HERE, 'mbub.png'), 'rb').read()]
MAX_SERVERS = 50
MAX_CONNEXIONS = 60
MAX_BUFFER = 65536          # bytes of incomplete message kept per connection
SEND_TIMEOUT = 5.0          # a peer that does not read is dropped
IDLE_TIMEOUT = 120.0        # connections without a listed game
SWEEP_INTERVAL = 10.0       # how often mainloop() looks for idle ones
MAX_TRACEBACKS = 100        # crash report files kept
MAX_TRACEBACK_SIZE = 16384   # a real traceback is a few KB
# where crash reports go: systemd's StateDirectory=, else next to this file
TB_DIR = os.environ.get('STATE_DIRECTORY', '').split(':')[0] or HERE


serversockets = {}
connexions = {}     # socket -> Connexion, for the idle check of mainloop()

def tracebackfiles():
    try:
        return [s for s in os.listdir(TB_DIR) if s.startswith('tb-')]
    except OSError:
        return []

class MetaServer:

    def __init__(self, port=META_SERVER_PORT, udpport=META_SERVER_UDP_PORT):
        s = socket(AF_INET, SOCK_STREAM)
        s.bind(('', port))
        s.listen(5)
        self.parentsock = s
        self.ServersDict = {}
        self.ServersList = []
        serversockets[s] = self.clientconnect, sys.exit
        self.udpsock = socket(AF_INET, SOCK_DGRAM)
        self.udpsock.bind(('', udpport))
        serversockets[self.udpsock] = self.udp_message, None
        self.udpdata = []

    def detach(self):
        pid = os.fork()
        if pid:
            print(pid)
            os._exit(0)
        # in the child process
        os.setsid()
        logfile = stdlog.LogFile(limitsize=131072)
        if logfile:
            print(file=logfile)
            print("Logging to", logfile.filename)
            fd = logfile.f.fileno()
            try:
                # detach from parent
                os.dup2(fd, 1)
                os.dup2(fd, 2)
                os.dup2(fd, 0)
            except OSError:
                pass
            logfile.close()
        # record pid
        f = open('pid', 'w')
        print(os.getpid(), file=f)
        f.close()

    def clientconnect(self):
        s, addr = self.parentsock.accept()
        Connexion(s, addr)

    def publish(self, server):
        key = server.serverkey
        if key in self.ServersDict:
            current = self.ServersDict[key]
            if current is server:
                return
            self.ServersList.remove(current)
        elif len(self.ServersDict) >= MAX_SERVERS:
            raise OverflowError
        self.ServersList.append(server)
        self.ServersDict[key] = server
        print('+', key)

    def unpublish(self, server):
        key = server.serverkey
        if key in self.ServersDict:
            current = self.ServersDict[key]
            if current is server:
                del self.ServersDict[key]
                self.ServersList.remove(server)
                print('-', key)

    def makelist(self):
        items = {}
        for srv in self.ServersList:
            items[srv.serverkey] = encodedict(srv.serverinfo)
        return encodedict(items)

    def getserver(self, key):
        return self.ServersDict[key]

    def udp_message(self):
        data, addr = self.udpsock.recvfrom(32)
        self.udpdata.append((data, addr))
        if len(self.udpdata) > 50:
            del self.udpdata[0]


class Connexion(MessageSocket):

    def __init__(self, s, addr):
        MessageSocket.__init__(self, s)
        self.serverinfo = {
            'time': int(time.time()),
            'icon': random.choice(ICONS),
            'iconformat': 'png',
            }
        self.addr = addr
        self.key = '%s:%d' % addr
        self.serverkey = None
        self.lastseen = time.time()
        print('[', self.key)
        self.backlinks = WeakValueDictionary()
        if len(serversockets) >= MAX_CONNEXIONS:
            self.disconnect()
            raise OverflowError
        # sendall() must not block the whole server on a peer that does
        # not read
        s.settimeout(SEND_TIMEOUT)
        serversockets[s] = self.receive, self.disconnect
        connexions[s] = self

    def receive(self):
        self.lastseen = time.time()
        MessageSocket.receive(self)
        if len(self.buffer) > MAX_BUFFER:
            raise OverflowError('message too long')

    def disconnect(self):
        metaserver.unpublish(self)
        try:
            del serversockets[self.s]
        except KeyError:
            pass
        connexions.pop(self.s, None)
        try:
            self.s.close()
        except error:
            pass
        print(']', self.key)

    def msg_serverinfo(self, info, *rest):
        print('|', self.key)
        if len(info) > 15000:
            raise OverflowError
        info = decodedict(info)
        # replace the previous description, do not add to it
        self.serverinfo = dict((k, self.serverinfo[k])
                               for k in ('time', 'icon', 'iconformat'))
        self.serverinfo.update(info)

    def msg_startserver(self, port, *rest):
        serverkey = '%s:%d' % (self.addr[0], port)
        if self.serverkey and self.serverkey != serverkey:
            metaserver.unpublish(self)
        self.serverkey = serverkey
        metaserver.publish(self)

    def msg_stopserver(self, *rest):
        metaserver.unpublish(self)

    def msg_list(self, *rest):
        self.s.sendall(message(RMSG_LIST, metaserver.makelist()))

    def msg_route(self, targetkey, *rest):
        key = targetkey.decode('utf-8', 'replace')
        try:
            target = metaserver.getserver(key)
        except KeyError:
            try:
                target = self.backlinks[key]
            except KeyError:
                self.s.sendall(message(RMSG_NO_HOST, targetkey))
                return
        target.route(self, *rest)

    def route(self, origin, msgcode, *rest):
        self.backlinks[origin.key] = origin
        try:
            self.s.sendall(message(msgcode, origin.key.encode('utf-8'), *rest))
        except error:
            # this peer does not read: drop it, not the one that wrote
            drop(self.s, self.disconnect)

    def msg_traceback(self, tb, *rest):
        name = os.path.join(TB_DIR, 'tb-%s.log' % (self.addr[0],))
        if not os.path.exists(name) and len(tracebackfiles()) >= MAX_TRACEBACKS:
            return
        f = stdlog.LogFile(name)
        if f:
            print(tb[:MAX_TRACEBACK_SIZE].decode('utf-8', 'replace'), file=f)
            f.close()

    def msg_udp_addr(self, pattern, *rest):
        for data, addr in metaserver.udpdata:
            if data == pattern:
                try:
                    host, port = addr
                    port = int(port)
                except ValueError:
                    continue
                self.s.sendall(message(RMSG_UDP_ADDR, host.encode('ascii'), port))
                return
        else:
            self.s.sendall(message(RMSG_UDP_ADDR))

    MESSAGES = {
        MMSG_INFO:  msg_serverinfo,
        MMSG_START: msg_startserver,
        MMSG_STOP:  msg_stopserver,
        MMSG_LIST:  msg_list,
        MMSG_ROUTE: msg_route,
        MMSG_TRACEBACK: msg_traceback,
        MMSG_UDP_ADDR:  msg_udp_addr,
        }


# ____________________________________________________________

import html.entities
text_to_html = {}
for key, value in list(html.entities.entitydefs.items()):
    text_to_html[value] = '&' + key + ';'
for i in range(32):
    text_to_html[chr(i)] = '?'
def htmlquote(s, getter=text_to_html.get):
    lst = [getter(c, c) for c in s if ' ' <= c < '\x7F']
    return ''.join(lst)
def txtfilter(s, maxlen=200):
    s = str(s)[:maxlen]
    l = [c for c in s if c in "!$*,-.0123456789:@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                              "^_`abcdefghijklmnopqrstuvwxyz{|}"]
    return ''.join(l)

f = open(os.path.join(HERE, 'index.html'), 'r')
HEADER, ROW, FOOTER = f.read().split('\\')
f.close()

def safe_join(join):
    """The 'join' address of the player's own game page, host:port/seed,
    or None if it has anything else in it."""
    if re.match(r'[A-Za-z0-9.:\[\]-]+/[A-Za-z0-9]+$', join or ''):
        return join
    return None

def httpport_of(info):
    try:
        return int(info.get('httpport'))
    except (TypeError, ValueError):
        return None

def makehosthtml(srv, bottommsg, join):
    info = srv.serverinfo
    hostname, port = srv.serverkey.split(':')
    # the IP address, as given by the connection: a reverse DNS lookup
    # here would block the whole server for each row
    fullhostname = hostname
    url = None
    if join:
        url = "http://%s/join.html?host=%s&port=%s&httpport=%s&m=%s" % (
            join, hostname, port, httpport_of(info) or 'off',
            time.time())
    else:
        httpport = httpport_of(info)
        if httpport is not None:
            url = "http://%s:%s/" % (hostname, httpport)
            javamsg = """
<p>Click on a server above to join the game.  This only works if:
<ul><li>your browser understands Java;
    <li>the server is not behind a firewall;
    <li>you don't mind not hearing the nice background music.
</ul></p>
<p>Alternatively, install the
<a href="http://bub-n-bros.sourceforge.net/download.html">Python version</a>
of the client, which can cope with all of the above problems.</p>
<br>"""
            if javamsg not in bottommsg:
                bottommsg.append(javamsg)
    result = '<strong>%s</strong>:%s' % (fullhostname, port)
    if url:
        result = '<a href="%s">%s</a>' % (url, result)
    return result

def indexloader(headers, join=[], head=[], **options):
    join = safe_join(join and join[0])
    data = [HEADER % htmlquote(head and head[0] or '')]
    bottommsg = []
    if metaserver.ServersList:
        counter = 0
        for srv in metaserver.ServersList:
            info = srv.serverinfo
            icon = '<img src="ico?key=%s">' % srv.serverkey
            bgcolor = ('#C0D0D0', '#E0D0A8')[counter&1]
            hosthtml = makehosthtml(srv, bottommsg, join)
            desc = htmlquote(totext(info.get('desc', ''))) or ''
            extradesc = htmlquote(totext(info.get('extradesc', ''))) or ''
            if isinstance(info.get('time'), int):
                stime = time.strftime('%a %b %d<br>%H:%M GMT',
                                      time.gmtime(info['time']))
            else:
                stime = ''
            data.append(ROW % locals())
            counter += 1
    else:
        data.append('''<tr><td bgcolor="#FFFFFF">
            Sorry, there is no registered server at the moment.
        </td></tr>''')
    if join:
        extrafooter = '''<p><img src="home.png">
        <a href="http://%s/?time=%s">Back to local games</a></p>''' % (
            join, time.time())
    else:
        extrafooter = ''
    bottommsg = '\n'.join(bottommsg)
    tbfiles = tracebackfiles()
    if tbfiles:
        tbfiles = len(tbfiles)
    else:
        tbfiles = ''
    data.append(FOOTER % locals())
    return StringIO(''.join(data)), 'text/html'

def icoloader(key, **options):
    srv = metaserver.getserver(key[0])
    iconformat = txtfilter(totext(srv.serverinfo['iconformat']), 32)
    return BytesIO(srv.serverinfo['icon']), 'image/' + iconformat

httpserver.register('', indexloader)
httpserver.register('index.html', indexloader)
httpserver.register('bub-n-bros.html', indexloader)
httpserver.register('ico', icoloader)
httpserver.register('mbub.png', httpserver.fileloader(os.path.join(HERE, 'mbub.png'), 'image/png'))
httpserver.register('home.png', httpserver.fileloader(os.path.join(HERE, 'home.png'), 'image/png'))

def openhttpsocket(port = META_SERVER_HTTP_PORT):
    from http.server import HTTPServer
    class ServerClass(HTTPServer):
        def get_request(self):
            sock, addr = self.socket.accept()
            sock.settimeout(5.0)
            return sock, addr
    HandlerClass = httpserver.MiniHandler
    server_address = ('', port)
    httpd = ServerClass(server_address, HandlerClass)
    s = httpd.socket
    serversockets[s] = httpd.handle_request, None


# ____________________________________________________________

def drop(s, close):
    """Close a connection that failed: a malformed message, a peer that
    does not read, too much data.  Leaving it open kept one of the
    MAX_CONNEXIONS slots, and its buffer, forever."""
    if close is not None:
        try:
            close()
        except Exception:
            pass
    serversockets.pop(s, None)
    connexions.pop(s, None)
    try:
        s.close()
    except error:
        pass

def mainloop():
    while 1:
        iwtd = list(serversockets.keys())
        iwtd, owtd, ewtd = select(iwtd, [], iwtd, SWEEP_INTERVAL)
        #print iwtd, owtd, ewtd, serversockets
        for s in iwtd:
            if s in serversockets:
                input, close = serversockets[s]
                try:
                    input()
                except Exception as e:
                    print('dropping a connection: %s: %s' % (
                        e.__class__.__name__, e), file=sys.stderr)
                    if s in connexions:      # not the listening sockets
                        drop(s, close)
        # connections that never listed a game and say nothing
        now = time.time()
        for s, c in list(connexions.items()):
            if c.serverkey is None and now - c.lastseen > IDLE_TIMEOUT:
                drop(s, c.disconnect)
        for s in ewtd:
            if s in serversockets:
                input, close = serversockets[s]
                try:
                    close()
                except:
                    import traceback
                    print("-"*60)
                    traceback.print_exc()
                    print("-"*60)


USAGE = '''usage: metaserver.py [-f] [--port N] [--http N] [--udp N]
  -f          detach (run in the background)
  --port N    TCP port for game servers and clients (default %d)
  --http N    port of the web page listing the games (default %d)
  --udp N     UDP port (default: the TCP port)
Clients find it with BUBBROS_METASERVER=host:port:httpport or the Options
page of the game.''' % (META_SERVER_PORT, META_SERVER_HTTP_PORT)

def parse_args(argv):
    import getopt
    try:
        opts, args = getopt.getopt(argv, 'fh', ['port=', 'http=', 'udp=', 'help'])
    except getopt.GetoptError as e:
        sys.exit('metaserver.py: %s\n%s' % (e, USAGE))
    if args:
        sys.exit(USAGE)
    result = {'detach': False, 'port': META_SERVER_PORT,
              'http': META_SERVER_HTTP_PORT, 'udp': None}
    for key, value in opts:
        if key == '-f':
            result['detach'] = True
        elif key in ('-h', '--help'):
            print(USAGE)
            sys.exit(0)
        else:
            result[key[2:]] = int(value)
    if result['udp'] is None:
        result['udp'] = result['port']
    return result

if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    metaserver = MetaServer(args['port'], args['udp'])
    if args['detach']:
        metaserver.detach()
    try:
        openhttpsocket(args['http'])
        print('listening to client port tcp %d / http %d / udp %d.' % (
            args['port'], args['http'], args['udp']))
        sys.stdout.flush()
        mainloop()
    finally:
        if metaserver.ServersList:
            print('*** servers still connected, waiting 5 seconds')
            time.sleep(5)
        print('*** leaving at', time.ctime())
