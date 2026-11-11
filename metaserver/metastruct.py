import sys, os
LOCALDIR = __file__
LOCALDIR = os.path.abspath(os.path.dirname(LOCALDIR))
sys.path.insert(0, os.path.dirname(LOCALDIR))

from common.msgstruct import *
from socket import error

MMSG_INFO     = b'I'
MMSG_START    = b'+'
MMSG_STOP     = b'-'
MMSG_LIST     = b'L'
MMSG_ROUTE    = b'R'
MMSG_TRACEBACK= b'T'
MMSG_UDP_ADDR = b'U'

RMSG_WAKEUP   = b'w'
RMSG_PING     = b'p'
RMSG_PONG     = b'o'
RMSG_SYNC     = b'y'
RMSG_CONNECT  = b'c'
RMSG_LIST     = b'l'
RMSG_UDP_ADDR = b'u'
RMSG_UDP_CONN = b'd'
RMSG_NO_HOST  = b'?'


# A dict travels as one '#' message per item.  Keys are text; values are
# ints, text or binary data (e.g. a PNG icon).  Text is sent as UTF-8.
# The receiver cannot tell text from binary, so decodedict() returns str
# keys and leaves the values as bytes: the reader decodes what it shows.

def _tobytes(value):
    if isinstance(value, str):
        return value.encode('utf-8')
    return value

def encodedict(dict):
    data = []
    for key, value in list(dict.items()):
        data.append(message(b'#', _tobytes(key), _tobytes(value)))
    return b''.join(data)

def encodelist(list):
    return message(b'[', *[_tobytes(x) for x in list])

def decodedict(buffer):
    result = {}
    while 1:
        msg, buffer = decodemessage(buffer)
        if msg is None or len(msg) < 3 or msg[0] != b'#':
            break
        result[msg[1].decode('utf-8', 'replace')] = msg[2]
    return result

def decodelist(buffer):
    msg, buffer = decodemessage(buffer)
    assert msg[0] == b'['
    return list(msg[1:])

def totext(value):
    """Show a value from decodedict() as text."""
    if isinstance(value, bytes):
        return value.decode('utf-8', 'replace')
    return str(value)


class MessageSocket:
    
    def __init__(self, s):
        self.s = s
        self.buffer = b""

    def receive(self):
        try:
            data = self.s.recv(2048)
        except error:
            data = b''
        if not data:
            self.disconnect()
            return
        self.buffer += data
        while 1:
            msg, self.buffer = decodemessage(self.buffer)
            if msg is None:
                break
            if msg[0] not in self.MESSAGES:
                print('unknown message %r' % (msg[0],), file=sys.stderr)
            else:
                fn = self.MESSAGES[msg[0]]
                fn(self, *msg[1:])
