#!/usr/bin/env python3
"""Verify source metadata, capacity, and a bounded remote manifest before transfer."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'


def validate_inventory(items, tag, source_sha, available_bytes, free_inodes):
    if not re.fullmatch(r'archium-checkpoint-[0-9]+-[0-9]+', tag):
        raise ValueError('Invalid checkpoint tag')
    if not re.fullmatch(r'[0-9a-f]{40}', source_sha):
        raise ValueError('Invalid checkpoint SHA')
    groups = [a for a in items if a.get('name', '').startswith(tag + '-')]
    groups.sort(key=lambda a: a['name'])
    if not groups or [a['name'] for a in groups] != [
            f'{tag}-{i:02d}' for i in range(len(groups))]:
        raise ValueError('Checkpoint groups incomplete or ambiguous')
    for group in groups:
        expires = datetime.fromisoformat(group['expires_at'].replace('Z', '+00:00'))
        if group.get('expired') or expires <= datetime.now(timezone.utc):
            raise ValueError('Checkpoint artifact expired')
        if type(group.get('size_in_bytes')) is not int or group['size_in_bytes'] <= 0:
            raise ValueError('Empty checkpoint artifact')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', group.get('digest', '')):
            raise ValueError('Checkpoint artifact digest absent')
        if group.get('workflow_run', {}).get('head_sha') != source_sha:
            raise ValueError('Checkpoint source SHA differs')
    archive_bytes = sum(a['size_in_bytes'] for a in groups)
    required = 75_000_000_000 + archive_bytes
    if available_bytes < required:
        raise ValueError(f'Insufficient disk before download: available={available_bytes} required={required}')
    if free_inodes < 2_000_000:
        raise ValueError(f'Insufficient free inodes before download: {free_inodes}')
    return groups


def remote_manifest(artifact_id, repository, token):
    # Never print/store tokens or signed URLs. No unbounded fallback if Range fails.
    import requests
    response = requests.get(
        f'https://api.github.com/repos/{repository}/actions/artifacts/{artifact_id}/zip',
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'},
        allow_redirects=False, timeout=30)
    if response.status_code != 302:
        raise ValueError(f'Artifact read access rejected: HTTP {response.status_code}')
    url = response.headers['Location']

    class RangeFile(io.RawIOBase):
        def __init__(self):
            self.position = 0
            self.transferred = 0
            _, total = self.get(0, 1)
            self.size = total

        def get(self, start, length):
            if not 0 < length <= 1024 * 1024:
                raise ValueError('Unbounded artifact read forbidden')
            try:
                r = requests.get(url, headers={'Range': f'bytes={start}-{start + length - 1}'},
                                 stream=True, timeout=60)
            except requests.RequestException as error:
                raise ValueError('Bounded artifact request failed: ' + type(error).__name__) from None
            try:
                match = re.fullmatch(r'bytes ([0-9]+)-([0-9]+)/([0-9]+)',
                                     r.headers.get('Content-Range', ''))
                if r.status_code != 206 or not match or tuple(map(int, match.groups()[:2])) != (
                        start, start + length - 1):
                    raise ValueError('HTTP Range unavailable; full download forbidden')
                try:
                    data = r.raw.read(length + 1)
                except Exception as error:
                    raise ValueError('Bounded artifact stream failed: ' + type(error).__name__) from None
                if len(data) != length:
                    raise ValueError('Wrong HTTP Range response length')
                self.transferred += len(data)
                return data, int(match.group(3))
            finally:
                r.close()

        def seek(self, offset, whence=0):
            self.position = offset if whence == 0 else (
                self.position + offset if whence == 1 else self.size + offset)
            return self.position

        def tell(self):
            return self.position

        def read(self, length=-1):
            length = self.size - self.position if length < 0 else min(
                length, self.size - self.position)
            if not length:
                return b''
            data, _ = self.get(self.position, length)
            self.position += length
            return data

    ranged = RangeFile()
    with zipfile.ZipFile(ranged) as archive:
        manifests = [n for n in archive.namelist() if n.endswith('checkpoint.json')]
        if len(manifests) != 1 or archive.getinfo(manifests[0]).file_size > 65536:
            raise ValueError('Missing, ambiguous or oversized checkpoint manifest')
        payload = archive.read(manifests[0])
    return payload, ranged.transferred


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts', type=Path, required=True)
    p.add_argument('--source-tag', required=True)
    p.add_argument('--source-sha', required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    capacity = os.statvfs(os.environ['RUNNER_TEMP'])
    free = capacity.f_frsize * capacity.f_bavail
    groups = validate_inventory(json.loads(args.artifacts.read_text())['artifacts'],
                                args.source_tag, args.source_sha, free, capacity.f_favail)
    payload, transferred = remote_manifest(groups[0]['id'], os.environ['GITHUB_REPOSITORY'],
                                           os.environ['GH_TOKEN'])
    manifest = json.loads(payload)
    spec = importlib.util.spec_from_file_location('checkpoint', ROOT / 'scripts/archium-checkpoint.py')
    checkpoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checkpoint)
    checkpoint.validate_manifest(manifest, {
        'schema': 1, 'revision': REVISION, 'commit': args.source_sha, 'tag': args.source_tag,
        'workspace': str(Path(os.environ['RUNNER_TEMP']) / 'chromium-archium')})
    if len(groups) != (len(manifest['parts']) + checkpoint.GROUP_SIZE - 1) // checkpoint.GROUP_SIZE:
        raise ValueError('Manifest part count differs from artifact groups')
    args.report.write_text(json.dumps({
        'CHECKPOINT_METADATA': 'PASS', 'DISK_PREFLIGHT': 'PASS',
        'CHECKPOINT_ALL_BYTES': 'PENDING_POST_DOWNLOAD',
        'source_tag': args.source_tag, 'source_sha': args.source_sha,
        'available_bytes': free, 'free_inodes': capacity.f_favail,
        'manifest_sha256': hashlib.sha256(payload).hexdigest(),
        'bounded_bytes_read': transferred}, indent=2) + '\n')
    print(f'CHECKPOINT_METADATA=PASS DISK_PREFLIGHT=PASS available={free} inodes={capacity.f_favail}', flush=True)


if __name__ == '__main__':
    main()
