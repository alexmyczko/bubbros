"""The client tells the game server where to send the UDP frames.  Through
the meta-server that address is the one seen from outside.  No network."""

import os
import sys
import unittest
from socket import socket, AF_INET, SOCK_DGRAM

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common'), os.path.join(ROOT, 'display')]

from common import msgstruct
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
        pf.snd = None
        pf.pending_udp_data = None
        pf.iwtd, pf.initial_iwtd = [], []
        pf.startplaying()
        msg = msgstruct.message(msgstruct.CMSG_UDP_PORT, 4321, b'203.0.113.5')
        self.assertEqual(pf.s.sent, msg)


if __name__ == '__main__':
    unittest.main()
