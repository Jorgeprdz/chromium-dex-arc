#!/usr/bin/env python3
"""Download each verified group once, sequentially; reject incomplete extraction before restore.
Part SHA256 verification remains mandatory in archium-checkpoint.py before extraction.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess


def download_groups(items, report, folder, repository, run_id, *, runner=subprocess.run):
    if not re.fullmatch(r'[0-9]+', run_id) or not report['source_tag'].startswith(f'archium-checkpoint-{run_id}-'):
        raise ValueError('Source run differs from preflight checkpoint')
    spec = importlib.util.spec_from_file_location('recovery', Path(__file__).with_name('check-recovery-checkpoint.py'))
    recovery = importlib.util.module_from_spec(spec); spec.loader.exec_module(recovery)
    groups = recovery.validate_inventory(items, report['source_tag'], report['source_sha'],
                                         report['available_bytes'], report['free_inodes'])
    if folder.exists() and any(folder.iterdir()):
        raise ValueError('Download target is not empty; no overwrite or automatic retry')
    folder.mkdir(parents=True, exist_ok=True)
    manifest = None
    for number, group in enumerate(groups):
        # Separate directories prevent parallel merging or collisions concealing an incomplete group.
        staging = folder.parent / (folder.name + f'-group-{number:02d}')
        staging.mkdir(exist_ok=False)
        print('CHECKPOINT_DOWNLOAD_START=' + group['name'], flush=True)
        runner(['gh', 'run', 'download', run_id, '--repo', repository,
                '--name', group['name'], '--dir', str(staging)], check=True, timeout=3600)
        if number == 0:
            path = staging/'checkpoint.json'
            if not path.is_file() or path.is_symlink():
                raise ValueError('Downloaded manifest absent or symlink')
            payload = path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != report['manifest_sha256']:
                raise ValueError('Downloaded manifest digest differs from bounded preflight')
            manifest = json.loads(payload)
            if manifest['tag'] != report['source_tag'] or manifest['commit'] != report['source_sha']:
                raise ValueError('Downloaded manifest identity differs')
            if (len(manifest['parts']) + 7)//8 != len(groups):
                raise ValueError('Downloaded manifest group count differs')
        parts = manifest['parts'][number*8:(number+1)*8]
        wanted = {part['name'] for part in parts} | ({'checkpoint.json'} if number == 0 else set())
        present = {p.name for p in staging.iterdir()}
        if wanted != present:
            raise ValueError(f"{group['name']}: missing={sorted(wanted-present)} unexpected={sorted(present-wanted)}")
        for name in wanted:
            path = staging/name
            if Path(name).name != name or not path.is_file() or path.is_symlink():
                raise ValueError('Invalid downloaded file: ' + name)
        for part in parts:
            if (staging/part['name']).stat().st_size != part['bytes']:
                raise ValueError('Downloaded part truncated: ' + part['name'])
        for name in sorted(wanted):
            destination = folder/name
            if destination.exists():
                raise ValueError('Duplicate checkpoint file: ' + name)
            (staging/name).rename(destination)
        staging.rmdir()
        print('CHECKPOINT_DOWNLOAD_COMPLETE=' + group['name'], flush=True)
    print(f'CHECKPOINT_DOWNLOAD_INVENTORY=PASS groups={len(groups)} parts={len(manifest["parts"])} hashes=PENDING_RESTORE', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--preflight', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    download_groups(json.loads(args.artifacts.read_text())['artifacts'],
                    json.loads(args.preflight.read_text()), args.directory,
                    os.environ['GITHUB_REPOSITORY'], os.environ['ARCHIUM_SOURCE_RUN_ID'])


if __name__ == '__main__':
    main()
