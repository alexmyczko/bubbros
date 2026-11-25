![bubbros](http2/header.png?raw=true "bubbros")

# The Bub's Brothers

A multiplayer game in the style of Bubble Bobble. Trap the monsters in
bubbles, burst them and collect the items. Up to 10 players can play
over the network. The game starts from a page in your web
browser, where you can also join games on other computers.

The Bub's Brothers was written by Armin Rigo and others from 2003 to
2005 (http://bub-n-bros.sourceforge.net). This repository ports it to
Python 3. The server, the clients and the meta-server still speak the
network protocol of version 1.6.2, so old Python 2 clients and servers
can play with the new ones.

Chat: https://matrix.to/#/%23bub-n-bros%3Amatrix.org

## Install on Debian

The game is in Debian unstable (https://tracker.debian.org/pkg/bubbros):

    sudo apt install bubbros

Then run `bubbros`, or `bubbros-server` and `bubbros-client` without
the browser. The Debian package leaves out what is not free: nonfree/
and the three fan level files (see License below).

## What you need to run it from this repository

- Python 3.5+ (3.8+ for the tests).
- On Linux and other systems: pygame, for the client display and
  sound.  
  On Debian or Ubuntu:

      sudo apt install python3 python3-pygame

  On non-managed Python installations:

      python3 -m pip install pygame

- On Windows: Either pygame, installed with `pip` same as above, or
  native Windows display and sound driver, in form of a C extension,
  built once with

      cd display && python setup.py build_ext -i

  Building the native driver needs Microsoft Visual C++ 14.x: Visual
  Studio 2015 or later, or the free Build Tools for Visual Studio, with
  the "Desktop development with C++" workload. setuptools finds the
  compiler by itself, no developer command prompt needed. With Python
  3.12 or later, first `pip install setuptools` (distutils is gone).

Optional:

- GTK 3 client display: `python3-gi gir1.2-gtk-3.0 python3-gi-cairo`
- X11 client display (`-d X`), a C extension: `python3-dev python3-setuptools
  libx11-dev libxext-dev`, then `make -C display`.
- OSS sound (`-s linux`) or Windows native sound (`-s windows`): the
  `audioop` module. Python 3.13 removed it from the standard library;
  install `python3-audioop-lts` (Debian) or `pip install audioop-lts`.

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
a meta-server, a list where servers register. The default is
`bubble.aiei.ch`, run by Alex Myczko.

To use another one, or none, give its address (empty for none) as `host`, `host:port` or
`host:port:httpport` (default ports 8055 and 8050), either on the Options
page, under Network options, or in an environment variable, which takes
precedence:

    BUBBROS_METASERVER=meta.example.org python3 BubBob.py

To run your own meta-server:

    python3 metaserver/metaserver.py [--port 8055] [--http 8050]

It needs these ports open: TCP and UDP 8055, TCP 8050. To run it as a
service, see `metaserver/bubbros-metaserver.service`.

## Tests

Python 3.8+:

    python3 -m unittest discover -s tests

Input and full screen on X11, GNOME, KDE, weston and sway, with real
input events (needs those compositors installed, see
tests/display/README.md):

    python3 tests/display/run.py

## Credits

- Sebastian Wegner (McSebi) made Bub & Bob 1 for the Mac (1997 to
  2001). The sprites, sounds, music and levels of this game come from
  it, and in 2005 he released them under a free licence.
- Armin Rigo wrote The Bub's Brothers (2003 to 2005).
- David Gowers redrew the graphics, based on McSebi's.
- Gio, Odie (Olivier Dormond), Michel-Stéphane and Armin Rigo made the
  levels in bubbob/levels/*.py.
- The original authors also thanked Odie and Brachamutanda, and the
  beta testers of IMA Connection.
- Fan level sets: Wim De Gent (Arena), Michael S. Repton (The House of
  Fun) and Patrick Viney (Lost Levels).
- Subgame music: Eric Matyas (www.soundimage.org), HydroGene, Cleyton
  Kauffman, OwlishMedia and Jonathan Shaw (www.jshaw.co.uk).
- Python 3 port: Christopher Bock, Alex Myczko, anzz1 and Juan Manuel
  Méndez Rey.
- Debian packages: Siegfried-Angel Gevatter Pujals and Juhani Numminen
  (1.6 to 1.6.2), Juan Manuel Méndez Rey (2.4, sponsored by Alex
  Myczko).

Sources for the game, graphics, levels and music credits are in
PROVENANCE.md.

## Contributing

Report bugs and send pull requests at
https://github.com/alexmyczko/bubbros . Please run the tests before you
send a change.

## License

- The code is by Armin Rigo and others, under the MIT license.
- The graphics are by David Gowers, based on McSebi's, under the
  Artistic License 2.0.
- Almost all sounds and music, and the levels in Levels.bin, come from
  the Mac game Bub & Bob 1 by Sebastian Wegner (McSebi), under the
  Artistic License 2.0.
- The music and sounds of the subgames (bubbob/ext1 to ext7) are free
  replacements, under CC-BY-3.0 or CC0-1.0. Authors and sources are in
  PROVENANCE.md.
- nonfree/ holds the original subgame sounds and some wall patterns.
  They have no free licence, see nonfree/README.md.
- The level files Arena.bin, HouseOfFun.bin and LostLevels.bin were made
  by fans and have no licence yet, see RELICENSING-PERMISSIONS.md.

Details: LICENSE.txt.
