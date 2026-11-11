"""Tests for bubbob/timeline.py and the Time Machine (clock) bonus.

Each game runs in its own process (timeline_run.py), with two players
and scripted inputs, and prints a digest of the screen after every
pass:  'P <pass> <board> <screen bytes> <sprites, points and lives>'.
"""

import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run(*args, hashseed='1'):
    env = dict(os.environ, PYTHONHASHSEED=hashseed)
    out = subprocess.run([sys.executable, os.path.join(HERE, 'timeline_run.py')]
                         + [str(a) for a in args],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env, check=True, universal_newlines=True)
    assert 'Traceback' not in out.stderr, out.stderr
    return out.stdout.splitlines()

def passes(lines, after=None):
    """{pass: (screen digest, state digest)}, from the line 'after' on."""
    result = {}
    started = after is None
    for line in lines:
        if not started:
            started = line.startswith(after)
            if not started:
                continue
            if line.startswith('REWOUND'):
                _, ok, n, raw, state = line.split()
                result[int(n)] = (raw, state)
                continue
        if line.startswith('P '):
            _, n, board, raw, state = line.split()
            result[int(n)] = (raw, state)
    return result

def line_with(lines, prefix):
    return [l for l in lines if l.startswith(prefix)][0]


class TestTimeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.plain = run('plain', 5, 1500)

    def test_game_is_deterministic(self):
        # same seed and inputs, different hash seeds: the same game, to
        # the byte, across a change of board
        other = run('plain', 5, 1500, hashseed='2')
        self.assertEqual(passes(self.plain), passes(other))
        boards = set(l.split()[2] for l in self.plain if l.startswith('P '))
        self.assertTrue(len(boards) >= 3, boards)  # -1 (between), 0, 1

    def check_rewind(self, frame, back):
        lines = run('rewind', 5, 1500, frame, back)
        self.assertIn('REWOUND True', line_with(lines, 'REWOUND'))
        before = passes(self.plain)
        after = passes(lines, after='REWOUND')
        self.assertTrue(len(after) > 100)
        # the state at the target, and every pass after it with the
        # same inputs, is the one of the game that never went back
        for n in sorted(after):
            self.assertEqual(after[n], before[n], 'pass %d' % n)

    def test_rewind_short(self):
        self.check_rewind(300, 200)

    def test_rewind_long(self):
        # 1644 passes are computed again
        self.check_rewind(1200, 700)

    def test_no_rewind_to_another_board(self):
        lines = run('rewind', 5, 1500, 1300, 1250)
        self.assertIn('REWOUND False', line_with(lines, 'REWOUND'))

    def test_clock(self):
        # the game drops a Time Machine; when a dragon takes it, the
        # game goes back to the moment the clock appeared
        lines = run('clock', 5, 600)
        saved = int(line_with(lines, 'CLOCK saved').split()[3].rstrip(','))
        states = [l.split()[4] for l in lines if l.startswith('P %d ' % saved)]
        self.assertEqual(len(states), 2, 'the game came back to pass %d' % saved)
        self.assertEqual(states[0], states[1])
        self.assertTrue(any(l.startswith('Re - Entering board') for l in lines))

    def test_big_clock(self):
        # the big clock replays the whole board with the ghosts of the
        # dragons of the first time
        lines = run('bigclock', 5, 600)
        self.assertTrue(any(l.startswith('BIGCLOCK given') for l in lines))
        self.assertTrue(any(l.startswith('Re - Entering board') for l in lines))
        self.assertTrue(any(l.startswith('BIGCLOCK 2 ghosts') for l in lines),
                        [l for l in lines if l.startswith('BIGCLOCK')])


if __name__ == '__main__':
    unittest.main()
