"""What the client accepts from a game server: file names, sizes,
compressed data, images and icon rectangles."""

import os
import shutil
import sys
import tempfile
import unittest
import zlib
from hashlib import md5

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path[:0] = [ROOT, os.path.join(ROOT, 'display')]

import caching
from common.pixmap import decodepixmap, encodepixmap, cliprect, MAX_SIDE


class FileNames(unittest.TestCase):

    def test_game_data_paths(self):
        self.assertEqual(caching.data_path('bubbob/images/dragon_0.ppm'),
                         ['bubbob', 'images', 'dragon_0.ppm'])

    def test_other_paths_are_refused(self):
        for name in ('bubbob/../../.ssh/id_rsa', '../bubbob/x', '/etc/passwd',
                     'http2/config.txt', 'bubbob//x', 'bubbob/./x',
                     'bubbob/a\\b', 'bubbob/c:x', 'bubbob/a\0b', ''):
            self.assertIsNone(caching.data_path(name), name)

    def test_server_cannot_check_files_outside_game_data(self):
        # what the MD5 answer would tell a server: is this file there?
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        os.makedirs(os.path.join(root, 'bubbob'))
        secret = b'private key'
        with open(os.path.join(root, 'secret'), 'wb') as f:
            f.write(secret)
        with open(os.path.join(root, 'bubbob', 'data'), 'wb') as f:
            f.write(secret)

        class Chunk(caching.Data):
            SOURCEDIR = root
            CACHEDIR = os.path.join(root, 'cache')

        def found(name):
            return Chunk().loadfrom(name, 0, len(secret), md5(secret).digest())
        self.assertTrue(found('bubbob/data'))
        self.assertFalse(found('bubbob/../secret'))


class Sizes(unittest.TestCase):

    def test_range(self):
        self.assertTrue(caching.valid_range(0, 1000))
        self.assertFalse(caching.valid_range(-1, 10))
        self.assertFalse(caching.valid_range(0, -10))
        self.assertFalse(caching.valid_range(caching.MAX_FILE_SIZE, 1))

    def test_inflate(self):
        self.assertEqual(caching.inflate(zlib.compress(b'abc' * 100)),
                         b'abc' * 100)
        bomb = zlib.compress(b'\0' * (caching.MAX_INFLATED + 1))
        self.assertRaises(ValueError, caching.inflate, bomb)

    def test_stream_inflater(self):
        co = zlib.compressobj()
        d = caching.stream_inflater()
        frame = co.compress(b'f' * 1000) + co.flush(zlib.Z_SYNC_FLUSH)
        self.assertEqual(d(frame), b'f' * 1000)
        big = co.compress(b'\0' * (caching.MAX_FRAME + 1)) + \
            co.flush(zlib.Z_SYNC_FLUSH)
        self.assertRaises(zlib.error, d, big)


class Images(unittest.TestCase):

    def test_good_image(self):
        w, h, data = decodepixmap(encodepixmap(2, 3, b'\1' * 18))
        self.assertEqual((w, h, len(data)), (2, 3, 18))

    def test_bad_images(self):
        for header, data in ((b'P6\n0 5\n255\n', b''),
                             (b'P6\n%d 1\n255\n' % (MAX_SIDE + 1), b'\0' * 3),
                             (b'P6\n10 10\n255\n', b'\0' * 299),     # too short
                             (b'P5\n1 1\n255\n', b'\0'),
                             (b'P6\n1 1\n65535\n', b'\0' * 6)):
            self.assertRaises(ValueError, decodepixmap, header + data)

    def test_icon_rectangles_stay_inside_their_image(self):
        self.assertEqual(cliprect((2, 3, 4, 5), (32, 32)), (2, 3, 4, 5))
        self.assertEqual(cliprect((30, 30, 10, 10), (32, 32)), (30, 30, 2, 2))
        self.assertEqual(cliprect((-5, 0, 10, 4), (32, 32)), (0, 0, 5, 4))
        self.assertEqual(cliprect((100, 100, 10, 10), (32, 32))[2:], (0, 0))


if __name__ == '__main__':
    unittest.main()
