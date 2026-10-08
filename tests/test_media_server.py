import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]


class MediaByteRangeTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'scripts/serve-media-tests.py'
        self.assertTrue(path.is_file(), 'Range-capable media fixture server is not implemented')
        spec = importlib.util.spec_from_file_location('media_server', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        (Path(self.tmp.name) / 'clip.mp4').write_bytes(b'0123456789')
        handler = module.handler_for(Path(self.tmp.name))
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.close)
        self.url = f'http://127.0.0.1:{self.server.server_port}/clip.mp4'

    def close(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def request(self, value=None, method='GET'):
        headers = {'Range': value} if value else {}
        return urllib.request.urlopen(urllib.request.Request(self.url, headers=headers, method=method), timeout=3)

    def test_normal_download_preserves_bytes_and_mime(self):
        with self.request() as r:
            self.assertEqual(r.status, 200); self.assertEqual(r.read(), b'0123456789')
            self.assertEqual(r.headers['Content-Type'], 'video/mp4')

    def test_bounded_range_returns_only_selected_bytes(self):
        with self.request('bytes=2-5') as r:
            self.assertEqual(r.status, 206); self.assertEqual(r.read(), b'2345')
            self.assertEqual(r.headers['Content-Range'], 'bytes 2-5/10')
            self.assertEqual(r.headers['Content-Length'], '4')

    def test_suffix_open_and_clamped_ranges(self):
        for requested, expected in [('bytes=-3', b'789'), ('bytes=7-', b'789'), ('bytes=7-99', b'789')]:
            with self.subTest(requested=requested), self.request(requested) as r:
                self.assertEqual(r.read(), expected); self.assertEqual(r.status, 206)

    def test_impossible_or_multiple_ranges_return_416(self):
        for value in ['bytes=20-', 'bytes=7-2', 'bytes=-0', 'bytes=0-2,5-7', 'bytes=-']:
            with self.subTest(value=value), self.assertRaises(HTTPError) as caught:
                self.request(value)
            self.assertEqual(caught.exception.code, 416)
            self.assertEqual(caught.exception.headers['Content-Range'], 'bytes */10')

    def test_head_range_has_no_body(self):
        with self.request('bytes=2-5', method='HEAD') as r:
            self.assertEqual(r.status, 206); self.assertEqual(r.read(), b'')
            self.assertEqual(r.headers['Content-Length'], '4')

    def test_symlink_cannot_expose_file_outside_fixture_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / 'private.txt'; outside.write_bytes(b'outside-fixture')
            (Path(self.tmp.name) / 'clip.mp4').unlink()
            (Path(self.tmp.name) / 'clip.mp4').symlink_to(outside)
            with self.assertRaises(HTTPError) as caught:
                self.request()
            self.assertEqual(caught.exception.code, 403)
