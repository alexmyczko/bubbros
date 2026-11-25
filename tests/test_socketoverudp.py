"""SocketOverUdp (metaserver/socketoverudp.py): the game's stream over
UDP, when the meta-server could only make a UDP connection."""

import os
import socket
import sys
import threading
import time
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
        self.addCleanup(t.join, 5.0)    # before the sockets are closed

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

    def test_silent_peer_shows_in_check_silence(self):
        # A peer that is gone sends nothing, so recv() is never called;
        # select() calls fileno(), which must not fail, even after the
        # congestion timeout, while check_silence() reports the peer.
        a, b = udp_pair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        saved = (socketoverudp.SILENCE_TIMEOUT,
                 socketoverudp.CONGESTION_TIMEOUT)
        socketoverudp.SILENCE_TIMEOUT = 0.5
        socketoverudp.CONGESTION_TIMEOUT = 0.2
        def restore():
            (socketoverudp.SILENCE_TIMEOUT,
             socketoverudp.CONGESTION_TIMEOUT) = saved
        self.addCleanup(restore)
        server = SocketOverUdp(b, (2, 1))
        server.check_silence()
        server.pl.timeout = 0.05            # repeats come quickly
        server.sendall(b'x' * 300000)       # more than it may send unanswered
        server.flush()
        deadline = time.time() + 1.0
        while time.time() < deadline:
            server.fileno()
            time.sleep(0.01)
        self.assertTrue(server.pl.is_congested())
        self.assertRaises(socket.error, server.check_silence)


    def test_reserved_packets_are_dropped(self):
        # 0xE6 to 0xEF: reserved for future use, not taken for frames
        frames = []
        a, b = udp_pair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        sock = SocketOverUdp(a, (1, 2))
        sock.udp_over_udp_decoder = frames.append
        for first in range(0xE6, 0xF0):
            for packet in (bytes([first]), bytes([first]) + b'\x00' * 20):
                self.assertEqual(sock._decode(packet), b'')
        self.assertEqual(frames, [])
        sock._decode(b'\x80frame')      # a frame still is one
        self.assertEqual(frames, [b'\x80frame'])

    def test_frame_that_looks_reserved_is_wrapped(self):
        # a frame starting with 0xE0 to 0xEF goes inside a mixed packet,
        # so that it reaches the frame decoder on the other side
        a, b = udp_pair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        sender = SocketOverUdp(a, (1, 2))
        receiver = SocketOverUdp(b, (2, 1))
        frames = []
        receiver.udp_over_udp_decoder = frames.append
        for first in (0xE2, 0xE7, 0xEF):
            sender.send_video_data(bytes([first]) + b'frame')
            b.settimeout(2)
            receiver._decode(b.recv(65535))
        self.assertEqual(frames, [bytes([f]) + b'frame'
                                  for f in (0xE2, 0xE7, 0xEF)])

    def test_large_frame_that_looks_reserved_is_wrapped(self):
        # too large to share a datagram with a stream packet: still
        # wrapped, alone
        a, b = udp_pair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        sender = SocketOverUdp(a, (1, 2))
        receiver = SocketOverUdp(b, (2, 1))
        frames = []
        receiver.udp_over_udp_decoder = frames.append
        b.settimeout(2)
        big = [bytes([first]) + b'x' * 2000 for first in (0xE4, 0xE7)]
        for frame in big:
            sender.sendall(b'stream data')      # a stream packet waits
            sender.send_video_data(frame)
            sender.send_video_data(frame)       # and none
        received = []
        while len(frames) < 4:
            packet = b.recv(65535)
            self.assertTrue(packet)             # no empty datagram
            received.append(receiver._decode(packet))
        self.assertEqual(frames, [big[0], big[0], big[1], big[1]])
        self.assertEqual(b''.join(received), b'stream data' * 2)

if __name__ == '__main__':
    unittest.main()
