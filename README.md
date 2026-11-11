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

## Tests

    python3 -m unittest discover -s tests

## License

The code is under the MIT license. The sounds, music and levels of the
original Mac game are by Sebastian Wegner (McSebi), under the Artistic
License 2.0. See LICENSE.txt.
