===============================
How to make your own level sets
===============================

The .bin files are MacBinary files from the original MacOS9 game.  The
.py files are the levels that we did ourselves.  To make new levels, you
need to make a new .py file in the current directory (bubbob/levels/).

For an example, open CompactLevels.py with any text editor.  The
structure should be fairly simple to understand even without knowledge
about Python.  (Just don't try to look at RandomLevels.py first: it is a
full Python program that generates the levels completely randomly.)

To get started, copy CompactLevels.py to a new name, like MyLevels.py,
and start editing it.  You can remove or change levels, but the last one
should always be called LevelFinal and have no monster in it.  All other
levels should have monsters, otherwise they'll be considered as the
final level.

Also note that all levels need to have the same size (width and height),
but different level sets can have different sizes.  For example, the
levels in CompactLevels.py are a bit smaller than the ones in the .bin
files, and the levels in scratch.py are a bit larger.

Wall patterns
-------------

A level of a .py file normally gets the wall pattern of the level with
the same number in the HouseOfFun levelset (listed in bubbob/patmap.py,
images in bubbob/tmp/).  It can have its own instead, with a 'patmap'
in the same format as bubbob/patmap.py but without the level number:

    class level07(boarddef.Level):
        patmap = {
            (0, 0): ('mywalls.ppm', (0, 0, 24, 24)),
            'l':    ('myborders.ppm', (0, 0, 40, 32)),
        }

(0, 0) is a wall tile, given as a file and a rectangle (x, y, width,
height) in it.  Wall tiles are 24x24: 16x16 and an 8 pixel shadow on
the right and at the bottom.  A larger repeated pattern is made of
several tiles, (0, 0), (1, 0), (0, 1), (1, 1) for a 2x2 one.  'l' and
'r' are the pieces of the left and right border walls, 40x32 (32x32 and
an 8 pixel shadow on the right); 'l' alone is used for both sides.  The
color 0x010101 is transparent.  The files (.ppm) are looked for next to
the level file first, then in bubbob/tmp/.  You can mix using the
original patterns: HouseOfFun (pat00-20), Levels (pat21-37), Arena
(pat38-51); with custom ones however you wish. A level set with its own
pictures can live in a folder of its own: see PatternDemo/.
