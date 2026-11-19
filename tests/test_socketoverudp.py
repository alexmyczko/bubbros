"""SocketOverUdp (metaserver/socketoverudp.py): the game's stream over
UDP, when the meta-server could only make a UDP connection."""

import os
import socket
import sys
import threading
import unittest
from select import select

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, 'metaserver'))
import socketoverudp
from socketoverudp import SocketOverUdp


class DropFirst:
    """A UDP socket that loses the first packet sent."""
    def __init__(self, sock):
        self.sock = sock
        self.dropped = False
    def send(self, data):
        if not self.dropped:
            self.dropped = True
            return len(data)
        return self.sock.send(data)
    def __getattr__(self, name):
        return getattr(self.sock, name)


def udp_pair():
    a = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    a.bind(('127.0.0.1', 0))
    b.bind(('127.0.0.1', 0))
    a.connect(b.getsockname())
    b.connect(a.getsockname())
    return a, b


class TestSocketOverUdp(unittest.TestCase):

    def test_recv_repeats_a_lost_packet(self):
        # The client sends the last packet of the handshake and then
        # waits in recv() for the server's welcome; the server answers
        # only once it has that packet.  It is lost: recv() must send it
        # again rather than wait forever.
        a, b = udp_pair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        client = SocketOverUdp(DropFirst(a), (1, 2))
        server = SocketOverUdp(b, (2, 1))

        def serve():
            got = b''
            while got != b'^':
                iwtd, owtd, ewtd = select([server], [], [], 5.0)
                if server not in iwtd:
                    return
                got += server.recv()
            server.sendall(b'welcome')
            server.flush()
            for i in range(20):     # answer the client's acks a while
                iwtd, owtd, ewtd = select([server], [], [], 0.1)
                if server in iwtd:
                    server.recv()
        t = threading.Thread(target=serve, daemon=True)
        t.start()

        client.sendall(b'^')
        client.flush()              # this packet is lost
        result = []
        def read():
            data = b''
            while not data:
                data = client.recv()
            result.append(data)
        r = threading.Thread(target=read, daemon=True)
        r.start()
        r.join(10.0)
        self.assertEqual(result, [b'welcome'])

    def test_recv_gives_up_on_a_silent_peer(self):
        a, b = udp_pair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        saved = socketoverudp.SILENCE_TIMEOUT
        socketoverudp.SILENCE_TIMEOUT = 1.0
        self.addCleanup(setattr, socketoverudp, 'SILENCE_TIMEOUT', saved)
        client = SocketOverUdp(a, (1, 2))
        client.sendall(b'^')
        client.flush()
        self.assertRaises(socket.error, client.recv)


if __name__ == '__main__':
    unittest.main()
