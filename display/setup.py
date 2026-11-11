#! /usr/bin/env python3

# distutils was removed in Python 3.12; setuptools provides the same API
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension

import sys

if sys.platform == 'win32':
    # the display and sound driver for Windows (the windows/*.dsp
    # project files are for Visual C++ 6 and Python 2)
    setup ( name="wingame",
            version="0.2",
            description="Windows display and sound for the Bub & Bob client",
            author="Armin & Odie",
            author_email="arigo@tunes.org",
            ext_modules=[Extension(name = 'wingame',
                                   sources = ['windows/wingame.c'],
                                   libraries = ['user32', 'gdi32', 'winmm'])]
            )
else:
    setup ( name="xshm",
            version="0.2",
            description="X window system Shared Memory extension",
            author="Armin & Odie",
            author_email="arigo@tunes.org",
            ext_modules=[Extension(name = 'xshm',
                                   sources = ['xshm.c'],
                                   include_dirs = ['/usr/X11R6/include'],
                                   library_dirs = ['/usr/X11R6/lib'],
                                   libraries = ['X11', 'Xext'])]
            )
