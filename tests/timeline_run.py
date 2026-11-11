"""Run the game server in-process, with scripted inputs, and print one
line per pass: pass number, board, and digests of the screen.  Used by
test_timeline.py; it starts the game but no client connects.

usage: timeline_run.py <mode> <seed> <frames> [args]
  mode 'plain'          just play
  mode 'rewind K D'     at frame K, timeline.rewind() D passes back
  mode 'clock'          bring a Time Machine (small clock) to a dragon
  mode 'bigclock'       the same with the big clock (replay with ghosts)
"""

import os, sys, hashlib, socket

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
BBDIR = os.path.join(ROOT, 'bubbob')
sys.path[:0] = [BBDIR, os.path.join(ROOT, 'common')]
os.chdir(BBDIR)

def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

import msgstruct
msgstruct.PORTS['LISTEN'] = free_port()
msgstruct.PORTS['HTTP'] = free_port()

mode, seed, nframes = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
args = [int(a) for a in sys.argv[4:]]

import random
random.seed(seed)
import bb, gamesrv, boards, images, player, bonuses, timeline
from player import BubPlayer, Dragon

game = bb.BubBobGame(os.path.join(BBDIR, 'levels', 'Levels.bin'))

class FakeClient:
    def killplayer(self, player):
        pass

for pn in (0, 1):
    p = BubPlayer.PlayerList[pn]
    p._client = FakeClient()
    p.playerjoin()
    p.setplayername('P%d' % pn)

if mode == 'clock':
    # let the game itself drop a Time Machine, through its cheat hook
    bonuses.Cheat.append((bonuses.Clock,))
if mode == 'bigclock':
    # the big clock is chosen at the start of a board, as if the bonus
    # class drawn there was the clock; make it the only choice
    saved_classes = bonuses.Classes[:]
    bonuses.Classes[:] = [bonuses.Clock]
random.seed(seed)
bonuses.DustStar.localrandom.seed(seed + 1)
KEYS = ['kLeft', 'kRight', 'kJump', 'kFire', 'kmLeft', 'kmRight', 'kmJump',
        'kmFire']

def inputs_before(n):
    # the inputs that arrive before pass n: a function of n only, so a
    # run that goes back in time gets the same inputs again
    r = random.Random(seed * 100003 + n)
    evs = []
    for pn in (0, 1):
        if r.random() < 0.08:
            evs.append((pn, r.choice(KEYS)))
        if r.random() < 0.3:
            evs.append((pn, 'kFire'))
    return evs

def digest():
    gamesrv.sprites[0] = b''
    raw = hashlib.sha1(b''.join(gamesrv.sprites)).hexdigest()[:12]
    h = hashlib.sha1()
    for s in images.ActiveSprites:
        h.update(('%s %d %d %d;' % (s.__class__.__name__, s.x, s.y,
                                    s.ico.code)).encode())
    for p in BubPlayer.PlayerList:
        h.update(('%r %r;' % (p.points, p.lives)).encode())
    return raw, h.hexdigest()[:12]

# log the state at the end of every pass
_run_pass = boards.run_pass
def logged_run_pass():
    if not timeline.replaying:
        # inputs arrive before a given pass, whatever the grouping of
        # passes into frames (which differs after a rewind)
        for pn, name in inputs_before(timeline.passes + 1):
            player = [p for p in BubPlayer.PlayerList if p.pn == pn][0]
            getattr(player, name)()
    ft = _run_pass()
    if not timeline.replaying:
        raw, logical = digest()
        board = boards.curboard.num if boards.curboard else -1
        print('P %d %d %s %s' % (timeline.passes, board, raw, logical))
    return ft
boards.run_pass = logged_run_pass

clock = None
bigclock_since = None
for frame in range(nframes):
    if mode == 'bigclock' and clock is None and bonuses.bigclockticker:
        bonuses.Classes[:] = saved_classes
        if bigclock_since is None:
            bigclock_since = timeline.passes
            print('BIGCLOCK ticking from pass %d' % timeline.passes)
        dragons = [d for d in BubPlayer.DragonList if isinstance(d, Dragon)]
        if timeline.passes > bigclock_since + 100 and dragons:
            for d in dragons:
                d.dcap['infinite_shield'] = 0
            clock = bonuses.Clock(dragons[0].x, dragons[0].y, 1)
            print('BIGCLOCK given at pass %d' % timeline.passes)
    if mode == 'bigclock' and clock is not None and clock != 'ghosts':
        ghosts = [s for s in images.ActiveSprites
                  if isinstance(s, bonuses.DragonGhost)]
        if ghosts:
            print('BIGCLOCK %d ghosts at pass %d' % (len(ghosts), timeline.passes))
            clock = 'ghosts'
    if mode == 'rewind' and frame == args[0]:
        target = timeline.passes - args[1]
        print('CHECKPOINT %d, NOW %d, TARGET %d' % (
            timeline.checkpoint['pass'], timeline.passes, target))
        ok = timeline.rewind(target)
        raw, logical = digest()
        print('REWOUND %s %d %s %s' % (ok, timeline.passes, raw, logical))
    if mode == 'clock' and clock is None:
        clocks = [s for s in images.ActiveSprites
                  if isinstance(s, bonuses.Clock)]
        if clocks:
            clock = clocks[0]
            print('CLOCK spawned at pass %d' % timeline.passes)
    if (isinstance(clock, bonuses.Clock) and clock.touchable and
            clock.savedpass is not None):
        # bring the clock to a dragon (the clock does not move by itself)
        dragons = [d for d in BubPlayer.DragonList if isinstance(d, Dragon)]
        if dragons:
            print('CLOCK saved pass %d, taken at pass %d'
                  % (clock.savedpass, timeline.passes))
            for d in dragons:
                d.dcap['infinite_shield'] = 0
            clock.move(dragons[0].x, dragons[0].y)
            clock = 'taken'
    game.FnFrame()
print('END %d' % timeline.passes)
