from struct import pack, unpack, calcsize

try:
    from localmsg import PORTS
except ImportError:
    PORTS = {}
try:
    from localmsg import HOSTNAME
except ImportError:
    from socket import gethostname
    HOSTNAME = gethostname()


MSG_WELCOME = b"Welcome to gamesrv.py(3) !\n"
MSG_BROADCAST_PORT= b"*"
MSG_DEF_PLAYFIELD = b"p"
MSG_DEF_KEY       = b"k"
MSG_DEF_ICON      = b"r"
MSG_DEF_BITMAP    = b"m"
MSG_DEF_SAMPLE    = b"w"
MSG_DEF_MUSIC     = b"z"
MSG_PLAY_MUSIC    = b"Z"
MSG_FADEOUT       = b"f"
MSG_PLAYER_JOIN   = b"+"
MSG_PLAYER_KILL   = b"-"
MSG_PLAYER_ICON   = b"i"
MSG_PING          = b"g"
MSG_PONG          = b"G"
MSG_INLINE_FRAME  = b"\\"
MSG_PATCH_FILE    = MSG_DEF_MUSIC
MSG_ZPATCH_FILE   = b"P"
MSG_MD5_FILE      = b"M"
MSG_UDP_TOKEN     = b"u"   # port, token: send DMSG_TOKEN to this port
MSG_RECORDED      = b"\x00"

CMSG_PROTO_VERSION= b"v"   # 4: understands MSG_UDP_TOKEN
CMSG_KEY          = b"k"
CMSG_ADD_PLAYER   = b"+"
CMSG_REMOVE_PLAYER= b"-"
CMSG_UDP_PORT     = b"<"
CMSG_ENABLE_SOUND = b"s"
CMSG_ENABLE_MUSIC = b"m"
CMSG_PING         = b"g"
CMSG_PONG         = b"G"
CMSG_DATA_REQUEST = b"M"
CMSG_PLAYER_NAME  = b"n"

BROADCAST_MESSAGE = b"game!"   # less than 6 bytes

# Control datagrams, over UDP: b'.' followed by messages (message()),
# with their own type codes.  A bare b'.' only opens the sender's NAT
# (a client sends it if the server gave it no token).  Types and fields
# that a program does not know are ignored, as for the messages of the
# stream.  A server only sends them to a client of protocol 4 or later:
# an older one would take them for frames.
DMSG_TOKEN        = b"t"   # token: from the client, see MSG_UDP_TOKEN


def message(tp, *values):
    # Everything sent over the network is bytes: 'tp' is one of the
    # one-byte MSG_* or CMSG_* codes, and string values must be bytes too.
    typecodes = ['']
    for v in values:
        if isinstance(v, bytes):
            typecodes.append('%ds' % len(v))
        elif isinstance(v, str):
            raise TypeError("message() needs bytes, not str: %r" % (v,))
        elif 0 <= v < 256:
            typecodes.append('B')
        else:
            typecodes.append('l')
    typecodes = ''.join(typecodes).encode('ascii')
    assert len(typecodes) < 256
    return pack(("!B%dsc" % len(typecodes)) + typecodes.decode('ascii'),
                len(typecodes), typecodes, tp, *values)

def datagram(*messages):
    return b'.' + b''.join(messages)

def decodedatagram(data):
    """The messages of a control datagram, as far as they can be read
    (it may come from anybody)."""
    result = []
    data = data[1:]
    try:
        while data:
            values, data = decodemessage(data)
            if values is None:
                break
            result.append(values)
    except Exception:
        pass
    return result

def decodemessage(data):
    if data:
        limit = data[0] + 1      # indexing bytes gives an int
        if len(data) >= limit:
            typecodes = "!c" + data[1:limit].decode('ascii')
            end = limit + calcsize(typecodes)
            if len(data) >= end:
                return unpack(typecodes, data[limit:end]), data[end:]
            elif end > 1000000:
                raise OverflowError
    return None, data
