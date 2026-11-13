"""The level sets the control page offers (bubbob/bb.py FnListBoards)."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [os.path.join(ROOT, 'bubbob'), os.path.join(ROOT, 'common')]

import bb


class LevelSets(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        for name in ('levels/Levels.bin', 'levels/Compact.py',
                     'levels/rnglevel', 'levels/README.txt',
                     'levels/pack/Arena.bin', 'levels/pack/notes.txt',
                     'levels/CVS/Entries.py', 'levels/pack/deeper/X.bin'):
            os.makedirs(os.path.dirname(name), exist_ok=True)
            open(name, 'w').close()
        os.makedirs('levels/empty')

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_top_level_and_one_folder_below(self):
        self.assertEqual(bb.BubBobGame.FnListBoards(), [
            ('Compact', 'levels/Compact.py'),
            ('Levels', 'levels/Levels.bin'),
            ('Arena', 'levels/pack/Arena.bin')])

    def test_installed_tree(self):
        # the real levels directory still lists what it always did
        os.chdir(os.path.join(ROOT, 'bubbob'))
        names = [n for n, p in bb.BubBobGame.FnListBoards()]
        self.assertIn('Levels', names)
        self.assertIn('CompactLevels', names)


if __name__ == '__main__':
    unittest.main()
