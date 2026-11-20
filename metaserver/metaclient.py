import sys, os, time, random, ast
from select import select
from socket import *
from metastruct import *

VERSION_TAG = 1601

# The meta-server keeps the list of Internet games.  The public one,
# ctpug.org.za, no longer runs, so there is no default: set one with the
# environment variable below or on the Options page ("metaserver" in the
# configuration file), as HOST, HOST:PORT or HOST:PORT:HTTPPORT.
ENVIRON_VAR = 'BUBBROS_METASERVER'
DEFAULT_PORT = 8055         # TCP and UDP
DEFAULT_HTTP_PORT = 8050    # the page listing the games
DEFAULT_ADDRESS = 'bubble.aiei.ch'    # public list run by Alex Myczko
CONNECT_TIMEOUT = 3.0
NOT_SET = ('no meta-server is set (environment variable %s, or the '
           'Options page)' % ENVIRON_VAR)

def parse_address(text):
    """'host[:port[:httpport]]' -> (host, port, httpport); ValueError if
    malformed, None if empty."""
    text = (text or '').strip()
    if not text:
        return None
    parts = text.split(':')
    if len(parts) > 3 or not parts[0]:
        raise ValueError('bad meta-server address %r' % (text,))
    try:
        port = int(parts[1]) if len(parts) > 1 and parts[1] else DEFAULT_PORT
        httpport = (int(parts[2]) if len(parts) > 2 and parts[2]
                    else DEFAULT_HTTP_PORT)
    except ValueError:
        raise ValueError('bad meta-server address %r' % (text,))
    return parts[0], port, httpport

def configured_address():
    """The text of the meta-server setting, environment first, then the
    configuration file of the web page (local options of this host), then
    DEFAULT_ADDRESS.  An empty setting means none."""
    text = os.environ.get(ENVIRON_VAR)
    if text is not None:
        return text
    try:
        from common import configfile
    except ImportError:
        import configfile
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
    try:
        with open(configfile.path(root)) as f:
            data = ast.literal_eval(f.read().strip() or '{}')
    except (OSError, SyntaxError, ValueError):
        data = {}
    text = data.get(gethostname(), {}).get('metaserver')
    if text is None:
        return DEFAULT_ADDRESS
    return text

def address():
    """(host, port, httpport) of the meta-server, or None if none is set
    or the setting cannot be read (a message is printed then)."""
    text = configured_address()
    try:
        return parse_address(text)
    except ValueError as e:
        print('*** %s' % e, file=sys.stderr)
        return None

def list_url(addr):
    return 'http://%s:%d/bub-n-bros.html' % (addr[0], addr[2])

def connect(failure=[], addr=None):
    if len(failure) >= 2:
        return None
    if addr is None:
        addr = address()
    if addr is None:
        print('*** %s' % NOT_SET, file=sys.stderr)
        return None
    print('Connecting to the meta-server %s:%d...' % addr[:2], file=sys.stderr)
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(CONNECT_TIMEOUT)
        s.connect(addr[:2])
        s.settimeout(None)
    except error as e:
        print('*** cannot contact meta-server %s:%d: %s' % (addr[:2] + (e,)),
              file=sys.stderr)
        failure.append(e)
        return None
    else:
        print('connected.', file=sys.stderr)
    return s

def reachable(addr):
    """None if the meta-server at addr accepts a connection, else the
    reason, as text."""
    try:
        s = create_connection(addr[:2], CONNECT_TIMEOUT)
    except (error, OSError) as e:
        return str(e) or e.__class__.__name__
    s.close()
    return None

# Python 2 tuned thread switching with sys.setcheckinterval(): 4096
# bytecodes normally (the game loop runs undisturbed), 64 while the
# helper threads of a connection handshake must answer quickly.  Python 3
# switches threads by time instead; the default (5 ms) plays the role
# of the normal setting and 0.5 ms that of the fast one.
def set_fast_thread_switching(fast):
    sys.setswitchinterval(0.0005 if fast else 0.005)

set_fast_thread_switching(False)


def float2str(f):
    # don't trust locale issues and write a string with a '.'
    s = str(int(f*1000000.0))
    return s[:-6] + '.' + s[-6:]

