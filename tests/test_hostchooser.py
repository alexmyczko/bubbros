"""The answers to the pings that find the game servers (hostchooser.py)."""

import os
import sys
import unittest
from unittest import mock

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common')]

import hostchooser
from hostchooser import PING_MESSAGE, PONG_MESSAGE, DESCR_SIZE, EXTRA_SIZE


class Pong(unittest.TestCase):

    def answer(self, *args):
        # what answer_ping() sends to a ping
        sent = []
        class Sock:
            def recvfrom(self, size):
                return PING_MESSAGE.encode('ascii'), ('x', 1)
            def sendto(self, data, addr):
                sent.append(data)
        with mock.patch('sys.stderr'):
            hostchooser.answer_ping(Sock(), *args)
        return sent[0]

    def fields(self, *args):
        fields = self.answer(*args).decode('utf-8', 'replace').split(':')
        self.assertEqual(fields[0], PONG_MESSAGE)
        return fields[1:]

    def test_fields(self):
        self.assertEqual(
            self.fields('Bub & Bob Levels', ('', 8000), 'one player', 8001),
            ['Bub & Bob Levels', '', '8000', 'one player', '8001'])

    def test_no_separator_in_the_texts(self):
        # the description ends with the name of the level file
        self.assertEqual(
            self.fields('Bub & Bob a:b', ('', 8000), 'x:y', 8001),
            ['Bub & Bob a b', '', '8000', 'x y', '8001'])

    def test_texts_are_cut(self):
        self.assertEqual(self.fields('d' * 300, ('', 8000), 'e' * 300, 8001),
                         ['d' * DESCR_SIZE, '', '8000', 'e' * EXTRA_SIZE,
                          '8001'])

    def test_longest_answer(self):
        # what the readers read of it: 200 bytes
        self.assertEqual(len(self.answer('d' * 300, ('255.255.255.255', 65535),
                                         'e' * 300, 65535)), 198)

    def test_answer_of_a_client(self):
        # a playing client answers with the server it plays on
        self.assertEqual(self.fields('Bub & Bob', ('10.0.0.1', 8000)),
                         ['Bub & Bob', '10.0.0.1', '8000', '', ''])


if __name__ == '__main__':
    unittest.main()
