"""The transport layer between a game server and its clients.

A client is connected with two channels:

 * a reliable, ordered byte stream ("tcp"), for the messages;
 * an optional unreliable datagram channel ("udp"), for the frames.

The game logic (gamesrv.py on the server, pclient.py on the client) only
talks to a Transport and does not know what is underneath:

 * NativeTransport   regular TCP and UDP sockets, for the Python clients
                     (the X, Windows, pygame and GTK display drivers) and
                     the Java applet;
 * BrowserTransport  WebSockets for the stream and a WebRTC data channel
                     for the datagrams, for the HTML5 client.  It needs
                     extra packages and lives in html5server.py.

On the server, the datagrams of all the NativeTransport clients go
through one UdpEndpoint: the UDP socket on the port number of the game's
TCP socket.

Only the standard library is used here.
"""

import socket as _socket
from socket import error
from select import select
import errno
from errno import EWOULDBLOCK

# Errors of a datagram socket that concern one datagram or one peer, not
# the socket: the socket keeps working (ECONNRESET is how Windows reports
# an ICMP "port unreachable" for an earlier datagram, to any peer).
TRANSIENT_UDP_ERRORS = set(getattr(errno, name) for name in
                           ('EWOULDBLOCK', 'EAGAIN', 'ECONNRESET',
                            'ECONNREFUSED', 'EMSGSIZE', 'ETIMEDOUT')
                           if hasattr(errno, name))


class Transport:
    """What the game needs from the connection to one client."""

    kind = 'none'
    udp_kind = None             # None until the datagram channel is open

    # ---- the reliable stream ----

    def send_tcp(self, data):
        """Send as much of 'data' as possible without blocking.  Return
        the number of bytes taken.  Raise socket.error, with EWOULDBLOCK
        as first argument if nothing can be sent right now."""
        raise NotImplementedError

    def sendall_tcp(self, data):
        "Send all of 'data'."
        raise NotImplementedError

    def recv_tcp(self, bufsize):
        """Return the data that is available, at least one byte; or b''
        (then see at_eof())."""
        raise NotImplementedError

    def at_eof(self):
        "After recv_tcp() returned b'': was the connection closed?"
        return True

    def set_low_delay(self):
        "The stream is about to carry the frames too: reduce its latency."

    # ---- the datagrams ----

    def open_udp(self, host=None, port=None):
        """Open the datagram channel towards the client, which asked for
        it with CMSG_UDP_PORT.  Raise socket.error if that is not
        possible."""
        raise error("no datagram channel in a %s transport" % self.kind)

    def send_udp(self, data):
        """Send one datagram.  Return the number of bytes sent, 0 if it
        was dropped."""
        raise NotImplementedError

    def close_udp(self):
        pass

    # ---- the rest ----

    def fileno(self):
        "For select(): readable means that recv_tcp() will not block."
        raise NotImplementedError

    def getsockname(self):
        return ('', 0)

    def getpeername(self):
        return ('', 0)

    def close(self):
        pass

    def __repr__(self):
        return '<%s %s:%s>' % ((self.__class__.__name__,) +
                               tuple(self.getpeername()[:2]))


