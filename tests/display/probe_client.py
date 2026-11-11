"""Run display/Client.py and log the input its display driver returns.

usage: probe_client.py LOG display/Client.py [client options...]

Each line of LOG is one event:
  DRIVER <name>             the graphics driver in use
  MOUSE <x> <y>             a click, in playfield coordinates
  KEY <keysym> <1|0>        a key press (1) or release (0)
  DEFINE <keysym>           a key given to the "choose four keys" step
  WINDOW <w> <h>            the size the playfield is shown in, at a click
  AREA <x> <y> <f> <ox> <oy>  GTK only: the click as the drawing area got
                            it, with the driver's scale and offset
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

    def window_size():
        if name.lower() == 'pygame':
            import pygame
            return pygame.display.get_window_size()
        if name.lower() == 'gtk':
            return (dpy.area.get_allocated_width(),
                    dpy.area.get_allocated_height())

    def logged_mouseevents():
        events = mouseevents()
        for x, y in events:
            LOG.write('MOUSE %d %d\n' % (x, y))
            size = window_size()
            if size:
                LOG.write('WINDOW %d %d\n' % size)
        return events

    if name.lower() == 'gtk':
        # listen on the toplevel window, where every click ends up, and
        # work out where it was in the drawing area from root coordinates;
        # asking the drawing area itself for button events would change
        # which window GTK delivers them to, and hide the difference
        def area_click(widget, event):
            ox, oy = dpy.area.get_window().get_origin()[1:]
            alloc = dpy.area.get_allocation()
            if not dpy.area.get_has_window():
                ox, oy = ox + alloc.x, oy + alloc.y
            view = tuple(getattr(dpy, 'view', (1.0, 0.0, 0.0)))
            LOG.write('AREA %d %d %.4f %.1f %.1f\n'
                      % ((event.x_root - ox, event.y_root - oy) + view))
            return False
        dpy.window.connect('button-press-event', area_click)

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