def str2float(s):
    try:
        return float(s)
    except:
        # locale issues may prevent float() from decoding the string
        s = s.strip()
        try:
            i = s.index('.')
        except ValueError:
            try:
                i = s.index(',')
            except ValueError:
                i = len(s)
        frac = s[i+1:]
        return float(s[:i] or '0') + float(frac or '0')/(10**len(frac))


# ____________________________________________________________
# Game Servers

class MetaClientSrv(MessageSocket):
    """A game server's connection to the meta-server.  Registrar reads
    it and sends on it, in a thread of its own."""

    def __init__(self, s, game):
        MessageSocket.__init__(self, s)
        self.game = game
        self.lastwakeup = None
        self.synsockets = {}
        self.closed = 0

    def close(self):
        if not self.closed:
            self.disconnect()
        try:
            self.s.close()
        except error:
            pass

    def disconnect(self):
        self.closed = 1
        print('disconnected from the meta-server', file=sys.stderr)

    def msg_wakeup(self, origin, *rest):
        if self.lastwakeup is None or time.time()-self.lastwakeup > 4.0:
            def fastresponses(wakeup):
                set_fast_thread_switching(True)
                time.sleep(12.01)
                if self.lastwakeup == wakeup:
                    set_fast_thread_switching(False)
                    self.synsockets.clear()
            import _thread
            self.lastwakeup = time.time()
            _thread.start_new_thread(fastresponses, (self.lastwakeup,))

    def msg_connect(self, origin, port, *rest):
        def connect(origin, port):
            host, _ = origin.decode('ascii').split(':')
            addr = host, port
            s = socket(AF_INET, SOCK_STREAM)
            print('backconnecting to', addr, file=sys.stderr)
            try:
                s.connect(addr)
            except error as e:
                print('backconnecting:', str(e), file=sys.stderr)
            else:
                self.game.newclient_threadsafe(s, addr)
        import _thread
        _thread.start_new_thread(connect, (origin, port))

    def msg_udp_conn(self, origin, secret, port, *rest):
        # older clients: they only wait for us (see msg_punch)
        host, _ = origin.decode('ascii').split(':')
        import _thread
        _thread.start_new_thread(self.udp_accept, ((host, port), secret, 5))

    def msg_punch_probe(self, nonce, udpport, *rest):
        # a client asked the meta-server to introduce us: show it the
        # address of our game port from outside
        endpoint = getattr(self.game, 'udp_endpoint', lambda: None)()
        if endpoint is not None:
            try:
                endpoint.sendto(nonce, (self.s.getpeername()[0], udpport))
            except error:
                pass

    def msg_punch(self, origin, host, port, secret, *rest):
        # the meta-server introduced us to a client: both send to each
        # other, until each NAT lets in what comes from the other
        addr = host.decode('ascii'), port
        import _thread
        _thread.start_new_thread(self.udp_accept, (addr, secret, 12))

    def udp_accept(self, addr, secret, tries):
        # through the game's UDP port if it has one: then the client's
        # NAT only needs to let in what comes from there
        endpoint = getattr(self.game, 'udp_endpoint', lambda: None)()
        if endpoint is not None:
            s = endpoint.open_peer(addr)
        else:
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(addr)
        print('udp connecting to', addr, file=sys.stderr)
        mysecret = random.randrange(0, 65536)
        packet = b'B' + bytes([  secret & 0xFF,   secret >> 8,
                               mysecret & 0xFF, mysecret >> 8])
        from socketoverudp import SocketOverUdp
        from socketoverudp import SOU_RANGE_START, SOU_RANGE_STOP
        for i in range(tries):
            #print 'sending', repr(packet)
            s.send(packet)
            iwtd, owtd, ewtd = select([s], [], [], 0.25)
            if s in iwtd:
                #print 'reading'
                try:
                    inbuf = s.recv(SocketOverUdp.PACKETSIZE)
                except error:
                    inbuf = b''
                    # try again?
                    iwtd, owtd, ewtd = select([s], [], [], 0.35)
                    if s in iwtd:
                        try:
                            inbuf = s.recv(SocketOverUdp.PACKETSIZE)
                        except error:
                            pass
                #print 'got', repr(inbuf)
                if (inbuf and
                    SOU_RANGE_START <= inbuf[0] < SOU_RANGE_STOP):
                    break
        else:
            print('udp connecting: no answer, giving up', file=sys.stderr)
            s.close()
            return
        sock = SocketOverUdp(s, (mysecret, secret))
        data = sock._decode(inbuf)
        #print 'decoded as', repr(data)
        expected = b'[bnb c->s]' + packet[3:5]
        while len(data) < len(expected) + 2:
            #print 'waiting for more'
            iwtd, owtd, ewtd = select([sock], [], [], 5.0)
            if sock not in iwtd:
                print('udp connecting: timed out', file=sys.stderr)
                sock.close()
                return
            #print 'decoding more'
            data += sock.recv()
            #print 'now data is', repr(data)
        if data[:-2] != expected:
            print('udp connecting: bad data', file=sys.stderr)
            sock.close()
            return
        sock.sendall(b'[bnb s->c]' + data[-2:])
        sock.flush()
        #print 'waiting for the last dot...'
        while 1:
            iwtd, owtd, ewtd = select([sock], [], [], 5.0)
            if sock not in iwtd:
                print('udp connecting: timed out', file=sys.stderr)
                sock.close()
                return
            data = sock.recv(200)
            if data:
                break
        if data != b'^':
            print('udp connecting: bad data', file=sys.stderr)
            sock.close()
            return
        #print 'done!'
        self.game.newclient_threadsafe(sock, addr)

    def msg_ping(self, origin, *rest):
        # ping time1  -->  pong time2 time1
        self.s.sendall(message(MMSG_ROUTE, origin,
                               RMSG_PONG, float2str(time.time()).encode('ascii'),
                               *rest))

    def msg_sync(self, origin, clientport, time3, time2, time1, *rest):
        time4 = time.time()
        s = socket(AF_INET, SOCK_STREAM)
        s.bind(('', INADDR_ANY))
        _, serverport = s.getsockname()
        self.s.sendall(message(MMSG_ROUTE, origin,
                               RMSG_CONNECT, serverport, clientport))
        #print 'times:', time1, time2, time3, time4
        doubleping = (str2float(time3)-str2float(time1)) + (time4-str2float(time2))
        connecttime = time4 + doubleping / 4.0
        def connect(origin, port, connecttime, s):
            host, _ = origin.decode('ascii').split(':')
            addr = host, port
            delay = connecttime - time.time()
            #print 'sleep(%r)' % delay
            if 0.0 <= delay <= 10.0:
                time.sleep(delay)
            print('synconnecting to', addr, file=sys.stderr)
            try:
                s.connect(addr)
            except error as e:
                print('synconnecting:', str(e), file=sys.stderr)
            else:
                self.game.newclient_threadsafe(s, addr)
        import _thread
        _thread.start_new_thread(connect, (origin, clientport, connecttime, s))

    MESSAGES = {
        RMSG_CONNECT: msg_connect,
        RMSG_WAKEUP:  msg_wakeup,
        RMSG_PING:    msg_ping,
        RMSG_SYNC:    msg_sync,
        RMSG_UDP_CONN:msg_udp_conn,
        RMSG_PUNCH_PROBE: msg_punch_probe,
        RMSG_PUNCH:   msg_punch,
        }

