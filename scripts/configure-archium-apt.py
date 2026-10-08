#!/usr/bin/env python3
"""Bound package network waits on this repository's disposable Ubuntu runner."""
import os
from pathlib import Path
import re
import sys


def configure(apt):
    candidates = [apt / 'sources.list', apt / 'apt-mirrors.txt']
    candidates.extend((apt / 'sources.list.d').glob('*.list'))
    candidates.extend((apt / 'sources.list.d').glob('*.sources'))
    for path in candidates:
        if not path.is_file():
            continue
        original = path.read_text()
        updated = re.sub(
            r'https?://azure\.archive\.ubuntu\.com/ubuntu(?=[/\s]|$)',
            'https://archive.ubuntu.com/ubuntu', original)
        updated = re.sub(
            r'http://(archive|security)\.ubuntu\.com/ubuntu(?=[/\s]|$)',
            r'https://\1.ubuntu.com/ubuntu', updated)
        if updated != original:
            path.write_text(updated)
            print(f'Configured official Ubuntu HTTPS source: {path}', flush=True)
    (apt / 'apt.conf.d/99archium-network').write_text(
        'Acquire::http::Timeout "30";\n'
        'Acquire::https::Timeout "30";\n'
        'Acquire::Retries "3";\n'
        'APT::Update::Error-Mode "any";\n')


if __name__ == '__main__':
    if (os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('GITHUB_REPOSITORY') != 'Jorgeprdz/chromium-dex-arc'):
        print('Refusing configuration outside the dedicated GitHub Actions repository.',
              file=sys.stderr)
        sys.exit(2)
    configure(Path('/etc/apt'))
