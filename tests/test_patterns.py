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


class LevelPatmap(unittest.TestCase):
    "A level's own 'patmap' (see levels/PatternDemo/PatternDemo.py)."

    def setUp(self):
        import boards, gamesrv
        self.boards, self.gamesrv = boards, gamesrv
        saved = (getattr(boards, 'haspat', None),
                 getattr(boards, 'loadpattern', None), gamesrv.game, os.getcwd())
        def restore():
            boards.haspat, boards.loadpattern, gamesrv.game = saved[:3]
            os.chdir(saved[3])
        self.addCleanup(restore)
        os.chdir(os.path.join(ROOT, 'bubbob'))      # as the game runs
        boards.haspat = images.haspat               # what loadmodules() does
        boards.loadpattern = images.loadpattern
        self.levels = self.load(os.path.join(ROOT, 'bubbob', 'levels',
                                             'PatternDemo', 'PatternDemo.py'))

    def load(self, levelfile):
        self.gamesrv.game = type('Game', (), {
            'levelfile': levelfile, 'finalboard': None,
            'FnBasePath': 'bubbob'})()
        d = {}
        with open(levelfile) as f:
            exec(compile(f.read(), levelfile, 'exec'), d)
        return d

    def pattern(self, board, key):
        bitmap, rect = board.loadpattern(key)
        return getattr(bitmap, 'filename', None), rect

    def test_own_folder(self):
        b = self.levels['level01'](0)
        self.assertTrue(b.haspat((0, 0)))
        self.assertFalse(b.haspat((1, 0)))
        self.assertTrue(b.haspat(('l',)))
        self.assertFalse(b.haspat(('r',)))
        self.assertEqual(self.pattern(b, (0, 0)),
                         ('levels/PatternDemo/walls.ppm', (0, 0, 24, 24)))
        self.assertEqual(self.pattern(b, ('l',)),
                         ('levels/PatternDemo/borders.ppm', (0, 0, 40, 32)))

    def test_stamp(self):
        b = self.levels['level02'](1)
        for key in ((0, 0), (1, 0), (0, 1), (1, 1), ('l',), ('r',)):
            self.assertTrue(b.haspat(key), key)
        self.assertFalse(b.haspat((2, 0)))
        self.assertFalse(b.haspat((0, 2)))
        self.assertEqual(self.pattern(b, (1, 1))[1], (0, 96, 24, 24))
        self.assertEqual(b.patget((1, 0)).h, 24)

    def test_game_sheets_as_fallback(self):
        b = self.levels['level03'](2)
        self.assertEqual(self.pattern(b, (0, 0)),
                         ('tmp/pat09.ppm', (0, 0, 24, 24)))

    def test_no_patmap(self):
        b = self.levels['level04'](3)
        bitmap, rect = images.loadpattern((3, 0, 0))
        self.assertEqual(self.pattern(b, (0, 0)), (bitmap.filename, rect))
        self.assertEqual(b.haspat(('l',)), images.haspat((3, 'l')))

    def test_tuple_key_for_borders(self):
        class level(self.levels['level01']):
            patmap = {(0, 0): ('walls.ppm', (0, 0, 24, 24)),
                      ('r',): ('borders.ppm', (0, 64, 40, 32))}
        b = level(0)
        self.assertFalse(b.haspat(('l',)))
        self.assertEqual(self.pattern(b, ('r',))[1], (0, 64, 40, 32))

    def test_outside_the_game_folder(self):
        # the clients cannot know such a path: the data is sent
        import shutil, tempfile
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        src = os.path.join(ROOT, 'bubbob', 'levels', 'PatternDemo')
        for fn in ('PatternDemo.py', 'walls.ppm', 'borders.ppm'):
            shutil.copy(os.path.join(src, fn), tmp)
        levels = self.load(os.path.join(tmp, 'PatternDemo.py'))
        bitmap, rect = levels['level01'](0).loadpattern((0, 0))
        self.assertIsInstance(bitmap, self.gamesrv.MemoryBitmap)
        self.assertEqual(rect, (0, 0, 24, 24))
        # the same bitmap for the same file
        self.assertIs(levels['level02'](1).loadpattern((0, 0))[0], bitmap)

    def test_missing_file(self):
        class level(self.levels['level01']):
            patmap = {(0, 0): ('nothing.ppm', (0, 0, 24, 24))}
        self.assertRaises(IOError, level(0).loadpattern, (0, 0))


if __name__ == '__main__':
    unittest.main()
