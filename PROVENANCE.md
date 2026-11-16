# Where every file of the game comes from

This file records the origin of the graphics, sounds, music and levels,
with the evidence and a full URL for every source, so that nobody has to
research it again.  Licence grants themselves, with the authors' mails,
are in RELICENSING-PERMISSIONS.md; the licence texts are in LICENSE.txt
and artistic.txt.  Research done in November 2026.

## Sources used

| What | URL |
|---|---|
| Original CVS repository (2003 to 2013, full history) | https://sourceforge.net/code-snapshots/cvs/b/bu/bub-n-bros.zip (sha256 e83a1207c9964109396fb47a05bcb1a6353f4e6ad5f6cb13b2f949d0c4506238) |
| SourceForge project | https://sourceforge.net/projects/bub-n-bros/ |
| Old site, authors page (May 2003) | https://web.archive.org/web/20030506000913/http://bub-n-bros.sourceforge.net:80/authors.html |
| Old site, authors page (2008) | https://web.archive.org/web/20080301141252/http://bub-n-bros.sourceforge.net:80/authors.html |
| McSebi's Bub & Bob 1 page (2002) | https://web.archive.org/web/20020808194157/http://www.mcsebi.de:80/bb1.php |
| McSebi's Bub & Bob 1 page (Dec 2002) | https://web.archive.org/web/20021209105909/http://www.mcsebi.com:80/bb1.php |
| McSebi's download list (2006) | https://web.archive.org/web/20060329183655/http://www.mcsebi.com/download_manager/files.php?cat=3&cmd=all&sort=date&order=asc&page=1 |
| Bub & Bob 1.7.3 | https://archive.org/download/tucows_205607_Bub_And_Bob/bubandbob.sit (sha256 fc1fc2a29db12b54bb0bebf800833332486da7fb7eb52696534217dcdbb90fb5) |
| Bub & Bob 1.0, 1.2, 1.6.3 | https://macintoshgarden.org/games/bub-bob (sha256 of the archives: 1.0 4f3dd7e6e1703b7743cb42e41b6d41c75319cfe971f599797c9a8b691add92f0, 1.2 3c2512053f4efe2395b68666485643ff5146e82b5d79c68f92af7e7ecbfc1f2e, 1.6.3 e5ad64fa75d6312a884d33d08ab777c721aff1e4ea076934ee67d29470f50f95) |
| The fan level packs as McSebi published them | https://web.archive.org/web/20060329181518/http://www.mcsebi.com/downloads/arena.sit , https://web.archive.org/web/20060329181500/http://www.mcsebi.com/downloads/HoF.sit , https://web.archive.org/web/20060329181628/http://www.mcsebi.com/downloads/lostlevels.sit |
| Debian's first ITP (2005) and McSebi's licence thread | https://bugs.debian.org/308148 , https://lists.debian.org/debian-devel/2005/05/msg00376.html |
| Mandriva's note of McSebi's 2009 mail | https://github.com/OpenMandrivaAssociation/bubbros/blob/1f2138cc/bubbros.spec |
| Old Debian packages (2008 to 2019) | https://snapshot.debian.org/package/bubbros/ |
| Debian bugs | https://bugs.debian.org/cgi-bin/pkgreport.cgi?src=bubbros;archive=both |
| OverClocked ReMix terms | https://ocremix.org/info/Content_Policy |
| OverClocked ReMix pages as of 2003 (withdrawn remixes) | https://web.archive.org/web/20031023174756/http://www.ocremix.org:80/detailmix.php?mixid=OCR00086 and the other detailmix.php pages |
| Withdrawn OverClocked ReMix remixes ("OC ReMoved") | https://musicbrainz.org/series/29eb0b44-aa4c-4ca8-9ea9-da482ce53f00 |
| Old OverClocked ReMix versions | https://archive.org/details/oldocremix |
| VGMix archive | https://vgmixarchive.com/ |
| remix.kwed.org (C64 remixes) | https://remix.kwed.org/ |
| Red Baron (Dynamix, 1990) | https://archive.org/download/msdos_Red_Baron_1990/Red_Baron_1990.zip , credits https://amiga.abime.net/games/view/red-baron#information |
| US Copyright Office public records | https://publicrecords.copyright.gov |

