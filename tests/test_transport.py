"""The transport layer (common/transport.py): what the game server and
the Python client send goes through it, over regular sockets."""

import errno
import os
import select
import socket
import sys
import time
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common')]

import transport
from transport import Transport, NativeTransport, BroadcastTransport
import gamesrv
from msgstruct import *


def tcp_pair():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('127.0.0.1', 0))
    listener.listen(1)
    a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    a.connect(listener.getsockname())
    b, addr = listener.accept()
    listener.close()
    return a, b


class Native(unittest.TestCase):

    def setUp(self):
        client, server = tcp_pair()
        self.client = NativeTransport(client, blocking=True)
        self.server = NativeTransport(server)
        self.addCleanup(self.client.close)
        self.addCleanup(self.server.close)

    def test_stream(self):
        self.assertEqual(self.server.send_tcp(b'hello'), 5)
        self.assertEqual(self.client.recv_tcp(100), b'hello')
        self.client.sendall_tcp(b'x' * 100000)
        got = b''
        while len(got) < 100000:
            select.select([self.server], [], [], 5)
            got += self.server.recv_tcp(65536)
        self.assertEqual(got, b'x' * 100000)

    def test_server_side_does_not_block(self):
        self.assertRaises(socket.error, self.server.recv_tcp, 100)
        try:
            for i in range(10000):
                self.server.send_tcp(b'x' * 65536)
        except socket.error as e:
            self.assertEqual(e.args[0], transport.EWOULDBLOCK)
        else:
            self.fail("send_tcp() never said EWOULDBLOCK")

    def test_eof(self):
        self.client.close()
        select.select([self.server], [], [], 5)
        self.assertEqual(self.server.recv_tcp(100), b'')
        self.assertTrue(self.server.at_eof())

    def test_select_and_names(self):
        self.assertEqual(self.server.getpeername(), self.client.getsockname())
        self.client.sendall_tcp(b'.')
        iwtd, owtd, ewtd = select.select([self.server], [], [], 5)
        self.assertEqual(iwtd, [self.server])

    def test_datagrams(self):
        # as the client and the server do: the client binds a port and
        # tells it to the server, which sends the frames there
        host, port = self.client.bind_udp()
        self.assertIsNone(self.server.udp_kind)
        self.server.open_udp('127.0.0.1', port)
        self.assertEqual(self.server.udp_kind, 'udp')
        self.assertEqual(self.server.send_udp(b'frame'), 5)
        select.select([self.client.udpsock], [], [], 5)
        self.assertEqual(self.client.recv_udp(65535), b'frame')
        self.server.close_udp()
        self.assertIsNone(self.server.udp_kind)

    def test_client_datagram_goes_to_the_server(self):
        # the dummy packet that opens the way through a NAT
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(receiver.close)
        receiver.bind(self.server.getsockname())
        self.client.bind_udp()
        self.client.send_udp(b'.')
        select.select([receiver], [], [], 5)
        self.assertEqual(receiver.recv(10), b'.')

    def test_client_datagram_read_does_not_block(self):
        # select() can report a datagram that another reader took first
        # (the meta-server's connection thread shares a given socket):
        # the client's main loop must not then wait for the next one
        shared = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        shared.bind(('127.0.0.1', 0))
        self.client.bind_udp(sock=shared)
        self.assertRaises(BlockingIOError, self.client.recv_udp, 65535)

    def test_socket_extras_are_reachable(self):
        # e.g. udp_over_udp_mixer of metaserver/socketoverudp.py
        self.assertFalse(hasattr(self.server, 'udp_over_udp_mixer'))
        self.assertEqual(self.server.family, socket.AF_INET)


