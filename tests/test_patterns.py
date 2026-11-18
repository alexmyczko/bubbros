"""The wall patterns of the .py level sets (bubbob/patmap.py)."""

import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [os.path.join(ROOT, 'bubbob'), os.path.join(ROOT, 'common')]

# the game reads its images relative to its own directory
_cwd = os.getcwd()
os.chdir(os.path.join(ROOT, 'bubbob'))
try:
    import images
finally:
    os.chdir(_cwd)


class GlobalPatmap(unittest.TestCase):

    def test_boards_from_100_repeat_the_first_100(self):
        # board 26 has a 2x2 stamp and border pieces: so has board 126
        for n in (126, 226):
            for key in ((0, 0), (1, 0), (0, 1), (1, 1), ('l',)):
                self.assertTrue(images.haspat((n,) + key), (n, key))
                self.assertEqual(images.loadpattern((n,) + key),
                                 images.loadpattern((26,) + key))
            self.assertFalse(images.haspat((n, 2, 0)))
            self.assertFalse(images.haspat((n, 'r')))


if __name__ == '__main__':
    unittest.main()
