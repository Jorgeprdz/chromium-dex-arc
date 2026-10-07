#!/usr/bin/env python3
"""Serve owned media fixtures on localhost with single HTTP byte-range support."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import shutil


class MediaHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      '.m3u8': 'application/vnd.apple.mpegurl', '.ts': 'video/mp2t',
                      '.m4a': 'audio/mp4', '.mp4': 'video/mp4', '.webm': 'video/webm'}

    def send_head(self):
        self.remaining = None
        path = Path(self.translate_path(self.path))
        if not path.resolve().is_relative_to(Path(self.directory).resolve()):
            self.send_error(403)
            return None
        if path.is_dir() or 'Range' not in self.headers:
            return super().send_head()
        try:
            source = path.open('rb')
        except OSError:
            self.send_error(404)
            return None
        length = path.stat().st_size
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', self.headers['Range'])
        first = last = None
        if match and any(match.groups()):
            if match[1]:
                first = int(match[1]); last = min(int(match[2]), length - 1) if match[2] else length - 1
            elif int(match[2]) > 0:
                first = max(0, length - int(match[2])); last = length - 1
        if first is None or not 0 <= first <= last < length:
            source.close()
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{length}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        self.remaining = last - first + 1
        source.seek(first)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Length', str(self.remaining))
        self.send_header('Content-Range', f'bytes {first}-{last}/{length}')
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        return source

    def copyfile(self, source, outputfile):
        if self.remaining is None:
            return shutil.copyfileobj(source, outputfile)
        while self.remaining > 0:
            data = source.read(min(self.remaining, 65536))
            if not data:
                break
            outputfile.write(data)
            self.remaining -= len(data)


def handler_for(directory):
    return partial(MediaHandler, directory=str(directory.resolve()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--directory', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'tests/runtime/media')
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(args.directory)) as server:
        print(f'Media fixtures: http://127.0.0.1:{server.server_port}/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
