# nonfree/: sounds of unknown licence

This folder holds the 14 sounds of the subgames (bubbob/ext1 to ext7),
under the same paths they had in bubbob/.  They are kept, not deleted,
but none has a free licence: four musics are extracts of OverClocked
ReMix remixes of game music, and the other files have no known author.  The game plays them from here, as before.  A
distribution can leave this folder out, and the game then plays those
subgames without sound (common/gamesrv.py, soundpath()); putting the
folder back, for example from a separate package, brings the sounds back.

| File | What it is |
|---|---|
| ext1/music.wav | "Black Block" by DJComet, OverClocked ReMix (https://ocremix.org/remix/OCR00958), Arkanoid |
| ext2/music.wav | "64-bit" by Peterrian Productions, OverClocked ReMix (https://ocremix.org/remix/OCR00021), Pac-Man |
| ext4/music.wav | "MkVaffQuasi Ultimix" by MkVaff, OverClocked ReMix (https://ocremix.org/remix/OCR00155), Tetris |
| ext5/music.wav | "DABOMB" by alk, OverClocked ReMix (https://ocremix.org/remix/OCR00105), Lemmings |
| ext3, ext6, ext7 music.wav | not identified; not in any OverClocked ReMix still published from before June 2005 |
| ext5/ouch.wav, ext6/crash.wav | not identified |
| ext1/brick.wav, ext1/wall.wav, ext3/shoot.wav, ext7/fire.wav, ext7/hit.wav | generated tones and noise, author unknown |

## What was said before

- Armin Rigo added all 14 files to CVS between June 2003 and June 2005.
  The logs name no source; ext7's says only "Red Baron music."
  (CVS repository: https://sourceforge.net/code-snapshots/cvs/b/bu/bub-n-bros.zip;
  this GitHub repository starts in 2021 and does not have that history.)
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
- Asked in November 2026, Armin first wrote: "I have absolutely no idea any
  more where the music came from." (RELICENSING-PERMISSIONS.md)  Reading
  a draft about the game, he remembered (mail of 14 November 2026): "I'm
  pretty sure they are all extracts of music from OCRemix.org."

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

The music was first compared by sound against about 3000 game soundtracks
and modules (https://modarchive.org , https://www.zophar.net/music ,
https://ftp.modland.com , free games in Debian).  That found the tunes
(Arkanoid, the Pac-Man jingle, Tetris) but not the recordings.  After
Armin's second mail, 270 OverClocked ReMix tracks posted before each
commit were compared, and four loops are exact excerpts of one of them
(waveform correlation 0.96 to 0.99 over the whole loop):

- ext1: OCR00958 from 0:00, played one semitone lower.
- ext2: OCR00021 from 0:08.
- ext4: OCR00155 from 0:01.6.  Its opening imitates the Game Boy, which
  is why it first looked like a recording of the game.
- ext5: OCR00105 from 0:00.

OverClocked ReMix allows redistribution only without profit, unmodified,
with credit, and may withdraw that permission
(https://ocremix.org/info/Content_Policy); the game tunes underneath
belong to their own copyright holders.  So these files are not free
software even with the credit above.

## Replacing them

The game loads each file by name, so a free sound with the same name in
bubbob/extN/ replaces the one here.  Candidates: new recordings or
compositions under a free licence, CC0 or CC-BY sounds (opengameart.org,
freesound.org), or sounds from free games already in Debian.  Searching
every OverClocked ReMix posted before June 2005 that is still published
(1228 tracks from the collection torrent "OC ReMix Collection 1 to 4000",
https://bt.ocremix.org/torrents/OC_ReMix_Collection_-_1_to_4000_%5Bv20201028%5D.torrent)
found no source for ext3, ext6 and ext7, at playback rates from 0.8 to
1.2, half and double; the same search finds ext1 and ext5 again.  They
may come from a remix OverClocked ReMix has since withdrawn, or from
elsewhere.  Record the
author and licence of each in RELICENSING-PERMISSIONS.md.
