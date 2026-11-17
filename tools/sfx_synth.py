#!/usr/bin/env python3
"""Render the seven sound effects of the subgames from a few numbers each:
ext1 brick and wall, ext3 shoot, ext5 ouch, ext6 crash (ext7 uses it too),
ext7 fire and hit.

They replace effects of unknown origin (see PROVENANCE.md).  Each sound is
written here from scratch: a sine, square, pulse or noise source, a pitch
path, filters and a volume envelope, with no sample taken from anywhere.
The noise uses fixed seeds, so the output is the same on every run.

usage: tools/sfx_synth.py TOP_DIR
writes TOP_DIR/bubbob/ext1/brick.wav and the six others (8-bit mono 44.1 kHz)

The files in bubbob/ are: tools/sfx_synth.py .

Copyright 2026 Juan Manuel Méndez Rey <juan.mendezr@proton.me>.
Released under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/
"""
import os, sys, wave
import numpy as np

SR = 44100


def t(seconds):
    return np.arange(int(round(seconds * SR))) / SR


def sine(freq):
    """Sine whose frequency follows the array freq (Hz per sample)."""
    return np.sin(2 * np.pi * np.cumsum(freq) / SR)


def square(freq):
    return np.sign(sine(freq))


def fade(x, ms=3):
    """Short fade in and out, against clicks."""
    n = int(SR * ms / 1000)
    x = x.copy()
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def lowpass(x, fc):
    """Two one-pole low-pass filters in a row; fc in Hz per sample."""
    y = np.zeros_like(x)
    s1 = s2 = 0.0
    for i in range(len(x)):
        a = 1 - np.exp(-2 * np.pi * fc[i] / SR)
        s1 += a * (x[i] - s1)
        s2 += a * (s1 - s2)
        y[i] = s2
    return y


def resonator(x, F, B):
    """Two-pole resonance at F Hz, bandwidth B Hz (arrays per sample)."""
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    for k in range(len(x)):
        r = np.exp(-np.pi * B[k] / SR)
        c = 2 * r * np.cos(2 * np.pi * F[k] / SR)
        v = (1 - r) * x[k] + c * y1 - r * r * y2
        y2, y1 = y1, v
        y[k] = v
    return y / np.abs(y).max()


def brick():
    # a short low blip, then the same note an octave up that rings and dies
    a, b = t(0.06), t(0.54)
    lo = square(np.full(len(a), 880.0))
    hi = square(np.full(len(b), 1760.0)) * np.minimum(1, 1.6 * (1 - b / b[-1]))
    return 0.22 * fade(np.concatenate([lo, hi]))


def wall():
    # a dull bonk: an overdriven 440 Hz sine fading out
    x = t(0.30)
    s = np.tanh(2.5 * sine(np.full(len(x), 440.0))) / np.tanh(2.5)
    return 0.9 * fade(s * (1 - x / x[-1]))


def shoot():
    # a laser: sine falling from 1150 to 450 Hz
    x = t(0.30)
    s = sine(1150 - 700 * x / x[-1])
    return 0.55 * fade(s * (1 - x / x[-1]))


def fire():
    # two quick shots of a falling tone, the second a little lower
    out = []
    for top in (540, 505):
        x = t(0.15)
        s = sine(top - 70 * x / x[-1])
        env = np.minimum(1, x / 0.012) * (1 - x / x[-1]) ** 1.5
        out.append(s * env)
    return 0.9 * fade(np.concatenate(out))


def hit():
    # a short burst of noise, softened a little
    rng = np.random.default_rng(7)
    x = t(0.075)
    n = rng.uniform(-1, 1, len(x))
    n = np.convolve(n, np.ones(3) / 3, mode='same')
    return 0.6 * fade(n * (1 - x / x[-1]), 1)


def crash():
    # a muffled crash: noise through a low-pass falling from 2500 to 500 Hz
    rng = np.random.default_rng(11)
    dur = 0.59
    n = int(dur * SR)
    x = np.arange(n) / n
    y = lowpass(rng.uniform(-1, 1, n), 2500 * (500 / 2500) ** x)
    y /= np.abs(y).max()
    y *= np.minimum(1, x * n / (0.02 * SR)) * (1 - x) ** 1.5
    return 0.37 * y / np.abs(y).max()


def ouch():
    # a small cartoon voice saying "ay": a glottal pulse train with some
    # jitter and breath, through three formants going from "a" to "i", with
    # pitch and formants raised together like a sped-up voice
    rng = np.random.default_rng(12)
    dur, scale = 0.22, 2.6
    n = int(dur * SR)
    x = np.arange(n) / n
    f0 = np.interp(x, [0, .5, 1], [1150, 1400, 950])
    f0 = f0 * (1 + 0.03 * np.sin(2 * np.pi * 28 * x * dur)
               + 0.01 * rng.standard_normal(n))
    ph = np.cumsum(f0) / SR % 1
    src = np.where(ph < 0.6, 0.5 - 0.5 * np.cos(np.pi * ph / 0.6),
                   np.cos(np.pi * (ph - 0.6) / 0.8))
    src = np.diff(src, prepend=0) * 20 + 0.15 * rng.uniform(-1, 1, n)
    a, i = (850, 1600, 2800), (320, 2300, 3000)
    out = np.zeros(n)
    for j, (gain, bw) in enumerate(((1.0, 110), (0.7, 140), (0.35, 200))):
        F = np.interp(x, [0, .5, 1], [a[j], a[j], i[j]]) * scale
        F = np.minimum(F, 0.45 * SR)
        out += gain * resonator(src, F, np.full(n, bw * scale))
    out *= np.minimum(1, x * dur / 0.02) * np.minimum(1, (1 - x) * dur / 0.06)
    return 0.30 * out / np.abs(out).max()


SOUNDS = [('ext1/brick.wav', brick), ('ext1/wall.wav', wall),
          ('ext3/shoot.wav', shoot), ('ext5/ouch.wav', ouch),
          ('ext6/crash.wav', crash), ('ext7/fire.wav', fire),
          ('ext7/hit.wav', hit)]


def write(path, x):
    data = np.clip(np.round(128 + 127 * x), 0, 255).astype(np.uint8)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == '__main__':
    top = sys.argv[1]
    for name, make in SOUNDS:
        path = os.path.join(top, 'bubbob', name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write(path, make())
        print(path)
