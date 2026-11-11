# Display tests

`run.py` checks that the client gets mouse and keyboard input, and that
full screen fills the screen, on X11 and on four Wayland compositors. It
sends real input events, not calls into the game.

```
python3 tests/display/run.py                       # everything, about 4 minutes
python3 tests/display/run.py gnome kde             # some environments
python3 tests/display/run.py --modes fullscreen    # some modes
```

Each line of the output is one case:

```
kde     fullscreen PASS  (pygame driver)
```

The exit status is 1 if a case failed, and the logs of the run are kept
(the path is printed). An environment whose programs are missing is
reported as `SKIP`.

## Environments

| Name | What runs | Input |
|---|---|---|
| `x11` | Xvfb and matchbox-window-manager | xdotool |
| `weston` | weston on Xvfb (X11 backend) | xdotool on its window |
| `sway` | sway on Xvfb (X11 backend) | xdotool on its window |
| `kde` | kwin_wayland on Xvfb | xdotool on its window |
| `gnome` | mutter `--headless` | GNOME's RemoteDesktop D-Bus API |

On Debian:

```
sudo apt install xvfb matchbox-window-manager xdotool weston sway \
    kwin-wayland mutter dbus-daemon python3-pygame python3-gi \
    python3-gi-cairo gir1.2-gtk-3.0
```

Nothing touches your own desktop: every case starts its own Xvfb or
headless compositor, its own session bus, and uses a temporary `HOME`
and `XDG_RUNTIME_DIR`. All of it is stopped at the end of the case.

## What a case does

Modes: `pygame` and `gtk` (windowed), `fullscreen` (pygame).

1. Start a game server and the client, `display/Client.py`, through
   `probe_client.py`, which logs what the display driver returns.
2. Click two points of the screen, to learn where the playfield is and
   how it is scaled (the window may be anywhere: points are tried until
   one reaches the client).
3. Click the first dragon of the taskbar and press Right, Left, Up and
   space, which define the keys of a new player.
4. Hold Left, then Right.

It passes when:

- the client received the click on the dragon, the four keys in that
  order and then the movement keys;
- the 656x400 playfield fills the window it was given, keeping its
  proportions (some window managers maximize it); in full screen it
  must also be centred on the 1024x768 screen;
- with GTK, the click the driver reports is the one the drawing area
  got: with client-side decorations a window's own coordinates include
  its title bar.
