#!/usr/bin/env python3
"""Fetch only Window Core from Chromium's exact AndroidX CIPD instance for local tests."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INSTANCE = 'sT3etXgwHmMgIIfG-lkBJlswQu9zgE_XvfXj_HaO-VsC'
URL = 'https://chrome-infra-packages.appspot.com/dl/chromium/third_party/androidx/+/' + INSTANCE
AAR_SHA256 = '8a99549bdc3e91eed60a63d714de659de6f46853eda2617c54fe174b91fb2210'
JAR_SHA256 = '7b66a18e30af7e4e8c7247d1785333c1ae8568938e288b8f52e77ab65bda7ee7'


class RemoteZip(io.RawIOBase):
    def __init__(self, size): self.pos, self.size = 0, size
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos
    def read(self, count=-1):
        count = self.size - self.pos if count < 0 else min(count, self.size - self.pos)
        if count <= 0: return b''
        start, end = self.pos, self.pos + count - 1
        request = urllib.request.Request(URL, headers={'Range': f'bytes={start}-{end}'})
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.headers.get('content-range') != f'bytes {start}-{end}/{self.size}':
                raise ValueError('Unexpected CIPD archive range')
            data = response.read()
        if len(data) != count: raise ValueError('Truncated CIPD archive')
        self.pos += count
        return data


def ensure_jar():
    destination = ROOT / '.sync-audit/androidx-window-core.jar'
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == JAR_SHA256:
        return destination
    request = urllib.request.Request(URL, headers={'Range': 'bytes=0-0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        header = response.headers.get('content-range', '')
        if not header.startswith('bytes 0-0/'): raise ValueError('Missing CIPD archive length')
        size = int(header.rsplit('/', 1)[1])
    with zipfile.ZipFile(RemoteZip(size)) as archive:
        aar = archive.read('libs/androidx_window_window_core_android/window-core-android.aar')
    if hashlib.sha256(aar).hexdigest() != AAR_SHA256:
        raise ValueError('Pinned Window Core AAR checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(aar)) as archive:
        jar = archive.read('classes.jar')
    if hashlib.sha256(jar).hexdigest() != JAR_SHA256:
        raise ValueError('Pinned Window Core JAR checksum mismatch')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(jar)
    return destination


if __name__ == '__main__':
    print('Verified pinned Window Core:', ensure_jar())
