#! /usr/bin/env python3

# distutils was removed in Python 3.12; setuptools provides the same API
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension

##setup (       name="gencopy",
##              version="0.1",
##              description="generator and iterator state",
##              author="Armin",
##        author_email="arigo@tunes.org",
##              ext_modules=[Extension(name = 'gencopy',
##                               sources = ['gencopy.c'])]
##        )

setup ( name="statesaver",
        version="0.1",
        description="object duplicator working on generators and iterators",
        author="Armin",
        author_email="arigo@tunes.org",
        ext_modules=[Extension(name = 'statesaver',
                               sources = ['statesaver.c'])]
        )
