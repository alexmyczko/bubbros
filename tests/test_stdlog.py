"""The game server's log file keeps only its last part.  No network."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'common')]

import stdlog


class LogSize(unittest.TestCase):

    def test_a_full_log_is_cut_not_fatal(self):
        d = tempfile.mkdtemp()
        name = os.path.join(d, 'BubBob.log')
        self.addCleanup(os.rmdir, d)
        self.addCleanup(os.unlink, name)
        with open(name, 'w') as f:
            f.write('old line é\n' * 4000)      # more than the limit
        log = stdlog.LogFile(name, limitsize=32768)
        print('new line', file=log)
        log.close()
        with open(name, encoding='utf-8') as f:
            data = f.read()
        self.assertTrue(data.startswith('(...)'))
        self.assertTrue(data.endswith('new line\n'))
        self.assertLess(len(data.encode()), 32768)


if __name__ == '__main__':
    unittest.main()
