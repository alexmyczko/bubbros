#!/usr/bin/env python3
"""Input and full screen tests of the client, with real input events,
on X11 and on Wayland compositors.  Nothing runs on your own desktop:
each environment gets its own Xvfb, session bus, XDG_RUNTIME_DIR and
HOME, and is stopped at the end.

usage: tests/display/run.py [environment...] [--modes pygame,gtk,fullscreen]

environments: x11 weston sway kde gnome (default: all)
  x11     Xvfb + matchbox-window-manager
  weston  weston, X11 backend, on Xvfb
  sway    sway, X11 backend, on Xvfb
  kde     kwin_wayland on Xvfb
  gnome   mutter --headless; input through its RemoteDesktop D-Bus API
An environment whose programs are missing is reported as SKIP.

Each case starts a server and a client, clicks the first dragon of the
taskbar, defines the keys Right Left Up space, then holds Left and
Right.  It passes when the client's display driver received the click
on the dragon, the four keys in that order, and the movement keys; in
full screen, the 656x400 playfield must also be scaled to the 1024x768
screen and centred.  See README.md.
"""

import argparse
import os
import re
import select
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir))
SCREEN = (1024, 768)
PLAYFIELD = (656, 400)
DRAGON = (38, 380)          # the first dragon of the taskbar, playfield coords
KEYS = ['Right', 'Left', 'Up', 'space']

# keysyms as the drivers return them: SDL keycodes (pygame), X keysyms
# (gtk and x)
KEYSYM_NAMES = {
    1073741903: 'Right', 1073741904: 'Left', 1073741906: 'Up', 32: 'space',
    0xff53: 'Right', 0xff51: 'Left', 0xff52: 'Up',
}
X_KEYSYMS = {'Right': 0xff53, 'Left': 0xff51, 'Up': 0xff52, 'space': 0x20,
             'Shift_L': 0xffe1}

# variables of the user's own session that must not reach the test
# environment (a KDE session's XDG_CURRENT_DESKTOP makes kwin crash in
# Qt's KDE theme without a KDE session bus, for instance)
SESSION_VARS = ('DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'SWAYSOCK',
                'DBUS_SESSION_BUS_ADDRESS', 'XDG_CURRENT_DESKTOP',
                'XDG_SESSION_TYPE', 'XDG_SESSION_DESKTOP', 'DESKTOP_SESSION',
                'GDK_BACKEND', 'SDL_VIDEODRIVER', 'QT_QPA_PLATFORM',
                'QT_QPA_PLATFORMTHEME')


class Skip(Exception):
    pass


def wait_for(condition, timeout, what):
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = condition()
        if result:
            return result
        time.sleep(0.1)
    raise RuntimeError('timeout waiting for %s' % what)


