#!/usr/bin/env python3
"""makeloop.py SRC START END RATE TARGET_DB OUT.wav
Cut SRC from START to END seconds as a seamless loop: the 50 ms of audio
right after END are crossfaded into the start.  Mono, unsigned 8 bit at
RATE Hz (the format of the game's other loops), mean level TARGET_DB.

Copyright 2026 Juan Manuel Méndez Rey <juan.mendezr@proton.me>.
Released under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/"""
import sys, subprocess, wave, numpy as np
src, a, b, rate, target, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
X = 0.05
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', src, '-ss', str(a), '-t', str(b - a + X + 0.2),
                      '-ac', '1', '-ar', str(rate), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).astype(float)
L = int(round((b - a) * rate)); n = int(X * rate)
y = x[:L].copy()
fade = np.linspace(0, 1, n)
y[:n] = y[:n] * fade + x[L:L + n] * (1 - fade)
rms = 20 * np.log10(np.sqrt((y ** 2).mean()))
g = 10 ** ((target - rms) / 20)
if np.abs(y).max() * g > 0.98:
    g = 0.98 / np.abs(y).max()
y *= g
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(1); w.setframerate(rate)
    w.writeframes(np.clip(np.round(y * 127 + 128), 0, 255).astype(np.uint8).tobytes())
print('%s: %.2f s, mean %.1f dB, peak %.1f dB' % (out, L / rate, 20 * np.log10(np.sqrt((y ** 2).mean())), 20 * np.log10(np.abs(y).max())))
