"""PipeLayer (metaserver/pipelayer.py): reliable delivery over UDP."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, 'metaserver'))
from pipelayer import PipeLayer


def exchange(data_a, data_b, lose=0.0, reorder=False, seed=0):
    """Send data_a from A to B and data_b from B to A over a simulated
    link that drops a fraction 'lose' of the packets.  Returns what
    each side received."""
    rnd = random.Random(seed)
    a = PipeLayer((1234, 5678))
    b = PipeLayer((5678, 1234))
    for chunk in data_a:
        a.queue(chunk)
    for chunk in data_b:
        b.queue(chunk)
    got_a, got_b = [], []
    clock = 0.0
    for step in range(5000):
        clock += 0.25
        packets = []
        for src, dst, got in ((a, b, got_b), (b, a, got_a)):
            src.settime(clock)
            packet = src.encode(200)
            if packet is not None and rnd.random() >= lose:
                packets.append((dst, got, packet))
        if reorder:
            rnd.shuffle(packets)
        for dst, got, packet in packets:
            dst.settime(clock)
            data = dst.decode(packet)
            assert isinstance(data, bytes)
            got.append(data)
        if (a.in_sync() and b.in_sync() and
                len(b''.join(got_b)) == len(b''.join(data_a)) and
                len(b''.join(got_a)) == len(b''.join(data_b))):
            break
    return b''.join(got_a), b''.join(got_b)


class TestPipeLayer(unittest.TestCase):

    def setUp(self):
        rnd = random.Random(42)
        self.data_a = [bytes(rnd.randrange(256) for i in range(rnd.randrange(1, 500)))
                       for j in range(40)]
        self.data_b = [b'pong %d ' % i for i in range(100)]

    def check(self, **kw):
        got_a, got_b = exchange(self.data_a, self.data_b, **kw)
        self.assertEqual(got_b, b''.join(self.data_a))
        self.assertEqual(got_a, b''.join(self.data_b))

    def test_perfect_link(self):
        self.check()

    def test_lossy_link(self):
        self.check(lose=0.3, seed=1)

    def test_lossy_reordering_link(self):
        self.check(lose=0.2, reorder=True, seed=2)

    def test_short_packet_is_invalid(self):
        from pipelayer import InvalidPacket
        with self.assertRaises(InvalidPacket):
            PipeLayer().decode(b'\xe2')


if __name__ == '__main__':
    unittest.main()
