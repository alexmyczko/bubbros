import sys
import wingame
from modes import BaseDisplay
from io import StringIO


class Display(BaseDisplay):
    
    def __init__(self, width, height, title, fullscreen='no'):
        self.xdpy = xdpy = wingame.Display(width, height,
                                           fullscreen.startswith('y'))
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


def htmloptionstext(nameval):
    return '''
<%s> Full Screen (Esc key to exit)</input><%s><br>
''' % (nameval("checkbox", "fullscreen", "yes", default="no"),
       nameval("hidden", "fullscreen", "no"))
