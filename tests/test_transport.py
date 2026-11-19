"""The transport layer (common/transport.py): what the game server and
the Python client send goes through it, over regular sockets."""

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
