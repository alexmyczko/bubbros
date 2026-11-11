 ################################################
##       GTK-based implementation of xshm      ##
################################################

# PyGTK (GTK 2) does not exist for Python 3, so this uses GTK 3 through
# PyGObject.  GTK 3 has no GdkPixmap or GC any more: the off-screen
# image is a cairo surface, and the window paints it when GTK asks.
# Images keep the same shape as before for pclient.py: (pixbuf,) while
# not drawn yet, and (surface, None, None) once ready to be drawn.

import os, sys, math
from modes import KeyPressed, KeyReleased

def import_trickery():
    global Gtk, Gdk, GdkPixbuf, GLib, cairo
    argv = sys.argv[:]
    del sys.argv[1:]
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
    import cairo
    sys.argv[:] = argv
import_trickery()


class Display:

    def __init__(self, width, height, title, zoom="100"):
        if zoom.endswith('%'):
            zoom = zoom[:-1]
        scale = float(zoom) / 100.0
        iscale = int(scale+0.001)
        if abs(scale - iscale) < 0.002:
            scale = iscale
        self.scale = scale

        self.width  = int(width * scale)
        self.height = int(height * scale)

        # create a top level window
        w = self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        w.connect("destroy", lambda w: sys.exit())
        w.connect("key-press-event", self.key_press_event)
        w.connect("key-release-event", self.key_release_event)
        w.add_events(Gdk.EventMask.KEY_PRESS_MASK |
                     Gdk.EventMask.KEY_RELEASE_MASK)
        # the mouse is read on the drawing area, not on the window: with
        # client-side decorations (GTK on Wayland) the window's
        # coordinates include the title bar and the shadow, and clicks
        # landed about 40 pixels below where they were made
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(self.width, self.height)
        self.area.connect("draw", self.draw_event)
        self.area.connect("motion-notify-event", self.motion_notify_event)
        self.area.connect("button-press-event", self.button_press_event)
        self.area.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
                             Gdk.EventMask.BUTTON_PRESS_MASK)
        w.add(self.area)
        w.set_title(title)
        w.show_all()
        # the window opens at the playfield's size and can then be resized
        # or maximized; draw_event() scales the playfield to it
        self.area.set_size_request(max(1, self.width // 4),
                                   max(1, self.height // 4))
        self.view = (1.0, 0.0, 0.0)     # scale and offset of the playfield

        self.offscreen = cairo.ImageSurface(cairo.FORMAT_RGB24,
                                            self.width, self.height)
        # what the window shows: a copy of 'offscreen' made by flip()
        self.front = cairo.ImageSurface(cairo.FORMAT_RGB24,
                                        self.width, self.height)
        self.clear()

        self.events_key = []
        self.events_mouse = []
        self.event_motion = None

        pixel = b"\x00\x00\x80"
        hole  = b"\x01\x01\x01"
        pb = self.pixmap(32, 32, ((pixel+hole)*16 + (hole+pixel)*16) * 16, 0x010101)
        self.taskbkgnd = self.renderpixbuf(pb)

    def taskbar(self, rect):
        (x, y, w, h) = rect
        scale = self.scale
        x2 = x+w
        y2 = y+h
        x, y, x2, y2 = int(x*scale), int(y*scale), int(x2*scale), int(y2*scale)
        surface, ignored1, ignored2 = self.taskbkgnd
        cr = cairo.Context(self.offscreen)
        pattern = cairo.SurfacePattern(surface)
        pattern.set_extend(cairo.EXTEND_REPEAT)
        matrix = cairo.Matrix()
        matrix.translate(-x, -y)
        pattern.set_matrix(matrix)
        cr.set_source(pattern)
        cr.rectangle(x, y, x2-x, y2-y)
        cr.fill()

    def pixmap(self, w, h, data, colorkey=-1):
        pb = GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(data),
                                             GdkPixbuf.Colorspace.RGB,
                                             False, 8, w, h, w*3)
        if colorkey >= 0:
            # pixels of the colorkey colour become transparent
            pb = pb.add_alpha(True, colorkey >> 16,
                              (colorkey >> 8) & 0xFF,
                              colorkey & 0xFF)
        if self.scale == 1:
            return self.renderpixbuf((pb,))
        else:
            return (pb,)

    def renderpixbuf(self, input):
        if len(input) == 3:
            return input
        pb, = input
        surface = Gdk.cairo_surface_create_from_pixbuf(pb, 1, None)
        return (surface, None, None)

    def getopticon(self, input, rect, ignored_alpha=255):
        (x, y, w, h) = rect
        if len(input) == 3:
            return None
        pb, = input
        scale = self.scale
        newpb = pb.new_subpixbuf(x, y, w, h)
        newpb = newpb.scale_simple(int(w*scale), int(h*scale),
                                   GdkPixbuf.InterpType.HYPER)
        if newpb is None:
            return None, None, None
        else:
            return self.renderpixbuf((newpb,))

    def getppm(self, rect, int=int, ceil=math.ceil):
        (x, y, w, h) = rect
        scale = self.scale
        if isinstance(scale, int):
            x *= scale
            y *= scale
            w *= scale
            h *= scale
        else:
            w = int(ceil((x+w)*scale))
            h = int(ceil((y+h)*scale))
            x = int(x*scale)
            y = int(y*scale)
            w -= x
            h -= y
        bkgnd = cairo.ImageSurface(cairo.FORMAT_RGB24, max(w, 1), max(h, 1))
        cr = cairo.Context(bkgnd)
        cr.set_source_surface(self.offscreen, -x, -y)
        cr.paint()
        return bkgnd, None, None

    def putppm(self, x, y, image, rect=None, int=int):
        (surface, ignored1, ignored2) = image
        if surface is None:
            return
        scale = self.scale
        if rect is None:
            srcx = srcy = 0
            w = h = 4095
        else:
            srcx, srcy, w, h = rect
        x = int(x*scale)
        y = int(y*scale)
        cr = cairo.Context(self.offscreen)
        cr.set_source_surface(surface, x-srcx, y-srcy)
        cr.rectangle(x, y, w, h)
        cr.fill()

    def draw_event(self, widget, cr):
        # the playfield scaled to the window, keeping its proportions,
        # centred, with black bars around it
        aw = widget.get_allocated_width()
        ah = widget.get_allocated_height()
        f = min(aw / self.width, ah / self.height)
        ox = (aw - self.width * f) / 2
        oy = (ah - self.height * f) / 2
        self.view = (f, ox, oy)
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        cr.translate(ox, oy)
        cr.scale(f, f)
        cr.set_source_surface(self.front, 0, 0)
        cr.paint()
        return True

    def playfield_xy(self, x, y):
        f, ox, oy = self.view
        return (int((x - ox) / f / self.scale), int((y - oy) / f / self.scale))

    def flip(self):
        # GTK paints the window later, when it handles the draw event,
        # but pclient.py changes the offscreen image right after flip()
        # (it erases the taskbar), so show a copy taken now.
        cr = cairo.Context(self.front)
        cr.set_source_surface(self.offscreen, 0, 0)
        cr.paint()
        self.area.queue_draw()
        self.events_poll()

    def close(self):
        self.window.destroy()

    def clear(self):
        cr = cairo.Context(self.offscreen)
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

    def events_poll(self):
        while Gtk.events_pending():
            Gtk.main_iteration()

    def key_press_event(self, window, event):
        self.events_key.append((event.keyval, KeyPressed))

    def key_release_event(self, window, event):
        self.events_key.append((event.keyval, KeyReleased))

    def motion_notify_event(self, window, event):
        self.event_motion = self.playfield_xy(event.x, event.y)

    def button_press_event(self, window, event):
        self.events_mouse.append(self.playfield_xy(event.x, event.y))

    def keyevents(self):
        self.events_poll()
        result = self.events_key
        self.events_key = []
        return result

    def pointermotion(self):
        result = self.event_motion
        self.event_motion = None
        return result

    def mouseevents(self):
        self.events_poll()
        result = self.events_mouse
        self.events_mouse = []
        return result

    def selectlist(self):
        return []


def htmloptionstext(nameval):
    return 'Scale image by <%s size=5>%%' % (
        nameval('text', 'zoom', default='100'))
