#
#  A demo of levels with their own wall patterns.
#
#  A level's 'patmap' has the format of bubbob/patmap.py, without the
#  board number: (x, y) for each tile of the stamp, 'l' and 'r' for the
#  left and right border pieces (one 'l' alone is used for both sides).
#  Wall tiles are 24x24 and border pieces 40x32, shadows included.  The
#  files are looked for in this folder, then in bubbob/tmp/.
#

import boarddef
from boarddef import LNasty, RNasty, LMonky, RMonky


LAYOUT = """
#############################
##                         ##
##                         ##
##                         ##
##                         ##
##                         ##
##         a     b         ##
####   ###############   ####
##                         ##
##                         ##
##                         ##
##         a     b         ##
####   ###############   ####
##                         ##
##                         ##
##                         ##
##         a     b         ##
####   ###############   ####
##                         ##
##                         ##
##                         ##
##                         ##
##                         ##
#############################
"""


class level01(boarddef.Level):
    # one tile and one border piece, from this folder
    patmap = {
        (0, 0): ('walls.ppm', (0, 0, 24, 24)),
        'l':    ('borders.ppm', (0, 0, 40, 32)),
    }
    a = LNasty
    b = RNasty
    walls = LAYOUT


class level02(boarddef.Level):
    # a 2x2 stamp, and different left and right border pieces
    patmap = {
        (0, 0): ('walls.ppm', (0, 24, 24, 24)),
        (1, 0): ('walls.ppm', (0, 48, 24, 24)),
        (0, 1): ('walls.ppm', (0, 72, 24, 24)),
        (1, 1): ('walls.ppm', (0, 96, 24, 24)),
        'l':    ('borders.ppm', (0, 32, 40, 32)),
        'r':    ('borders.ppm', (0, 64, 40, 32)),
    }
    a = LMonky
    b = RMonky
    walls = LAYOUT


class level03(boarddef.Level):
    # tiles of the game's own sheets, in bubbob/tmp/
    patmap = {
        (0, 0): ('pat09.ppm', (0, 0, 24, 24)),
        'l':    ('pat14.ppm', (0, 160, 40, 32)),
    }
    a = LNasty
    b = RMonky
    walls = LAYOUT


class level04(boarddef.Level):
    # no patmap: the patterns of board 4 in bubbob/patmap.py
    a = LMonky
    b = RNasty
    walls = LAYOUT


class levelFinal(level02):
    # the same patterns as level02, by inheriting from it
    walls = """
#############   #############
##                         ##
##                         ##
##                         ##
##                         ##
##                         ##
####  #################  ####
##        ###   ###        ##
##         ##   ##         ##
#######     #####     #######
##                         ##
##                         ##
##                         ##
##                         ##
#########           #########
##                         ##
##                         ##
##                         ##
##########         ##########
##                         ##
##                         ##
##                         ##
##                         ##
#############   #############
"""