def port_open(port):
    with socket.socket() as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Session:
    """The processes and the private directories of one test case."""

    def __init__(self, workdir):
        self.dir = tempfile.mkdtemp(prefix='bubbros-display-', dir=workdir)
        self.runtime = os.path.join(self.dir, 'run')
        os.mkdir(self.runtime, 0o700)
        self.procs = []
        env = dict((k, v) for k, v in os.environ.items()
                   if k not in SESSION_VARS and not k.startswith(('KDE_', 'QT_')))
        env.update(HOME=self.dir, XDG_RUNTIME_DIR=self.runtime,
                   XDG_CONFIG_HOME=os.path.join(self.dir, 'config'),
                   XDG_DATA_HOME=os.path.join(self.dir, 'data'),
                   XDG_CACHE_HOME=os.path.join(self.dir, 'cache'),
                   SDL_AUDIODRIVER='dummy')
        self.env = env

    def spawn(self, name, cmd, env=None, **kw):
        log = open(os.path.join(self.dir, name + '.log'), 'w')
        # a session of its own, so that stop() ends exactly this process
        # and its children
        p = subprocess.Popen(cmd, env=env or self.env, stdout=log,
                             stderr=subprocess.STDOUT, start_new_session=True,
                             **kw)
        self.procs.append(p)
        return p

    def read_fd_line(self, name, cmd, option_fmt, timeout=10):
        """Start cmd with a pipe for option_fmt (e.g. '-displayfd %d') and
        return the first line the program writes to it."""
        r, w = os.pipe()
        self.spawn(name, cmd + (option_fmt % w).split(), pass_fds=(w,))
        os.close(w)
        if not select.select([r], [], [], timeout)[0]:
            raise RuntimeError('%s did not start' % name)
        line = os.read(r, 4096).decode().split('\n')[0].strip()
        os.close(r)
        return line

    def stop(self):
        for p in reversed(self.procs):
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        deadline = time.time() + 5
        for p in self.procs:
            try:
                p.wait(max(0.1, deadline - time.time()))
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()

    def log(self, name):
        with open(os.path.join(self.dir, name + '.log')) as f:
            return f.read()

    # ____________________________________________________________
    # building blocks

    def xvfb(self):
        display = self.read_fd_line(
            'xvfb', ['Xvfb', '-screen', '0', '%dx%dx24' % SCREEN,
                     '-nolisten', 'tcp'], '-displayfd %d')
        self.env['DISPLAY'] = ':' + display
        return self.env['DISPLAY']

    def dbus(self):
        address = self.read_fd_line(
            'dbus', ['dbus-daemon', '--session', '--nofork'],
            '--print-address=%d')
        self.env['DBUS_SESSION_BUS_ADDRESS'] = address
        return address

    def wayland(self, name):
        socket_path = os.path.join(self.runtime, name)
        wait_for(lambda: os.path.exists(socket_path), 20,
                 'the Wayland socket %s' % name)
        self.env.update(WAYLAND_DISPLAY=name, SDL_VIDEODRIVER='wayland',
                        GDK_BACKEND='wayland')

    def window_under_centre(self):
        """The X window of a nested compositor (it covers the screen)."""
        def find():
            subprocess.run(['xdotool', 'mousemove', str(SCREEN[0] // 2),
                            str(SCREEN[1] // 2)], env=self.env)
            out = subprocess.run(['xdotool', 'getmouselocation', '--shell'],
                                 env=self.env, capture_output=True,
                                 text=True).stdout
            m = re.search(r'WINDOW=(\d+)', out)
            return m and m.group(1) != '0' and m.group(1)
        return wait_for(find, 20, 'the compositor window')


# ____________________________________________________________
# environments: each sets up a Session and returns an injector

def env_x11(s):
    s.xvfb()
    kbd = os.path.join(s.dir, 'matchbox-kbd')
    open(kbd, 'w').close()     # no key bindings: all keys go to the client
    s.spawn('wm', ['matchbox-window-manager', '-use_titlebar', 'no',
                   '-kbdconfig', kbd])
    return XdoInjector(s, None)

def env_weston(s):
    s.xvfb()
    s.spawn('weston', ['weston', '--backend=x11-backend.so',
                       '--renderer=pixman', '--shell=desktop-shell.so',
                       '--width=%d' % SCREEN[0], '--height=%d' % SCREEN[1],
                       '--socket=bbweston', '--idle-time=0'])
    s.wayland('bbweston')
    return XdoInjector(s, s.window_under_centre())

def env_sway(s):
    s.xvfb()
    config = os.path.join(s.dir, 'sway.config')
    with open(config, 'w') as f:
        f.write('output * resolution %dx%d\n' % SCREEN)
    env = dict(s.env, WLR_BACKENDS='x11', WLR_RENDERER='pixman',
               WLR_X11_OUTPUTS='1')
    s.spawn('sway', ['sway', '--config', config], env=env)
    name = wait_for(lambda: [n for n in os.listdir(s.runtime)
                             if re.match(r'wayland-\d+$', n)],
                    20, 'the sway socket')[0]
    s.wayland(name)
    return XdoInjector(s, s.window_under_centre())

def env_kde(s):
    s.xvfb()
    s.dbus()
    env = dict(s.env, KWIN_COMPOSE='Q')
    s.spawn('kwin', ['kwin_wayland', '--x11-display', s.env['DISPLAY'],
                     '--width', str(SCREEN[0]), '--height', str(SCREEN[1]),
                     '--socket', 'bbkwin', '--no-lockscreen',
                     '--no-global-shortcuts', '--no-kactivities'], env=env)
    s.wayland('bbkwin')
    return XdoInjector(s, s.window_under_centre())

def env_gnome(s):
    address = s.dbus()
    s.spawn('mutter', ['mutter', '--headless', '--wayland', '--no-x11',
                       '--virtual-monitor', '%dx%d' % SCREEN,
                       '--wayland-display', 'bbmutter'])
    s.wayland('bbmutter')
    return MutterInjector(s, address)

ENVIRONMENTS = {
    'x11':    (env_x11, ['Xvfb', 'matchbox-window-manager', 'xdotool']),
    'weston': (env_weston, ['Xvfb', 'weston', 'xdotool']),
    'sway':   (env_sway, ['Xvfb', 'sway', 'xdotool']),
    'kde':    (env_kde, ['Xvfb', 'kwin_wayland', 'dbus-daemon', 'xdotool']),
    'gnome':  (env_gnome, ['mutter', 'dbus-daemon']),
}


# ____________________________________________________________
# real input

class XdoInjector:
    """XTEST input with xdotool.  The pointer moves relative to the
    compositor's X window; clicks and keys are not sent with --window,
    which would make them synthetic events (XSendEvent), which weston's
    X11 backend refuses."""

    def __init__(self, session, window):
        self.s = session
        self.window = ['--window', window] if window else []

    def xdo(self, *args):
        subprocess.run(['xdotool'] + [str(a) for a in args], env=self.s.env,
                       check=True)

    def click(self, x, y):
        self.xdo('mousemove', *(self.window + [int(x), int(y)]))
        time.sleep(0.2)
        self.xdo('click', 1)

    def key(self, name, hold=0.05):
        self.xdo('keydown', name)
        time.sleep(hold)
        self.xdo('keyup', name)


class MutterInjector:
    """Input through org.gnome.Mutter.RemoteDesktop, the API of GNOME's
    remote desktop.  Pointer motion is relative, from the top-left
    corner."""

    def __init__(self, session, address):
        from gi.repository import Gio, GLib
        self.GLib = GLib
        self.bus = Gio.DBusConnection.new_for_address_sync(
            address, Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
            Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
        self.Gio = Gio
        self.path = None
        self.pos = None

    def start(self):
        # only once the client window exists: a session started before
        # it gave no input at all to the window
        if self.path is None:
            self.path = wait_for(self.create_session, 20,
                                 'the RemoteDesktop service')
            self.call('Start')
            time.sleep(0.5)

    def create_session(self):
        try:
            return self._call('/org/gnome/Mutter/RemoteDesktop',
                              'org.gnome.Mutter.RemoteDesktop',
                              'CreateSession', None)[0]
        except Exception:
            return None

    def _call(self, path, iface, method, sig, *args):
        return self.bus.call_sync(
            'org.gnome.Mutter.RemoteDesktop', path, iface, method,
            self.GLib.Variant(sig, args) if sig else None, None,
            self.Gio.DBusCallFlags.NONE, -1, None).unpack()

    def call(self, method, sig=None, *args):
        return self._call(self.path, 'org.gnome.Mutter.RemoteDesktop.Session',
                          method, sig, *args)

    def click(self, x, y):
        self.start()
        if self.pos is None:
            self.call('NotifyPointerMotionRelative', '(dd)',
                      -10.0 * SCREEN[0], -10.0 * SCREEN[1])
            self.pos = (0, 0)
        self.call('NotifyPointerMotionRelative', '(dd)',
                  float(x - self.pos[0]), float(y - self.pos[1]))
        self.pos = (x, y)
        time.sleep(0.2)
        for pressed in (True, False):
            self.call('NotifyPointerButton', '(ib)', 0x110, pressed)
            time.sleep(0.05)

    def key(self, name, hold=0.05):
        self.start()
        sym = X_KEYSYMS[name]
        self.call('NotifyKeyboardKeysym', '(ub)', sym, True)
        time.sleep(hold)
        self.call('NotifyKeyboardKeysym', '(ub)', sym, False)


# ____________________________________________________________
# one test case

class ProbeLog:
    def __init__(self, path):
        self.path = path

    def lines(self):
        try:
            with open(self.path) as f:
                return f.read().split('\n')
        except OSError:
            return []

    def mouse(self):
        return [tuple(map(int, l.split()[1:])) for l in self.lines()
                if l.startswith('MOUSE ')]

    def driver(self):
        for l in self.lines():
            if l.startswith('DRIVER '):
                return l.split()[1]

    def new_mouse(self, count, timeout=5):
        return wait_for(lambda: len(self.mouse()) > count and self.mouse()[-1],
                        timeout, 'a click to reach the client')


def run_case(envname, mode, workdir):
    setup, programs = ENVIRONMENTS[envname]
    missing = [p for p in programs if not shutil.which(p)]
    if missing:
        raise Skip('missing ' + ', '.join(missing))
    s = Session(workdir)
    try:
        injector = setup(s)
        port = free_port()
        env = dict(s.env)
        s.spawn('server', [sys.executable, os.path.join(ROOT, 'bubbob', 'bb.py'),
                           os.path.join(ROOT, 'bubbob', 'levels', 'Levels.bin'),
                           '--port', 'LISTEN=%d' % port,
                           '--port', 'HTTP=%d' % free_port()], env=env)
        wait_for(lambda: port_open(port), 20, 'the game server')
        probe = ProbeLog(os.path.join(s.dir, 'probe.log'))
        options = {'pygame': ['--display=pygame'], 'gtk': ['--display=gtk'],
                   'fullscreen': ['--display=pygame', '--fullscreen=yes']}[mode]
        s.spawn('client', [sys.executable, '-u',
                           os.path.join(HERE, 'probe_client.py'), probe.path,
                           os.path.join(ROOT, 'display', 'Client.py')]
                + options + ['--sound=off', '127.0.0.1:%d' % port], env=env)
        wait_for(probe.driver, 30, 'the client window')
        time.sleep(2)            # the first frames and the taskbar
        return drive_and_check(injector, probe, mode)
    finally:
        s.stop()


def drive_and_check(inj, probe, mode):
    problems = []
    # the first key of a new virtual keyboard can be lost while the
    # client takes its keymap: send one that does nothing here
    inj.key('Shift_L' if isinstance(inj, MutterInjector) else 'shift')
    time.sleep(0.5)
    # calibration: where do two screen points land in the playfield?
    cx, cy = SCREEN[0] // 2, SCREEN[1] // 2
    inj.click(cx, cy)
    px, py = probe.new_mouse(0)
    inj.click(cx + 100, cy + 100)
    qx, qy = probe.new_mouse(1)
    scale = 100.0 / max(1, qx - px)
    if mode == 'fullscreen':
        expected = min(SCREEN[0] / PLAYFIELD[0], SCREEN[1] / PLAYFIELD[1])
        centre = (PLAYFIELD[0] // 2, PLAYFIELD[1] // 2)
        if abs(scale - expected) > 0.02 or abs(px - centre[0]) > 3 \
                or abs(py - centre[1]) > 3:
            problems.append('full screen not scaled and centred: scale %.3f, '
                            'screen centre at %d,%d' % (scale, px, py))
    # click the first dragon, then define the keys
    inj.click(cx + 100 + (DRAGON[0] - qx) * scale,
              cy + 100 + (DRAGON[1] - qy) * scale)
    x, y = probe.new_mouse(2)
    if abs(x - DRAGON[0]) > 3 or abs(y - DRAGON[1]) > 3:
        problems.append('the click on the dragon arrived at %d,%d' % (x, y))
    for name in KEYS:
        inj.key(name)
        time.sleep(0.4)
    time.sleep(3)
    for name in ('Left', 'Right'):
        inj.key(name, hold=1.5)
        time.sleep(0.5)
    time.sleep(0.5)

    lines = probe.lines()
    defined = []
    for l in lines:
        if l.startswith('DEFINE '):
            name = KEYSYM_NAMES.get(int(l.split()[1]), l.split()[1])
            if name not in defined:
                defined.append(name)
    if defined[:4] != KEYS:
        problems.append('keys defined: %s' % ' '.join(defined))
    last_define = max([i for i, l in enumerate(lines) if l.startswith('DEFINE ')]
                      or [len(lines)])
    moved = set(KEYSYM_NAMES.get(int(l.split()[1]))
                for l in lines[last_define + 1:]
                if l.startswith('KEY ') and l.split()[2] == '1')
    if not {'Left', 'Right'} <= moved:
        problems.append('movement keys received after the definition: %s'
                        % ' '.join(sorted(n for n in moved if n)))
    return probe.driver(), problems


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('environments', nargs='*', default=list(ENVIRONMENTS),
                        metavar='environment')
    parser.add_argument('--modes', default='pygame,gtk,fullscreen')
    parser.add_argument('--keep', action='store_true',
                        help='keep the logs of each case')
    args = parser.parse_args()
    unknown = set(args.environments) - set(ENVIRONMENTS)
    if unknown:
        parser.error('unknown environment: %s' % ' '.join(sorted(unknown)))
    workdir = tempfile.mkdtemp(prefix='bubbros-display-tests-')
    failed = 0
    for envname in args.environments or list(ENVIRONMENTS):
        for mode in args.modes.split(','):
            label = '%-7s %-10s' % (envname, mode)
            try:
                driver, problems = run_case(envname, mode, workdir)
            except Skip as e:
                print('%s SKIP  %s' % (label, e), flush=True)
                continue
            except Exception as e:
                driver, problems = None, ['%s: %s' % (type(e).__name__, e)]
            if problems:
                failed += 1
                print('%s FAIL  %s' % (label, '; '.join(problems)), flush=True)
            else:
                print('%s PASS  (%s driver)' % (label, driver), flush=True)
    if args.keep or failed:
        print('logs in', workdir)
    else:
        shutil.rmtree(workdir)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
