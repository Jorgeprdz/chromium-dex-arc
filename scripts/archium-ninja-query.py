#!/usr/bin/env python3
"""Query real GN manifests with pinned Ninja without touching Siso state/logs."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def query(out, ninja, target, report):
    out, ninja = out.resolve(), ninja.resolve()
    if not (out / 'build.ninja').is_file():
        raise ValueError('Generated build.ninja is absent')
    with tempfile.TemporaryDirectory(prefix='archium-ninja-query-') as directory:
        scratch = Path(directory)
        count = 0
        for source in out.rglob('*.ninja'):
            # Reject log directories or includes that could escape the snapshot.
            # Ninja manifests and paths are byte strings, not necessarily UTF-8.
            # Parse ASCII directives without dropping or replacing other bytes.
            for line in source.read_bytes().splitlines():
                if re.match(rb'^\s*builddir\s*=', line):
                    if line.split(b'=', 1)[1].strip() != b'.':
                        raise ValueError('Ninja builddir must remain inside query snapshot')
                match = re.match(rb'^\s*(?:include|subninja)\s+(.+)$', line)
                if match:
                    included = Path(os.fsdecode(match.group(1).strip()))
                    if included.is_absolute() or '..' in included.parts or '$' in str(included):
                        raise ValueError('Ninja include must remain inside query snapshot')
            destination = scratch / source.relative_to(out)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            count += 1
        result = subprocess.run([str(ninja), '-C', str(scratch), '-t', 'query', target],
                                capture_output=True, timeout=120)
        if result.stderr:
            sys.stderr.buffer.write(result.stderr)
        if result.returncode:
            return result.returncode
        report.write_bytes(result.stdout)
        print(f'NINJA_QUERY=PASS manifests={count} graph_source={out} scope=isolated_manifest_query')
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--ninja', required=True, type=Path)
    parser.add_argument('--target', required=True)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    try:
        sys.exit(query(args.out, args.ninja, args.target, args.report))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f'NINJA_QUERY=FAIL: {error}', file=sys.stderr)
        sys.exit(1)
