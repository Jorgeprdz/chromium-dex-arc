#!/usr/bin/env python3
"""Build a disposable window-policy test APK against pinned AndroidX constants and Android APIs."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', required=True, help='Explicit ADB serial; do not infer an emulator from its name')
    parser.add_argument('--sdk', type=Path, default=Path('/opt/android-sdk'))
    args = parser.parse_args()
    work = ROOT / '.test-build/window-policy'
    work.mkdir(parents=True, exist_ok=True)
    classes = work / 'classes'
    if classes.exists():
        shutil.rmtree(classes)
    classes.mkdir()
    dex = work / 'dex'
    if dex.exists():
        shutil.rmtree(dex)
    dex.mkdir()
    tools = args.sdk / 'build-tools/36.0.0'
    android = args.sdk / 'platforms/android-36/android.jar'
    sources = [ROOT / 'tests/android/window/ArchiumWindowMetricsTest.java']
    module = ROOT / ('chromium/chrome/browser/desktop_policy/android/java/src/'
                     'org/chromium/chrome/browser/desktop_policy')
    sources += list(module.glob('*.java')) if module.exists() else []
    spec = importlib.util.spec_from_file_location('window_core', ROOT / 'scripts/fetch-window-core.py')
    window_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(window_module)
    window_core = window_module.ensure_jar()
    run('javac', '-source', '17', '-target', '17', '-cp', str(android) + ':' + str(window_core),
        '-d', classes, *sources)
    jar = work / 'tests.jar'
    run('jar', 'cf', jar, '-C', classes, '.')
    run(tools / 'd8', '--min-api', '29', '--lib', android, '--output', dex, jar)
    apk = work / 'unsigned.apk'
    modern_aapt2 = args.sdk / 'build-tools/37.0.0/aapt2'
    aapt2 = str(modern_aapt2) if modern_aapt2.is_file() else (shutil.which('aapt2') or str(tools / 'aapt2'))
    run(aapt2, 'link', '-I', android, '--manifest', ROOT / 'tests/android/window/AndroidManifest.xml',
        '-o', apk)
    with zipfile.ZipFile(apk, 'a') as archive:
        archive.write(dex / 'classes.dex', 'classes.dex')
    keystore = work / 'test.keystore'
    if not keystore.exists():
        run('keytool', '-genkeypair', '-keystore', keystore, '-storepass', 'test-only',
            '-keypass', 'test-only', '-alias', 'test', '-keyalg', 'RSA', '-validity', '3650',
            '-dname', 'CN=Archium disposable tests', '-noprompt')
    signed = work / 'windowtests.apk'
    run(tools / 'apksigner', 'sign', '--ks', keystore, '--ks-pass', 'pass:test-only',
        '--out', signed, apk)
    run('adb', '-s', args.device, 'install', '-r', signed)
    result = subprocess.run(['adb', '-s', args.device, 'shell', 'am', 'instrument', '-w',
                             'app.archium.windowtests/app.archium.windowtests.ArchiumWindowMetricsTest'],
                            capture_output=True, text=True, check=True)
    print(result.stdout)
    if 'PASS:' not in result.stdout or 'FAIL:' in result.stdout:
        raise SystemExit('Android window-policy test failed')



if __name__ == '__main__':
    main()
