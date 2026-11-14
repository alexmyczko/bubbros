# nonfree/: sounds of unknown licence

This folder holds the 14 sounds of the subgames (bubbob/ext1 to ext7),
under the same paths they had in bubbob/.  They are kept, not deleted,
but they have no known author and no licence, and some are music from
commercial games.  A distribution can leave this folder out: the game
then plays those subgames without sound (common/gamesrv.py, soundpath()).

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
- The site said "Almost all sprite images, sounds, background musics and
  levels are directly taken from the MacOS version of Bub & Bob 1 by
  McSebi".  That text is from May 2003, before the first of these files.
- McSebi released "the graphics and sound data" of his own game under the
  Artistic License (2005, LICENSE.txt; again in 2009 as Artistic-2.0).
  These sounds are not in his game: compared with Bub & Bob 1 versions
  1.2, 1.6.3 and 1.7.3, no file matches.
- Debian shipped them from 2008 to 2019 as Artistic, copied from
  LICENSE.txt, and so did other distributions.  In
  https://bugs.debian.org/934972 (2019) a user said the graphics were
  copied from Taito's Bubble Bobble; the bug was closed with "Bubbros has
  a DFSG-compliant license".  That answer was about LICENSE.txt, and nobody
  checked the subgame sounds.  The first Debian ITP,
  https://bugs.debian.org/308148, mentioned "some legal problems which
  need to be figured out first", without detail.
- Asked in November 2026, Armin wrote: "I have absolutely no idea any more
  where the music came from." (RELICENSING-PERMISSIONS.md)

## What was checked (November 2026)

- The full SourceForge CVS history, the old site on the Wayback Machine,
  the SourceForge forum and trackers, pypy-dev, #pypy logs and the Debian
  bugs: nothing names a source.
- The music, by audio comparison against about 3000 game soundtracks and
  modules (modarchive.org, zophar.net, modland, free games in Debian).
  ext4 matches the Game Boy Tetris track note for note, at the same tempo
  and tuning.  ext1 has the notes, rhythm and drums of NES Arkanoid's
  intro.  ext2's melody is the Pac-Man jingle.

## Replacing them

The game loads each file by name, so a free sound with the same name in
bubbob/extN/ replaces the one here.  Candidates: new recordings or
compositions under a free licence, CC0 or CC-BY sounds (opengameart.org,
freesound.org), or sounds from free games already in Debian.  Record the
author and licence of each in RELICENSING-PERMISSIONS.md.
