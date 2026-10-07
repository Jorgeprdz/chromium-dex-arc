#!/usr/bin/env python3
"""Check effective GN media configuration; never certify decoder/runtime support."""
import argparse
import json
from pathlib import Path
import re
import subprocess


REQUIRED = {
    'target_os': 'android',
    'proprietary_codecs': True,
    'ffmpeg_branding': 'Chrome',
    'media_use_ffmpeg': True,
    'media_use_libvpx': True,
    'enable_av1_decoder': True,
    'enable_hls_demuxer': True,
    'enable_mse_mpeg2ts_stream_parser': True,
    'enable_platform_hevc': True,
    'enable_widevine': True,
    'enable_library_cdms': False,
    'is_chrome_branded': False,
    'chrome_public_manifest_package': 'app.archium.android',
}


def parse_args(text):
    values = {}
    for line in text.splitlines():
        match = re.fullmatch(r'\s*([a-zA-Z_][a-zA-Z_0-9]*)\s*=\s*(.*?)\s*', line)
        if not match or match[1] not in {*REQUIRED, 'target_cpu'}:
            continue
        name, raw = match.groups()
        if name in values:
            raise ValueError(f'Duplicate GN argument: {name}')
        values[name] = json.loads(raw)
    return values


def issues(values):
    errors = [f'{name}: expected {expected!r}, got {values.get(name)!r}'
              for name, expected in REQUIRED.items()
              if type(values.get(name)) is not type(expected) or values.get(name) != expected]
    if values.get('target_cpu') not in ('arm64', 'x64'):
        errors.append('target_cpu must be arm64 or x64')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--gn', default='gn')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    values = {}
    try:
        result = subprocess.run([args.gn, 'args', str(args.out), '--list', '--short'],
                                check=True, text=True, capture_output=True, timeout=120)
        values = parse_args(result.stdout)
        errors = issues(values)
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        errors = [f'Unable to read effective GN media arguments: {error}']
    report = {'status': 'FAIL' if errors else 'PASS', 'effective_args': values,
              'errors': errors, 'playback_runtime': 'NOT_EXECUTED',
              'hardware_decode': 'NOT_VERIFIED', 'premium_drm': 'NOT_VERIFIED'}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
