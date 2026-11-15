#!/usr/bin/env python3
"""Check that each subgame music in nonfree/ is an excerpt of the
OverClocked ReMix recording named in nonfree/README.md.

For each loop it downloads the source MP3 from its public URL (or uses a
copy in --cache), checks its sha256, decodes both files with ffmpeg to
mono 44.1 kHz and plays the source at the stated speed.  Then it cuts the
loop into 1 second pieces and slides each piece along the whole source,
computing at every position the normalised correlation of the two
waveforms (1.0 = the same samples, about 0 = unrelated).  It prints where
each piece is found and its correlation.  As a control it does the same
against the other recordings of the list, which are unrelated music.

The pieces are placed one by one because some loops are cut from two
places of the remix (ext1, ext2).

Needs python3-numpy and ffmpeg.  Usage, from the top of the repository:
    python3 nonfree/verify_sources.py [--cache DIR] [ext1 ext3 ...]
"""

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.request

import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))

# loop, source page, source MP3, its sha256, speed of the source in the loop
SOURCES = [
    ('ext1', 'https://ocremix.org/remix/OCR00958',
     'https://ocrmirror.org/files/music/remixes/Arkanoid_Black_Block_OC_ReMix.mp3',
     'f026567718aedec58a6d078f0d745ae4de915f82c2944b29d9f447666373345c',
     2 ** (-1 / 12)),
    ('ext2', 'https://ocremix.org/remix/OCR00021',
     'https://ocrmirror.org/files/music/remixes/Pac-Man_64-bit_OC_ReMix.mp3',
     'bf20093f2ad29f78b7d07ba3444d0ad55bc4b577e0aa9bb46ce02712e5175d33',
     1.0),
    ('ext3', 'https://web.archive.org/web/20031023174756/http://www.ocremix.org:80/detailmix.php?mixid=OCR00086',
     'https://web.archive.org/web/20130831210310id_/http://doulifee.com//Storage/OC_Removed/Galaga_Galagzee_OC_ReMoved.mp3',
     '755dc6e4ff35ce1bc9abef5d23ec5cb0db25df0d3d1a25c20d02f364279a7c9b',
     1.0),
    ('ext4', 'https://ocremix.org/remix/OCR00155',
     'https://ocrmirror.org/files/music/remixes/Tetris_MkVaffQuasi_Ultimix_OC_ReMix.mp3',
     'f7f828d5e1b87803a34e9927bddb19764084356ecffe4d7eeedc6bfac8dc8869',
     1.0),
    ('ext5', 'https://ocremix.org/remix/OCR00105',
     'https://ocrmirror.org/files/music/remixes/Lemmings_DABOMB_OC_ReMix.mp3',
     'b868cc7a8d8079630ffe64ea7a99be22eabe4a6ecb26b76907a1a29684d63ebe',
     1.0),
]


def decode(path):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path,
                          '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         check=True, stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, dtype='<f4').astype(np.float64)


def fetch(url, sha, cache):
    path = os.path.join(cache, os.path.basename(url))
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={'User-Agent': 'bubbros-verify'})
        with urllib.request.urlopen(req) as r, open(path + '.part', 'wb') as f:
            f.write(r.read())
        os.rename(path + '.part', path)
    with open(path, 'rb') as f:
        got = hashlib.sha256(f.read()).hexdigest()
    if got != sha:
        sys.exit('%s: sha256 %s, expected %s' % (path, got, sha))
    return path


def correlate(loop, src):
    """Normalised correlation of loop against src at every position."""
    n = len(loop)
    loop = loop - loop.mean()
    size = 1 << int(np.ceil(np.log2(len(src) + n)))
    num = np.fft.irfft(np.fft.rfft(src, size) *
                       np.conj(np.fft.rfft(loop, size)), size)[:len(src) - n + 1]
    c1 = np.concatenate(([0.0], np.cumsum(src)))
    c2 = np.concatenate(([0.0], np.cumsum(src * src)))
    s1 = c1[n:] - c1[:-n]
    var = np.maximum(c2[n:] - c2[:-n] - s1 * s1 / n, 1e-12)
    return num / (np.sqrt(var) * np.linalg.norm(loop))


def ncc(a, b):
    a = a - a.mean(); b = b - b.mean()
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def pieces(loop):
    return [loop[k:k + SR] for k in range(0, len(loop) - SR + 1, SR)]


def place(piece, src):
    c = np.abs(correlate(piece, src))
    at = int(np.argmax(c))
    return at, float(c[at])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache', help='directory for the downloaded MP3s')
    ap.add_argument('only', nargs='*')
    args = ap.parse_args()
    cache = args.cache or tempfile.mkdtemp(prefix='bubbros-verify-')
    os.makedirs(cache, exist_ok=True)
    srcs = {}
    for ext, page, url, sha, speed in SOURCES:
        src = decode(fetch(url, sha, cache))
        if speed != 1.0:   # the loop plays the source at this speed
            src = np.interp(np.arange(0, len(src) - 1, speed),
                            np.arange(len(src)), src)
        srcs[ext] = src
    for ext, page, url, sha, speed in SOURCES:
        if args.only and ext not in args.only:
            continue
        loop = decode(os.path.join(HERE, 'bubbob', ext, 'music.wav'))
        print('%s/music.wav (%.2f s) in %s, speed %.4f' %
              (ext, len(loop) / SR, page, speed))
        found, control = [], []
        for i, piece in enumerate(pieces(loop)):
            at, c = place(piece, srcs[ext])
            other = max(place(piece, s)[1] for e, s in srcs.items() if e != ext)
            found.append(c); control.append(other)
            print('  %2d-%2d s of the loop = %7.3f s of the source, '
                  'correlation %.3f (best in the other recordings %.3f)'
                  % (i, i + 1, at * speed / SR, c, other))
        print('  lowest %.3f, highest control %.3f' % (min(found), max(control)))


if __name__ == '__main__':
    main()
