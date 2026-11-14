"""Start the game server in-process, switch to one subgame (ext1..ext7)
and play it with random inputs.  Used by test_nonfree_sounds.py.

usage: subgame_run.py <ext> <frames>
Prints where each of the subgame's sounds is read from ('none' when
missing), the music playing at the end, then 'END <passes>'.
"""

import os, sys, random, socket

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

ext, nframes = sys.argv[1], int(sys.argv[2])
random.seed(1)
import bb, gamesrv, boards
from player import BubPlayer

game = bb.BubBobGame(os.path.join(BBDIR, 'levels', 'Levels.bin'))

class FakeClient:
    def killplayer(self, player):
        pass

for pn in (0, 1):
    p = BubPlayer.PlayerList[pn]
    p._client = FakeClient()
    p.playerjoin()
    p.setplayername('P%d' % pn)

for frame in range(2000):     # until the first board is in play
    if boards.curboard is not None and boards.curboard.playingboard:
        break
    game.FnFrame()

mod = __import__(ext)
for name in sorted(dir(mod)):
    obj = getattr(mod, name)
    if name == 'music' or name.startswith('snd_'):
        if isinstance(obj, gamesrv.Sample):
            assert obj.read()[:4] == b'RIFF'
            print('SOUND', name, os.path.relpath(obj.path, ROOT))
        elif isinstance(obj, gamesrv.Music):
            assert obj.read((0, 4)) == b'RIFF'
            print('SOUND', name, os.path.relpath(obj.f.name, ROOT))
        else:
            print('SOUND', name, 'none')
mod.run()

KEYS = ['kLeft', 'kRight', 'kJump', 'kFire', 'kmLeft', 'kmRight', 'kmJump',
        'kmFire']
for frame in range(nframes):
    for p in BubPlayer.PlayerList[:2]:
        if random.random() < 0.3:
            getattr(p, random.choice(KEYS))()
    game.FnFrame()
# the subgame's music is what plays now, or nothing when it is missing
playing = [m.filename for m in gamesrv.music_by_id.values()
           if m.fileid in gamesrv.currentmusics[1:]]
print('PLAYING', ' '.join(playing) or 'nothing')
print('END', frame + 1)
