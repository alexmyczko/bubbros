"""Run display/Client.py and log the input its display driver returns.

usage: probe_client.py LOG display/Client.py [client options...]

Each line of LOG is one event:
  DRIVER <name>             the graphics driver in use
  MOUSE <x> <y>             a click, in playfield coordinates
  KEY <keysym> <1|0>        a key press (1) or release (0)
  DEFINE <keysym>           a key given to the "choose four keys" step
run.py reads LOG while the client runs.  The client's own output goes
to stdout as usual.
"""

import os
import runpy
import sys

LOG = open(sys.argv[1], 'w', buffering=1)
sys.argv = sys.argv[2:]
DISPLAY_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path[:0] = [DISPLAY_DIR, os.path.dirname(DISPLAY_DIR)]

import modes
import pclient

_open_dpy = modes.open_dpy

def open_dpy(mode, *args):
    dpy = _open_dpy(mode, *args)
    name = modes.findmode(mode[0], modes.graphicmodeslist()).name
    LOG.write('DRIVER %s\n' % name.lower())
    keyevents, mouseevents = dpy.keyevents, dpy.mouseevents

    def logged_keyevents():
        events = keyevents()
        for keysym, event in events:
            LOG.write('KEY %d %d\n' % (keysym, event == modes.KeyPressed))
        return events

    def logged_mouseevents():
        events = mouseevents()
        for x, y in events:
            LOG.write('MOUSE %d %d\n' % (x, y))
        return events

    dpy.keyevents = logged_keyevents
    dpy.mouseevents = logged_mouseevents
    return dpy

modes.open_dpy = open_dpy

_define_key = pclient.Playfield.define_key

def define_key(self, keysym):
    LOG.write('DEFINE %d\n' % keysym)
    return _define_key(self, keysym)

pclient.Playfield.define_key = define_key

runpy.run_path(sys.argv[0], run_name='__main__')
