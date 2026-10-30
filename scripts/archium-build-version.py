#!/usr/bin/env python3
"""Allocate checkpoint-stable Archium identity and verify its packaged APK asset."""
import argparse
import json
from pathlib import Path
import re
import zipfile

RESOURCE = Path('chrome/browser/desktop_policy/android/archium-build.json')


def validate(data):
    if (not isinstance(data, dict) or data.get('schema') != 1
            or not isinstance(data.get('build_number'), int)
            or isinstance(data.get('build_number'), bool)
            or not 1 <= data['build_number'] <= 2_147_483_647
            or data.get('version') != '0.9.' + str(data['build_number'])
            or not re.fullmatch('[0-9a-f]{40}', str(data.get('source_sha', '')))
            or not re.fullmatch('[1-9][0-9]*', str(data.get('run_id', '')))):
        raise ValueError('Invalid Archium build identity; preserving existing metadata')
    return data


def allocate(checkout, source_sha, build_number, run_id):
    if (not re.fullmatch('[0-9a-f]{40}', source_sha)
            or not re.fullmatch('[1-9][0-9]{0,9}', build_number)
            or not re.fullmatch('[1-9][0-9]*', run_id)):
        raise ValueError('Exact source SHA, positive CI build number and run ID required')
    path = Path(checkout) / RESOURCE
    previous = validate(json.loads(path.read_text())) if path.exists() else None
    if previous and previous['source_sha'] == source_sha:
        return previous  # Same source/checkpoint is a resumed build, not a new version.
    number = max(int(build_number), previous['build_number'] + 1 if previous else 1)
    data = validate(dict(schema=1, version=f'0.9.{number}', build_number=number,
                         source_sha=source_sha, run_id=run_id))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n')
    temporary.replace(path)
    return data


def verify_apk(checkout, apk):
    expected = validate(json.loads((Path(checkout) / RESOURCE).read_text()))
    with zipfile.ZipFile(apk) as archive:
        members = [x for x in archive.infolist() if x.filename == 'assets/archium-build.json']
        if len(members) != 1 or members[0].file_size > 4096:
            raise ValueError('APK must contain one bounded Archium build identity')
        actual = validate(json.loads(archive.read(members[0])))
    if actual != expected:
        raise ValueError('APK Archium version/source differs from the allocated build')
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--source-sha')
    parser.add_argument('--build-number')
    parser.add_argument('--run-id')
    parser.add_argument('--verify-apk', type=Path)
    args = parser.parse_args()
    if args.verify_apk:
        data = verify_apk(args.checkout, args.verify_apk)
    else:
        if not all((args.source_sha, args.build_number, args.run_id)):
            parser.error('Allocation needs source SHA, CI build number and run ID')
        data = allocate(args.checkout, args.source_sha, args.build_number, args.run_id)
    print(json.dumps(data, sort_keys=True))


if __name__ == '__main__':
    main()
