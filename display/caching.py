
import os, zlib, sys
from hashlib import md5
#import common.debug


class FileCache:
    MAX_FILES = 8
    
    def __init__(self):
        self.cache = {}
        self.time = 0
    
    def access(self, filename, position, writing=0):
        if filename in self.cache:
            time, mode, f = self.cache[filename]
            if writing > mode:
                f.close()
                del self.cache[filename]
        if filename not in self.cache:
            if len(self.cache) >= FileCache.MAX_FILES:
                (time, mode, f), k = min([(v,k) for (k,v) in list(self.cache.items())])
                f.close()
                del self.cache[k]
            try:
                f = open(filename, ('rb', 'r+b')[writing])
            except (IOError, OSError):
                if not writing:
                    raise
                if not os.path.isdir(os.path.dirname(filename)):
                    os.mkdir(os.path.dirname(filename))
                f = open(filename, 'w+b')
            mode = writing
        self.time += 1
        self.cache[filename] = self.time, mode, f
        f.seek(position)
        return f


class MemoryBlock:
    def __init__(self, data):
        self.data = data
    def overwrite(self, newdata):
        self.data = newdata
    def read(self):
        return self.data

class FileBlock:
    def __init__(self, filename, position, length, readonly=1, complete=1):
        self.filename = filename
        self.position = position
        self.length = length
        self.readonly = readonly
        self.complete = complete
    def overwrite(self, newdata):
        self.memorydata = newdata
        if self.readonly:
            print("cannot overwrite file", self.filename, file=sys.stderr)
            return
        try:
            f = Data.Cache.access(self.filename, self.position, writing=1)
            f.write(newdata)
        except (IOError, OSError):
            print("cache write error:", self.filename, file=sys.stderr)
            return
        self.complete = 1
        del self.memorydata
    def read(self):
        if self.complete:
            f = Data.Cache.access(self.filename, self.position)
            return f.read(self.length)
        else:
            return self.memorydata


# What a game server may send.  It names files of its own game data,
# which the client may already have; it must not be able to make the
# client look at any other file, since the answer (whether the MD5 of a
# piece of it matches) lets it guess the contents.
DATA_DIRS = ('bubbob',)          # game.FnBasePath of the servers
MAX_FILE_SIZE = 64 * 1024 * 1024 # the largest file of the game is ~11 MB
MAX_INFLATED = 16 * 1024 * 1024  # one message, decompressed

def data_path(filename):
    """The components of 'filename' if it is a Unix-style relative path
    inside DATA_DIRS, else None."""
    parts = filename.split('/')
    if parts[0] not in DATA_DIRS:
        return None
    for p in parts:
        if p in ('', '.', '..') or '\\' in p or ':' in p or '\0' in p:
            return None
    return parts

def valid_range(position, length):
    return 0 <= position and 0 <= length and position + length <= MAX_FILE_SIZE

def inflate(data):
    """zlib.decompress() for data from a server, with a size limit."""
    d = zlib.decompressobj()
    result = d.decompress(data, MAX_INFLATED)
    if d.unconsumed_tail:
        raise ValueError("compressed data larger than %d bytes" % MAX_INFLATED)
    return result


MAX_FRAME = 1024 * 1024          # one frame of the game, decompressed

def stream_inflater():
    """Like zlib.decompressobj().decompress, for the frames a server
    sends as one zlib stream, with a size limit per call.  Too much data
    raises zlib.error, which the callers handle as a lost frame."""
    d = zlib.decompressobj()
    def inflate_frame(data):
        result = d.decompress(data, MAX_FRAME)
        if d.unconsumed_tail:
            raise zlib.error("frame larger than %d bytes" % MAX_FRAME)
        return result
    return inflate_frame


