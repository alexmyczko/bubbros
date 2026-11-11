# bubbros
Adopt from sf.net Bub n Bros for port to Python3

Original: http://bub-n-bros.sourceforge.net

The game now runs on Python 3. The server, the clients and the
metaserver use the same network protocol as version 1.6.2, so old
Python 2 clients and servers can still play with the new ones.

## What you need

- Python 3.
- pygame, for the usual client display and sound.

On Debian or Ubuntu:

    sudo apt install python3 python3-pygame

Optional:

- GTK 3 client display: `python3-gi gir1.2-gtk-3.0 python3-gi-cairo`
- X11 client display (`-d X`), a C extension: `python3-dev python3-setuptools
  libx11-dev libxext-dev`, then `make -C display`.
- OSS sound (`-s linux`) or Windows sound: the `audioop` module. Python 3.13
  removed it from the standard library; install `python3-audioop-lts`
  (Debian) or `pip install audioop-lts`.

## How to play

Start the game and open its page in your web browser:

    python3 BubBob.py

From the page you start a server, choose the levels and join the game.

Without the browser:

    python3 bubbob/bb.py bubbob/levels/Levels.bin     # the server
    python3 display/Client.py localhost:PORT          # a client

The server prints the PORT it listens on.

`python3 bubbob/bb.py --help` and `python3 display/Client.py --help` list
the options.

## Internet games

Games on your local network show up by themselves, and you can always
join a game by its address. To find games on the Internet, the game uses
a meta-server, a list where servers register. The public one
(ctpug.org.za) no longer runs, so none is set by default.

To use one, give its address as `host`, `host:port` or
`host:port:httpport` (default ports 8055 and 8050), either on the Options
page, under Network options, or in an environment variable, which takes
precedence:

    BUBBROS_METASERVER=meta.example.org python3 BubBob.py

To run your own meta-server:

    python3 metaserver/metaserver.py [--port 8055] [--http 8050]

It needs these ports open: TCP and UDP 8055, TCP 8050. To run it as a
service, see `metaserver/bubbros-metaserver.service`.

## Tests

    python3 -m unittest discover -s tests

Input and full screen on X11, GNOME, KDE, weston and sway, with real
input events (needs those compositors installed, see
tests/display/README.md):

    python3 tests/display/run.py

## License

The code is under the MIT license. The sounds, music and levels of the
original Mac game are by Sebastian Wegner (McSebi), under the Artistic
License 2.0. See LICENSE.txt.
