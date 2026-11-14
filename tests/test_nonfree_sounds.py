"""The ext1..ext7 sounds live in nonfree/ (see nonfree/README.md).  The
subgames find them there, and play silently when that folder is not
installed."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), os.pardir))
EXTS = ['ext%d' % i for i in range(1, 8)]


def run(root, ext):
    out = subprocess.run(
        [sys.executable, os.path.join(root, 'tests', 'subgame_run.py'),
         ext, '400'], capture_output=True, text=True, timeout=300)
    if out.returncode != 0:
        raise AssertionError('%s failed:\n%s%s' % (ext, out.stdout,
                                                   out.stderr))
    return out.stdout


class NonFreeSounds(unittest.TestCase):

    def test_every_sound_is_in_nonfree(self):
        # nothing is left behind in bubbob/ext*/, and nothing is missing
        for ext in EXTS:
            d = os.path.join(ROOT, 'bubbob', ext)
            self.assertEqual([f for f in os.listdir(d) if f.endswith('.wav')],
                             [], ext)
        for ext in EXTS:
            out = run(ROOT, ext)
            sounds = [l.split() for l in out.splitlines()
                      if l.startswith('SOUND')]
            self.assertTrue(sounds, ext)
            for _, name, path in sounds:
                # ext7 also uses ext6's crash.wav
                self.assertRegex(path, r'^nonfree/bubbob/ext\d/\w+\.wav$')
            self.assertIn('PLAYING %s/music.wav\n' % ext, out)
            self.assertIn('END 400', out)

    def test_subgames_without_nonfree(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        root = os.path.join(tmp, 'tree')
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(
            'nonfree', '.git', '__pycache__'))
        for ext in EXTS:
            out = run(root, ext)
            for line in out.splitlines():
                if line.startswith('SOUND'):
                    self.assertTrue(line.endswith(' none'), line)
            self.assertIn('PLAYING nothing\n', out)
            self.assertIn('END 400', out)


if __name__ == '__main__':
    unittest.main()
