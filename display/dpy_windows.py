import sys
import wingame
from modes import BaseDisplay
from io import StringIO


class Display(BaseDisplay):
    
    def __init__(self, width, height, title, transparency='yes',
                 fullscreen='no', controller='yes'):
        self.use_transparency = not transparency.startswith('n')
        use_controller = not (controller.startswith('n') or controller == 'off')
        self.xdpy = xdpy = wingame.Display(width, height,
                                           fullscreen.startswith('y'),
                                           use_controller)
        xdpy.settitle(title)
        self.pixmap = xdpy.pixmap
        self.getppm = xdpy.getppm
        self.putppm = xdpy.putppm
        self.close  = xdpy.close
        self.clear  = xdpy.clear
        self.flip   = xdpy.flip
        self.keyevents = xdpy.keyevents
        self.mouseevents = xdpy.mouseevents
        self.pointermotion = xdpy.pointermotion

    def selectlist(self):
        return []

    def getopticon(self, pixmap, rect, alpha=255):
        # a slightly transparent icon: its own pixels, with its alpha
        if alpha >= 255 or not self.use_transparency:
            return None
        w, h, data, keycol = pixmap
        x, y, rw, rh = rect
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + rw, w), min(y + rh, h)
        if x1 <= x0 or y1 <= y0:
            return None
        bpp = len(data) // (w * h)
        rows = [data[(j*w + x0) * bpp:(j*w + x1) * bpp] for j in range(y0, y1)]
        return (x1 - x0, y1 - y0, b''.join(rows), keycol, alpha)


def htmloptionstext(nameval):
    return '''
<%s> Full Screen (Esc key to exit)</input><%s><br>
<%s> Draw slightly transparent bubbles</input><%s><br>
<%s> Controller Input</input><%s><br>
''' % (nameval("checkbox", "fullscreen", "yes", default="no"),
       nameval("hidden", "fullscreen", "no"),
       nameval("checkbox", "transparency", "yes", default="yes"),
       nameval("hidden", "transparency", "no"),
       nameval("checkbox", "controller", "yes", default="yes"),
       nameval("hidden", "controller", "no"))
