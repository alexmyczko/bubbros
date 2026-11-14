# nonfree/: sounds of unknown licence

This folder holds the 14 sounds of the subgames (bubbob/ext1 to ext7),
under the same paths they had in bubbob/.  They are kept, not deleted,
but they have no known author and no licence, and some are music from
commercial games.  The game plays them from here, as before.  A
distribution can leave this folder out, and the game then plays those
subgames without sound (common/gamesrv.py, soundpath()); putting the
folder back, for example from a separate package, brings the sounds back.

| File | What it is |
|---|---|
| ext1/music.wav | Taito's Arkanoid intro theme, same arrangement as NES Arkanoid |
| ext2/music.wav | the Pac-Man start jingle (Namco 1980) over a funk loop |
| ext4/music.wav | the Game Boy Tetris A-Type music (Nintendo 1989), recorded from the game |
| ext3, ext5, ext6, ext7 music.wav | not identified |
| ext5/ouch.wav, ext6/crash.wav | not identified |
| ext1/brick.wav, ext1/wall.wav, ext3/shoot.wav, ext7/fire.wav, ext7/hit.wav | generated tones and noise, author unknown |

## What was said before

- Armin Rigo added all 14 files to CVS between June 2003 and June 2005.
  The logs name no source; ext7's says only "Red Baron music."
  (CVS repository: https://sourceforge.net/code-snapshots/cvs/b/bu/bub-n-bros.zip,
  also in this repository's history.)
- The site said "Almost all sprite images, sounds, background musics and
  levels are directly taken from the MacOS version of Bub & Bob 1 by
  McSebi".  That text is from May 2003, before the first of these files:
  https://web.archive.org/web/20030506000913/http://bub-n-bros.sourceforge.net:80/authors.html
- McSebi released "the graphics and sound data" of his own game under the
  Artistic License in 2005 (LICENSE.txt), and again in 2009 as
  Artistic-2.0 (artistic.txt; Mandriva's note of that mail:
  https://github.com/OpenMandrivaAssociation/bubbros/blob/1f2138cc/bubbros.spec).
  These sounds are not in his game: compared with Bub & Bob 1 versions
  1.2, 1.6.3 and 1.7.3, no file matches (https://macintoshgarden.org/games/bub-bob,
  https://archive.org/download/tucows_205607_Bub_And_Bob/bubandbob.sit).
- Debian shipped them from 2008 to 2019 as Artistic, copied from
  LICENSE.txt (https://snapshot.debian.org/package/bubbros/), and other
  distributions did the same.  In https://bugs.debian.org/934972 (2019) a
  user said the graphics were copied from Taito's Bubble Bobble; the bug
  was closed with "Bubbros has a DFSG-compliant license".  That answer was
  about LICENSE.txt, and nobody checked the subgame sounds.  The first
  Debian ITP, https://bugs.debian.org/308148, mentioned "some legal
  problems which need to be figured out first", without detail.
- Asked in November 2026, Armin wrote: "I have absolutely no idea any more
  where the music came from." (RELICENSING-PERMISSIONS.md)

## What was checked (November 2026)

Nothing names a source for these files in:

- the CVS history: https://sourceforge.net/code-snapshots/cvs/b/bu/bub-n-bros.zip
- the old site on the Wayback Machine, 2003 to 2008:
  https://web.archive.org/web/2003*/bub-n-bros.sourceforge.net*
- the SourceForge forum, trackers and file releases:
  https://sourceforge.net/p/bub-n-bros/discussion/ ,
  https://sourceforge.net/p/bub-n-bros/bugs/ ,
  https://sourceforge.net/p/bub-n-bros/patches/ ,
  https://sourceforge.net/p/bub-n-bros/feature-requests/ ,
  https://sourceforge.net/projects/bub-n-bros/files/
- pypy-dev, 2003 to 2008: https://mail.python.org/pipermail/pypy-dev/
- the #pypy IRC logs around the ext6 and ext7 commits (April and June
  2005): https://web.archive.org/web/2007/http://tismerysoft.de/pypy/irc-logs/pypy/
- the Debian bugs: https://bugs.debian.org/cgi-bin/pkgreport.cgi?src=bubbros;archive=both

The music was compared by sound against about 3000 game soundtracks and
modules from https://modarchive.org , https://www.zophar.net/music ,
https://ftp.modland.com and free games in Debian:

- ext4/music.wav is the Game Boy Tetris A-Type track, note for note, at
  the same tempo and tuning: track 1 of DMG-TRA-1.gbs in
  https://fi.zophar.net/soundfiles/gameboy-gbs/tetris/Tetris%20%28EMU%29.zophar.zip
- ext1/music.wav has the notes, rhythm and drums of NES Arkanoid's intro,
  one semitone lower:
  https://fi.zophar.net/soundfiles/nintendo-nes-nsf/arkanoid/4%20-%20Track%204.mp3
- ext2/music.wav: its melody is the Pac-Man start jingle (Namco 1980),
  found by writing down its notes; the backing is not from Pac-Man.

## Replacing them

The game loads each file by name, so a free sound with the same name in
bubbob/extN/ replaces the one here.  Candidates: new recordings or
compositions under a free licence, CC0 or CC-BY sounds (opengameart.org,
freesound.org), or sounds from free games already in Debian.  Record the
author and licence of each in RELICENSING-PERMISSIONS.md.
