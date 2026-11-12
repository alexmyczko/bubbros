
 ################################################
##     pygame-based implementation of xshm     ##
################################################

import os
import pygame
from pygame.locals import *
from modes import KeyPressed, KeyReleased


class Display:
    musthidemouse = 0
    mousevisible = 1

    def __init__(self, width, height, title, transparency='yes', fullscreen='no'):
        self.use_transparency = not transparency.startswith('n')
        self.use_fullscreen = fullscreen.startswith('y')

        # Initialize pygame
        pygame.init()

        # Set the display mode.  In full screen, pygame 2's SCALED fills
        # the screen at the screen's own resolution and scales the 656x400
        # playfield, keeping its proportions; asking for a 656x400 screen
        # mode, as before, left it unscaled in a corner, and Wayland
        # compositors do not change screen modes at all.  In a window,
        # SCALED only scales by whole multiples, so a maximized window
        # showed the playfield unscaled: the window is resizable and
        # flip() scales the playfield to it.
        scaled = getattr(pygame, 'SCALED', 0)
        winstyle = HWSURFACE
        if self.use_fullscreen:
            winstyle |= FULLSCREEN | scaled
        else:
            winstyle |= RESIZABLE
        bestdepth = pygame.display.mode_ok((width, height), winstyle, 32)
        self.screen = pygame.display.set_mode((width, height),
                                              winstyle, bestdepth)
        if self.use_fullscreen and scaled:
            # some Wayland setups ignore FULLSCREEN at window creation
            if not pygame.display.is_fullscreen():
                pygame.display.toggle_fullscreen()
        self.size = (width, height)
        self.winstyle = winstyle
        self.view = (1.0, 0, 0)     # scale and offset of the playfield
        self.scaledsize = None
        self.offscreen = pygame.Surface((width, height))
        #decorate the game window
        pygame.display.set_caption(title)
        #pygame.mouse.set_visible(0)
        self.tbcache = None, None
        self.events_key = []
        self.events_mouse = []
        self.prevposition = None
        EVENT_HANDLERS[KEYDOWN] = self.keydown_handler
        EVENT_HANDLERS[KEYUP] = self.keyup_handler
        EVENT_HANDLERS[MOUSEBUTTONDOWN] = self.mousebuttondown_handler
        EVENT_HANDLERS[VIDEORESIZE] = self.videoresize_handler

    def videoresize_handler(self, e):
        # pygame 2 resizes the display surface by itself; pygame 1 needs
        # a new set_mode()
        if pygame.display.get_surface().get_size() != tuple(e.size):
            pygame.display.set_mode(e.size, self.winstyle)

    def playfield_xy(self, pos):
        f, ox, oy = self.view
        return (int((pos[0] - ox) / f), int((pos[1] - oy) / f))

    def keydown_handler(self, e):
        if e.key == K_ESCAPE and self.use_fullscreen:
            raise SystemExit        # ESC to exit the game if full-screen
        self.showmouse(not self.musthidemouse)
        self.events_key.append((e.key, KeyPressed))
        del self.events_key[:-16]

    def keyup_handler(self, e):
        self.events_key.append((e.key, KeyReleased))
        del self.events_key[:-16]

    def mousebuttondown_handler(self, e):
        self.showmouse(1)
        self.events_mouse.append(self.playfield_xy(e.pos))
        del self.events_mouse[:-8]

    def pixmap(self, w, h, data, colorkey=-1):
        img = pygame.image.fromstring(data, (w, h), "RGB")
        if colorkey >= 0:
            r = colorkey & 0xFF
            g = (colorkey >> 8) & 0xFF
            b = (colorkey >> 16) & 0xFF
            img.set_colorkey([r, g, b])
        return img   # not optimized -- must use getopticon()

    def getopticon(self, pixmap, rect, alpha=255):
        if not self.use_transparency:
            alpha = 255
        img = pixmap.subsurface(rect)
        colorkey = pixmap.get_colorkey()
        if alpha == 255 and not colorkey:
            return img.convert(self.offscreen)
        else:
            if colorkey:
                img.set_colorkey(colorkey, RLEACCEL)
            if alpha < 255:
                img.set_alpha(alpha, RLEACCEL)
            img = img.convert_alpha(self.offscreen)
            img.set_alpha(255, RLEACCEL)
            return img

