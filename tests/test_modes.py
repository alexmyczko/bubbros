"""Which graphics driver the client picks when none is asked for."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, 'display'))
import modes


def pick(available):
    """The driver findmode() picks when only 'available' can be used."""
    lst = modes.graphicmodeslist()
    for mode in lst:
        # what Mode.imperror() caches: a message if the driver cannot load
        mode._Mode__imperror = (mode.name not in available) and 'not installed'
    return modes.findmode(None, lst).name


class TestDriverChoice(unittest.TestCase):

    def test_pygame_before_x11(self):
        # X11 cannot resize, scale or go full screen
        self.assertEqual(pick({'X', 'pygame', 'gtk'}), 'pygame')

    def test_gtk_before_x11(self):
        self.assertEqual(pick({'X', 'gtk'}), 'gtk')

    def test_x11_as_last_resort(self):
        self.assertEqual(pick({'X'}), 'X')

    def test_x11_on_request(self):
        lst = modes.graphicmodeslist()
        for mode in lst:
            mode._Mode__imperror = False
        self.assertEqual(modes.findmode('x', lst).name, 'X')


if __name__ == '__main__':
    unittest.main()
