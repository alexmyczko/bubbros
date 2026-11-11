import sys, os
from io import StringIO, BytesIO
import httpserver

PLAYERNAMES = ['Bub', 'Bob', 'Boob', 'Beb',
               'Biob', 'Bab', 'Bib',
               'Baub', 'Beab', 'Biab']
LOCALDIR = os.path.abspath(os.path.dirname(__file__))
DATADIR  = os.path.join(LOCALDIR, os.pardir, 'http2', 'data')

EMPTY_PAGE = '''<html>
<head><title>No server is running</title></head>
<body><h1>No server is running at the moment.</h1>
</body>
</html>
'''

INDEX_PAGE = '''<html>
<head><title>%(title)s</title></head>
<body><h1>%(title)s</h1>
 <applet code=pclient.class width=%(width)s height=%(height)s>
  <param name="gameport" value="%(gameport)d">
  %(names1)s
 </applet>
<br>
<p align="center"><a href="name.html?%(names2)s">Player Names &amp; Teams</a></p>
</body>
</html>
'''

NAME_LINE1 = '<param name="%s" value="%s">'
NAME_SEP1  = '\n'
NAME_LINE2 = '%s=%s'
NAME_SEP2  = '&'

def playernames(options):
    NUM_PLAYERS = len(PLAYERNAMES)
    result = {}
    anyname = None
    for id in range(NUM_PLAYERS):
        keyid = 'player%d' % id
        if keyid in options:
            value = options[keyid][0]
            anyname = anyname or value
            teamid = 'team%d' % id
            if teamid in options:
                team = options[teamid][0]
                if len(team) == 1:
                    value = '%s (%s)' % (value, team)
            result[keyid] = value
    if 'c' in options:
        for id in range(NUM_PLAYERS):
            keyid = 'player%d' % id
            try:
                del result[keyid]
            except KeyError:
                pass
    if 'f' in options:
        for id in range(NUM_PLAYERS):
            keyid = 'player%d' % id
            if not result.get(keyid):
                result[keyid] = anyname or PLAYERNAMES[id]
            else:
                anyname = result[keyid]
    return result

def indexloader(**options):
    if 'cheat' in options:
        for opt in options.pop('cheat'):
            __cheat(opt)
    import gamesrv
    if gamesrv.game is None:
        indexdata = EMPTY_PAGE
    else:
        names = list(playernames(options).items())
        indexdata = INDEX_PAGE % {
            'title':    gamesrv.game.FnDesc,
            'width':    gamesrv.game.width,
            'height':   gamesrv.game.height,
            'gameport': gamesrv.game.address[1],
            'names1':   NAME_SEP1.join([NAME_LINE1 % kv for kv in names]),
            'names2':   NAME_SEP2.join([NAME_LINE2 % kv for kv in names]),
            }
    return StringIO(indexdata), 'text/html'

def nameloader(**options):
    if 's' in options:
        return indexloader(**options)
    locals = {
        'options': playernames(options),
        }
    return httpserver.load(os.path.join(DATADIR, 'name.html'),
                           'text/html', locals=locals)


wave_cache = {}

# The audioop module was removed in Python 3.13.  These three functions
# do what audioop.bias(), ratecv() and lin2ulaw() did, for 8-bit mono
# samples only, following the C code of CPython's audioop module.

def _signed8(data):
    # audioop.bias(data, 1, -128): unsigned 8-bit samples (128 = silence)
    # to signed ones
    return [b - 128 for b in data]

def _ratecv8(samples, inrate, outrate):
    # audioop.ratecv(data, 1, 1, inrate, outrate, None), on the values
    # as audioop stores them internally (sample << 24)
    import math
    g = math.gcd(inrate, outrate)
    inrate //= g
    outrate //= g
    d = -outrate
    prev = cur = 0
    out = []
    it = iter(samples)
    while True:
        while d < 0:
            try:
                s = next(it)
            except StopIteration:
                return out
            prev = cur
            cur = s << 24
            d += outrate
        while d >= 0:
            out.append(int((prev * d + cur * (outrate - d)) / outrate) >> 24)
            d -= inrate

_SEG_UEND = (0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF, 0x1FFF)

def _ulaw(sample):
    # audioop.lin2ulaw(data, 1) for one signed 8-bit sample
    pcm = (sample << 24) >> 18           # 14-bit linear value
    if pcm < 0:
        pcm, mask = -pcm, 0x7F
    else:
        mask = 0xFF
    pcm = min(pcm, 8159) + (0x84 >> 2)
    for seg, end in enumerate(_SEG_UEND):
        if pcm <= end:
            return ((seg << 4) | ((pcm >> (seg + 1)) & 0xF)) ^ mask
    return 0x7F ^ mask

def wav2au(data):
    # Very limited! Assumes a standard 8-bit mono .wav as input
    import struct
    freq, = struct.unpack("<i", data[24:28])
    samples = _signed8(data[44:])
    samples = _ratecv8(samples, freq, 8000)
    data = bytes([_ulaw(s) for s in samples])
    data = struct.pack('>4siiiii8s',
                       b'.snd',                        # header
                       struct.calcsize('>4siiiii8s'),  # header size
                       len(data),                      # data size
                       1,                              # encoding
                       8000,                           # sample rate
                       1,                              # channels
                       b'magic.au') + data
    return data

def sampleloader(code=[], **options):
    import gamesrv
    try:
        data = wave_cache[code[0]]
    except KeyError:
        for key, snd in list(gamesrv.samples.items()):
            if str(getattr(snd, 'code', '')) == code[0]:
                data = wave_cache[code[0]] = wav2au(snd.read())
                break
        else:
            raise KeyError(code[0])
    return BytesIO(data), 'audio/wav'


def setup():
    dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       os.pardir,
                                       'java'))
    if not os.path.isdir(dir):
        return

    # register all '.class' files
    for name in os.listdir(dir):
        if name.endswith('.class'):
            httpserver.register(name, httpserver.fileloader(os.path.join(dir, name)))

    # register a '', an 'index.html', and a 'name.html' file
    httpserver.register('', indexloader)
    httpserver.register('index.html', indexloader)
    httpserver.register('name.html',  nameloader)

    # 'name.html' has a few images, list the .png files in DATADIR
    for fn in os.listdir(DATADIR):
        fn = fn.lower()
        if fn.endswith('.png'):
            httpserver.register(fn, httpserver.fileloader(
                os.path.join(DATADIR, fn)))

    # register the sample loader
    httpserver.register('sample.wav', sampleloader)

setup()
