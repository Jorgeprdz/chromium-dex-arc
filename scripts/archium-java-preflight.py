#!/usr/bin/env python3
"""Resolve every delivered Java file to actual javac actions in the generated GN graph.

Header-only compilation, synthetic contracts, and guessed target names are insufficient.
The emitted Ninja outputs belong to real compile_java.py actions in this build directory.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
KEY_JAVA_PREFIX = 'chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/'
# Exactly the sources in the enable_archium_local_passwords-guarded archium_key_java
# target. Manager/CSV/settings sources still have owners when this flag is false.
CONDITIONAL_KEY_SOURCES = frozenset(KEY_JAVA_PREFIX + name for name in (
    'ArchiumPasswordKey.java', 'ArchiumPasswordKeyBridge.java'))


def parse_local_passwords_enabled(text):
    matches = re.findall(r'^\s*enable_archium_local_passwords\s*=\s*(true|false)\s*$',
                         text, re.MULTILINE)
    if len(matches) != 1:
        raise RuntimeError('Missing or ambiguous effective GN local-passwords flag')
    return matches[0] == 'true'


def gn_path(value, checkout):
    if value.startswith('//'):
        return (checkout / value[2:]).resolve()
    return Path(value).resolve() if Path(value).is_absolute() else (checkout / value).resolve()


def resolve(graph, paths, checkout, out, *, local_passwords_enabled=True):
    if not local_passwords_enabled:
        paths = [path for path in paths if path not in CONDITIONAL_KEY_SOURCES]
    checkout, out = checkout.resolve(), out.resolve()
    wanted = {gn_path('//' + name, checkout): name for name in paths}
    coverage = {}
    outputs = set()
    for label, target in graph.items():
        if (target.get('type') != 'action'
                or not target.get('script', '').endswith('/compile_java.py')):
            continue
        owned = wanted.keys() & {gn_path(path, checkout) for path in target.get('inputs', [])}
        if not owned:
            continue
        jars = [path for path in target.get('outputs', []) if path.endswith('.jar')]
        if not jars:
            raise RuntimeError(f'Java compile action has no jar output: {label}')
        output = gn_path(jars[0], checkout)
        try:
            ninja_output = output.relative_to(out).as_posix()
        except ValueError:
            raise RuntimeError(f'Java compile output is outside requested build directory: {label}')
        outputs.add(ninja_output)
        for path in owned:
            coverage.setdefault(wanted[path], []).append(label)
    missing = sorted(set(paths) - coverage.keys())
    if missing:
        raise RuntimeError('Missing real javac action for delivered Java source(s):\n' + '\n'.join(missing))
    if not outputs:
        raise RuntimeError('Java compile preflight resolved no actions')
    return sorted(outputs), coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--targets-file', type=Path, required=True)
    parser.add_argument('--scope', choices=('full', 'arc-media'), default='full')
    args = parser.parse_args()
    out = args.out.resolve()
    checkout = out.parent.parent
    manifest = json.loads((ROOT / 'patches/upstream-files.json').read_text())
    paths = sorted(path for path in manifest['modified'] if path.endswith('.java'))
    enabled = True
    if args.scope == 'arc-media':
        flag = subprocess.run(['gn', 'args', str(out),
                               '--list=enable_archium_local_passwords', '--short'],
                              text=True, capture_output=True, check=True, timeout=120)
        enabled = parse_local_passwords_enabled(flag.stdout)
        if enabled:
            raise RuntimeError('Arc/media build requires effective local passwords disabled')
    # Default-toolchain actions match the configured APK/test build. Action inputs
    # contain invoker.source_files in pinned internal_rules.gni:3068.
    result = subprocess.run(['gn', 'desc', str(out), '*', '--format=json',
                             '--default-toolchain'], text=True, capture_output=True,
                            check=True, timeout=180)
    targets, coverage = resolve(json.loads(result.stdout), paths, checkout, out,
                                local_passwords_enabled=enabled)
    args.targets_file.write_text('\n'.join(targets) + '\n')
    (out / 'archium-java-coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
    inactive = sorted(set(paths) & CONDITIONAL_KEY_SOURCES) if not enabled else []
    (out / 'archium-build-scope.json').write_text(json.dumps({
        'scope': args.scope, 'local_passwords_enabled': enabled,
        'inactive_java_sources': inactive,
        'reason': 'effective GN flag excludes archium_key_java' if inactive else None,
    }, indent=2) + '\n')
    print(f'Java preflight coverage: {len(coverage)}/{len(paths) - len(inactive)} active sources, '
          f'{len(inactive)} sources excluded by verified GN flag, '
          f'{len(targets)} real javac actions', flush=True)


if __name__ == '__main__':
    main()
