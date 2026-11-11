"""Where the options chosen in the web page are saved.

The server writes them and the client reads them.  They live in
http2/config.txt, next to the game, when that directory is writable
(the game run from its own directory); otherwise, as when the game is
installed system-wide, in the user's configuration directory.
"""

import os


def path(sourcedir):
    """The configuration file of the game installed in 'sourcedir'."""
    local = os.path.join(sourcedir, 'http2', 'config.txt')
    if os.path.exists(local) or os.access(os.path.dirname(local), os.W_OK):
        return local
    base = os.environ.get('XDG_CONFIG_HOME') or os.path.join(
        os.path.expanduser('~'), '.config')
    return os.path.join(base, 'bubbros', 'config.txt')