##    def vflipppm(self, img):
##        w, h = img.get_size()
##        colorkey = img.get_colorkey()
##        data = pygame.image.tostring(img, "RGB", 1)
##        flipimg = pygame.image.fromstring(data, (w, h), "RGB")
##        flipimg.set_colorkey(colorkey, RLEACCEL)
##        return flipimg, h

    def getppm(self, rect):
        bkgnd = pygame.Surface(rect[2:])
        bkgnd.blit(self.offscreen, (0, 0), rect)
        return bkgnd

    def putppm(self, x, y, bitmap, rect=None):
        if rect:
            self.offscreen.blit(bitmap, (x, y), rect)
        else:
            self.offscreen.blit(bitmap, (x, y))

    def flip(self):
        screen = pygame.display.get_surface()
        if screen.get_size() == self.size:
            screen.blit(self.offscreen, (0, 0))
            self.view = (1.0, 0, 0)
            self.scaledsize = None
        else:
            # the window was resized or maximized: scale the playfield to
            # it, keeping its proportions, centred, black bars around it
            sw, sh = screen.get_size()
            w, h = self.size
            f = min(sw / w, sh / h)
            tw, th = max(1, int(w * f)), max(1, int(h * f))
            ox, oy = (sw - tw) // 2, (sh - th) // 2
            if self.scaledsize != (sw, sh):
                screen.fill((0, 0, 0))
                self.scaledsize = (sw, sh)
            screen.blit(pygame.transform.smoothscale(self.offscreen,
                                                     (tw, th)), (ox, oy))
            self.view = (f, ox, oy)
        pygame.display.flip()
        events_dispatch()

    def raise_window(self):
        # on Wayland the compositor decides: it may only mark the
        # window as asking for attention
        try:
            from pygame._sdl2.video import Window
            Window.from_display_module().focus()
        except Exception:
            pass

    def close(self):
        self.showmouse(1)
        pygame.display.quit()

    def clear(self):
        self.offscreen.fill([0,0,0,])

    def events_poll(self):
        while 1:
            e = pygame.event.poll()
            if e.type == NOEVENT:
                break
            elif e.type == KEYDOWN:
                self.events_key.append((e.key, KeyPressed))
                del self.events_key[:-16]
            elif e.type == KEYUP:
                self.events_key.append((e.key, KeyReleased))
                del self.events_key[:-16]
            elif e.type == MOUSEBUTTONDOWN:
                self.events_mouse.append(self.playfield_xy(e.pos))
                del self.events_mouse[:-8]
            elif e.type == ENDMUSICEVENT:
                self.next_music()
            elif e.type == QUIT:
                raise SystemExit

    def keyevents(self):
        events_dispatch()
        events = self.events_key
        self.events_key = []
        return events

    def pointermotion(self):
        position = self.playfield_xy(pygame.mouse.get_pos())
        if position != self.prevposition:
            self.showmouse(1)
            self.prevposition = position
            return position
        else:
            return None

    def mouseevents(self):
        events_dispatch()
        events = self.events_mouse
        self.events_mouse = []
        return events

    def selectlist(self):
        return []

    def taskbar(self, xxx_todo_changeme):
        (x, y, w, h) = xxx_todo_changeme
        tbs, tbh = self.tbcache
        if tbh != h:
            tbs = pygame.Surface((32, h)).convert_alpha(self.offscreen)
            alpha_f = 256.0 / h
            for j in range(h):
                tbs.fill((128, 128, 255, int(j*alpha_f)),
                         (0, j, 32, 1))
            self.tbcache = tbs, h
        for i in range(x, x+w, 32):
            dw = x+w-i
            if dw < 32:
                self.offscreen.blit(tbs, (i, y), (0, 0, dw, h))
            else:
                self.offscreen.blit(tbs, (i, y))

    def settaskbar(self, tb_visible):
        self.showmouse(1)
        self.musthidemouse = not tb_visible # and self.use_fullscreen

    def showmouse(self, v):
        if v != self.mousevisible:
            self.mousevisible = v
            pygame.mouse.set_visible(v)


def quit_handler(e):
    raise SystemExit

EVENT_HANDLERS = {
    QUIT: quit_handler,
    }

def events_dispatch(handlers = EVENT_HANDLERS):
    while 1:
        e = pygame.event.poll()
        if e.type == NOEVENT:
            break
        elif e.type in handlers:
            handlers[e.type](e)


def htmloptionstext(nameval):
    return '''
<%s> Full Screen (Esc key to exit)</input><%s><br>
<%s> Draw slightly transparent bubbles</input><%s><br>
''' % (nameval("checkbox", "fullscreen", "yes", default="no"),
       nameval("hidden", "fullscreen", "no"),
       nameval("checkbox", "transparency", "yes", default="yes"),
       nameval("hidden", "transparency", "no"))