class Data:
    # characters kept as they are in cache file names; others become '_'
    SafeChars = ".abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    Cache = FileCache()

    def __init__(self):
        self.content = {}
        self.backupfile = None
        self.readonly = 0

    clear = __init__

    ### Public interface ###

    def store(self, position, data, filename=None, readonly=1):
        """This class assumes that all accesses to block within the data
        are done for disjoint intervals: no overlapping writes !"""
        if self.content is not None:
            try:
                self.content[position].overwrite(data)
            except KeyError:
                if filename is None:
                    self.content[position] = MemoryBlock(data)
                else:
                    self.content[position] = FileBlock(filename, position,
                                                       len(data), readonly)
        if self.backupfile and not self.readonly:
            try:
                f = Data.Cache.access(self.backupfile, position, writing=1)
                f.write(data)
                f.flush()
            except (IOError, OSError):
                print("cache write error:", self.backupfile, file=sys.stderr)

    def loadfrom(self, filename, position, length, checksum):
        """Try to load data from the given filename, with the given
        expected MD5 checksum.  The filename must be Unix-style, and is
        looked up both in the directory SOURCEDIR (only for game data,
        see data_path()) and with a mangled name in the cache directory
        CACHEDIR."""
        parts = data_path(filename)
        directname = parts and os.path.join(self.SOURCEDIR, *parts)
        mangledname = ''.join([c if c in Data.SafeChars else '_'
                               for c in filename])
        cachename = os.path.join(self.CACHEDIR, mangledname)
        for name, readonly in ((directname, 1), (cachename, 0)):
            if not name:
                continue
            try:
                f = Data.Cache.access(name, position)
                data = f.read(length)
            except (IOError, OSError):
                pass
            else:
                if len(data) == length and md5(data).digest() == checksum:
                    # correct data
                    self.store(position, data, name, readonly)
                    return 1
        if self.content is not None and position not in self.content:
            self.content[position] = FileBlock(cachename, position, length,
                                               readonly=0, complete=0)
        elif self.readonly:
            print("Note: the music data has changed. You can get", file=sys.stderr)
            print("the server's version by deleting", directname, file=sys.stderr)
            return 1   # incorrect data, but ignored
        return 0

    def read(self):
        """Return the data as built so far."""
        if self.content is not None:
            items = list(self.content.items())
            items.sort()
            result = b''
            for position, block in items:
                if len(result) < position:
                    result += b'\x00' * (position-len(result))
                data = block.read()
                result = result[:position] + data + result[position+len(data):]
            return result
        else:
            f = Data.Cache.access(self.backupfile, 0)
            return f.read()

    def fopen(self):
        if self.content is not None:
            from io import BytesIO
            return BytesIO(self.read())
        else:
            return Data.Cache.access(self.backupfile, 0)

    def freezefilename(self, fileexthint='.wav'):
        """Return the name of a file from which the data can be read. If all
        the current data comes from the same file, it is assumed to be exactly
        the file that we want."""
        if not self.backupfile:
            files = {}
            for position, block in list(self.content.items()):
                if not isinstance(block, FileBlock):
                    break
                if block.complete:
                    files[block.filename] = block
            else:
                if len(files) == 1:
                    self.backupfile, block = list(files.items())[0]
                    self.readonly = block.readonly
            if not self.backupfile:
                self.backupfile = mktemp(fileexthint)
                f = Data.Cache.access(self.backupfile, 0, writing=1)
                for position, block in list(self.content.items()):
                    f.seek(position)
                    f.write(block.read())
                f.flush()
            #print 'freezefilename ->', self.backupfile
            #print '                    readonly =', self.readonly
        self.content = None
        return self.backupfile

# ____________________________________________________________
# Temporary files management
# from the 'py' lib, mostly written by hpk

def try_remove_dir(udir):
    try:
        for name in os.listdir(udir):
            try:
                os.unlink(os.path.join(udir, name))
            except:
                pass
        os.rmdir(udir)
    except:
        pass

def make_numbered_dir(prefix='tmp-bub-n-bros-', rootdir=None, keep=0,
                      lock_timeout = 172800):   # two days
    """ return unique directory with a number greater than the current
        maximum one.  The number is assumed to start directly after prefix.
        Directories with a number less than (maxnum-keep) will be removed.
    """
    import atexit, tempfile
    if rootdir is None:
        rootdir = tempfile.gettempdir()

    def parse_num(bn):
        """ parse the number out of a path (if it matches the prefix) """
        if bn.startswith(prefix):
            try:
                return int(bn[len(prefix):])
            except ValueError:
                pass

    # compute the maximum number currently in use with the
    # prefix
    maxnum = -1
    for basename in os.listdir(rootdir):
        num = parse_num(basename)
        if num is not None:
            maxnum = max(maxnum, num)

    # make the new directory
    udir = os.path.join(rootdir, prefix + str(maxnum+1))
    os.mkdir(udir)

    # try to remove the directory at process exit
    atexit.register(try_remove_dir, udir)

    # prune old directories
    for basename in os.listdir(rootdir):
        num = parse_num(basename)
        if num is not None and num <= (maxnum - keep):
            d1 = os.path.join(rootdir, basename)
            try:
                t1 = os.stat(d1).st_mtime
                t2 = os.stat(udir).st_mtime
                if abs(t2-t1) < lock_timeout:
                    continue   # skip directories still recently used
            except:
                pass
            try_remove_dir(d1)
    return udir

def enumtempfiles():
    tempdir = make_numbered_dir()
    i = 0
    while True:
        yield os.path.join(tempdir, 'b%d' % i)
        i += 1

def mktemp(fileext, gen = enumtempfiles()):
    return next(gen) + fileext
