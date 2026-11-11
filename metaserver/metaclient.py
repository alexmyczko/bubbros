import sys, os, time, random
from select import select
from socket import *
from metastruct import *

_SERVER = 'ctpug.org.za'

METASERVER = (_SERVER, 8055)
METASERVER_UDP = (_SERVER, 8055)
METASERVER_URL = 'http://%s:8050/bub-n-bros.html' % (_SERVER,)
VERSION_TAG = 1601

def connect(failure=[]):
    if len(failure) >= 2:
        return None
    print('Connecting to the meta-server %s:%d...' % METASERVER, file=sys.stderr)
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect(METASERVER)
    except error as e:
        print('*** cannot contact meta-server:', str(e), file=sys.stderr)
        failure.append(e)
        return None
    else:
        print('connected.', file=sys.stderr)
    return s

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
    
    def __init__(self, s, game):
        MessageSocket.__init__(self, s)
        self.game = game
        self.lastwakeup = None
        self.synsockets = {}
        import gamesrv
        gamesrv.addsocket('META', s, self.receive)
        self.closed = 0

    def close(self):
        if not self.closed:
            self.disconnect()
            try:
                self.s.shutdown(2)
            except:
                pass

    def disconnect(self):
        import gamesrv
        gamesrv.removesocket('META', self.s)
        self.closed = 1
        print('disconnected from the meta-server', file=sys.stderr)

    def send_traceback(self):
        if not self.closed:
            import traceback, io, sys
            f = io.StringIO()
            print(sys.version, file=f)
            print('platform:   ', sys.platform, file=f)
            print('executable: ', sys.executable, file=f)
            print('argv:       ', sys.argv, file=f)
            print('cwd:        ', os.getcwd(), file=f)
            print('version tag:', VERSION_TAG, file=f)
            print(file=f)
            traceback.print_exc(file = f)
            self.s.sendall(message(MMSG_TRACEBACK, f.getvalue().encode('utf-8')))

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
        def connect(origin, secret, port):
            host, _ = origin.decode('ascii').split(':')
            addr = host, port
            s = socket(AF_INET, SOCK_DGRAM)
            print('udp connecting to', addr, file=sys.stderr)
            s.connect(addr)
            mysecret = random.randrange(0, 65536)
            packet = b'B' + bytes([  secret & 0xFF,   secret >> 8,
                                   mysecret & 0xFF, mysecret >> 8])
            from socketoverudp import SocketOverUdp
            from socketoverudp import SOU_RANGE_START, SOU_RANGE_STOP
            for i in range(5):
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
                    return
                #print 'decoding more'
                data += sock.recv()
                #print 'now data is', repr(data)
            if data[:-2] != expected:
                print('udp connecting: bad data', file=sys.stderr)
                return
            sock.sendall(b'[bnb s->c]' + data[-2:])
            sock.flush()
            #print 'waiting for the last dot...'
            while 1:
                iwtd, owtd, ewtd = select([sock], [], [], 5.0)
                if sock not in iwtd:
                    print('udp connecting: timed out', file=sys.stderr)
                    return
                data = sock.recv(200)
                if data:
                    break
            if data != b'^':
                print('udp connecting: bad data', file=sys.stderr)
                return
            #print 'done!'
            self.game.newclient_threadsafe(sock, addr)

        import _thread
        _thread.start_new_thread(connect, (origin, secret, port))

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
        }

metaclisrv = None

def meta_register(game):
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

    if not metaclisrv or metaclisrv.closed:
        s = connect()
        if not s:
            return
        metaclisrv = MetaClientSrv(s, game)
    metaclisrv.s.sendall(message(MMSG_INFO, encodedict(info)) +
                         message(MMSG_START, port))

def meta_unregister(game):
    global metaclisrv
    if metaclisrv:
        metaclisrv.close()
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
    
    def __init__(self, serverkey, backconnectport):
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
            self.s = connect()
            _thread.start_new_thread(self.acquire_udp_port, ())
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
            self.s = connect()
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
        for i in range(3):     # three attempts
            self.attempt_udp_connect()
            if self.resultsocket is not None:
                break

    def attempt_udp_connect(self):
        if '*udpsock*' in PORTS:
            s, (host, port) = PORTS['*udpsock*']
        else:
            s = socket(AF_INET, SOCK_DGRAM)
            s.bind(('', PORTS.get('CLIENT', INADDR_ANY)))
            host, port = s.getsockname()
            if 'sendudpto' in PORTS:
                host = PORTS['sendudpto']
        secret = originalsecret = random.randrange(0, 65536)
        self.routemsg(RMSG_UDP_CONN, secret, port)
        secret = b'B' + bytes([secret & 0xFF, secret >> 8])
        while True:
            iwtd, owtd, ewtd = select([s], [], [], 2.94)
            if s not in iwtd:
                return
            packet, addr = s.recvfrom(200)
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
                s.sendto(randomdata, METASERVER_UDP)
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
    global METASERVER
    if PORTS.get('SSH_RELAY'):
        METASERVER = PORTS['SSH_RELAY']
    c = MetaClientCli(serverkey, backconnectport)
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
