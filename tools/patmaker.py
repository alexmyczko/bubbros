#!/usr/bin/env python3
"""patmaker.py - build Bub & Bros wall/border pattern sheets from 24-bit BMPs.

usage: patmaker.py [--transparent] INPUT_DIR [OUTPUT_DIR]   (OUTPUT_DIR defaults to "out")

By default 0x010101 pixels (the transparent colorkey) are turned into 0x000000
so they don't punch accidental holes; --transparent keeps them as-is.

16x16 BMPs -> walls   (24x24 with right-bottom shadow), 10 per sheet: wNNNN.ppm
32x32 BMPs -> borders (40x32 with right shadow),         8 per sheet: bNNNN.ppm
"""
import argparse, os, struct, sys

KEYCOL = (1, 1, 1)  # 0x010101, transparent colorkey
WALLS_PER_SHEET = 10
BORDERS_PER_SHEET = 8


def load_bmp24(path):
    """Return image as list of rows of (r, g, b), or None if not a 24-bit BMP."""
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) < 30 or data[:2] != b'BM':
        return None
    offset = struct.unpack_from('<I', data, 10)[0]
    hdrsize = struct.unpack_from('<I', data, 14)[0]
    if hdrsize == 12:  # BITMAPCOREHEADER
        w, h, planes, bpp = struct.unpack_from('<HHHH', data, 18)
        compression = 0
    elif hdrsize >= 40:
        w, h, planes, bpp, compression = struct.unpack_from('<iiHHI', data, 18)
    else:
        return None
    if bpp != 24 or compression != 0 or w <= 0 or h == 0:
        return None
    topdown = h < 0
    h = abs(h)
    stride = (w * 3 + 3) & ~3
    if offset + stride * (h - 1) + w * 3 > len(data):
        return None
    img = []
    for y in range(h):
        p = offset + stride * y
        row = data[p:p + w * 3]
        img.append([(row[i + 2], row[i + 1], row[i]) for i in range(0, w * 3, 3)])
    if not topdown:
        img.reverse()
    return img


def meancolor(img):
    r1 = g1 = b1 = 0
    count = float(len(img) * len(img[0]))
    for line in img:
        for r, g, b in line:
            r1 += r
            g1 += g
            b1 += b
    return r1 / count, g1 / count, b1 / count


# addshadow / addrshadow: same as bubbob/binboards.py
def addshadow(img, color, depth=8):
    r1, g1, b1 = color
    w = len(img[0])
    h = len(img)
    pad = depth * [KEYCOL]
    result = [line + pad for line in img] + [
        (w + depth) * [KEYCOL] for d in range(depth)]
    for d in range(depth):
        f = 1.0 - float(d) / depth
        c = (r1 * f, g1 * f, b1 * f)
        for i in range(w):
            result[h + d][1 + d + i] = c
        for i in range(h):
            result[d + i][w + d] = c
    return result


def addrshadow(img, color, depth=8):
    r1, g1, b1 = color
    w = len(img[0])
    h = len(img)
    pad = depth * [KEYCOL]
    result = [line + pad for line in img]
    for d in range(depth):
        f = 1.0 - float(d) / depth
        c = (r1 * f, g1 * f, b1 * f)
        for i in range(h):
            result[i][w + d] = c
    return result


def save_sheet(sprites, path):
    w = len(sprites[0][0])
    rows = [line for spr in sprites for line in spr]
    body = b''.join(bytes((int(r), int(g), int(b))) for line in rows for r, g, b in line)
    with open(path, 'wb') as f:
        f.write(b'P6\n%d %d\n255\n' % (w, len(rows)) + body)
    print("saved '%s'" % os.path.basename(path))


def main():
    ap = argparse.ArgumentParser(
        description='Build Bub & Bros wall/border pattern sheets from 24-bit BMPs.')
    ap.add_argument('indir', metavar='INPUT_DIR')
    ap.add_argument('outdir', metavar='OUTPUT_DIR', nargs='?', default='out',
                    help='default: out')
    ap.add_argument('--transparent', action='store_true',
                    help='keep 0x010101 pixels as transparent (default: turn them into 0x000000)')
    args = ap.parse_args()
    indir, outdir = args.indir, args.outdir
    if not os.path.isdir(indir):
        sys.exit('Input directory not found: %s' % indir)

    names = sorted(n for n in os.listdir(indir)
                   if n.lower().endswith('.bmp') and os.path.isfile(os.path.join(indir, n)))

    walls, borders = [], []
    nwalls = nborders = 0
    wsheet = bsheet = 0
    found = False

    for name in names:
        try:
            img = load_bmp24(os.path.join(indir, name))
        except OSError as e:
            print("skipping '%s' (%s)" % (name, e.strerror))
            continue
        if img is None:
            print("skipping '%s' (not a 24-bit bitmap file)" % name)
            continue
        h, w = len(img), len(img[0])
        if (w, h) not in ((32, 32), (16, 16)):
            print("skipping '%s' (invalid size %dx%d, must be 32x32 or 16x16)" % (name, w, h))
            continue
        if not found:
            os.makedirs(outdir, exist_ok=True)
            found = True

        if not args.transparent:
            img = [[(0, 0, 0) if px == KEYCOL else px for px in line] for line in img]

        if w == 32:
            print("processing '%s' (border) ..." % name)
            borders.append(addrshadow(img, meancolor(img)))
            nborders += 1
            if len(borders) == BORDERS_PER_SHEET:
                save_sheet(borders, os.path.join(outdir, 'b%04d.ppm' % bsheet))
                bsheet += 1
                borders = []
        else:
            print("processing '%s' (wall) ..." % name)
            walls.append(addshadow(img, meancolor(img)))
            nwalls += 1
            if len(walls) == WALLS_PER_SHEET:
                save_sheet(walls, os.path.join(outdir, 'w%04d.ppm' % wsheet))
                wsheet += 1
                walls = []

    if not found:
        sys.exit('No bitmaps found in the input directory.')

    if walls:
        save_sheet(walls, os.path.join(outdir, 'w%04d.ppm' % wsheet))
        wsheet += 1
    if borders:
        save_sheet(borders, os.path.join(outdir, 'b%04d.ppm' % bsheet))
        bsheet += 1

    print("processed %d borders and %d walls into %d border-sheets and %d wall-sheets"
          % (nborders, nwalls, bsheet, wsheet))


if __name__ == '__main__':
    main()
