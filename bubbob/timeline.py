"""Going back in time on the current board.

The Time Machine (Clock) bonus brings the game back to an earlier
moment.  Everything that moves in the game is driven by a generator,
and generators cannot be copied, so the earlier state is not saved:
it is computed again.  What happens on a board depends only on

  - the state of the board when normal play starts,
  - the state of the random generators at that moment, and
  - the players' inputs: keys, joining, leaving, changing name.

So at the start of normal play on each board we take a checkpoint of
the plain data (no generators), and we log every input with the
number of the "pass" before which it arrived (a pass is one step of
all the board generators, see boards.run_pass()).  To go back to pass
N, we rebuild the board from the checkpoint and run the passes again
up to N, applying the logged inputs, without sounds.  The clients get
no frames during that time: frames are sent between the passes of the
live game, and the game simply continues from the recomputed state.

The rest of the game needs nothing special for this to work, as long
as it stays deterministic: no wall-clock time, no iteration over sets
of objects, and all randomness from the generators saved here.
tests/test_timeline.py checks this.
"""

import copy
import random
import gamesrv


# number of passes run since the server started (boards.run_pass())
passes = 0

checkpoint = None           # dict, see take_checkpoint()
checkpoint_requested = False
events = {}                 # {pass: [(player number, method, args)]}
replaying = False


# BubPlayer class attributes that bonuses change during a board
GLOBAL_ATTRS = ('FrameCounter', 'LimitScore', 'LimitScoreColor',
                'LimitTime', 'MultiplyerReset', 'PlayersPrivateTime',
                'Moebius', 'HighScore', 'HighScoreColor', 'LatestLetsGo')
_MISSING = object()


def request_checkpoint():
    """Called by boards.next_board() when normal play is about to start."""
    global checkpoint_requested
    checkpoint_requested = True

def forget():
    """No going back into this board (e.g. a bonus level)."""
    global checkpoint, checkpoint_requested
    checkpoint = None
    checkpoint_requested = False
    events.clear()

def begin_pass():
    """Called by boards.run_pass() before each pass."""
    global passes, checkpoint_requested, checkpoint
    passes += 1
    if replaying:
        for pn, method, args in events.get(passes, ()):
            _apply(pn, method, args)
    elif checkpoint_requested:
        checkpoint_requested = False
        events.clear()
        import boards
        if len(boards.BoardGen) == 1:
            checkpoint = take_checkpoint()
        else:
            # _rebuild() only recreates normal_play(); with other
            # board generators running, this board cannot be rewound
            checkpoint = None

def has_checkpoint():
    """True if this board has a checkpoint to go back to."""
    import boards
    return (checkpoint is not None and boards.curboard is not None and
            boards.curboard.num == checkpoint['num'])

def can_rewind():
    return has_checkpoint() and not replaying


# ____________________________________________________________
# Inputs

def recorded(method):
    """Decorator for the BubPlayer methods called by the network:
    the call is logged, then done."""
    name = method.__name__
    def wrapper(self, *args):
        if checkpoint is not None and not replaying:
            events.setdefault(passes + 1, []).append((self.pn, name, args))
        return method(self, *args)
    wrapper.__name__ = name
    wrapper.__doc__ = method.__doc__
    return wrapper

class _ReplayClient:
    # stands for the network client of a player during a replay;
    # gamesrv.Player.isplaying() only checks that there is one
    def killplayer(self, player):
        pass

def _apply(pn, method, args):
    p = _player(pn)
    if method == 'playerjoin':
        p._client = _ReplayClient()
    elif method == 'playerleaves':
        try:
            del p._client
        except AttributeError:
            pass
    getattr(p, method)(*args)

def _player(pn):
    from player import BubPlayer
    for p in BubPlayer.PlayerList:
        if p.pn == pn:
            return p
    raise KeyError(pn)


# ____________________________________________________________
# Checkpoint

def _copy(value):
    # a deep copy of plain player data.  The players themselves are
    # permanent objects (e.g. stats['catch'] is keyed by player): keep
    # them as they are, do not copy them.
    from player import BubPlayer
    memo = dict([(id(p), p) for p in BubPlayer.PlayerList])
    return copy.deepcopy(value, memo)

