"""Game controllers in the pygame display: which keys the axes press.

The first tests feed axis values to Joysticks by hand, as SDL reports
them.  The last one makes a virtual controller with /dev/uinput, so the
values go through the kernel, SDL and pygame as from a real pad; it is
skipped without write access to /dev/uinput.
"""

import fcntl
import os
import struct
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, 'display'))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
try:
    import pygame
    import dpy_pygame
except ImportError:
    pygame = None


class FakeJoystick:

    def __init__(self, axes):
        self.axes = list(axes)

    def get_numaxes(self):
        return len(self.axes)

    def get_axis(self, axis):
        return self.axes[axis]


@unittest.skipIf(pygame is None, 'needs pygame')
class TestAxes(unittest.TestCase):

    def setUp(self):
        self.keys = []
        self.pads = dpy_pygame.Joysticks.__new__(dpy_pygame.Joysticks)
        self.pads.key = lambda keysym, event: self.keys.append(
            (self.name(keysym), event is dpy_pygame.KeyPressed))
        self.pads.pads = {}

    def plug(self, axes):
        self.pads.pads[7] = dpy_pygame.Pad(FakeJoystick(axes), 0)

    def name(self, keysym):
        kind = (keysym >> 12) & 0xf
        number = keysym & 0xfff
        return {dpy_pygame.JOY_AXIS_NEG: '-', dpy_pygame.JOY_AXIS_POS: '+'
                }[kind] + str(number)

    def move(self, axis, *values):
        for value in values:
            self.pads.event(types.SimpleNamespace(
                type=dpy_pygame.JOYAXISMOTION, instance_id=7,
                axis=axis, value=value))

    def test_stick_left_and_back(self):
        self.plug([0.0, 0.0])
        self.move(0, -0.3, -0.77, -1.0, -0.4, 0.0)
        self.assertEqual(self.keys, [('-0', True), ('-0', False)])

    def test_stick_springs_back_past_the_press_point(self):
        # an Xbox 360 pad on Linux, let go from full left: the first
        # value after -1.0 was 0.586.  That counts as a press to the
        # right, as a fast move from left to right would.
        self.plug([0.0, 0.0])
        self.move(0, -0.3, -0.77, -1.0, 0.586, 0.0)
        self.assertEqual(self.keys, [('-0', True), ('-0', False),
                                     ('+0', True), ('+0', False)])

    def test_stick_left_then_right(self):
        self.plug([0.0, 0.0])
        self.move(0, -0.3, -1.0, -0.5, -0.1, 0.4, 0.9)
        self.assertEqual(self.keys, [('-0', True), ('-0', False),
                                     ('+0', True)])

    def test_trigger_resting_at_minus_one(self):
        self.plug([0.0, -1.0])
        self.move(1, -1.0, -0.85, -0.43, 0.2, 1.0, -1.0)
        self.assertEqual(self.keys, [('+1', True), ('+1', False)])

    def test_trigger_pulled_twice(self):
        self.plug([0.0, -1.0])
        self.move(1, -0.4, 1.0, -1.0, -0.4, 1.0, -1.0)
        self.assertEqual(self.keys, [('+1', True), ('+1', False),
                                     ('+1', True), ('+1', False)])


# /dev/uinput, from linux/uinput.h and linux/input-event-codes.h
EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
ABS_X, ABS_Y = 0, 1
BTN_SOUTH, BTN_EAST = 0x130, 0x131


def _iow(number, size):
    return (1 << 30) | (size << 16) | (ord('U') << 8) | number


UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_ABSBIT = _iow(100, 4), _iow(101, 4), _iow(103, 4)
UI_DEV_SETUP, UI_ABS_SETUP = _iow(3, 92), _iow(4, 28)
UI_DEV_CREATE, UI_DEV_DESTROY = (ord('U') << 8) | 1, (ord('U') << 8) | 2


def uinput_usable():
    return (sys.platform.startswith('linux') and
            os.access('/dev/uinput', os.W_OK))


@unittest.skipIf(pygame is None, 'needs pygame')
@unittest.skipUnless(uinput_usable(), 'needs write access to /dev/uinput')
class TestVirtualPad(unittest.TestCase):

    def make_pad(self, stored):
        """A pad whose sticks go 0..255, centre 128, opened before its
        first report: the kernel holds 'stored' for both sticks."""
        fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
        self.addCleanup(os.close, fd)
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(fd, UI_SET_EVBIT, EV_ABS)
        for button in (BTN_SOUTH, BTN_EAST):
            fcntl.ioctl(fd, UI_SET_KEYBIT, button)
        for axis in (ABS_X, ABS_Y):
            fcntl.ioctl(fd, UI_SET_ABSBIT, axis)
            fcntl.ioctl(fd, UI_ABS_SETUP, struct.pack(
                'HH6i', axis, 0, stored, 0, 255, 0, 0, 0))
        fcntl.ioctl(fd, UI_DEV_SETUP, struct.pack(
            'HHHH80sI', 3, 0x1234, 0x5678, 1, b'bubbros test pad', 0))
        fcntl.ioctl(fd, UI_DEV_CREATE)
        self.addCleanup(fcntl.ioctl, fd, UI_DEV_DESTROY)
        time.sleep(1.0)       # udev makes the device node
        return fd

    def report(self, fd, x, y):
        for axis, value in ((ABS_X, x), (ABS_Y, y)):
            os.write(fd, struct.pack('llHHi', 0, 0, EV_ABS, axis, value))
        os.write(fd, struct.pack('llHHi', 0, 0, EV_SYN, 0, 0))
        time.sleep(0.2)

    def held_after(self, stored, first_report):
        """The keys held after the first report (None: no report)."""
        fd = self.make_pad(stored)
        pygame.init()
        self.addCleanup(pygame.quit)
        keys = []
        pads = dpy_pygame.Joysticks(lambda k, e: keys.append(k))
        if not pads.pads:
            self.skipTest('SDL does not see the virtual pad')
        if first_report is None:
            time.sleep(0.2)
        else:
            self.report(fd, first_report, first_report)
        for e in pygame.event.get():
            if e.type in dpy_pygame.JOYSTICK_EVENTS:
                pads.event(e)
        return [k for pad in pads.pads.values() for k in pad.held]

    def test_opened_at_centre(self):
        self.assertEqual(self.held_after(128, 128), [])

    @unittest.expectedFailure
    def test_trigger_at_rest_opened_before_first_report(self):
        # the axes rest at 0 of 0..255, -1.0 for SDL, and the pad has
        # sent nothing yet.  pygame still delivers 0.0 then -1.0 for
        # each axis after opening: Pad follows SDL and takes the first
        # 0.0 as a stick at its centre, so the trigger holds its
        # negative key.  The fault mode chosen, see
        # https://github.com/alexmyczko/bubbros/pull/58
        self.assertEqual(self.held_after(0, None), [])

    def test_opened_before_first_report(self):
        # SDL gives -1.0 at open; its first event, at the centre, gives
        # the rest (has_second_value in SDL_joystick.c)
        self.assertEqual(self.held_after(0, 128), [])


if __name__ == '__main__':
    unittest.main()
