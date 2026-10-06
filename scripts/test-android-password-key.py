#!/usr/bin/env python3
"""Build a disposable test APK from the actual key class and exercise Android Keystore."""
import argparse
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
    work = ROOT / '.test-build/password-key'
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
    sources = [ROOT / 'tests/android/ArchiumPasswordKeyTest.java']
    production = ROOT / ('chromium/chrome/browser/password_manager/android/java/src/'
                         'org/chromium/chrome/browser/password_manager/ArchiumPasswordKey.java')
    if production.exists():
        sources.append(production)
    run('javac', '-source', '17', '-target', '17', '-cp', android, '-d', classes, *sources)
    jar = work / 'tests.jar'
    run('jar', 'cf', jar, '-C', classes, '.')
    run(tools / 'd8', '--min-api', '29', '--lib', android, '--output', dex, jar)
    apk = work / 'unsigned.apk'
    modern_aapt2 = args.sdk / 'build-tools/37.0.0/aapt2'
    aapt2 = str(modern_aapt2) if modern_aapt2.is_file() else (shutil.which('aapt2') or str(tools / 'aapt2'))
    run(aapt2, 'link', '-I', android, '--manifest', ROOT / 'tests/android/AndroidManifest.xml',
        '-o', apk)
    with zipfile.ZipFile(apk, 'a') as archive:
        archive.write(dex / 'classes.dex', 'classes.dex')
    keystore = work / 'test.keystore'
    if not keystore.exists():
        run('keytool', '-genkeypair', '-keystore', keystore, '-storepass', 'test-only',
            '-keypass', 'test-only', '-alias', 'test', '-keyalg', 'RSA', '-validity', '3650',
            '-dname', 'CN=Archium disposable tests', '-noprompt')
    signed = work / 'keytests.apk'
    run(tools / 'apksigner', 'sign', '--ks', keystore, '--ks-pass', 'pass:test-only',
        '--out', signed, apk)
    run('adb', '-s', args.device, 'install', '-r', signed)
    for phase in ('suite', 'reopen'):
        if phase == 'reopen':
            run('adb', '-s', args.device, 'shell', 'am', 'force-stop', 'app.archium.keytests')
        result = subprocess.run(['adb', '-s', args.device, 'shell', 'am', 'instrument', '-w',
                                 '-e', 'phase', phase,
                                 'app.archium.keytests/app.archium.keytests.ArchiumPasswordKeyTest'],
                                capture_output=True, text=True, check=True)
        print(result.stdout)
        if 'PASS:' not in result.stdout or 'FAIL:' in result.stdout:
            raise SystemExit('Android key test failed')


if __name__ == '__main__':
    main()
