# nonfree/: files of the game that are not free

This folder holds the 14 sounds of the subgames (bubbob/ext1 to ext7)
and 21 sheets of wall patterns (bubbob/tmp/pat00-20.ppm), under the same
paths they had in bubbob/.  None of them has a free licence, so they are
kept apart from the rest of the game.

## Why they are not free

- The five identified musics are cut from OverClocked ReMix remixes.
  OverClocked ReMix allows redistribution only without profit,
  unmodified, with credit, and may withdraw that permission
  (https://ocremix.org/info/Content_Policy).  The game tunes underneath
  belong to their own copyright holders.
- ext7's music is an arrangement of the title theme of Red Baron
  (Dynamix, 1990), a copyrighted composition.
- The other sounds have no known author, so no licence can be shown.
- The wall patterns were drawn by Michael S. Repton for his level set
  The House of Fun (bubbob/levels/HouseOfFun.bin, 2002), which has no
  licence either.

## Credits

| File | Source |
|---|---|
| ext1/music.wav | "Black Block" by DJComet, Arkanoid. https://ocremix.org/remix/OCR00958 , MP3: https://ocrmirror.org/files/music/remixes/Arkanoid_Black_Block_OC_ReMix.mp3 |
| ext2/music.wav | "64-bit" by Peterrian Productions, Pac-Man. https://ocremix.org/remix/OCR00021 , MP3: https://ocrmirror.org/files/music/remixes/Pac-Man_64-bit_OC_ReMix.mp3 |
| ext3/music.wav | "Galagzee" by zee-roh, Galaga, OCR00086 (withdrawn later). 2003 page: https://web.archive.org/web/20031023174756/http://www.ocremix.org:80/detailmix.php?mixid=OCR00086 , MP3: https://web.archive.org/web/20130831210310id_/http://doulifee.com//Storage/OC_Removed/Galaga_Galagzee_OC_ReMoved.mp3 |
| ext4/music.wav | "MkVaffQuasi Ultimix" by MkVaff, Tetris. https://ocremix.org/remix/OCR00155 , MP3: https://ocrmirror.org/files/music/remixes/Tetris_MkVaffQuasi_Ultimix_OC_ReMix.mp3 |
| ext5/music.wav | "DABOMB" by alk, Lemmings. https://ocremix.org/remix/OCR00105 , MP3: https://ocrmirror.org/files/music/remixes/Lemmings_DABOMB_OC_ReMix.mp3 |
| ext7/music.wav | arrangement of the Red Baron (Dynamix, 1990) title theme; music of the game credited to Cayanie Music; arranger and recording unknown |
| ext6/music.wav | unknown (rock, with drums and guitar) |
| ext5/ouch.wav, ext6/crash.wav | unknown |
| ext1/brick.wav, ext1/wall.wav, ext3/shoot.wav, ext7/fire.wav, ext7/hit.wav | generated tones and noise, author unknown |
| tmp/pat00.ppm to tmp/pat20.ppm | the wall patterns of The House of Fun by Michael S. Repton (152 of their 153 tiles are in HouseOfFun.bin and in no file of McSebi's) |

The evidence for each line, the parts of each remix used, and what was
searched for the unknown files are in ../PROVENANCE.md.  To check the five
remixes yourself: `python3 tools/verify_sources.py` (needs python3-numpy
and ffmpeg).

## How the game uses this folder

When this folder is installed, the game plays these sounds
(common/gamesrv.py, soundpath()) and draws the .py level sets with these
walls (bubbob/images.py, choose_patterns()).  A distribution can leave it
out: each subgame then plays its free music and sound effects from
bubbob/extN/, and the .py level sets get McSebi's wall patterns from
Levels.bin (bubbob/tmp/pat21-37.ppm and pat52.ppm; credits in
../PROVENANCE.md).  Putting the folder back, for example from a separate
package, brings the original sounds and walls back.