class Others(unittest.TestCase):

    def test_gettransport(self):
        a, b = socket.socketpair()
        self.addCleanup(a.close)
        t = transport.gettransport(b)
        self.addCleanup(t.close)
        self.assertIsInstance(t, NativeTransport)
        self.assertIs(transport.gettransport(t), t)

    def test_base_class_has_no_datagrams(self):
        self.assertRaises(socket.error, Transport().open_udp, 'x', 1)

    def test_broadcast(self):
        t = BroadcastTransport(18999)
        self.addCleanup(t.close)
        self.assertEqual(t.getsockname(), ('', 18999))
        self.assertEqual(t.udp_kind, 'broadcast')


class Endpoint(unittest.TestCase):
    """The server's one UDP socket (UdpEndpoint), on the game's port."""

    def setUp(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(('127.0.0.1', 0))
        self.listener.listen(4)
        self.addCleanup(self.listener.close)
        self.port = self.listener.getsockname()[1]
        self.endpoint = transport.UdpEndpoint(self.port)
        self.addCleanup(self.endpoint.close)

    def connect(self):
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect(self.listener.getsockname())
        s, addr = self.listener.accept()
        client = NativeTransport(c, blocking=True)
        server = NativeTransport(s, endpoint=self.endpoint)
        self.addCleanup(client.close)
        self.addCleanup(server.close)
        return client, server

    def test_frames_come_from_where_the_client_sent(self):
        # A port-restricted NAT only lets in datagrams from the address
        # and port the client sent to: the server's address and game
        # port (see startplaying() in pclient.py).  A connected UDP
        # socket filters in the same way.  Two clients at once.
        for i in range(2):
            client, server = self.connect()
            host, port = client.bind_udp()
            client.udpsock.connect(client.getpeername())    # the "NAT"
            server.open_udp('127.0.0.1', port)
            self.assertEqual(server.udp_kind, 'udp')
            server.send_udp(b'frame%d' % i)
            iwtd, owtd, ewtd = select.select([client.udpsock], [], [], 2)
            self.assertEqual(iwtd, [client.udpsock], 'frame %d filtered' % i)
            self.assertEqual(client.recv_udp(65535), b'frame%d' % i)

    def test_frames_go_where_the_datagrams_come_from(self):
        # a NAT that changes the port: the client says one port, but its
        # datagrams come from another, where the replies get through
        for learn_first in (True, False):
            client, server = self.connect()
            host, port = client.bind_udp()
            wrong = port + 1 if port < 65535 else port - 1
            if learn_first:
                server.learn_udp_peer(('127.0.0.1', port))
                server.open_udp('127.0.0.1', wrong)
            else:
                server.open_udp('127.0.0.1', wrong)
                server.learn_udp_peer(('127.0.0.1', port))
            server.send_udp(b'frame')
            iwtd, owtd, ewtd = select.select([client.udpsock], [], [], 2)
            self.assertEqual(client.recv_udp(65535), b'frame')

    def test_udp_datagram(self):
        # gamesrv.udp_datagram(): which client a datagram is from
        class C:
            def __init__(self, transport, token=None):
                self.transport, self.udp_token = transport, token
            def log(self, text):
                pass
        saved = gamesrv.clients[:], dict(gamesrv.udp_tokens)
        def restore():
            gamesrv.clients[:] = saved[0]
            gamesrv.udp_tokens.clear()
            gamesrv.udp_tokens.update(saved[1])
        self.addCleanup(restore)
        new = C(self.connect()[1], b'tokn')
        old1, old2 = C(self.connect()[1]), C(self.connect()[1])
        gamesrv.clients[:] = [new, old1]
        gamesrv.udp_tokens.clear()
        gamesrv.udp_tokens[b'tokn'] = new
        def token(t, *extra):
            return datagram(message(DMSG_TOKEN, t, *extra))
        gamesrv.udp_datagram(token(b'tokn'), ('127.0.0.1', 5000))
        self.assertEqual(new.transport.learned_udppeer, ('127.0.0.1', 5000))
        for data in (token(b'xxxx'),            # an unknown token
                     b'.\xff\x00garbage',       # not readable
                     b'\x01reserved',           # not a control datagram
                     datagram(message(b'?', 1))):    # an unknown type
            gamesrv.udp_datagram(data, ('127.0.0.1', 5001))
        self.assertEqual(new.transport.learned_udppeer, ('127.0.0.1', 5000))
        # more fields, or an unknown message before it: still understood
        gamesrv.udp_datagram(datagram(message(b'?', b'future'),
                                      message(DMSG_TOKEN, b'tokn', 7)),
                             ('127.0.0.1', 5002))
        self.assertEqual(new.transport.learned_udppeer, ('127.0.0.1', 5002))
        # an older client sends b'.': only if it is alone at this address
        gamesrv.udp_datagram(b'.', ('127.0.0.1', 6000))
        self.assertEqual(old1.transport.learned_udppeer, ('127.0.0.1', 6000))
        gamesrv.clients.append(old2)
        gamesrv.udp_datagram(b'.', ('127.0.0.1', 6001))
        self.assertEqual(old1.transport.learned_udppeer, ('127.0.0.1', 6000))
        self.assertIsNone(old2.transport.learned_udppeer)

    def test_closing_a_client_keeps_the_endpoint(self):
        client, server = self.connect()
        host, port = client.bind_udp()
        server.open_udp('127.0.0.1', port)
        server.close()
        client.send_udp(b'.')       # the endpoint still receives
        select.select([self.endpoint], [], [], 2)
        self.assertEqual([data for data, addr in self.endpoint.datagrams()],
                         [b'.'])

    def test_errors_of_one_datagram_are_ignored(self):
        class Sock:
            def __init__(self, errors):
                self.errors = errors
            def recvfrom(self, size):
                raise self.errors.pop(0)
        real = self.endpoint.sock
        self.addCleanup(setattr, self.endpoint, 'sock', real)
        # an ICMP error report (Windows), then nothing more to read
        self.endpoint.sock = Sock([ConnectionResetError(errno.ECONNRESET, ''),
                                   OSError(errno.EMSGSIZE, ''),
                                   BlockingIOError(errno.EWOULDBLOCK, '')])
        self.assertEqual(list(self.endpoint.datagrams()), [])
        # but a real error of the socket is one
        self.endpoint.sock = Sock([OSError(errno.EBADF, '')])
        self.assertRaises(OSError, list, self.endpoint.datagrams())


class Peers(unittest.TestCase):
    """The meta-server's UDP connections through the endpoint."""

    def setUp(self):
        self.endpoint = transport.UdpEndpoint(0)
        self.addCleanup(self.endpoint.close)
        self.port = self.endpoint.getsockname()[1]
        self.remote = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.remote.bind(('127.0.0.1', 0))
        self.remote.connect(('127.0.0.1', self.port))
        self.addCleanup(self.remote.close)
        self.peer = self.endpoint.open_peer(self.remote.getsockname())
        self.addCleanup(self.peer.close)

    def pump(self):
        # what the server's main loop does with the endpoint
        select.select([self.endpoint], [], [], 1)
        return list(self.endpoint.datagrams())

    def test_routing(self):
        self.remote.send(b'\xe2stream')
        self.remote.send(b'.')
        self.assertEqual([d for d, a in self.pump()], [b'.'])
        iwtd, owtd, ewtd = select.select([self.peer], [], [], 1)
        self.assertEqual(iwtd, [self.peer])
        self.assertEqual(self.peer.recv(100), b'\xe2stream')
        # from elsewhere, or not in 0xE0..0xEF: not for the peer
        other = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(other.close)
        other.sendto(b'\xe2other', ('127.0.0.1', self.port))
        self.remote.send(b'\x80reserved')
        self.pump()
        self.assertEqual(select.select([self.peer], [], [], 0.2)[0], [])

    def test_send_comes_from_the_game_port(self):
        self.peer.send(b'\xe2back')
        self.remote.settimeout(1)
        self.assertEqual(self.remote.recv(100), b'\xe2back')  # connected:
        # it only accepts what comes from the game port

    def test_close(self):
        self.peer.close()
        self.assertNotIn(self.remote.getsockname(), self.endpoint.peers)
        self.remote.send(b'\xe2late')
        self.pump()                 # dropped, no error

    def test_reopen(self):
        # a second handshake from the same address takes over; the first
        # one's socket stays usable until its owner closes it
        addr = self.remote.getsockname()
        second = self.endpoint.open_peer(addr)
        self.addCleanup(second.close)
        self.remote.send(b'\xe2new')
        self.pump()
        self.assertEqual(select.select([self.peer], [], [], 0.2)[0], [])
        self.assertEqual(second.recv(100), b'\xe2new')
        self.peer.close()
        self.assertIs(self.endpoint.peers[addr], second)

    def test_stream_over_udp(self):
        # metaserver/socketoverudp.py over a peer, against a client on a
        # socket of its own, losing 10% of the packets both ways
        import random, threading
        sys.path.insert(0, os.path.join(ROOT, 'metaserver'))
        from socketoverudp import SocketOverUdp
        rnd = random.Random(1)
        class Lossy:
            def __init__(self, sock):
                self.sock = sock
            def send(self, data):
                if rnd.random() < 0.1:
                    return len(data)
                return self.sock.send(data)
            def __getattr__(self, name):
                return getattr(self.sock, name)
        server = SocketOverUdp(Lossy(self.peer), (1, 2))
        client = SocketOverUdp(Lossy(self.remote), (2, 1))
        stop = threading.Event()
        self.addCleanup(stop.set)
        def loop():
            while not stop.is_set():
                self.pump()
        threading.Thread(target=loop, daemon=True).start()
        data_up = bytes(range(256)) * 200
        data_down = bytes(range(255, -1, -1)) * 200
        client.sendall(data_up)
        server.sendall(data_down)
        got_up = got_down = b''
        deadline = time.time() + 20
        while (len(got_up) < len(data_up) or len(got_down) < len(data_down)) \
                and time.time() < deadline:
            iwtd, owtd, ewtd = select.select([server, client], [], [], 0.1)
            if server in iwtd:
                got_up += server.recv()
            if client in iwtd:
                got_down += client.recv()
        self.assertEqual(got_up, data_up)
        self.assertEqual(got_down, data_down)


class GameSockets(unittest.TestCase):
    """The game's TCP and UDP sockets share their port number."""

    def test_same_port(self):
        s, u = gamesrv.opengamesockets(0)
        self.addCleanup(s.close)
        self.addCleanup(u.close)
        self.assertEqual(s.getsockname()[1], u.getsockname()[1])

    def test_udp_port_taken(self):
        # a fixed port: the game still runs, without its UdpEndpoint
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(('', 0))
        port = probe.getsockname()[1]
        probe.close()
        taken = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        taken.bind(('', port))
        self.addCleanup(taken.close)
        s, u = gamesrv.opengamesockets(port)
        self.addCleanup(s.close)
        self.assertIsNone(u)
        self.assertEqual(s.getsockname()[1], port)


class FakeTransport(Transport):
    """Records what the game server sends."""
    kind = 'fake'

    def __init__(self):
        self.r, self.w = socket.socketpair()
        self.stream = []
        self.datagrams = []
        self.low_delay = False
        self.closed = False
        self.can_open_udp = True

    def send_tcp(self, data):
        self.stream.append(bytes(data))
        return len(data)

    def recv_tcp(self, bufsize):
        return self.r.recv(bufsize)

    def set_low_delay(self):
        self.low_delay = True

    def open_udp(self, host=None, port=None):
        if not self.can_open_udp:
            raise socket.error("no datagrams")
        self.udp_kind = 'fake'
        self.udp_address = host, port

    def send_udp(self, data):
        self.datagrams.append(data)
        return len(data)

    def close_udp(self):
        self.udp_kind = None

    def fileno(self):
        return self.r.fileno()

    def getpeername(self):
        return ('fake', 1)

    def close(self):
        self.closed = True
        self.r.close()
        self.w.close()


class FakeGame:
    FnDesc = 'Test'
    width = 100
    height = 50
    backcolor = 0
    broadcast_port = None
    FnKeys = []

    def FnPlayers(self):
        return {}

    def FnDisconnected(self):
        pass

    def deffieldmsg(self):
        return message(MSG_DEF_PLAYFIELD, 100, 50, 0, b'Test')


class GameServerClient(unittest.TestCase):
    """gamesrv.Client only knows its Transport."""

    def setUp(self):
        saved = gamesrv.game, gamesrv.clients[:], dict(gamesrv.bitmaps)
        def restore():
            gamesrv.game = saved[0]
            gamesrv.clients[:] = saved[1]
            gamesrv.bitmaps.clear()
            gamesrv.bitmaps.update(saved[2])
        self.addCleanup(restore)
        gamesrv.game = FakeGame()
        gamesrv.bitmaps.clear()
        gamesrv.NOW = time.time()
        self.t = FakeTransport()
        self.c = gamesrv.Client(self.t, ('fake', 1))
        self.addCleanup(lambda: self.c.transport and self.c.disconnect())
        self.c.opengame(gamesrv.game)

    def stream(self):
        data = b''.join(self.t.stream)
        del self.t.stream[:]
        return data

    def messages(self):
        data = self.stream()
        result = []
        while data:
            values, data = decodemessage(data)
            result.append(values)
        return result

    def ready(self):
        self.c.emit(b'', None)      # the rest of the initial data
        self.c.receive(message(CMSG_PING))
        self.c.emit(b'', None)      # the answer
        self.stream()

    def test_welcome_goes_through_the_transport(self):
        self.c.emit(b'', None)
        data = self.stream()
        self.assertTrue(data.startswith(MSG_WELCOME + b'Test\n'), data)
        self.assertIn(gamesrv.game.deffieldmsg(), data)

    def test_frames_over_datagrams(self):
        self.ready()
        self.c.receive(message(CMSG_UDP_PORT, 12345))
        self.assertEqual(self.t.udp_address, ('fake', 12345))
        self.c.emit(b'sprites', None)
        self.assertEqual(self.t.datagrams, [b'sprites'])

    def test_frames_in_the_stream(self):
        import zlib
        self.ready()
        self.c.receive(message(CMSG_UDP_PORT, MSG_INLINE_FRAME))
        self.assertTrue(self.t.low_delay)
        self.c.emit(b'sprites', None)
        self.assertEqual(self.t.datagrams, [])
        frames = [values[1] for values in self.messages()
                  if values[0] == MSG_INLINE_FRAME]
        self.assertEqual(len(frames), 1)
        self.assertEqual(zlib.decompressobj().decompress(frames[0]),
                         b'sprites')

    def test_no_datagram_channel(self):
        self.ready()
        self.t.can_open_udp = False
        self.c.receive(message(CMSG_UDP_PORT, 12345))
        self.c.last_ping = 0        # long ago
        self.c.emit(b'sprites', None)
        self.c.emit(b'sprites', None)
        self.assertEqual(self.t.datagrams, [])
        # the client is told that it missed everything, in a message
        # that still fits (it then asks for the frames in the stream)
        self.assertIn((MSG_PING, 0x7FFFFFFF), self.messages())

    def test_input_and_disconnect(self):
        self.t.w.send(message(CMSG_PROTO_VERSION, 3))
        self.c.input_handler()
        self.assertEqual(self.c.proto, 3)
        self.t.w.close()
        self.t.w = self.t.r         # (closed twice otherwise)
        self.c.input_handler()
        self.assertIsNone(self.c.transport)
        self.assertTrue(self.t.closed)
        self.assertNotIn(self.c, gamesrv.clients)


if __name__ == '__main__':
    unittest.main()
