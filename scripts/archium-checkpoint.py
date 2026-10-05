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


def run(*args):
    subprocess.run(args, check=True)


def identity(workspace):
    return {'schema': 1, 'workspace': str(workspace.resolve()),
            'commit': os.environ['GITHUB_SHA'],
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
        path = Path(temporary) / 'checkpoint.json'
        path.write_text(json.dumps(manifest, indent=2) + '\n')
        # Manifest is the commit marker: consumers never restore incomplete checkpoints.
        run('gh', 'release', 'upload', tag, str(path), '--repo', repo)
    print(f'Checkpoint complete: {len(manifest["parts"])} parts', flush=True)


def restore(workspace, tag, repo):
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError('Restore requires an empty dedicated workspace')
    with tempfile.TemporaryDirectory(prefix='archium-transfer-') as temporary:
        run('gh', 'release', 'download', tag, '--repo', repo, '--pattern',
            'checkpoint.json', '--dir', temporary)
        manifest = json.loads((Path(temporary) / 'checkpoint.json').read_text())
        validate_manifest(manifest, identity(workspace))
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
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') != 'true' \
            or os.environ.get('GITHUB_REPOSITORY') != args.repo:
        raise SystemExit('Only supported in the dedicated disposable CI runner')
    (pack if args.mode == 'pack' else restore)(args.workspace, args.tag, args.repo)
