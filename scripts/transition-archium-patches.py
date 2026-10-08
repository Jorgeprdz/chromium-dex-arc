#!/usr/bin/env python3
"""Verify and replace only old/new patch inputs, retaining untouched Ninja timestamps."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile

REVISION = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'
ROOT = Path(__file__).resolve().parents[1]
RECEIPT = '.archium-transition.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(checkout, *args):
    return subprocess.check_output(['git', '-C', str(checkout), *args], stderr=subprocess.STDOUT)


def safe_path(root, name):
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or relative.as_posix() != name \
            or '\\' in name or any(p in ('.', '..', '.git') for p in relative.parts) \
            or name == RECEIPT:
        raise ValueError('Unsafe transition path: ' + name)
    target = root / name
    for length in range(1, len(relative.parts) + 1):
        part = root.joinpath(*relative.parts[:length])
        if part.is_symlink():
            raise ValueError('Symlink transition path: ' + name)
        if part.exists() and length < len(relative.parts) and not part.is_dir():
            raise ValueError('Invalid parent path: ' + name)
    if target.exists() and not target.is_file():
        raise ValueError('Not a regular input file: ' + name)
    return target


def validate_bundle(manifest, patch_file):
    if manifest.get('revision') != REVISION:
        raise ValueError('Unsupported transition revision')
    if digest(Path(patch_file).read_bytes()) != manifest.get('patch_sha256'):
        raise ValueError('Transition patch checksum mismatch')
    originals, modified = manifest.get('originals'), manifest.get('modified')
    if not isinstance(originals, dict) or not isinstance(modified, dict) \
            or not originals or originals.keys() != modified.keys():
        raise ValueError('Invalid transition manifest')
    for name in originals:
        if not isinstance(name, str): raise ValueError('Invalid manifest path')
        for value in (originals[name], modified[name]):
            if value is not None and not re.fullmatch('[0-9a-f]{64}', str(value)):
                raise ValueError('Invalid source checksum')
        if modified[name] is None: raise ValueError('Modified source checksum required')


def _atomic_write(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.archium-write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            os.fchmod(output.fileno(), mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def _write_file(path, data, mode):
    if data is None: path.unlink()
    else: _atomic_write(path, data, mode)


def reconstruct(root, manifest, patch_file, originals):
    root.mkdir()
    for name in manifest['originals']:
        data = originals[name]
        if data is not None:
            p = safe_path(root, name)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    git(root, 'init', '-q')
    try:
        git(root, 'apply', '--check', str(Path(patch_file).resolve()))
        git(root, 'apply', str(Path(patch_file).resolve()))
    except subprocess.CalledProcessError as error:
        raise ValueError('Patch does not apply to pinned originals') from error
    files = {p.relative_to(root).as_posix() for p in root.rglob('*')
             if p.is_file() and '.git' not in p.relative_to(root).parts}
    if files != set(manifest['modified']):
        raise ValueError('Patch changes paths outside its declared manifest')
    result = {}
    for name, sha in manifest['modified'].items():
        data = safe_path(root, name).read_bytes()
        if digest(data) != sha: raise ValueError('Patched content differs from manifest: ' + name)
        result[name] = data
    return result


def transition(checkout, old_manifest, new_manifest, old_patch, new_patch, original_sources=None,
               *, source_commit=None, implementation_commit=None):
    checkout = Path(checkout)
    if checkout.is_symlink(): raise ValueError('Checkout root must not be a symlink')
    checkout = checkout.resolve()
    if Path(git(checkout, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != checkout \
            or git(checkout, 'rev-parse', 'HEAD').decode().strip() != REVISION:
        raise ValueError('Transition requires exact pinned checkout root and revision')
    validate_bundle(old_manifest, old_patch)
    validate_bundle(new_manifest, new_patch)
    receipt_path = checkout / RECEIPT
    previous_receipt = None
    previous_receipt_info = None
    if receipt_path.is_symlink() or (receipt_path.exists() and not receipt_path.is_file()):
        raise ValueError('Transition receipt must be a regular file')
    if receipt_path.exists():
        previous_receipt_info = receipt_path.stat()
        previous_receipt = receipt_path.read_bytes()
        try:
            previous = json.loads(previous_receipt)
        except (ValueError, UnicodeDecodeError) as error:
            raise ValueError('Invalid previous transition receipt') from error
        # Checkpoints retain the receipt written by their producing implementation.
        # Authorize another transition only from that exact commit and patch;
        # every source byte is still checked below before any mutation.
        if not isinstance(previous, dict) or previous.get('schema') != 1 \
                or previous.get('revision') != REVISION \
                or not re.fullmatch('[0-9a-f]{40}', str(source_commit)) \
                or not re.fullmatch('[0-9a-f]{40}', str(implementation_commit)) \
                or not re.fullmatch('[0-9a-f]{40}', str(previous.get('source_commit'))) \
                or not re.fullmatch('[0-9a-f]{64}', str(previous.get('old_patch_sha256'))) \
                or previous.get('implementation_commit') != source_commit \
                or previous.get('new_patch_sha256') != old_manifest['patch_sha256']:
            raise ValueError('Previous transition receipt does not match source checkpoint identity')
    names = sorted(old_manifest['originals'].keys() | new_manifest['originals'].keys())
    originals = {}
    snapshots = {}
    for name in names:
        target = safe_path(checkout, name)
        hashes = [m['originals'][name] for m in (old_manifest, new_manifest)
                  if name in m['originals']]
        if len(hashes) == 2 and hashes[0] != hashes[1]:
            raise ValueError('Conflicting pinned original: ' + name)
        sha = hashes[0]
        if sha is None:
            originals[name] = None
        else:
            if original_sources is None:
                data = git(checkout, 'show', REVISION + ':' + name)
            else:
                data = safe_path(Path(original_sources), name).read_bytes()
            if digest(data) != sha: raise ValueError('Wrong pinned original: ' + name)
            originals[name] = data
        info = target.stat() if target.exists() else None
        before = target.read_bytes() if info else None
        expected = old_manifest['modified'].get(name, sha)
        if (digest(before) if before is not None else None) != expected:
            raise ValueError('Checkout input diverged: ' + name)
        snapshots[name] = (before, info)

    with tempfile.TemporaryDirectory(prefix='archium-transition-') as temporary:
        staging = Path(temporary)
        reconstruct(staging / 'old', old_manifest, old_patch, originals)
        new_state = reconstruct(staging / 'new', new_manifest, new_patch, originals)
        desired = {name: new_state.get(name, originals[name]) for name in names}

    receipt = {'schema': 1, 'revision': REVISION,
               'source_commit': source_commit, 'implementation_commit': implementation_commit,
               'old_patch_sha256': old_manifest['patch_sha256'],
               'new_patch_sha256': new_manifest['patch_sha256']}
    changed = []
    created_directories = set()
    try:
        for name in names:
            before, info = snapshots[name]
            after = desired[name]
            if before == after: continue
            target = checkout / name
            parent = target.parent
            while parent != checkout and not parent.exists():
                created_directories.add(parent); parent = parent.parent
            # Include the current file before mutation so failures during replacement roll back.
            changed.append(name)
            _write_file(target, after, stat.S_IMODE(info.st_mode) if info else 0o644)
        _write_file(receipt_path, (json.dumps(receipt, indent=2) + '\n').encode(), 0o644)
    except BaseException:
        if previous_receipt is None:
            if receipt_path.exists(): receipt_path.unlink()
        else:
            _atomic_write(receipt_path, previous_receipt,
                          stat.S_IMODE(previous_receipt_info.st_mode))
            os.utime(receipt_path, ns=(previous_receipt_info.st_atime_ns,
                                     previous_receipt_info.st_mtime_ns))
        for name in reversed(changed):
            target = checkout / name
            before, info = snapshots[name]
            if before is None:
                if target.exists(): target.unlink()
            else:
                _atomic_write(target, before, stat.S_IMODE(info.st_mode))
                os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns))
        for directory in sorted(created_directories, key=lambda p: len(p.parts), reverse=True):
            if directory.exists(): directory.rmdir()
        raise
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--implementation-commit', required=True)
    args = parser.parse_args()
    for value in [args.source_commit, args.implementation_commit]:
        if not re.fullmatch('[0-9a-f]{40}', value): raise ValueError('Full implementation commit required')
    if git(ROOT, 'rev-parse', 'HEAD').decode().strip() != args.implementation_commit:
        raise ValueError('Implementation checkout identity mismatch')
    with tempfile.TemporaryDirectory(prefix='archium-old-patch-') as temporary:
        old_patch = Path(temporary) / 'old.patch'
        old_patch.write_bytes(git(ROOT, 'show', args.source_commit + ':patches/archium-desktop.patch'))
        old_manifest = json.loads(git(ROOT, 'show', args.source_commit + ':patches/upstream-files.json'))
        new_patch = ROOT / 'patches/archium-desktop.patch'
        new_manifest = json.loads(git(ROOT, 'show', args.implementation_commit + ':patches/upstream-files.json'))
        transition(args.checkout, old_manifest, new_manifest, old_patch, new_patch,
                   source_commit=args.source_commit, implementation_commit=args.implementation_commit)
    print('Verified patch transition complete; unchanged source timestamps preserved')


if __name__ == '__main__':
    try: main()
    except (ValueError, subprocess.CalledProcessError) as error: raise SystemExit(str(error))
