"""The client tells the game server where to send the UDP frames.  Through
the meta-server that address is the one seen from outside.  No network."""

import os
import sys
import unittest
from unittest import mock
from socket import socket, AF_INET, SOCK_DGRAM

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common'), os.path.join(ROOT, 'display')]

from common import msgstruct
from common.transport import NativeTransport
import pclient


class FakeTCP:
    def __init__(self, peer):
        self.peer, self.sent = peer, b''
    def getpeername(self):
        return self.peer
    def sendall(self, data):
        self.sent += data


class UdpAddress(unittest.TestCase):

    def test_address_seen_from_outside(self):
        server = socket(AF_INET, SOCK_DGRAM)
        server.bind(('127.0.0.1', 0))
        self.addCleanup(server.close)
        udp = socket(AF_INET, SOCK_DGRAM)
        udp.bind(('127.0.0.1', 0))
        self.addCleanup(udp.close)
        msgstruct.PORTS['*udpsock*'] = (udp, ('203.0.113.5', 4321))
        self.addCleanup(msgstruct.PORTS.pop, '*udpsock*')
        pf = pclient.Playfield.__new__(pclient.Playfield)
        pf.s = FakeTCP(server.getsockname())
        pf.transport = NativeTransport(pf.s, blocking=True)
        pf.snd = None
        pf.pending_udp_data = None
        pf.iwtd, pf.initial_iwtd = [], []
        pf.startplaying()
        msg = msgstruct.message(msgstruct.CMSG_UDP_PORT, 4321)
        self.assertEqual(pf.s.sent, msg)


    def test_token_goes_to_the_game_port(self):
        # a server that sent MSG_UDP_TOKEN: the client sends b'.'+token
        # to the UDP port it said, not to the stream's port
        server = socket(AF_INET, SOCK_DGRAM)
        server.bind(('127.0.0.1', 0))
        self.addCleanup(server.close)
        pf = pclient.Playfield.__new__(pclient.Playfield)
        pf.s = FakeTCP(('127.0.0.1', 1))        # the stream's port: not there
        pf.transport = NativeTransport(pf.s, blocking=True)
        self.addCleanup(pf.transport.close_udp)
        pf.snd = None
        pf.pending_udp_data = None
        pf.iwtd, pf.initial_iwtd = [], []
        pf.udpbytecounter = 0
        pf.animdelay = 0.5
        pf.msg_udp_token(server.getsockname()[1], b'tokn')
        pf.startplaying()
        server.settimeout(2)
        self.assertEqual(server.recvfrom(100)[0], msgstruct.datagram(
            msgstruct.message(msgstruct.DMSG_TOKEN, b'tokn')))


    def test_unknown_control_datagram_is_ignored(self):
        pf = pclient.Playfield.__new__(pclient.Playfield)
        seen = []
        pf.update_sprites = seen.append
        pf.udp_control(msgstruct.datagram(msgstruct.message(b'?', 1)))
        self.assertEqual(seen, [])


