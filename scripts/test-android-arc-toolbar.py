#!/usr/bin/env python3
"""Run the production rectangle method in a disposable Android instrumentation APK.

This validates the method's ViewRoot/coordinate contract, not the complete Arc UI.
"""
import argparse
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import TOOLBAR, method_body, toolbar_body


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--platform-version', required=True)
    parser.add_argument('--build-tools-version', required=True)
    parser.add_argument('--aapt2-wrapper', default='', help='Optional host emulator command prefix')
    parser.add_argument('--original', action='store_true', help='Reproduce with pinned pre-fix method')
    args = parser.parse_args()
    work = ROOT / '.test-build/arc-toolbar-runtime'
    work.mkdir(parents=True, exist_ok=True)
    classes, dex = work / 'classes', work / 'dex'
    for directory in (classes, dex):
        if directory.exists(): shutil.rmtree(directory)
        directory.mkdir()
    tools = args.sdk / 'build-tools' / args.build_tools_version
    android = args.sdk / 'platforms' / ('android-' + args.platform_version) / 'android.jar'
    body = toolbar_body()
    if args.original:
        body = method_body((ROOT / '.source-reference' / TOOLBAR).read_text(),
                           r'void getLocationBarContentRect\(Rect outRect\)')
    source = work / 'ArcToolbarGeometryTest.java'
    source.write_text((ROOT / 'tests/android/toolbar/ArcToolbarGeometryTest.java.in').read_text()
                      .replace('__TOOLBAR_BODY__', body))
    run('javac', '-source', '17', '-target', '17', '-cp', android, '-d', classes, source)
    jar = work / 'probe.jar'
    run('jar', 'cf', jar, '-C', classes, '.')
    run(tools / 'd8', '--min-api', '29', '--lib', android, '--output', dex, jar)
    apk = work / 'unsigned.apk'
    run(*shlex.split(args.aapt2_wrapper), tools / 'aapt2', 'link', '-I', android,
        '--manifest', ROOT / 'tests/android/toolbar/AndroidManifest.xml', '-o', apk)
    with zipfile.ZipFile(apk, 'a') as archive:
        archive.write(dex / 'classes.dex', 'classes.dex')
    key = work / 'test.keystore'
    if not key.exists():
        run('keytool', '-genkeypair', '-keystore', key, '-storepass', 'test-only',
            '-keypass', 'test-only', '-alias', 'test', '-keyalg', 'RSA', '-validity', '3650',
            '-dname', 'CN=Archium disposable geometry probe', '-noprompt')
    signed = work / 'toolbar-probe.apk'
    run(tools / 'apksigner', 'sign', '--ks', key, '--ks-pass', 'pass:test-only',
        '--out', signed, apk)
    run('adb', '-s', args.device, 'install', '-r', signed)
    result = subprocess.run(['adb', '-s', args.device, 'shell', 'am', 'instrument', '-w',
                             'app.archium.toolbarprobe/app.archium.toolbarprobe.ArcToolbarGeometryTest'],
                            capture_output=True, text=True, check=True, timeout=60)
    print(result.stdout)
    if 'PASS:' not in result.stdout or 'FAIL:' in result.stdout:
        raise SystemExit('Real Android toolbar geometry probe failed')


if __name__ == '__main__':
    main()