RETRY_DELAY = 60.0      # seconds between attempts to reach the meta-server

class Registrar:
    """A game server's listing on the meta-server, kept up by a thread of
    its own: the game never waits for the meta-server, and when it cannot
    be reached, or the connection is lost, the thread tries again."""

    def __init__(self, game):
        import threading
        self.game = game
        self.lock = threading.Lock()
        self.listing = None     # the latest MMSG_INFO + MMSG_START
        self.listing_sent = False
        self.outbox = []        # other messages to send
        self.stopped = False
        self.wake_r, self.wake_w = socketpair()
        threading.Thread(target=self.run, daemon=True).start()

    # ---- in the game's thread ----

    def update(self, listing):
        with self.lock:
            self.listing = listing
            self.listing_sent = False
        self.wakeup()

    def send(self, data):
        with self.lock:
            self.outbox.append(data)
        self.wakeup()

    def send_traceback(self):
        import traceback, io
        f = io.StringIO()
        print(sys.version, file=f)
        print('platform:   ', sys.platform, file=f)
        print('argv:       ', [os.path.basename(a) for a in sys.argv[:1]]
              + sys.argv[1:], file=f)
        print('version tag:', VERSION_TAG, file=f)
        print(file=f)
        traceback.print_exc(file = f)
        self.send(message(MMSG_TRACEBACK, f.getvalue().encode('utf-8')))

    def stop(self):
        self.stopped = True
        self.wakeup()

    def wakeup(self):
        try:
            self.wake_w.send(b'!')
        except error:
            pass

    # ---- in the thread ----

    def setstatus(self, status):
        if metaclisrv is self:
            self.game.metastatus = status

    def wait(self, delay):
        """Sleep, unless stopped."""
        end = time.time() + delay
        while not self.stopped:
            left = end - time.time()
            if left <= 0:
                break
            if select([self.wake_r], [], [], left)[0]:
                self.wake_r.recv(1024)

    def run(self):
        failed = None
        next_attempt = time.time()
        try:
            while not self.stopped:
                self.wait(next_attempt - time.time())
                if self.stopped:
                    break
                next_attempt = time.time() + RETRY_DELAY
                addr = address()
                if addr is None:
                    continue
                try:
                    s = create_connection(addr[:2], CONNECT_TIMEOUT)
                    s.settimeout(None)
                except (error, OSError) as e:
                    if failed is None:
                        print('*** cannot reach the meta-server %s:%d: %s '
                              '(trying again every %d seconds)' % (
                              addr[:2] + (e, RETRY_DELAY)), file=sys.stderr)
                    failed = e
                    self.setstatus('unreachable')
                    continue
                failed = None
                print('connected to the meta-server %s:%d' % addr[:2],
                      file=sys.stderr)
                conn = MetaClientSrv(s, self.game)
                with self.lock:
                    self.listing_sent = False
                try:
                    self.serve(conn)
                except Exception:
                    import traceback
                    traceback.print_exc()
                conn.close()
                if not self.stopped:
                    self.setstatus('unreachable')
        finally:
            self.wake_r.close()
            self.wake_w.close()

    def serve(self, conn):
        while not self.stopped and not conn.closed:
            with self.lock:
                data = b''.join(self.outbox)
                del self.outbox[:]
                listing = None
                if not self.listing_sent and self.listing is not None:
                    listing = self.listing
                    self.listing_sent = True
            try:
                if listing is not None:
                    conn.s.sendall(listing)
                    self.setstatus('listed')
                if data:
                    conn.s.sendall(data)
            except error:
                conn.disconnect()
                break
            iwtd, owtd, ewtd = select([conn.s, self.wake_r], [], [])
            if self.wake_r in iwtd:
                self.wake_r.recv(1024)
            if conn.s in iwtd:
                try:
                    conn.receive()
                except error:
                    conn.disconnect()