class FallbackToTcp(unittest.TestCase):
    # msg_ping(): the frames go into the TCP stream when less than 60% of
    # the UDP bytes came in, three pings in a row, unless 90% came in
    # since the last ping; frames every 50 ms, pings as the server sends
    # them (once a kbyte is sent, then 0.8 s later, 0.2 s more each time,
    # up to 2.4 s); 'old' servers send whole kbytes only

    def setUp(self, old=False):
        pf = self.pf = pclient.Playfield.__new__(pclient.Playfield)
        pf.transport = mock.Mock()
        pf.checkcfgfile = lambda: None
        pf.initlevel = 1
        pf.udpsock_low = 0
        pf.udpbytecounter = 0
        pf.udpwindow = [(0, 0)]
        pf.udppings = 0
        self.fallback = None
        def start_udp_over_tcp():
            self.fallback = self.now
            pf.udpsock_low = None
        pf.start_udp_over_tcp = start_udp_over_tcp
        self.old = old
        self.now = 0.0
        self.sent = 0           # bytes, as the server counts them
        self.lastping = 0.0
        self.delay = 0.6

    def play(self, seconds, rate=3.5, lost=lambda t: False):
        # 'rate' kbytes per second; 'lost(t)': the frame at t is lost
        end = self.now + seconds
        frame = int(rate * 1024 * 0.05)
        while self.now < end - 1e-9 and self.fallback is None:
            self.now = round(self.now + 0.05, 2)
            self.sent += frame
            if not lost(self.now):
                self.pf.udpbytecounter += frame
            if (self.now - self.lastping > self.delay + 1e-9 and
                    self.sent >= 1024):
                values = (self.sent >> 10,)
                if not self.old:
                    values += (self.sent & 1023,)
                with mock.patch('builtins.print'):
                    self.pf.msg_ping(*values)
                self.lastping = self.now
                self.delay = min(self.delay + 0.2, 2.4)

    def both(self):
        for old in (False, True):
            self.setUp(old)
            yield old

    def test_nothing_ever_received(self):
        for old in self.both():
            self.play(10, lost=lambda t: True)
            # 0.6 s after connecting (the 1st kbyte was at 0.3 s), then
            # 0.8 s and 1.0 s later
            self.assertAlmostEqual(self.fallback, 2.55, msg=old)

    def test_nothing_received_from_a_slow_start(self):
        # whole kbytes: the first pings may say the same one, which says
        # nothing, unless nothing came in at all, as here
        self.setUp(old=True)
        self.play(2.9, rate=0.5, lost=lambda t: True)
        pings = self.pf.udppings
        self.play(10, lost=lambda t: True)
        self.assertEqual(pings, 2)      # at 2.05 and 2.9 s: 1 kbyte each
        # strikes at the 1st, 2nd and 3rd ping
        self.assertAlmostEqual(self.fallback, 3.95, delta=0.06)

    def test_server_cannot_send_frames(self):
        # every ping says the same: the most the message holds, or for
        # an older server on 32-bit, sys.maxsize; in whole kbytes from an
        # old server
        for values in ((0x7FFFFFFF, 1023), (0x7FFFFFFF,),
                       ((2**31 - 1) >> 10, 1023)):
            self.setUp()
            for ping in range(1, 10):
                with mock.patch('builtins.print'):
                    self.pf.msg_ping(*values)
                if self.fallback is not None:
                    break
            self.assertEqual(ping, 3, values)

    def test_blackout(self):
        for old in self.both():
            for start in (0.0, 0.5, 1.2, 2.0):  # where between two pings
                self.setUp(old)
                self.play(300 + start)
                begin = self.now
                self.play(60, lost=lambda t: True)
                self.assertTrue(12 <= self.fallback - begin <= 15.5,
                                (old, start, self.fallback - begin))

    def test_blackout_that_ends(self):
        for old in self.both():
            for rate in (3.5, 2.7, 0.8):
                for start in (0.0, 0.35, 0.9, 1.6):
                    for length in (5, 7, 9, 10):
                        self.setUp(old)
                        self.play(300 + start, rate=rate)
                        end = self.now + length
                        self.play(120, rate=rate, lost=lambda t: t <= end)
                        self.assertIsNone(self.fallback,
                                          (old, rate, start, length))

    def test_steady_loss(self):
        for old in self.both():
            self.play(600, lost=lambda t: int(t * 20) % 10 < 3)     # 30%
            self.assertIsNone(self.fallback, old)
            self.setUp(old)
            self.play(600, lost=lambda t: int(t * 20) % 2 == 0)     # 50%
            self.assertIsNotNone(self.fallback, old)

    def test_slow_game(self):
        for old in self.both():
            self.play(600, rate=0.8)
            self.assertIsNone(self.fallback, old)
            begin = self.now
            self.play(60, rate=0.8, lost=lambda t: True)
            self.assertTrue(12 <= self.fallback - begin <= 15.5, old)

    def test_window_size(self):
        self.play(300)
        self.assertEqual(len(self.pf.udpwindow), 9)     # 8 ping spacings

if __name__ == '__main__':
    unittest.main()
