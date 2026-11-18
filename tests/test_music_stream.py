"""The music each client is told to play is the music streamed to it,
also when the game shortens its playlist without telling the clients
(the cactus: Snd4, then the board's music, see bonuses.cactusbonussound).
A client without the music files needs the data."""

import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [os.path.join(ROOT, 'common')]

import gamesrv
from msgstruct import decodemessage, MSG_MD5_FILE, MSG_PLAY_MUSIC


class FakeClient(gamesrv.Client):
    # only what the music needs: no connection
    def __init__(self):
        self.has_music = 2
        self.musicpos = {}
        self.musiclist = [0]
        self.msgl = []

    def messages(self):
        result = []
        for msg in self.msgl:
            while msg:
                args, msg = decodemessage(msg)
                result.append(args)
        self.msgl = []
        return result


class MusicStream(unittest.TestCase):

    def setUp(self):
        saved = (gamesrv.clients[:], gamesrv.currentmusics[:], gamesrv.game,
                 os.getcwd())
        def restore():
            gamesrv.clients[:], gamesrv.currentmusics[:] = saved[:2]
            gamesrv.game = saved[2]
            os.chdir(saved[3])
        self.addCleanup(restore)
        # paths as the game gives them: relative to its directory
        os.chdir(os.path.join(ROOT, 'bubbob'))
        gamesrv.game = type('Game', (), {'FnBasePath': 'bubbob'})()
        self.modern = gamesrv.getmusic('music/Snd4-8.wav')
        self.intro = gamesrv.getmusic('music/Snd1-8.wav')
        self.game = gamesrv.getmusic('music/Snd2-8.wav')
        self.client = FakeClient()
        gamesrv.clients[:] = [self.client]
        gamesrv.currentmusics[:] = [0]

    def streamed(self, seconds):
        # the file ids of the blocks sent in that many seconds
        self.client.messages()
        for i in range(seconds):
            self.client.sendmusicdata()
        return [m[1] for m in self.client.messages() if m[0] == MSG_MD5_FILE]

    def test_cactus(self):
        # bonuses.cactusbonussound(), with the first ten boards' music
        gamesrv.set_musics([], [])
        gamesrv.set_musics([self.modern, self.intro], [self.game], reset=0)
        play = [m for m in self.client.messages() if m[0] == MSG_PLAY_MUSIC]
        self.assertEqual(play[-1][1:], (2, self.modern.fileid,
                                        self.intro.fileid, self.game.fileid))
        gamesrv.set_musics([self.intro], [self.game], reset=0)
        self.assertEqual(self.client.messages(), [])    # nothing changes
        # so Snd4 must come first, all of it, then Snd1
        seconds = self.modern.endpos // self.modern.filerate
        self.assertEqual(set(self.streamed(seconds)), {self.modern.fileid})
        self.assertEqual(set(self.streamed(3)), {self.intro.fileid})

    def test_new_playlist(self):
        gamesrv.set_musics([self.intro], [self.game])
        self.assertEqual(set(self.streamed(3)), {self.intro.fileid})
        gamesrv.set_musics([self.modern], [self.game])
        self.assertEqual(set(self.streamed(3)), {self.modern.fileid})

    def test_fadeout(self):
        gamesrv.set_musics([self.intro], [self.game])
        self.client.messages()
        gamesrv.fadeout(1.5)
        self.assertEqual(self.streamed(3), [])


if __name__ == '__main__':
    unittest.main()
