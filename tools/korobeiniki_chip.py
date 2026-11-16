#!/usr/bin/env python3
"""Render a short 8-bit style loop of Korobeiniki, the Russian folk song
(public domain), for the Tetris subgame (bubbob/ext4/music.wav).

Only the folk melody is used; the bass line and drums are written here.
Two pulse waves (melody, and a softer echo a sixth below), a triangle bass and
noise percussion, like the sound chips of 1980s consoles.  The output is
generated entirely by this script, so it can be rebuilt from source.

usage: korobeiniki_chip.py OUT.wav [BPM]

bubbob/ext4/music.wav is: tools/korobeiniki_chip.py bubbob/ext4/music.wav 150
"""
import sys, wave
import numpy as np

SR = 44100
BPM = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
BEAT = 60.0 / BPM

def hz(n):
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    k = names[n[0]] + (1 if '#' in n else 0)
    octave = int(n[-1])
    return 440.0 * 2 ** ((k + 12 * (octave + 1) - 69) / 12)

# the folk melody, A minor: (note or None for a rest, length in beats)
MELODY = [
    ('E5', 1), ('B4', .5), ('C5', .5), ('D5', 1), ('C5', .5), ('B4', .5),
    ('A4', 1), ('A4', .5), ('C5', .5), ('E5', 1), ('D5', .5), ('C5', .5),
    ('B4', 1.5), ('C5', .5), ('D5', 1), ('E5', 1),
    ('C5', 1), ('A4', 1), ('A4', 2),
    (None, .5), ('D5', 1), ('F5', .5), ('A5', 1), ('G5', .5), ('F5', .5),
    ('E5', 1.5), ('C5', .5), ('E5', 1), ('D5', .5), ('C5', .5),
    ('B4', 1), ('B4', .5), ('C5', .5), ('D5', 1), ('E5', 1),
    ('C5', 1), ('A4', 1), ('A4', 1), (None, 1),
]
# one chord root per bar; the bass plays root and fifth in eighths
ROOTS = ['A2', 'A2', 'E2', 'A2', 'D2', 'A2', 'E2', 'A2']

BARS = 8
N = int(round(BARS * 4 * BEAT * SR))
t_all = np.arange(N) / SR

def pulse(f, n, duty):
    ph = (np.arange(n) * f / SR) % 1.0
    return np.where(ph < duty, 1.0, -1.0)

def triangle(f, n):
    ph = (np.arange(n) * f / SR) % 1.0
    return 4 * np.abs(ph - 0.5) - 1

def env(n, attack=0.004, release=0.03, gate=0.85):
    e = np.ones(n)
    a = int(attack * SR); r = int(release * SR); g = int(n * gate)
    e[:a] = np.linspace(0, 1, a)
    e[g:] = 0
    e[max(0, g - r):g] *= np.linspace(1, 0, g - max(0, g - r))
    return e

def place(buf, start, sig):
    s = int(round(start * SR))
    buf[s:s + len(sig)] += sig[:max(0, N - s)]

lead = np.zeros(N); echo = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)

t = 0.0
for note, beats in MELODY:
    n = int(round(beats * BEAT * SR))
    if note:
        f = hz(note)
        place(lead, t, pulse(f, n, 0.5) * env(n))
        # a softer echo a sixth below, one eighth later, 25% duty
        place(echo, t + BEAT / 2, pulse(f * 2 ** (-9 / 12), n, 0.25) * env(n) * 0.5)
    t += beats * BEAT

for bar, root in enumerate(ROOTS):
    for k in range(8):
        f = hz(root) * (1.5 if k % 2 else 1.0)
        n = int(BEAT / 2 * SR)
        place(bass, (bar * 4 + k / 2) * BEAT, triangle(f, n) * env(n, gate=0.9))

rng = np.random.default_rng(1)
def noise_hit(length, decay, lowpass):
    n = int(length * SR)
    x = rng.uniform(-1, 1, n)
    if lowpass:
        x = np.convolve(x, np.ones(lowpass) / lowpass, mode='same')
    return x * np.exp(-np.arange(n) / (decay * SR))

for beat in range(BARS * 4):
    if beat % 2 == 0:
        place(drums, beat * BEAT, noise_hit(0.12, 0.03, 24) * 1.6)   # kick
    else:
        place(drums, beat * BEAT, noise_hit(0.15, 0.05, 3) * 0.8)    # snare
    for h in (0, 0.5):
        place(drums, (beat + h) * BEAT, noise_hit(0.04, 0.008, 0) * 0.25)  # hat

mix = 0.30 * lead + 0.30 * echo + 0.35 * bass + 0.25 * drums
# mean level -24.7 dBFS, the level of the loop it replaces
mix *= 10 ** (-24.7 / 20) / np.sqrt((mix ** 2).mean())
mix = np.clip(mix, -1, 1)
out = np.clip(np.round(mix * 127 + 128), 0, 255).astype(np.uint8)  # u8 mono, like the original
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(1); w.setframerate(SR)
    w.writeframes(out.tobytes())
print('%s: %.2f s at %g BPM' % (sys.argv[1], N / SR, BPM))