metaclisrv = None       # the Registrar of this game server

def meta_register(game):
    """List the game on the meta-server, or update its listing.  This
    does not wait: game.metastatus becomes 'listed' or 'unreachable'."""
    global metaclisrv
    import gamesrv
    info = {}
    if game.FnDesc:
        info['desc'] = game.FnDesc or ''
        info['extradesc'] = game.FnExtraDesc() or ''

    s = gamesrv.opentcpsocket()
    hs = gamesrv.openhttpsocket()
    port = int(gamesrv.displaysockport(s))
    info['httpport'] = gamesrv.displaysockport(hs)

    if metaclisrv is None:
        metaclisrv = Registrar(game)
    metaclisrv.update(message(MMSG_INFO, encodedict(info)) +
                      message(MMSG_START, port))

def meta_unregister(game):
    global metaclisrv
    if metaclisrv:
        metaclisrv.stop()
        metaclisrv = None


# ____________________________________________________________
# Game Clients

class Event:
    def __init__(self):
        import _thread
        self.lock = _thread.allocate_lock()
        self.lock.acquire()
    def signal(self):
        try:
            self.lock.release()
        except:
            pass
    def wait1(self):
        self.lock.acquire()


class MetaClientCli:
    fatalerror = False
    
    def __init__(self, serverkey, backconnectport, metaserver):
        self.metaserver = metaserver[:2]    # (host, port), TCP and UDP
        self.resultsocket = None
        self.serverkey = serverkey
        self.backconnectport = backconnectport
        self.threads = {}

    def run(self):
        import _thread
        print('Trying to connect to', self.serverkey, file=sys.stderr)
        self.ev = Event()
        self.ev2 = Event()
        self.buffer = b""
        self.sendlock = _thread.allocate_lock()
        self.recvlock = _thread.allocate_lock()
        self.inputmsgqueue = []
        self.gotudpport = None
        if not (PORTS.get('CLIENT') or PORTS.get('sendudpto')):
            self.s = connect(addr=self.metaserver)
            if self.s is not None:
                _thread.start_new_thread(self.acquire_udp_port, ())
            else:
                self.ev2.signal()     # no meta-server: no outside UDP port
        else:
            self.s = None
            self.ev2.signal()
            self.startthread(self.try_udp_connect)

        _thread.start_new_thread(self.bipbip, ())
        self.startthread(self.try_direct_connect, 0.75)
        self.startthread(self.try_indirect_connect, 1.50)
        while self.resultsocket is None:
            self.threadsleft()
            self.ev.wait1()
        self.ev2.wait1()
        return self.resultsocket

    def done(self):
        set_fast_thread_switching(False)

    def bipbip(self):
        while self.resultsocket is None:
            time.sleep(0.31416)
            self.ev.signal()

    def startthread(self, fn, sleep=0.0, args=()):
        import _thread
        def bootstrap(fn, atom, sleep, args):
            try:
                time.sleep(sleep)
                if self.resultsocket is None:
                    fn(*args)
            finally:
                del self.threads[atom]
                self.ev.signal()
        atom = object()
        self.threads[atom] = time.time()
        _thread.start_new_thread(bootstrap, (fn, atom, sleep, args))

    def threadsleft(self):
        if self.fatalerror:
            sys.exit(1)
        now = time.time()
        TIMEOUT = 11
        for starttime in list(self.threads.values()):
            if now < starttime + TIMEOUT:
                break
        else:
            if self.threads:
                print('*** time out, giving up.', file=sys.stderr)
            else:
                print('*** failed to connect.', file=sys.stderr)
            sys.exit(1)

    def try_direct_connect(self):
        host, port = self.serverkey.split(':')
        port = int(port)
        s = socket(AF_INET, SOCK_STREAM)
        try:
            s.connect((host, port))
        except error as e:
            print('direct connexion failed:', str(e), file=sys.stderr)
        else:
            print('direct connexion accepted.', file=sys.stderr)
            self.resultsocket = s

    def try_indirect_connect(self):
        import _thread, time
        if not self.s:
            self.s = connect(addr=self.metaserver)
        if not self.s:
            return
        self.routemsg(RMSG_WAKEUP)
        self.startthread(self.try_backconnect)
        self.socketcache = {}
        tries = [0.6, 0.81, 1.2, 1.69, 2.6, 3.6, 4.9, 6.23]
        for delay in tries:
            self.startthread(self.send_ping, delay)
        while self.resultsocket is None:
            msg = self.inputmsg()
            now = time.time()
            if self.resultsocket is not None:
                break
            if msg[0] == RMSG_CONNECT:
                # connect serverport clientport
                self.startthread(self.try_synconnect, args=msg[1:])
            if msg[0] == RMSG_PONG:
                # pong time2 time1  -->  sync port time3 time2 time1
                if len(self.socketcache) < len(tries):
                    s = socket(AF_INET, SOCK_STREAM)
                    s.bind(('', INADDR_ANY))
                    _, port = s.getsockname()
                    self.socketcache[port] = s
                    self.routemsg(RMSG_SYNC, port, float2str(now).encode('ascii'),
                                  *msg[2:])

    def sendmsg(self, data):
        self.sendlock.acquire()
        try:
            self.s.sendall(data)
        finally:
            self.sendlock.release()

    def routemsg(self, *rest):
        self.sendmsg(message(MMSG_ROUTE, self.serverkey.encode('ascii'), *rest))

    def _readnextmsg(self, blocking):
        self.recvlock.acquire()
        try:
            while 1:
                msg, self.buffer = decodemessage(self.buffer)
                if msg is not None:
                    if msg[0] == RMSG_UDP_ADDR:
                        if len(msg) > 2:
                            self.gotudpport = msg[1].decode('ascii'), int(msg[2])
                        continue
                    if (msg[0] == RMSG_PUNCH and len(msg) > 1 and
                            msg[1] == self.serverkey.encode('ascii')):
                        self.punchreply = msg[2:]   # () if no introduction
                        continue
                    if (msg[0] == RMSG_NO_HOST and
                            msg[1] == self.serverkey.encode('ascii')):
                        print(('*** server %r is not registered'
                                             ' on the meta-server' % (msg[1],)), file=sys.stderr)
                        self.fatalerror = True
                        sys.exit()
                    self.inputmsgqueue.append(msg)
                    return
                iwtd, owtd, ewtd = select([self.s], [], [], 0)
                if not iwtd:
                    if self.inputmsgqueue or not blocking:
                        return
                data = self.s.recv(2048)
                if not data:
                    print('disconnected from the meta-server', file=sys.stderr)
                    sys.exit()
                self.buffer += data
        finally:
            self.recvlock.release()

    def inputmsg(self):
        self._readnextmsg(blocking=True)
        return self.inputmsgqueue.pop(0)

    def try_backconnect(self):
        s1 = socket(AF_INET, SOCK_STREAM)
        s1.bind(('', self.backconnectport or INADDR_ANY))
        s1.listen(1)
        _, port = s1.getsockname()
        self.routemsg(RMSG_CONNECT, port)
        print('listening for backward connection', file=sys.stderr)
        iwtd, owtd, ewtd = select([s1], [], [], 7.5)
        if s1 in iwtd:
            s, addr = s1.accept()
            print('accepted backward connection from', addr, file=sys.stderr)
            self.resultsocket = s

    def send_ping(self):
        sys.stderr.write('. ')
        self.routemsg(RMSG_PING, float2str(time.time()).encode('ascii'))

    def try_synconnect(self, origin, remoteport, localport, *rest):
        sys.stderr.write('+ ')
        s = self.socketcache[localport]
        remotehost, _ = origin.decode('ascii').split(':')
        remoteaddr = remotehost, remoteport
        try:
            s.connect(remoteaddr)
        except error as e:
            print('SYN connect failed:', str(e), file=sys.stderr)
            return
        print(('simultaneous SYN connect succeeded with %s:%d' %
                              remoteaddr), file=sys.stderr)
        self.resultsocket = s

    def try_udp_connect(self):
        # first with an introduction by the meta-server, where both sides
        # send; an older meta-server or server does not answer it
        self.attempt_udp_connect(punch=True)
        for i in range(3):     # three attempts
            if self.resultsocket is not None:
                break
            self.attempt_udp_connect()

    def ask_punch(self, s, secret):
        """Ask the meta-server to introduce us to the server: return the
        address of its game port from outside, or None."""
        if not self.s:
            return None
        # show the meta-server our UDP address, and ask
        pattern = hex(random.randrange(0, sys.maxsize)).encode('ascii')
        for i in range(3):
            try:
                s.sendto(pattern, self.metaserver)
            except error:
                pass
        time.sleep(0.1)     # before our request, which goes over TCP
        self.punchreply = None
        self.sendmsg(message(MMSG_PUNCH, self.serverkey.encode('ascii'),
                             pattern, secret))
        deadline = time.time() + 2.5
        while (self.punchreply is None and self.resultsocket is None and
               time.time() < deadline):
            if self.recvlock.acquire(False):    # else another thread reads
                self.recvlock.release()
                self._readnextmsg(blocking=False)
            time.sleep(0.05)
        reply = self.punchreply
        if not reply or len(reply) < 2:
            return None
        return reply[0].decode('ascii'), reply[1]

    def attempt_udp_connect(self, punch=False):
        if '*udpsock*' in PORTS:
            s, (host, port) = PORTS['*udpsock*']
        else:
            s = socket(AF_INET, SOCK_DGRAM)
            s.bind(('', PORTS.get('CLIENT', INADDR_ANY)))
            host, port = s.getsockname()
            if 'sendudpto' in PORTS:
                host = PORTS['sendudpto']
        secret = originalsecret = random.randrange(0, 65536)
        if punch:
            punchaddr = self.ask_punch(s, secret)
            if punchaddr is None:
                return
            deadline = time.time() + 3.5
        else:
            punchaddr = None
            self.routemsg(RMSG_UDP_CONN, secret, port)
            deadline = time.time() + 2.94
        secret = b'B' + bytes([secret & 0xFF, secret >> 8])
        nextpunch = 0.0
        while True:
            # Stop as soon as another connection won: the game then uses
            # this UDP socket for its frames (and may close it), and
            # reading them here would leave the game waiting for them.
            if self.resultsocket is not None:
                return
            now = time.time()
            if now >= deadline:
                return
            timeout = deadline - now
            if punchaddr is not None:
                # our NAT then lets in what the server sends us
                if now >= nextpunch:
                    try:
                        s.sendto(datagram(message(DMSG_PUNCH)), punchaddr)
                    except error:
                        pass
                    nextpunch = now + 0.2
                timeout = min(timeout, max(0, nextpunch - now))
            try:
                iwtd, owtd, ewtd = select([s], [], [], timeout)
                if self.resultsocket is not None:
                    return
                if s not in iwtd:
                    continue
                packet, addr = s.recvfrom(200)
            except (error, ValueError):
                if s.fileno() < 0:
                    return  # the game closed it
                continue    # e.g. an ICMP error on Windows (WinError 10054)
            if packet.startswith(secret) and len(packet) == 5:
                break
        s.connect(addr)
        #print 'got', repr(packet)
        remotesecret = packet[3] | (packet[4] << 8)
        secret = random.randrange(0, 65536)
        secret = bytes([secret & 0xFF, secret >> 8])
        packet = b'[bnb c->s]' + packet[3:5] + secret
        for name in ('*udpsock*', 'CLIENT'):
            if name in PORTS:
                del PORTS[name]
        from socketoverudp import SocketOverUdp
        sock = SocketOverUdp(s, (originalsecret, remotesecret))
        #print 'sending', repr(packet)
        sock.sendall(packet)
        sock.flush()
        data = b''
        expected = b'[bnb s->c]' + secret
        while len(data) < len(expected):
            #print 'waiting'
            iwtd, owtd, ewtd = select([sock], [], [], 2.5)
            if sock not in iwtd:
                print('socket-over-udp timed out', file=sys.stderr)
                return
            #print 'we get:'
            data += sock.recv()
            #print repr(data)
        if data != expected:
            print('bad udp data from', addr, file=sys.stderr)
        else:
            sock.sendall(b'^')
            sock.flush()
            print('udp connexion handshake succeeded')
            self.resultsocket = sock

    def acquire_udp_port(self):
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            s.bind(('', INADDR_ANY))
            randomdata = hex(random.randrange(0, sys.maxsize)).encode('ascii')
            for i in range(5):
                s.sendto(randomdata, self.metaserver)
                time.sleep(0.05)
                self.sendmsg(message(MMSG_UDP_ADDR, randomdata))
                time.sleep(0.05)
                self._readnextmsg(blocking=False)
                if self.gotudpport:
                    PORTS['*udpsock*'] = s, self.gotudpport
                    udphost, udpport = self.gotudpport
                    print(('udp port %d is visible from '
                                          'outside on %s:%d' % (
                        s.getsockname()[1], udphost, udpport)), file=sys.stderr)
                    self.startthread(self.try_udp_connect)
                    break
        finally:
            self.ev2.signal()


