#!/usr/bin/env python3
"""Serve local synthetic login forms; discard POST bodies and never log values."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        route = self.path.split('?', 1)[0]
        files = {'/login': 'login.html', '/update': 'update.html', '/frame': 'frame.html'}
        if route == '/done':
            data = b'<!doctype html><meta charset="utf-8"><title>Done</title><h1>Synthetic login completed</h1>'
        elif route in files:
            data = (ROOT / files[route]).read_bytes()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != '/done':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            length = -1
        if not 0 <= length <= 8192:
            self.send_error(400)
            return
        self.rfile.read(length)  # Consume and discard. No parse, persistence or log.
        self.send_response(303)
        self.send_header('Location', '/done')
        self.send_header('Content-Length', '0')
        self.end_headers()


if __name__ == '__main__':
    servers = [ThreadingHTTPServer(('127.0.0.1', port), Handler) for port in (8765, 8766)]
    for server in servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    print('Synthetic fixtures listening on loopback ports 8765 and 8766; no request/body logs.', flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        for server in servers:
            server.shutdown()
            server.server_close()
