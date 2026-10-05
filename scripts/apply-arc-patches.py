#!/usr/bin/env python3
"""Apply Archium changes to the pinned Chromium revision after complete preflight."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REVISION = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'
ROOT = Path(__file__).resolve().parents[1]


def git(checkout, *arguments):
    return subprocess.check_output(['git', '-C', str(checkout), *arguments],
                                   text=True, stderr=subprocess.STDOUT).strip()


def apply_to_checkout(checkout, patch_file, originals, expected_revision, *, check_only=False):
    checkout = Path(checkout).resolve()
    if Path(git(checkout, 'rev-parse', '--show-toplevel')).resolve() != checkout:
        raise ValueError('path must be the Chromium src checkout root')
    if git(checkout, 'rev-parse', 'HEAD') != expected_revision:
        raise ValueError('unsupported revision: expected ' + expected_revision)
    for name, original_hash in originals.items():
        relative = Path(name)
        path = checkout / relative
        if relative.is_absolute() or '..' in relative.parts or path.is_symlink() \
                or not path.resolve().is_relative_to(checkout):
            raise ValueError('unsafe path: ' + name)
        # Refuse symlink parents even when they resolve inside the checkout.
        if any((checkout / Path(*relative.parts[:i])).is_symlink()
               for i in range(1, len(relative.parts))):
            raise ValueError('symlink path: ' + name)
        if original_hash is None:
            if path.exists():
                raise ValueError('new file already exists: ' + name)
        elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != original_hash:
            raise ValueError('source differs from pinned revision: ' + name)
    # git apply validates the whole diff before writing; one conflicting hunk aborts all changes.
    git(checkout, 'apply', '--check', str(Path(patch_file).resolve()))
    if not check_only:
        git(checkout, 'apply', str(Path(patch_file).resolve()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--check', action='store_true', help='Validate without writing')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'patches/upstream-files.json').read_text())
    if manifest['revision'] != REVISION:
        raise ValueError('patch manifest revision does not match the pinned revision')
    apply_to_checkout(args.checkout, ROOT / 'patches/archium-desktop.patch',
                      manifest['originals'], REVISION, check_only=args.check)
    print('Archium patch compatible' if args.check else 'Archium patch applied')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
