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
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--platform-version', required=True)
    parser.add_argument('--build-tools-version', required=True)
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
    tools = args.sdk / 'build-tools' / args.build_tools_version
    android = args.sdk / 'platforms' / f'android-{args.platform_version}' / 'android.jar'
    if not android.is_file():
        raise SystemExit(f'Pinned Android platform jar missing: {android}')
    for tool in ('aapt2', 'd8', 'apksigner'):
        if not (tools / tool).is_file():
            raise SystemExit(f'Pinned Android build tool missing: {tools / tool}')
    generated = work / 'generated'
    generated.mkdir(exist_ok=True)
    resource = work / 'resources.zip'
    aapt2 = str(tools / 'aapt2')
    run(aapt2, 'compile', '--dir', ROOT / 'chromium/chrome/android/java/res', '-o', resource)
    apk = work / 'unsigned.apk'
    run(aapt2, 'link', '-I', android, '--manifest', ROOT / 'tests/android/window/AndroidManifest.xml',
        '--custom-package', 'org.chromium.chrome', '--java', generated, '-o', apk, resource)
    sources = list((ROOT / 'tests/android/window').glob('*.java'))
    module = ROOT / ('chromium/chrome/browser/desktop_policy/android/java/src/'
                     'org/chromium/chrome/browser/desktop_policy')
    sources += list(module.glob('*.java')) if module.exists() else []
    appearance = ROOT / ('chromium/chrome/browser/ui/vertical_tabs/android/java/src/'
                         'org/chromium/chrome/browser/ui/vertical_tabs')
    sources += [appearance / 'ArcDesktopAppearance.java', appearance / 'ArcDesktopPolicy.java']
    sources += list(generated.rglob('*.java'))
    dialog = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcAppearanceDialog.java'
    if dialog.exists():
        sources.append(dialog)
    arc = dialog.parent
    for name in ('ArcSidebarState', 'ArcSidebarStore', 'ArcTabActions',
                 'ArcCollectionsController', 'ArcCollectionsView'):
        source = arc / (name + '.java')
        if source.exists():
            sources.append(source)
    passwords = ROOT / 'chromium/chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager'
    for name in ('ArchiumPasswordCsv', 'ArchiumPasswordManagerBridge'):
        source = passwords / (name + '.java')
        if source.exists(): sources.append(source)
    protocol_stubs = {
        'org/chromium/chrome/browser/profiles/Profile.java': 'package org.chromium.chrome.browser.profiles; public class Profile {}',
        'org/jni_zero/CalledByNative.java': 'package org.jni_zero; public @interface CalledByNative {}',
        'org/jni_zero/NativeMethods.java': 'package org.jni_zero; public @interface NativeMethods {}',
        'org/jni_zero/JniType.java': 'package org.jni_zero; public @interface JniType { String value(); }',
        'org/chromium/build/annotations/NullMarked.java': 'package org.chromium.build.annotations; public @interface NullMarked {}',
        'org/chromium/build/annotations/Nullable.java': 'package org.chromium.build.annotations; @java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.FIELD,java.lang.annotation.ElementType.PARAMETER}) public @interface Nullable {}',
    }
    for name, body in protocol_stubs.items():
        source = work / 'stubs' / name
        source.parent.mkdir(parents=True, exist_ok=True); source.write_text(body); sources.append(source)
    observer = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopWindowObserver.java'
    sources.append(observer)
    lifecycle = work / 'stubs/org/chromium/chrome/browser/lifecycle'
    lifecycle.mkdir(parents=True, exist_ok=True)
    for name, body in {
        'ConfigurationChangedObserver': 'public interface ConfigurationChangedObserver { void onConfigurationChanged(android.content.res.Configuration c); }',
        'ActivityLifecycleDispatcher': 'public interface ActivityLifecycleDispatcher { void register(ConfigurationChangedObserver o); void unregister(ConfigurationChangedObserver o); }',
    }.items():
        source = lifecycle / (name + '.java')
        source.write_text('package org.chromium.chrome.browser.lifecycle;\n' + body + '\n')
        sources.append(source)
    spec = importlib.util.spec_from_file_location('window_core', ROOT / 'scripts/fetch-window-core.py')
    window_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(window_module)
    window_core = window_module.ensure_jar()
    run('javac', '-source', '17', '-target', '17', '-cp', str(android) + ':' + str(window_core),
        '-d', classes, *sources)
    jar = work / 'tests.jar'
    run('jar', 'cf', jar, '-C', classes, '.')
    run(tools / 'd8', '--min-api', '29', '--lib', android, '--output', dex, jar)
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
    for phase in ('suite', 'reopen'):
        if phase == 'reopen':
            run('adb', '-s', args.device, 'shell', 'am', 'force-stop', 'app.archium.windowtests')
        result = subprocess.run(['adb', '-s', args.device, 'shell', 'am', 'instrument', '-w',
                                 '-e', 'phase', phase,
                                 'app.archium.windowtests/app.archium.windowtests.ArchiumWindowMetricsTest'],
                                capture_output=True, text=True, check=True)
        print(result.stdout)
        if 'PASS:' not in result.stdout or 'FAIL:' in result.stdout:
            raise SystemExit('Android window-policy test failed')



if __name__ == '__main__':
    main()