def take_checkpoint():
    import boards, bonuses, images
    from player import BubPlayer
    cp = {}
    cp['pass'] = passes
    cp['num'] = boards.curboard.num
    cp['random'] = random.getstate()
    cp['bonusrandom'] = (bonuses.random, bonuses.random.getstate())
    cp['localrandom'] = bonuses.DustStar.localrandom.getstate()
    cp['extensions'] = list(bonuses.Potion.Extensions)
    cp['cheat'] = list(bonuses.Cheat)
    # the scoreboard as shown: Board.enter() draws it between two
    # shuffles of PlayerList, so it cannot be redrawn from the data
    cp['scoreboard'] = [(s.x, s.y, s.ico) for s in
                        boards.curboard.sprites.get('scoreboard', [])]
    cp['globals'] = dict([(name, getattr(BubPlayer, name, _MISSING))
                          for name in tuple(BubPlayer.INIT_BOARD_CAP)
                                      + GLOBAL_ATTRS])
    cp['players'] = []
    for p in BubPlayer.PlayerList:
        d = {}
        for key, value in list(p.__dict__.items()):
            if key not in BubPlayer.TRANSIENT_DATA and key != 'dragons':
                d[key] = _copy(value)
        keys = (p.key_left, p.key_right, p.key_jump, p.key_fire)
        cp['players'].append((p.pn, p.isplaying(), d, keys))
    cp['dragons'] = [(d.bubber.pn, d.x, d.y, d.dir, dict(d.dcap))
                     for d in BubPlayer.DragonList]
    cp['monsters'] = [(m.__class__, m.mdef, m.dir)
                      for m in BubPlayer.MonsterList]
    return cp

def _rebuild(cp):
    import boards, bonuses, images, player
    from player import BubPlayer, Dragon
    # remove everything from the current board
    for s in images.ActiveSprites[:]:
        s.kill()
    del BubPlayer.DragonList[:]
    del BubPlayer.MonsterList[:]
    for p in BubPlayer.PlayerList:
        del p.dragons[:]
    for t in boards.curboard.leave(inplace=1):
        pass
    player.reset_global_board_state()
    boards.set_frametime(1.0)
    # enter the same board again
    brd = boards.BoardList[cp['num']](cp['num'])
    for t in brd.enter(complete=0, inplace=1):
        pass
    brd.playingboard = 1
    # players as they were, playing or not (this also gives back their
    # letters, which are numbers at the checkpoint, not sprites)
    byn = dict([(p.pn, p) for p in BubPlayer.PlayerList])
    BubPlayer.PlayerList[:] = [byn[pn] for pn, _, _, _ in cp['players']]
    for pn, playing, d, keys in cp['players']:
        p = byn[pn]
        p.__dict__.update(_copy(d))
        p.key_left, p.key_right, p.key_jump, p.key_fire = keys
        if playing and not p.isplaying():
            p._client = _ReplayClient()
        elif not playing and p.isplaying():
            del p._client
    player.scoreboard(1, inplace=1)
    brd.writesprites('scoreboard', cp['scoreboard'])
    # dragons and monsters as they were
    for pn, x, y, dir, dcap in cp['dragons']:
        d = Dragon(byn[pn], x, y, dir)
        d.dcap = dict(dcap)
        byn[pn].dragons.append(d)
    for cls, mdef, dir in cp['monsters']:
        cls(mdef, dir=dir)
    for name, value in cp['globals'].items():
        if value is _MISSING:
            if name in BubPlayer.__dict__:
                delattr(BubPlayer, name)
        else:
            setattr(BubPlayer, name, value)
    bonuses.Potion.Extensions[:] = cp['extensions']
    bonuses.Cheat[:] = cp['cheat']
    bonuses.bigclockticker = None
    random.setstate(cp['random'])
    bonusrandom, state = cp['bonusrandom']
    bonuses.random = bonusrandom
    bonusrandom.setstate(state)
    bonuses.DustStar.localrandom.setstate(cp['localrandom'])
    boards.BoardGen[:] = [boards.normal_play()]


# ____________________________________________________________
# Going back

def rewind(target):
    """Bring the game back to the end of pass 'target', on the
    current board.  Returns False if that is not possible."""
    global passes, replaying
    import boards, player
    from player import BubPlayer
    cp = checkpoint
    if not can_rewind() or not (cp['pass'] <= target < passes):
        return False
    # who is really connected now; the replay must not touch them
    clients = {}
    for p in BubPlayer.PlayerList:
        if p.isplaying():
            clients[p.pn] = p._client
    replaying = True
    gamesrv.sounds_muted += 1
    try:
        _rebuild(cp)
        passes = cp['pass'] - 1
        while passes < target:
            boards.run_pass()
    finally:
        replaying = False
        gamesrv.sounds_muted -= 1
    # forget the inputs of the future we just left
    for n in list(events):
        if n > target:
            del events[n]
    # put the real network clients back.  A player connected now who
    # was not playing at 'target' joins now; one who has left since
    # leaves now.  Both are logged as usual for later rewinds.
    for p in BubPlayer.PlayerList:
        playing = p.isplaying()
        if p.pn in clients:
            p._client = clients[p.pn]
            if not playing:
                p.playerjoin()
        elif playing:
            del p._client
            p.playerleaves()
    return True
