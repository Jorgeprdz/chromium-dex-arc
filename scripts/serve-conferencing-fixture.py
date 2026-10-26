#!/usr/bin/env python3
"""Local secure-context fixture. ADB reverse tcp:8769 tcp:8769, then open localhost:8769.

No camera/capture starts on load; requests require explicit buttons and native consent.
"""
import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'tests/fixtures/conferencing'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Accept-CH', 'Sec-CH-UA-Platform-Version, Sec-CH-UA-Arch, Sec-CH-UA-Bitness, Sec-CH-UA-Full-Version-List')
        super().end_headers()
    def do_GET(self):
        if self.path == '/headers':
            body = json.dumps({k:v for k,v in self.headers.items() if k.lower()=='user-agent' or k.lower().startswith('sec-ch-ua')}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        else:
            super().do_GET()
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--port', type=int, default=8769);args=parser.parse_args()
    ThreadingHTTPServer(('127.0.0.1',args.port), Handler).serve_forever()
