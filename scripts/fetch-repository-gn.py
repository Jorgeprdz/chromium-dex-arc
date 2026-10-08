#!/usr/bin/env python3
"""Fetch standalone GN for repository tests, without restoring a Chromium checkout."""
import argparse
import hashlib
import io
import os
from pathlib import Path
import platform
import tempfile
import urllib.request
import zipfile

# Chromium cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 DEPS gn_version.
REVISION = '3fef1f00031be0d3505e5338ca671ea3752e6fd8'
DIGESTS = {
    'amd64': 'c0dec98e11c4008b165a44bf407e06704710cf76e2af4aea22dd3b7102f0778e',
    'arm64': '1a8d35260a4b18e77fd698f7224091b7c08358df9aebd1532c4655033a6eb557',
}


def ensure_gn(cache: Path, machine: str) -> Path:
    arch = {'x86_64': 'amd64', 'aarch64': 'arm64'}.get(machine)
    if arch is None:
        raise ValueError(f'Unsupported GN host architecture: {machine}')
    destination = cache / f'gn-linux-{arch}'
    if destination.exists():
        data = destination.read_bytes()
    else:
        url = ('https://chrome-infra-packages.appspot.com/dl/gn/gn/linux-'
               + arch + '/+/git_revision:' + REVISION)
        with urllib.request.urlopen(url, timeout=30) as response:
            with zipfile.ZipFile(io.BytesIO(response.read())) as archive:
                data = archive.read('gn')
    if hashlib.sha256(data).hexdigest() != DIGESTS[arch]:
        raise ValueError(f'Pinned GN checksum mismatch: {destination}')
    if not destination.exists():
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=cache, delete=False) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)
        try:
            temporary_path.chmod(0o755)
            os.replace(temporary_path, destination)
        finally:
            temporary_path.unlink(missing_ok=True)
    return destination.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, required=True)
    args = parser.parse_args()
    print(ensure_gn(args.cache_dir, platform.machine()))


if __name__ == '__main__':
    main()
