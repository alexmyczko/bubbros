# The modules in this directory import each other by their plain names
# ("import gamesrv"), and they are loaded both as a package
# ("common.gamesrv") and as top-level modules, with the directory on
# sys.path.  Python 2 resolved such imports relative to the package;
# Python 3 does not, so put this directory on sys.path here.
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
if _here not in _sys.path:
    _sys.path.append(_here)
