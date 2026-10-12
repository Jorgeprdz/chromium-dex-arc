#!/usr/bin/env python3
"""Reject reactivation or APK dependencies on the retired Archium password feature."""
import argparse
from pathlib import Path
import re
import subprocess


def issues(effective_args, deps):
    errors = []
    if re.findall(r'^enable_archium_local_passwords\s*=\s*(\w+)\s*$',
                  effective_args, re.M) != ['false']:
        errors.append('Retired password flag must be false in effective GN args')
    retired = re.findall(r':(archium_(?:key_\w+|local_password_manager|password_\w+|'
                         r'login_database_tests|import_preview))(?=[(\s]|$)', deps)
    if retired:
        errors.append('Retired password dependencies in APK graph: ' + ', '.join(sorted(set(retired))))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--deps', required=True, type=Path)
    args = parser.parse_args()
    result = subprocess.run(['gn', 'args', args.out,
                             '--list=enable_archium_local_passwords', '--short'],
                            capture_output=True, text=True, timeout=120)
    if result.returncode:
        print(result.stdout, end='')
        print(result.stderr, end='')
        return result.returncode
    errors = issues(result.stdout, args.deps.read_text())
    if errors:
        print('PASSWORD_DEPRECATION=FAIL: ' + '; '.join(errors))
        return 1
    print('PASSWORD_FEATURE=DEPRECATED effective_flag=false apk_dependencies=ABSENT')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
