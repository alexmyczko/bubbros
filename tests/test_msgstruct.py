"""Round trips for the wire format in common/msgstruct.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, 'common'))
import msgstruct
from msgstruct import message, decodemessage


class TestMessage(unittest.TestCase):

    def roundtrip(self, tp, *values):
        data = message(tp, *values)
        self.assertIsInstance(data, bytes)
        decoded, rest = decodemessage(data)
        self.assertEqual(rest, b'')
        self.assertEqual(decoded, (tp,) + values)

    def test_no_arguments(self):
        self.roundtrip(msgstruct.MSG_PING)

    def test_small_and_large_ints(self):
        # 0..255 travel as one byte ('B'), anything else as 'l'
        self.roundtrip(msgstruct.MSG_DEF_ICON, 0, 255, 256, -1, 2**31 - 1)

    def test_bytes_values(self):
        self.roundtrip(msgstruct.MSG_DEF_BITMAP, 7, b'\x00\xff' * 300, b'')

    def test_every_code_is_one_byte(self):
        for name in dir(msgstruct):
            if name.startswith(('MSG_', 'CMSG_')) and name != 'MSG_WELCOME':
                value = getattr(msgstruct, name)
                self.assertIsInstance(value, bytes, name)
                self.assertEqual(len(value), 1, name)
                self.roundtrip(value, 1)

    def test_str_value_is_rejected(self):
        with self.assertRaises(TypeError):
            message(msgstruct.MSG_DEF_BITMAP, 'not bytes')

    def test_stream_of_messages(self):
        stream = (message(msgstruct.MSG_PING, 1) +
                  message(msgstruct.MSG_PONG, b'abc') +
                  message(msgstruct.MSG_FADEOUT, 300))
        out = []
        while stream:
            msg, stream = decodemessage(stream)
            out.append(msg)
        self.assertEqual(out, [(msgstruct.MSG_PING, 1),
                               (msgstruct.MSG_PONG, b'abc'),
                               (msgstruct.MSG_FADEOUT, 300)])

    def test_partial_message_waits_for_more_data(self):
        data = message(msgstruct.MSG_PONG, b'hello')
        for cut in range(len(data)):
            self.assertEqual(decodemessage(data[:cut]), (None, data[:cut]))


if __name__ == '__main__':
    unittest.main()
