#!/usr/bin/env python3
"""Stream complete CI workspace checkpoints through bounded GitHub release assets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

CHUNK_BYTES = 1024 ** 3  # Each release asset must be below 2 GiB.


def run(*args, capture=False):
    return subprocess.run(args, check=True, text=True, capture_output=capture)


def verify_assets(parts, tag, repo):
    # Newly created draft releases are not resolved by GitHub's by-tag endpoint.
    response = run('gh', 'api', f'repos/{repo}/releases?per_page=100', '--paginate', '--jq',
                   f'.[] | select(.tag_name == {json.dumps(tag)})', capture=True)
    release = json.loads(response.stdout)
    if release.get('tag_name') != tag:
        raise ValueError('Checkpoint release identity mismatch')
    assets = {asset['name']: asset for asset in release.get('assets', [])}
    for part in parts:
        asset = assets.get(part['name'], {})
        if (asset.get('state') != 'uploaded' or asset.get('size') != part['bytes']
                or asset.get('digest') != 'sha256:' + part['sha256']):
            raise ValueError('Uploaded checkpoint part verification failed: ' + part['name'])
    print(f'Checkpoint remote parts verified: {len(parts)}', flush=True)


def identity(workspace, *, source_commit=None):
    return {'schema': 1, 'workspace': str(workspace.resolve()),
            'commit': source_commit if source_commit is not None else os.environ['GITHUB_SHA'],
            'revision': 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'}


def pack(workspace, tag, repo):
    manifest = identity(workspace)
    manifest['parts'] = []
    run('gh', 'release', 'create', tag, '--repo', repo, '--target', manifest['commit'],
        '--draft', '--title', tag, '--notes',
        'Temporary Archium build checkpoint. Not an installable browser release.')
    with tempfile.TemporaryDirectory(prefix='archium-transfer-') as temporary:
        # Stream compression: never duplicate the full checkout on the runner disk.
        process = subprocess.Popen(['tar', '--format=pax', '-C', str(workspace), '-I', 'gzip -1', '-cf', '-', '.'],
                                   stdout=subprocess.PIPE)
        try:
            number = 0
            while True:
                path = Path(temporary) / f'checkpoint-{number:04d}.tar.gz.part'
                digest = hashlib.sha256()
                size = 0
                with path.open('wb') as output:
                    while size < CHUNK_BYTES:
                        block = process.stdout.read(min(8 * 1024 ** 2, CHUNK_BYTES - size))
                        if not block:
                            break
                        output.write(block)
                        digest.update(block)
                        size += len(block)
                if size == 0:
                    path.unlink()
                    break
                run('gh', 'release', 'upload', tag, str(path), '--repo', repo)
                manifest['parts'].append({'name': path.name, 'bytes': size,
                                          'sha256': digest.hexdigest()})
                print(f'Checkpoint part {number}: {size} bytes uploaded', flush=True)
                path.unlink()
                number += 1
            if process.wait() != 0:
                raise RuntimeError('Checkpoint tar failed; manifest will not be published')
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.kill()
                process.wait()
        # Verify remote receipts before making this checkpoint consumable.
        verify_assets(manifest['parts'], tag, repo)
        path = Path(temporary) / 'checkpoint.json'
        path.write_text(json.dumps(manifest, indent=2) + '\n')
        # Manifest is the commit marker: consumers never restore incomplete checkpoints.
        run('gh', 'release', 'upload', tag, str(path), '--repo', repo)
        # Read back only the small commit marker, never the multi-GB parts.
        with tempfile.TemporaryDirectory(dir=temporary) as readback:
            run('gh', 'release', 'download', tag, '--repo', repo, '--pattern',
                'checkpoint.json', '--dir', readback)
            if json.loads((Path(readback) / 'checkpoint.json').read_text()) != manifest:
                raise ValueError('Checkpoint manifest readback mismatch')
    print(f'Checkpoint complete: {len(manifest["parts"])} parts', flush=True)


def restore(workspace, tag, repo, *, source_commit=None):
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError('Restore requires an empty dedicated workspace')
    with tempfile.TemporaryDirectory(prefix='archium-transfer-') as temporary:
        run('gh', 'release', 'download', tag, '--repo', repo, '--pattern',
            'checkpoint.json', '--dir', temporary)
        manifest = json.loads((Path(temporary) / 'checkpoint.json').read_text())
        validate_manifest(manifest, identity(workspace, source_commit=source_commit))
        workspace.mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(['tar', '-C', str(workspace), '-xzf', '-'],
                                   stdin=subprocess.PIPE)
        try:
            for part in manifest['parts']:
                run('gh', 'release', 'download', tag, '--repo', repo, '--pattern',
                    part['name'], '--dir', temporary)
                path = Path(temporary) / part['name']
                digest = hashlib.sha256()
                with path.open('rb') as source:
                    for block in iter(lambda: source.read(8 * 1024 ** 2), b''):
                        digest.update(block)
                if path.stat().st_size != part['bytes'] or digest.hexdigest() != part['sha256']:
                    raise ValueError('Checkpoint part checksum mismatch: ' + part['name'])
                with path.open('rb') as source:
                    for block in iter(lambda: source.read(8 * 1024 ** 2), b''):
                        process.stdin.write(block)
                path.unlink()
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError('Checkpoint extraction failed')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
    print('Complete workspace restored, including timestamps and Ninja state', flush=True)



# R3.3 checkpoint transport: GitHub Actions artifacts, not GitHub Releases.
# Checkpoint chunks are grouped into bounded <10-GiB upload-artifact@v4 items.
GROUP_SIZE = 8
MAX_CHUNKS = 64


def pack_actions(workspace, tag, folder):
    if not workspace.is_dir() or not any(workspace.iterdir()):
        raise ValueError('Missing checkpoint workspace')
    if folder.exists() and any(folder.iterdir()):
        raise ValueError('Refusing to overwrite staged checkpoint data')
    folder.mkdir(parents=True, exist_ok=True)
    receipt = {**identity(workspace), 'tag': tag, 'parts': []}
    tar = subprocess.Popen(
        ['tar', '--format=pax', '-C', str(workspace), '-I', 'gzip -1', '-cf', '-', '.'],
        stdout=subprocess.PIPE)
    try:
        for number in range(MAX_CHUNKS):
            part = f'checkpoint-{number:04d}.tar.gz.part'
            group = folder / f'group-{number // GROUP_SIZE:02d}'
            group.mkdir(exist_ok=True)
            target = group / part
            digest = hashlib.sha256()
            length = 0
            with target.open('wb') as dest:
                while length < CHUNK_BYTES:
                    block = tar.stdout.read(min(8 * 1024 * 1024, CHUNK_BYTES - length))
                    if not block:
                        break
                    dest.write(block)
                    digest.update(block)
                    length += len(block)
            if length == 0:
                target.unlink()
                if not any(group.iterdir()):
                    group.rmdir()
                break
            receipt['parts'].append({'name': part, 'bytes': length,
                                     'sha256': digest.hexdigest()})
        else:
            raise ValueError('Checkpoint exceeds 64 bounded parts')
        if tar.wait():
            raise RuntimeError('Checkpoint tar stream failed')
    finally:
        tar.stdout.close()
        if tar.poll() is None:
            tar.kill()
            tar.wait()
    validate_manifest(receipt, {**identity(workspace), 'tag': tag})
    for number, part in enumerate(receipt['parts']):
        target = folder / f'group-{number // GROUP_SIZE:02d}' / part['name']
        if target.stat().st_size != part['bytes']:
            raise ValueError('Staged checkpoint size changed')
        digest = hashlib.sha256()
        with target.open('rb') as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != part['sha256']:
            raise ValueError('Staged checkpoint hash changed')
    # The manifest is written LAST and uploaded in the first required group.
    (folder / 'group-00' / 'checkpoint.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'ACTIONS_CHECKPOINT_STAGED=PASS parts={len(receipt["parts"])}', flush=True)


def restore_actions(workspace, tag, folder, *, source_commit=None):
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError('Checkpoint restore target is not empty')
    manifest_path = folder / 'checkpoint.json'
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError('Checkpoint completion manifest absent')
    receipt = json.loads(manifest_path.read_text())
    validate_manifest(receipt, {**identity(workspace, source_commit=source_commit), 'tag': tag})
    wanted = {'checkpoint.json'} | {part['name'] for part in receipt['parts']}
    present = {item.name for item in folder.iterdir() if item.is_file()}
    if wanted != present:
        raise ValueError('Incomplete or unexpected checkpoint artifacts')
    for part in receipt['parts']:
        target = folder / part['name']
        if target.is_symlink() or not target.is_file() or target.stat().st_size != part['bytes']:
            raise ValueError('Checkpoint part is missing or truncated: ' + part['name'])
        digest = hashlib.sha256()
        with target.open('rb') as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != part['sha256']:
            raise ValueError('Checkpoint part hash mismatch: ' + part['name'])
    workspace.mkdir(parents=True, exist_ok=True)
    untar = subprocess.Popen(['tar', '-C', str(workspace), '--no-same-owner', '-xzf', '-'],
                             stdin=subprocess.PIPE)
    try:
        for part in receipt['parts']:
            with (folder / part['name']).open('rb') as source:
                for block in iter(lambda: source.read(8 * 1024 * 1024), b''):
                    untar.stdin.write(block)
        untar.stdin.close()
        if untar.wait():
            raise RuntimeError('Checkpoint extraction failed')
    finally:
        if untar.poll() is None:
            untar.kill()
            untar.wait()
    print('ACTIONS_CHECKPOINT_RESTORE=PASS', flush=True)


def validate_manifest(manifest, expected):
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError('Incompatible checkpoint: ' + key)
    parts = manifest.get('parts')
    if not isinstance(parts, list) or not parts:
        raise ValueError('Checkpoint has no complete parts')
    for number, part in enumerate(parts):
        if part.get('name') != f'checkpoint-{number:04d}.tar.gz.part' \
                or not isinstance(part.get('bytes'), int) \
                or not 0 < part['bytes'] <= CHUNK_BYTES \
                or len(part.get('sha256', '')) != 64:
            raise ValueError('Invalid checkpoint part')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['pack', 'restore'])
    parser.add_argument('workspace', type=Path)
    parser.add_argument('tag')
    parser.add_argument('--repo', default='Jorgeprdz/chromium-dex-arc')
    parser.add_argument('--source-commit', help='Explicit commit that produced a source checkpoint; restore only')
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') != 'true' \
            or os.environ.get('GITHUB_REPOSITORY') != args.repo:
        raise SystemExit('Only supported in the dedicated disposable CI runner')
    if args.mode == 'pack':
        if args.source_commit: raise SystemExit('Source identity is only accepted for restore')
        if os.environ.get('ARCHIUM_CHECKPOINT_STORAGE') == 'artifact':
            pack_actions(args.workspace, args.tag, Path(os.environ['ARCHIUM_CHECKPOINT_DIR']))
        else:
            pack(args.workspace, args.tag, args.repo)
    elif os.environ.get('ARCHIUM_CHECKPOINT_STORAGE') == 'artifact' and (
            not args.source_commit or os.environ.get('ARCHIUM_SOURCE_RUN_ID')):
        restore_actions(args.workspace, args.tag, Path(os.environ['ARCHIUM_CHECKPOINT_DIR']),
                        source_commit=args.source_commit)
    else:
        restore(args.workspace, args.tag, args.repo, source_commit=args.source_commit)
