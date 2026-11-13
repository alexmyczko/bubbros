"""The colored images are not rebuilt when they are up to date, also
when every file has the same time, as in a distribution package."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)


class UpToDate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.bubbob = os.path.join(cls.tmp.name, 'bubbob')
        shutil.copytree(os.path.join(ROOT, 'bubbob'), cls.bubbob,
                        ignore=shutil.ignore_patterns('*_[1-9]*.ppm',
                                                      'image1-[1-9]*.ppm'))
        subprocess.run([sys.executable, 'buildcolors.py'], check=True,
                       cwd=os.path.join(cls.bubbob, 'images'),
                       stderr=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def rebuild(self):
        code = ('import sys; import os; ns = {"__name__": "check", "__file__": os.path.abspath("buildcolors.py")}; '
                'exec(open("buildcolors.py").read(), ns); '
                'print(sorted(f for f, r in ns["updatecheck"]().items() if r))')
        out = subprocess.run([sys.executable, '-c', code], check=True,
                             cwd=os.path.join(self.bubbob, 'images'),
                             capture_output=True, text=True).stdout
        return eval(out)

    def test_just_built(self):
        self.assertEqual(self.rebuild(), [])

    def test_same_time_everywhere(self):
        for d, _, files in os.walk(self.bubbob):
            for f in files:
                os.utime(os.path.join(d, f), (1e9, 1e9))
        self.assertEqual(self.rebuild(), [])


if __name__ == '__main__':
    unittest.main()