This GitHub repository starts with "import from sf.net" (2021); the CVS
history before that is only in the SourceForge snapshot above.

## The game: McSebi's Bub & Bob 1

Sebastian Wegner (McSebi) released Bub & Bob for the Mac as shareware in
November 1997 (its 1.0 ReadMe: "Version 1.0 (November 1997)"); 1.7.3,
the last, came out on 2001-05-20 (mcsebi.de news).  His page called it "a
clone of the very popular arcade game Bubble Bobble, created by Taito".
Armin Rigo started The Bub's Brothers as a network clone of it; the first
CVS commit is from 2003-01-31.

## Graphics

- bubbob/images/: McSebi's sprites, redrawn by David Gowers in 2007.
  Gowers also drew http2/data/*.png and http2/header.png (CVS logs
  "Credits to David Gowers", "Credits for the updated graphics.").
- Licence: McSebi's "graphics and sound data", Artistic (2005, quoted in
  LICENSE.txt), and Artistic-2.0 (2009, artistic.txt); Gowers' redrawing,
  Artistic-2.0 (2026, RELICENSING-PERMISSIONS.md).
- McSebi's page said of his game: "Graphics and sound effects identical to
  Bubble Bobble."  Debian bug https://bugs.debian.org/934972 (2019) raised
  the likeness to Taito's graphics; it was closed because the licence is
  DFSG-compliant.

## Sounds and music of the main game

bubbob/sounds/*.wav and bubbob/music/*.wav are McSebi's: each matches a
sound resource of Bub & Bob 1.7.3 one to one (cross-correlation 1.000).
Licence: McSebi's grant above.

## Levels

| File | Author | Licence |
|---|---|---|
| bubbob/levels/Levels.bin | McSebi (all 100 layouts and 154 wall patterns match his releases) | McSebi's 2005 grant, given in answer to the 2005 ITP's question about the files the game shipped |
| bubbob/levels/*.py | Gio, Odie (Olivier Dormond), Michel-Stéphane, Armin Rigo | MIT, confirmed by Armin in 2026 |
| bubbob/levels/Arena.bin | Wim De Gent, published by McSebi 2002-01-04 | none |
| bubbob/levels/HouseOfFun.bin | Michael S. Repton, published 2002-07-21 | none |
| bubbob/levels/LostLevels.bin | Patrick Viney, published 2001-06-23 | none |

The three fan packs: 99 new layouts each.  Their wall patterns are
McSebi's in Arena and LostLevels, and mostly new in HouseOfFun; the last
level of each is McSebi's.  The authors are credited on McSebi's pages
(https://web.archive.org/web/20020808194157/http://www.mcsebi.de:80/bb1.php ,
https://web.archive.org/web/20021209105909/http://www.mcsebi.com:80/bb1.php).
No contact address was found for any of them (Usenet Mac game groups,
Macintosh Garden, Info-Mac, discmaster); a 1998 address for Wim De Gent
bounced.  Neither the packs nor McSebi's site give any licence or
submission terms.  The CVS logs say: "contributed by fans of the original
MacOS9 Bub&Bob" (2003) and "Adding them in the assumption that the
authors' mind was to share them" (2005).

## Subgame sounds and music (ext1 to ext7)

Kept apart in nonfree/ because none is free; nonfree/README.md has the
short list of credits.  This section has the evidence.

### What was said before

- Armin Rigo added all 14 files to CVS between June 2003 and June 2005.
  The logs name no source.  ext6's music came on 2005-04-05 with the log
  "ext6."; ext7's on 2005-06-16 with "Red Baron music."
- The site said "Almost all sprite images, sounds, background musics and
  levels are directly taken from the MacOS version of Bub & Bob 1 by
  McSebi".  That text is from May 2003, before the first of these files
  (authors page in the table above).
- These sounds are not in McSebi's game, so his grant does not cover
  them: compared with Bub & Bob 1 versions 1.2, 1.6.3 and 1.7.3, no file
  matches.
- Debian shipped them from 2008 to 2019 as Artistic, copied from
  LICENSE.txt, and other distributions did the same.  Nobody had checked
  the subgame sounds.  https://bugs.debian.org/934972 (2019) was about the
  graphics; the first ITP, https://bugs.debian.org/308148, mentioned "some
  legal problems which need to be figured out first", without detail.
- Asked in November 2026, Armin first wrote: "I have absolutely no idea any
  more where the music came from." (RELICENSING-PERMISSIONS.md)  Reading
  a draft about the game, he remembered (mail of 14 November 2026): "I'm
  pretty sure they are all extracts of music from OCRemix.org."

Nothing names a source for these files in the CVS history, the old site
on the Wayback Machine (https://web.archive.org/web/2003*/bub-n-bros.sourceforge.net*),
the SourceForge forum, trackers and file releases
(https://sourceforge.net/p/bub-n-bros/discussion/ ,
https://sourceforge.net/p/bub-n-bros/bugs/ ,
https://sourceforge.net/p/bub-n-bros/patches/ ,
https://sourceforge.net/p/bub-n-bros/feature-requests/ ,
https://sourceforge.net/projects/bub-n-bros/files/), pypy-dev 2003 to
2008 (https://mail.python.org/pipermail/pypy-dev/), the #pypy IRC logs
around the ext6 and ext7 commits
(https://web.archive.org/web/2007/http://tismerysoft.de/pypy/irc-logs/pypy/),
or the Debian bugs.

### ext1 to ext5: OverClocked ReMix excerpts

Five loops are exact excerpts of one remix each, posted before the loop
was committed.  Times are in the remix as published:

| Loop | Remix | Page | MP3 | Parts used |
|---|---|---|---|---|
| ext1 (17.0 s) | "Black Block" by DJComet (Arkanoid) | https://ocremix.org/remix/OCR00958 | https://ocrmirror.org/files/music/remixes/Arkanoid_Black_Block_OC_ReMix.mp3 | 0:00.0 to 0:13.2, then 0:09.2 to 0:11.1 again; played one semitone lower (speed 0.9439) |
| ext2 (8.0 s) | "64-bit" by Peterrian Productions (Pac-Man) | https://ocremix.org/remix/OCR00021 | https://ocrmirror.org/files/music/remixes/Pac-Man_64-bit_OC_ReMix.mp3 | 0:12.1 to 0:14.1, then 0:10.1 to 0:16.1 |
| ext3 (6.4 s) | "Galagzee" by zee-roh (Galaga), withdrawn later | https://web.archive.org/web/20031023174756/http://www.ocremix.org:80/detailmix.php?mixid=OCR00086 | https://web.archive.org/web/20130831210310id_/http://doulifee.com//Storage/OC_Removed/Galaga_Galagzee_OC_ReMoved.mp3 | 0:06.4 to 0:12.8 |
| ext4 (12.9 s) | "MkVaffQuasi Ultimix" by MkVaff (Tetris) | https://ocremix.org/remix/OCR00155 | https://ocrmirror.org/files/music/remixes/Tetris_MkVaffQuasi_Ultimix_OC_ReMix.mp3 | 0:01.6 to 0:14.5 |
| ext5 (7.9 s) | "DABOMB" by alk (Lemmings) | https://ocremix.org/remix/OCR00105 | https://ocrmirror.org/files/music/remixes/Lemmings_DABOMB_OC_ReMix.mp3 | 0:00.0 to 0:07.9 |

sha256 of the MP3s:

    f026567718aedec58a6d078f0d745ae4de915f82c2944b29d9f447666373345c  Arkanoid_Black_Block_OC_ReMix.mp3
    bf20093f2ad29f78b7d07ba3444d0ad55bc4b577e0aa9bb46ce02712e5175d33  Pac-Man_64-bit_OC_ReMix.mp3
    755dc6e4ff35ce1bc9abef5d23ec5cb0db25df0d3d1a25c20d02f364279a7c9b  Galaga_Galagzee_OC_ReMoved.mp3
    f7f828d5e1b87803a34e9927bddb19764084356ecffe4d7eeedc6bfac8dc8869  Tetris_MkVaffQuasi_Ultimix_OC_ReMix.mp3
    b868cc7a8d8079630ffe64ea7a99be22eabe4a6ecb26b76907a1a29684d63ebe  Lemmings_DABOMB_OC_ReMix.mp3

Every second of every loop is found in its remix with a waveform
correlation of 0.94 to 1.00 (1.00 means the same samples).  The same
seconds score at most 0.29 anywhere in the other four remixes, which is
what unrelated music gives.  No part of a loop is new material: where a
loop does not follow the remix straight through (ext1, ext2), it is two
pieces of the same remix joined to make a seamless loop.  To check it
again, from the top of the repository (downloads the five MP3s, 12 MB,
about two minutes):

    python3 tools/verify_sources.py

Notes:

- ext4's opening imitates the Game Boy, which is why it first looked like
  a recording of the game.
- ext3's remix was withdrawn by OverClocked ReMix later; it was still
  listed in October 2003, after ext3 was committed (June 2003).  The MP3
  above is the "OC ReMoved" re-release, listed by MusicBrainz:
  https://musicbrainz.org/recording/062669b7-5e22-40ba-bf2d-90cdb218f2ec

### ext7: the Red Baron title theme

ext7's log says "Red Baron music."  The loop is the title theme of Red
Baron (Dynamix, published by Sierra, 1990, MS-DOS): the same melody and
tempo, but a different arrangement, without the drums and the war sounds
of the game.

- Game: https://archive.org/download/msdos_Red_Baron_1990/Red_Baron_1990.zip
  (sha1 90693626209483f3d43afc9c4b5f8cb7c4eff94c).  Its title music,
  recorded in DOSBox with AdLib, and the MT-32 recordings
  https://youtu.be/1it1OvVZp-I and https://youtu.be/L7z0P5yav30 score 28
  to 40 landmark pairs against ext7.  Unrelated music scores at most 17,
  and the same recording 128 or more.  So the notes match, but none of
  these is the recording.  Listening confirms it: same melody, reworked.
- Credits of the game: Music Score, Cayanie Music; Sound Effects and
  Music Editing, Christopher Stevens; Audio Director, Alan McKean; Amiga
  music, Ken Rogers (https://amiga.abime.net/games/view/red-baron#information).
  A later fan arrangement on YouTube also credits the original music to
  Cayanie Music: https://www.youtube.com/watch?v=lupk2oqy4JU
- US Copyright Office recordation V2393P099 (1988-02-29) names "John
  Benjamin (Benjy) G. Wertheimer & Cathy S. Hudnall d.b.a. Cayanie
  Music" (https://publicrecords.copyright.gov , record voyager_1502666).
  They are Oregon musicians and Dynamix was in Eugene, Oregon, but no
  source ties them to the game yet.
- Who made the arrangement in ext7 is unknown.  It is not in any
  collection searched (list below).

The composition is copyrighted, so ext7's music is not free, whoever
arranged it.

### ext6: unknown

ext6 is now a snake game.  It began as a Tron light-cycle game, which is
why its class is named Tron; the log of 2005-05-10 says: Gave up
emulating a "tron" and did a "snake".  So the Tron name says nothing
about the music, and no Tron soundtrack matched.  The loop (19.6 s) is
rock with drums and guitar.  Shazam finds nothing.

ext6 and ext7 are 22.05 kHz; ext1 to ext5 are 44.1 kHz.  ext6 never
repeats a bar exactly (best self-correlation 0.61), unlike a plain MIDI
rendering, so it is probably cut from a recording.

### The sound effects

| File | Committed | Format | What it is |
|---|---|---|---|
| ext1/brick.wav | 2003-06-07, "sound and music for ext1" | 44.1 kHz, 0.66 s | simple tone, 26 distinct sample values |
| ext1/wall.wav | 2003-06-07, same commit | 44.1 kHz, exactly 0.300 s | pure tone starting at zero |
| ext3/shoot.wav | 2003-06-13, "new ext3" | 44.1 kHz, exactly 0.300 s | pure tone starting at zero |
| ext7/hit.wav | 2005-06-15, "Sounds for ext7.  Still missing the music, though." | 44.1 kHz, 3308 samples | noise burst |
| ext7/fire.wav | 2005-06-15, then "Red Baron music." and "Tweaks." | 11.025 kHz, 3308 samples | short tone |
| ext5/ouch.wav | 2004-01-09, "New ext5 extension." | 11.025 kHz, 0.23 s | a recorded voice |
| ext6/crash.wav | 2005-04-05, "ext6." | 22.05 kHz, 0.59 s | a recorded crash; ext7 uses it too |

No commit, comment, page or WAV header (no metadata chunk) names a
source.  The first five look made by a program: exact round lengths,
waveforms that start at zero, and two files of exactly the same length.
So they are probably Armin's own, but he has not confirmed it.  ouch.wav
and crash.wav are recordings of unknown origin; they were never compared
with game sound effects.  Without nonfree/, these effects are silent.

### What was searched for ext6 and ext7

Each loop was compared by landmark fingerprint at playback rates 0.25 to
4, tempo 0.5 to 2 and pitch shifts of up to two octaves (also reversed,
and on the left, right and difference channels for the OverClocked ReMix
sets).  The same search finds ext1, ext3 and ext5 again.  No match above
noise in:

- every OverClocked ReMix posted before June 2005 that is still
  published (1228 tracks of
  https://bt.ocremix.org/torrents/OC_ReMix_Collection_-_1_to_4000_%5Bv20201028%5D.torrent);
- the 125 withdrawn remixes up to OCR01364 (MusicBrainz "OC ReMoved"
  series https://musicbrainz.org/series/29eb0b44-aa4c-4ca8-9ea9-da482ce53f00 ,
  172 archived files and 8 copies on old mirrors), and 107 old versions
  at https://archive.org/details/oldocremix ;
- VGMix: 4688 songs of the VGMix Archive 3.0 torrent (https://vgmixarchive.com/ ,
  info hash e3930ea1139b3d7e1038070ebd376ddc0491e842), all of VGMix 1
  and every VGMix 2 song dated before 2005-04-06 or undated;
- remix.kwed.org: 1904 C64 remixes, the torrents "RKO-2000 Complete" to
  "RKO-2005 Complete" and "Not on RKO Anymore" (https://remix.kwed.org/);
- rock game-music covers: Grospixels "Gromix" (228,
  https://www.grospixels.com/site/remixang.php), Dwelling of Duels
  2003-09 to 2005-03 (184, https://www.dwellingofduels.net/duels/), the
  NESkimos, Minibosses, The Advantage, The OneUps, Machinae Supremacy,
  Metroid Metal, Black Mages, Press Play On Tape;
- music of free games in Debian (274 files: Nexuiz, Alien Arena,
  Warzone 2100 and others), Jets'n'Guns and Quake III Arena;
- about 3000 game soundtracks and modules (https://modarchive.org ,
  https://www.zophar.net/music , https://ftp.modland.com);
- for ext7: over 40 recordings of Red Baron (1990) and of other biplane
  and Snoopy games and songs (Wings, Knights of the Sky, Sopwith, Blue
  Max, 1942, Snoopy vs the Red Baron), and MIDI files of them;
- for ext6: Tron soundtracks (Wendy Carlos 1982, the arcade game, Discs
  of Tron, Tron 2.0) and Armagetron Advanced.

## Free music of the subgames (bubbob/ext1 to ext7/music.wav)

Each subgame has a free music in bubbob/extN/music.wav.  The game plays
the original from nonfree/ when that folder is installed, and this free
music otherwise (common/gamesrv.py, soundpath()).  Chosen by ear in
November 2026.  Each file is a cut of the published track, mono, unsigned
8 bit like the files it replaces, made with tools/makeloop.py (the 50 ms
after the cut are crossfaded into the start, so it loops without a
click), except ext4, which tools/korobeiniki_chip.py generates.

| File | Title, author | Licence | Page | Download (sha256) | Part used |
|---|---|---|---|---|---|
| ext1/music.wav | "Arcade Puzzler (Looping)", Eric Matyas, www.soundimage.org | CC-BY 3.0, https://creativecommons.org/licenses/by/3.0/ | https://opengameart.org/content/arcade-puzzler-looping | https://opengameart.org/sites/default/files/arcade_puzzler.ogg (e3e281cc6af7f02d2650bcd6fb8ba985ec21cd8e4a0c9c218aaebea36a077760) | 6.46 to 20.44 s |
| ext2/music.wav | "Caffeine Crazed Coin-Op Kids (Looping)", Eric Matyas, www.soundimage.org | CC-BY 3.0, https://creativecommons.org/licenses/by/3.0/ | https://opengameart.org/content/caffeine-crazed-coin-op-kids-looping | https://opengameart.org/sites/default/files/caffeine_crazed_coin-op_kids.ogg (b88f8fa02026a782859c69fd6eee6e226203fa677081a5766d48c1e372158688) | 1.38 to 11.41 s |
| ext3/music.wav | "8-bit Epic Space Shooter Music", HydroGene | CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/ | https://opengameart.org/content/8-bit-epic-space-shooter-music | https://opengameart.org/sites/default/files/8bit-spaceshooter.mp3 (f8a232f6fc5a52d1ea85705447617a1d6132e63d993d63ad542c253f1b614b93) | 42.40 to 49.27 s |
| ext4/music.wav | Korobeiniki, Russian folk song (public domain), 8-bit arrangement generated by tools/korobeiniki_chip.py | CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/ | this repository | `tools/korobeiniki_chip.py bubbob/ext4/music.wav 150` (output df73876922ad0b1c856d19cb4617c242b101d9898d42639c14fa32bc1d5987ae) | whole |
| ext5/music.wav | "Children's March Theme", Cleyton Kauffman, https://soundcloud.com/cleytonkauffman | CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/ | https://opengameart.org/content/childrens-march-theme | https://opengameart.org/sites/default/files/childrens_march_theme.zip (feea4abc34d3ba19a742603bedc2619b75820e1bef423773ccaae03538f7f02a; "Children's March Theme.wav" inside, d00e4f68256ceb8f13420a1b2d9e5572ae96e01aa41e61ff6199326b9f4b9b94) | 16.00 to 24.00 s |
| ext6/music.wav | "Race of the Wasp", OwlishMedia | CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/ | https://opengameart.org/content/race-of-the-wasp | https://opengameart.org/sites/default/files/Race%20of%20the%20Wasp.mp3 (e5f30493ef5dcb8888e93c7aed01c48368eb1d061dfe0a049ad2619a722ef783) | 18.69 to 38.01 s |
| ext7/music.wav | "The Tread of War", Jonathan Shaw, www.jshaw.co.uk | CC-BY 3.0, https://creativecommons.org/licenses/by/3.0/ | https://opengameart.org/content/the-tread-of-war-rpg-orchestral-essentials-military-music | https://opengameart.org/sites/default/files/The%20Tread%20of%20War%20-%20MP3_0.mp3 (7230283eb7fd48f76981781b2ea47b2c44cdd52d470308ab98d57bfba7f7b06e) | 3.98 to 19.96 s |

sha256 of the files in this repository:

    2aa5fd9218a14d22af0399b2939834abbd00d7a846ae2066aacaf77d24e2e6e5  bubbob/ext1/music.wav
    9cb70aa0252cdcc3f2c37489cd126162070293f0a314daeb1d29f33d0b413c70  bubbob/ext2/music.wav
    4129866157323f2aa923f59ed434933d998fd0935c9b6878889c8127ebebfe0d  bubbob/ext3/music.wav
    df73876922ad0b1c856d19cb4617c242b101d9898d42639c14fa32bc1d5987ae  bubbob/ext4/music.wav
    4a929bfdcf27468b9405634f87998f63bac8526195844d7d240b1ad859f970fd  bubbob/ext5/music.wav
    e8ba581d53734897b5eadf923657ded269b2adfd177248f14385b03d85f63bb1  bubbob/ext6/music.wav
    118ab1832b3374527097eff75e3fc2db69d772ccd7b39d1a2f49caf928e534bb  bubbob/ext7/music.wav

Commands (level = mean dBFS of the loop it replaces):

    tools/makeloop.py arcade_puzzler.ogg 6.46 20.44 44100 -16.8 bubbob/ext1/music.wav
    tools/makeloop.py caffeine_crazed_coin-op_kids.ogg 1.38 11.41 44100 -23.2 bubbob/ext2/music.wav
    tools/makeloop.py 8bit-spaceshooter.mp3 42.40 49.27 44100 -15.4 bubbob/ext3/music.wav
    tools/makeloop.py "Children's March Theme.wav" 16.00 24.00 44100 -13.8 bubbob/ext5/music.wav
    tools/makeloop.py "Race of the Wasp.mp3" 18.69 38.01 22050 -21.2 bubbob/ext6/music.wav
    tools/makeloop.py "The Tread of War - MP3_0.mp3" 3.98 19.96 22050 -22.4 bubbob/ext7/music.wav

The result can differ in the last bits with another ffmpeg version.

Attribution required by CC-BY (ext1, ext2, ext7), changes: cut, mixed to
mono, converted to 8 bit:

- "Arcade Puzzler" by Eric Matyas, www.soundimage.org, CC-BY 3.0.
- "Caffeine Crazed Coin-Op Kids" by Eric Matyas, www.soundimage.org, CC-BY 3.0.
- "The Tread of War" composed by Jonathan Shaw (www.jshaw.co.uk), CC-BY 3.0.

ext4: only the folk melody of Korobeiniki is used, not the Game Boy
"A-Type" arrangement; the echo voice, bass and drums are written in the
script.

## How the comparisons were made

- Mac resources: the .sit archives were unpacked, and every sound, LEVL
  and ppat resource was compared by sha1 or by cross-correlation with the
  files of this game.
- Subgame musics: each loop was slid along every candidate recording at a
  range of playback rates, scoring log-spectrum correlation, then checked
  by waveform correlation in 1 second chunks.  Unrelated recordings score
  0.2 to 0.6; the same recording 0.9 or more.  Candidates: about 3000 game
  soundtracks and modules (https://modarchive.org ,
  https://www.zophar.net/music , https://ftp.modland.com) and every
  OverClocked ReMix posted before June 2005 and still published (1228
  tracks of the collection torrent
  https://bt.ocremix.org/torrents/OC_ReMix_Collection_-_1_to_4000_%5Bv20201028%5D.torrent ,
  named in https://ocremix.org/remix/OCR00001 and following pages).
  The search was checked by finding the known matches again in the
  torrent copies (0.975 and 0.880).
- The five matches can be checked again with tools/verify_sources.py,
  which downloads each remix from its public URL, checks its sha256 and
  prints the correlation of every second of the loop, with a control.
- Wider search for ext6 and ext7: landmark fingerprints (peaks of a log
  spectrogram, paired into hashes), queried over a grid of playback
  rates, tempos and pitch shifts.  Unrelated music gives 9 to 22
  matching pairs, another arrangement of the same tune 20 to 40, the
  same recording 128 to 937.
