#!/usr/bin/env python3
"""Derive ARM64 or x64 GN configuration from Archium's common configuration."""
import argparse
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-cpu', choices=('arm64', 'x64'), default='arm64')
    parser.add_argument('--source', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'config/archium-args.gn')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = args.source.read_text()
    text, count = re.subn(r'^target_cpu\s*=\s*"(?:arm64|x64)"\s*$',
                         f'target_cpu = "{args.target_cpu}"', text, flags=re.M)
    if count != 1:
        parser.error('Common configuration must declare target_cpu exactly once')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
