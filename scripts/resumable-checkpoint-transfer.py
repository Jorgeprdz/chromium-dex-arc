#!/usr/bin/env python3
"""Bounded HTTP Range download of one immutable artifact; never dispatches a build."""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import requests


def artifact_url(repository, artifact_id):
    # Credentials go to GitHub API only. Signed blob URLs are never logged or saved.
    response = requests.get(
        f'https://api.github.com/repos/{repository}/actions/artifacts/{artifact_id}/zip',
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Accept': 'application/vnd.github+json', 'Cache-Control': 'no-cache'},
        allow_redirects=False, timeout=(15, 30))
    try:
        if response.status_code in (408, 429, 500, 502, 503, 504):
            error = requests.ConnectionError('Artifact authorization transient failure')
            error.http_status = response.status_code
            raise error
        if response.status_code != 302:
            raise RuntimeError(f'Artifact authorization HTTP {response.status_code}')
        url = response.headers['Location']
        if not url.startswith('https://'):
            raise ValueError('Artifact redirect must use HTTPS')
        return url
    finally:
        response.close()


def download_archive(group, path, repository, deadline, *, get_url=None,
                     chunk_bytes=32 * 1024 * 1024, recovery_limit=8, max_recoveries=32, pause=time.sleep):
    """Resume bytes in this job/process, cap recoveries, then verify full ZIP SHA256.

    At most8 consecutive no-progress recoveries and32 total recoveries per group.
    Files and immutable identity sidecar survive network failures. They are not a
    cache across ephemeral runners. No extraction is permitted before full hash PASS.
    """
    identity = {key: group[key] for key in ('id', 'name', 'size_in_bytes', 'digest')}
    size = identity['size_in_bytes']
    if (type(size) is not int or size <= 0 or not re.fullmatch(r'sha256:[0-9a-f]{64}', identity['digest'])
            or not 0 < chunk_bytes <= 32 * 1024 * 1024 or not 0 <= recovery_limit <= 8
            or not 0 <= max_recoveries <= 32):
        raise ValueError('Invalid bounded artifact transfer')
    if time.monotonic() >= deadline:
        raise TimeoutError('Checkpoint transfer budget exhausted')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = path.with_name(path.name + '.identity.json')
    progress = path.with_name(path.name + '.progress.json')
    if path.is_symlink() or sidecar.is_symlink():
        raise ValueError('Artifact path must not be a symlink')
    if sidecar.exists():
        if json.loads(sidecar.read_text()) != identity:
            raise ValueError('Partial artifact identity differs')
    elif path.exists():
        raise ValueError('Partial artifact identity absent')
    else:
        with sidecar.open('x') as output:
            json.dump(identity, output)
    digest = hashlib.sha256()
    offset = 0
    if path.exists():
        with path.open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                offset += len(block)
                if offset > size:
                    raise ValueError('Partial artifact exceeds declared size')
                digest.update(block)
    url = None
    url_at = 0
    recoveries = 0
    no_progress = 0
    events = []
    last_report = 0
    def record(status):
        progress.write_text(json.dumps(dict(artifact_id=identity['id'], bytes=offset,
            expected_bytes=size, recoveries=recoveries, no_progress_failures=no_progress,
            max_recoveries=max_recoveries, status=status, events=events), indent=2) + '\n')
    while offset < size:
        if time.monotonic() >= deadline:
            record('BUDGET_EXHAUSTED')
            raise TimeoutError('Checkpoint transfer budget exhausted')
        end = min(size - 1, offset + chunk_bytes - 1)
        response = None
        attempt_start = offset
        try:
            if url is None or time.monotonic() - url_at >= 40:
                url = get_url() if get_url else artifact_url(repository, identity['id'])
                url_at = time.monotonic()
            response = requests.get(url, headers={
                'Range': f'bytes={offset}-{end}', 'Accept-Encoding': 'identity'},
                stream=True, timeout=(15, 30))
            if response.status_code in (403, 408, 429, 500, 502, 503, 504):
                error = requests.ConnectionError('Artifact response transient failure')
                error.http_status = response.status_code
                raise error
            if (response.status_code != 206 or response.headers.get('Content-Range') != f'bytes {offset}-{end}/{size}'
                    or response.headers.get('Content-Encoding', 'identity') != 'identity'):
                raise ValueError(f'Artifact Range rejected: HTTP {response.status_code}')
            with path.open('ab') as output:
                for block in response.iter_content(chunk_size=65536):
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Checkpoint transfer budget exhausted')
                    if not block:
                        continue
                    if offset + len(block) > end + 1:
                        raise ValueError('Artifact response exceeds requested range')
                    output.write(block)
                    digest.update(block)
                    offset += len(block)
                    if time.monotonic() - last_report >= 30:
                        output.flush()
                        record('DOWNLOADING')
                        print(f'CHECKPOINT_BYTES id={identity["id"]} bytes={offset}/{size} recoveries={recoveries}', flush=True)
                        last_report = time.monotonic()
                output.flush()
            if offset != end + 1:
                raise requests.ConnectionError('TruncatedRange')
            no_progress = 0
        except requests.RequestException as error:
            # Do not include exception text: requests can embed signed URLs in it.
            advanced = offset - attempt_start
            no_progress = 0 if advanced > 0 else no_progress + 1
            events.append(dict(offset=offset, error=type(error).__name__,
                               http_status=getattr(error, 'http_status', None), bytes_received=advanced))
            record('NETWORK_INTERRUPTED')
            if recovery_limit == 0 or no_progress > recovery_limit or recoveries >= max_recoveries:
                raise RuntimeError(f'Checkpoint network recovery limit reached: artifact={identity["id"]} bytes={offset}') from None
            recoveries += 1
            url = None
            print(f'CHECKPOINT_NETWORK_RESUME id={identity["id"]} offset={offset} recovery={recoveries}/{max_recoveries} no_progress={no_progress}/{recovery_limit}', flush=True)
            pause(min(2 ** min(no_progress + 1, 6), 60))
        except TimeoutError:
            record('BUDGET_EXHAUSTED')
            raise
        finally:
            if response is not None:
                response.close()
    if digest.hexdigest() != identity['digest'][7:]:
        record('HASH_FAILED')
        raise ValueError('Complete artifact ZIP hash mismatch')
    record('ZIP_HASH_VERIFIED')
    print(f'CHECKPOINT_ZIP_HASH=PASS id={identity["id"]} bytes={offset}', flush=True)
    return path