class NativeTransport(Transport):
    """Regular sockets: a connected TCP socket (or an object that looks
    like one, see metaserver/socketoverudp.py), and a UDP socket."""

    kind = 'tcp'

    def __init__(self, sock, blocking=False, endpoint=None):
        self.sock = sock
        self.udpsock = None
        self.udppeer = None     # for an unconnected UDP socket
        self.endpoint = endpoint    # server side: the game's UdpEndpoint
        if not blocking:
            sock.setblocking(0)

    # ---- the reliable stream ----

    def send_tcp(self, data):
        return self.sock.send(data)

    def sendall_tcp(self, data):
        self.sock.sendall(data)

    def recv_tcp(self, bufsize):
        return self.sock.recv(bufsize)

    def at_eof(self):
        if hasattr(self.sock, 'RECV_CAN_RETURN_EMPTY'):
            return False
        # safecheck that an empty recv() means disconnected
        iwtd, owtd, ewtd = select([self.sock], [], [], 0.0)
        return self.sock in iwtd

    def set_low_delay(self):
        for level, option, value, name in [
                ('SOL_IP',  'IP_TOS',      0x10, 'IPTOS_LOWDELAY'),
                ('SOL_TCP', 'TCP_NODELAY', 1,    'TCP_NODELAY')]:
            try:
                self.sock.setsockopt(getattr(_socket, level),
                                     getattr(_socket, option), value)
            except (error, AttributeError) as e:
                print("Cannot set %s:" % name, str(e))

    # ---- the datagrams ----

    def open_udp(self, host=None, port=None):
        """Server side: send the datagrams to the client's port, from
        the game's UdpEndpoint, or else from a UDP socket of our own."""
        self.close_udp()
        if hasattr(self.sock, 'udp_over_udp_mixer'):
            # for SocketOverUdp: the frames share its UDP socket
            self.udpsock = self.sock.udp_over_udp_mixer()
            self.udp_kind = 'udp-over-udp'
        elif self.endpoint is not None:
            self.udpsock = self.endpoint
            self.udppeer = (host or self.getpeername()[0], port)
            self.udp_kind = 'udp'
            return
        else:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            try:
                s.setblocking(0)
                s.connect((host or self.getpeername()[0], port))
            except error:
                s.close()
                raise
            self.udpsock = s
            self.udp_kind = 'udp'
        try:
            self.udpsock.setsockopt(_socket.SOL_IP, _socket.IP_TOS, 0x10)
        except (error, AttributeError) as e:
            print("Cannot set IPTOS_LOWDELAY:", str(e))

    def bind_udp(self, port=0, sock=None):
        """Client side: a UDP socket that receives the frames, either
        'sock' or a new one bound to 'port'.  send_udp() then sends to
        the server.  Return the address of the socket."""
        self.close_udp()
        if sock is None:
            sock = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            try:
                sock.bind(('', port))
            except error:
                sock.close()
                raise
        # non-blocking: select() may report a datagram that is gone when
        # recv_udp() comes (read by the meta-server's connection thread,
        # which shares 'sock', or an error report on Windows)
        sock.setblocking(0)
        self.udpsock = sock
        self.udppeer = self.getpeername()
        self.udp_kind = 'udp'
        return sock.getsockname()

    def send_udp(self, data):
        if self.udppeer is not None:
            return self.udpsock.sendto(data, self.udppeer)
        return self.udpsock.send(data)

    def recv_udp(self, bufsize):
        return self.udpsock.recv(bufsize)

    def close_udp(self):
        s = self.udpsock
        self.udpsock = None
        self.udppeer = None
        self.udp_kind = None
        if s is not None and s is not self.endpoint and hasattr(s, 'close'):
            try:
                s.close()
            except error:
                pass

    # ---- the rest ----

    def fileno(self):
        return self.sock.fileno()

    def getsockname(self):
        return self.sock.getsockname()

    def getpeername(self):
        return self.sock.getpeername()

    def close(self):
        self.close_udp()
        self.sock.close()

    def __getattr__(self, name):
        # the extras of the socket-like objects of the meta-server code
        # (udp_over_udp_mixer, udp_over_udp_decoder...)
        if name == 'sock':
            raise AttributeError(name)
        return getattr(self.sock, name)


class UdpEndpoint:
    """Server side: the game's UDP socket, on the port number of its
    TCP socket, where the clients send their first datagram to open the
    way through their NAT.  It sends the datagrams of all the clients,
    so that they come from there: a NAT may only let in what comes from
    where its client sent to.  It also receives what the clients send."""

    SNDBUF = 1 << 20            # the frames of all the clients

    def __init__(self, port):
        s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        try:
            s.bind(('', port))
        except error:
            s.close()
            raise
        s.setblocking(0)
        for level, option, value in [('SOL_SOCKET', 'SO_SNDBUF', self.SNDBUF),
                                     ('SOL_IP', 'IP_TOS', 0x10)]:
            try:
                s.setsockopt(getattr(_socket, level),
                             getattr(_socket, option), value)
            except (error, AttributeError):
                pass
        self.sock = s

    def sendto(self, data, addr):
        return self.sock.sendto(data, addr)

    def datagrams(self):
        """The (data, address) received so far, without blocking."""
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
            except error as e:
                if e.errno not in TRANSIENT_UDP_ERRORS:
                    raise
                if e.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                continue
            yield data, addr

    def fileno(self):
        return self.sock.fileno()

    def getsockname(self):
        return self.sock.getsockname()

    def close(self):
        self.sock.close()


class BroadcastTransport(Transport):
    """Datagrams only, to everybody on the local network: the frames
    for all the clients that asked for them with MSG_BROADCAST_PORT."""

    kind = 'broadcast'
    udp_kind = 'broadcast'

    def __init__(self, port):
        self.port = port
        self.udpsock = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        try:
            self.udpsock.setsockopt(_socket.SOL_SOCKET,
                                    _socket.SO_BROADCAST, 1)
        except error:
            self.udpsock.close()
            raise

    def send_udp(self, data):
        return self.udpsock.sendto(data, ('<broadcast>', self.port))

    def fileno(self):
        return self.udpsock.fileno()

    def getsockname(self):
        return ('', self.port)

    def close(self):
        self.udpsock.close()


def gettransport(conn, **kwds):
    """The Transport for a new connection: 'conn' itself if it is one
    already, else a NativeTransport around this socket."""
    if isinstance(conn, Transport):
        return conn
    return NativeTransport(conn, **kwds)
