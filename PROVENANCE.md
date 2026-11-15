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

Kept apart in nonfree/; see nonfree/README.md for the files one by one,
what was claimed about them before, and the OverClocked ReMix sources
found.  In short: Armin Rigo added them in 2003 to 2005 without naming a
source; in 2026 he remembered that the musics are extracts of
OverClocked ReMix remixes, and four were matched to exact excerpts
(ext1, ext2, ext4, ext5).  ext3, ext6 and ext7 are in none of the 1228
OverClocked ReMix tracks from before June 2005 that are still published.

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
