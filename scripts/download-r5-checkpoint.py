#!/usr/bin/env python3
"""Download verified groups sequentially with bounded in-job network resumption.
Part SHA256 verification remains mandatory in archium-checkpoint.py before extraction.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import time
import zipfile


def download_groups(items, report, folder, repository, run_id, *, archive_fetcher=None, transfer_seconds=5400):
    if not 0 < transfer_seconds <= 5400:
        raise ValueError('Invalid checkpoint transfer budget')
    deadline = time.monotonic() + transfer_seconds
    if archive_fetcher is None:
        spec = importlib.util.spec_from_file_location('transfer', Path(__file__).with_name('resumable-checkpoint-transfer.py'))
        transfer = importlib.util.module_from_spec(spec); spec.loader.exec_module(transfer)
        archive_fetcher = transfer.download_archive
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
        archive_path = folder.parent / (folder.name + '-transfers') / (group['name'] + '.zip.part')
        archive_fetcher(group, archive_path, repository, deadline)
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise ValueError('Duplicate checkpoint ZIP member')
            if number == 0:
                if 'checkpoint.json' not in names or archive.getinfo('checkpoint.json').file_size > 65536:
                    raise ValueError('Downloaded manifest absent or oversized')
                payload = archive.read('checkpoint.json')
                if hashlib.sha256(payload).hexdigest() != report['manifest_sha256']:
                    raise ValueError('Downloaded manifest digest differs from bounded preflight')
                manifest = json.loads(payload)
                if manifest['tag'] != report['source_tag'] or manifest['commit'] != report['source_sha']:
                    raise ValueError('Downloaded manifest identity differs')
                if (len(manifest['parts']) + 7)//8 != len(groups):
                    raise ValueError('Downloaded manifest group count differs')
            parts = manifest['parts'][number*8:(number+1)*8]
            wanted = {part['name'] for part in parts} | ({'checkpoint.json'} if number == 0 else set())
            present = set(names)
            if wanted != present:
                raise ValueError(f"{group['name']}: missing={sorted(wanted-present)} unexpected={sorted(present-wanted)}")
            for info in infos:
                if (Path(info.filename).name != info.filename or info.is_dir()
                        or stat.S_ISLNK(info.external_attr >> 16)):
                    raise ValueError('Invalid downloaded ZIP file: ' + info.filename)
            for part in parts:
                if archive.getinfo(part['name']).file_size != part['bytes']:
                    raise ValueError('Downloaded part truncated: ' + part['name'])
            for name in sorted(wanted):
                expected = next((part for part in parts if part['name'] == name), None)
                digest = hashlib.sha256()
                with archive.open(name) as source, (staging/name).open('xb') as output:
                    for block in iter(lambda: source.read(1024 * 1024), b''):
                        output.write(block)
                        digest.update(block)
                if expected and digest.hexdigest() != expected['sha256']:
                    raise ValueError('Downloaded part hash mismatch: ' + name)
        for name in sorted(wanted):
            destination = folder/name
            if destination.exists():
                raise ValueError('Duplicate checkpoint file: ' + name)
            (staging/name).rename(destination)
        staging.rmdir()
        archive_path.unlink()
        archive_path.with_name(archive_path.name + '.identity.json').unlink(missing_ok=True)
        print('CHECKPOINT_DOWNLOAD_COMPLETE=' + group['name'], flush=True)
    print(f'CHECKPOINT_DOWNLOAD_INVENTORY=PASS groups={len(groups)} parts={len(manifest["parts"])} part_hashes=PASS restore_hashes=MANDATORY', flush=True)


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