def meta_connect(serverkey, backconnectport=None):
    metaserver = PORTS.get('SSH_RELAY') or address()
    if metaserver is None:
        print('*** %s' % NOT_SET, file=sys.stderr)
        return None
    c = MetaClientCli(serverkey, backconnectport, metaserver)
    s = c.run()
    c.done()
    return s

def print_server_list():
    s = connect()
    if s is not None:
        s.sendall(message(MMSG_LIST))
        buffer = b""
        while decodemessage(buffer)[0] is None:
            buffer += s.recv(8192)
        s.close()
        msg = decodemessage(buffer)[0]
        assert msg[0] == RMSG_LIST
        entries = decodedict(msg[1])
        if not entries:
            print('No registered server.', file=sys.stderr)
        else:
            print()
            print(' %-25s | %-30s | %s' % (
                'server', 'game', 'players'))
            print('-'*27+'+'+'-'*32+'+'+'-'*11)
            for key, value in list(entries.items()):
                if ':' in key:
                    try:
                        addr, _, _ = gethostbyaddr(key[:key.index(':')])
                    except:
                        pass
                    else:
                        addr = '%-27s' % (addr,)
                        if len(addr) < 28: addr += '|'
                        addr = '%-60s' % (addr,)
                        if len(addr) < 61: addr += '|'
                        print(addr)
                value = decodedict(value)
                print(' %-25s | %-30s | %s' % (
                    key, totext(value.get('desc', '<no description>')),
                    totext(value.get('extradesc', ''))))
            print()

if __name__ == '__main__':
    print_server_list()
