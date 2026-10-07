#!/usr/bin/env python3
"""Archium test execution gates.

This orchestrator deliberately separates:
  * host gates: repository/pure-Java tests that can execute on the Linux runner;
  * device gates: Android raw native tests and instrumentation that require an explicit device;
  * post-build gates: smoke validation of the produced APK on an explicit device.

It never treats compilation as test execution. Every execution gate is fail-closed.
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

# These GN targets are intentionally Android raw executables (use_raw_android_executable=true).
# They are compile-gated on the host runner but EXECUTED only on an explicit Android device.
ANDROID_NATIVE_TEST_TARGETS = (
    '//chrome/browser/password_manager/android:archium_key_provider_tests',
    '//components/password_manager/core/browser/password_store:archium_login_database_tests',
    '//components/password_manager/core/browser/import:archium_password_import_tests',
    '//chrome/browser/password_manager/android:archium_password_manager_tests',
)


def run(argv: list[str], *, cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print('+ ' + ' '.join(shlex.quote(str(x)) for x in argv), flush=True)
    return subprocess.run(
        [str(x) for x in argv], cwd=cwd, check=True,
        text=True, capture_output=capture,
    )


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise SystemExit(f'{description} not found: {path}')




def resolve_pinned_android_sdk(out_dir: Path) -> tuple[Path, str, str, Path]:
    """Resolve the SDK shipped by the exact Chromium checkout that owns ``out_dir``.

    This intentionally reads Chromium's pinned public SDK declarations instead of
    assuming a GitHub runner SDK path or API level. Missing/malformed inputs fail closed.
    """
    checkout = out_dir.resolve().parent.parent
    config = checkout / 'build' / 'config' / 'android' / 'config.gni'
    require_file(config, 'Pinned Chromium Android config')
    body = config.read_text(encoding='utf-8')
    platform_match = re.search(
        r'^\s*public_android_sdk_platform_version\s*=\s*"([^"]+)"',
        body, re.MULTILINE)
    tools_match = re.search(
        r'^\s*public_android_sdk_build_tools_version\s*=\s*"([^"]+)"',
        body, re.MULTILINE)
    if not platform_match or not tools_match:
        raise SystemExit('Unable to resolve pinned Chromium Android SDK/build-tools versions')
    platform_version = platform_match.group(1)
    build_tools_version = tools_match.group(1)
    platform_dir_name = platform_version
    sdk_root = checkout / 'third_party' / 'android_sdk' / 'public'
    android_jar = sdk_root / 'platforms' / f'android-{platform_dir_name}' / 'android.jar'
    build_tools = sdk_root / 'build-tools' / build_tools_version
    require_file(android_jar, 'Pinned Chromium Android platform jar')
    for tool in ('aapt2', 'd8', 'apksigner'):
        require_file(build_tools / tool, f'Pinned Chromium Android build tool {tool}')
    return sdk_root, platform_dir_name, build_tools_version, android_jar


def host_gate(android_jar: Path, out_dir: Path) -> None:
    """Execute every Archium gate that is runnable on the Linux CI host."""
    require_file(android_jar, 'Android platform jar')
    run([
        sys.executable,
        str(ROOT / 'scripts/check-arc-preparation.py'),
        '--android-jar', str(android_jar),
    ], cwd=ROOT)
    run([
        sys.executable, '-m', 'unittest', 'discover',
        '-s', str(ROOT / 'tests'), '-p', 'test_*.py',
    ], cwd=ROOT)

    out_dir = out_dir.resolve()
    robolectric_runner = (
        out_dir / 'bin' / 'run_chrome_junit_tests'
    )
    require_file(robolectric_runner, 'Chromium Robolectric runner')
    # Class names and registrations verified in the exact pinned junit/BUILD.gn
    # and toolbar:junit. Each suite executes separately, keeping missing classes visible.
    for test_filter in (
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.'
            'VerticalTabListCoordinatorUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.'
            'TabVerticalViewBinderUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.'
            'VerticalTabRailLayoutUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.NestedLayoutDelegateUnitTest.*',
            'org.chromium.chrome.browser.tasks.tab_management.TabListMediatorUnitTest.*',
            'org.chromium.chrome.browser.toolbar.top.ToolbarTabletUnitTest.*'):
        run([str(robolectric_runner), '-f', test_filter], cwd=out_dir.parent.parent)
    print('ARCHIUM_HOST_EXECUTION_GATE=PASS', flush=True)


def android_test_runner(out_dir: Path, target: str) -> Path:
    """Return Chromium's generated Android gtest launcher for a GN test target.

    testing/test.gni generates <out>/bin/run_<output_name> for Android test()
    targets, including use_raw_android_executable=true. Using that launcher keeps
    deployment, runtime deps, symbolization and device selection in Chromium's
    supported test infrastructure instead of reimplementing adb push logic.
    """
    target_name = target.rsplit(':', 1)[-1]
    runner = out_dir.resolve() / 'bin' / f'run_{target_name}'
    require_file(runner, f'Chromium Android test runner for {target}')
    return runner



def verify_device_runners(out_dir: Path) -> None:
    """Fail closed unless every compile-gated Android test has its Chromium launcher."""
    for target in ANDROID_NATIVE_TEST_TARGETS:
        android_test_runner(out_dir, target)
    print(f'ARCHIUM_DEVICE_RUNNERS_READY={len(ANDROID_NATIVE_TEST_TARGETS)}', flush=True)


def adb(serial: str, *args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return run(['adb', '-s', serial, *args], capture=capture)


def device_gate(out_dir: Path, serial: str) -> None:
    """Execute Android-native + instrumentation tests on an explicitly named device."""
    if not serial.strip():
        raise SystemExit('DEVICE_GATE requires an explicit non-empty ADB serial')
    sdk, platform_version, build_tools_version, _ = resolve_pinned_android_sdk(out_dir)
    adb(serial, 'get-state')
    for target in ANDROID_NATIVE_TEST_TARGETS:
        runner = android_test_runner(out_dir, target)
        # Chromium's generated runner owns deployment and runtime dependencies.
        # Explicit --device prevents accidental sharding across unrelated devices.
        run([str(runner), '--device', serial, '-f', 'Archium*'], cwd=out_dir.parent.parent)

    run([
        sys.executable, str(ROOT / 'scripts/test-android-password-key.py'),
        '--device', serial, '--sdk', str(sdk),
        '--platform-version', platform_version, '--build-tools-version', build_tools_version,
    ], cwd=ROOT)
    run([
        sys.executable, str(ROOT / 'scripts/test-android-window-policy.py'),
        '--device', serial, '--sdk', str(sdk),
        '--platform-version', platform_version, '--build-tools-version', build_tools_version,
    ], cwd=ROOT)
    print('ARCHIUM_ANDROID_DEVICE_GATE=PASS', flush=True)


def post_build_gate(apk: Path, serial: str, package: str) -> None:
    """Automated post-build smoke gate; deeper behavior remains explicit runtime acceptance."""
    require_file(apk, 'Archium APK')
    if not serial.strip():
        raise SystemExit('POST_BUILD_GATE requires an explicit non-empty ADB serial')
    adb(serial, 'get-state')
    # `-r` exercises update-over-existing-install semantics. Signature mismatch must fail closed.
    adb(serial, 'install', '-r', str(apk))
    resolved = adb(
        serial, 'shell', 'cmd', 'package', 'resolve-activity', '--brief',
        '-a', 'android.intent.action.MAIN',
        '-c', 'android.intent.category.LAUNCHER',
        '-p', package,
        capture=True,
    ).stdout.strip()
    if not resolved or 'No activity found' in resolved:
        raise SystemExit(f'Unable to resolve launch activity for {package!r}: {resolved!r}')
    component = resolved.splitlines()[-1].strip()
    start = adb(serial, 'shell', 'am', 'start', '-W', '-n', component, capture=True)
    if 'Error:' in start.stdout or 'Exception' in start.stdout:
        raise SystemExit('Archium startup smoke failed:\n' + start.stdout)
    pid = adb(serial, 'shell', 'pidof', package, capture=True).stdout.strip()
    if not pid:
        raise SystemExit(f'Archium process {package!r} is not running after startup')
    print('ARCHIUM_POST_BUILD_SMOKE_GATE=PASS', flush=True)
    print('NOTE: password/restore/visual acceptance still requires the documented runtime checklist.', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='gate', required=True)

    host = sub.add_parser('host')
    host.add_argument('--android-jar', type=Path, required=True)
    host.add_argument('--out', type=Path, required=True)

    verify = sub.add_parser('verify-device-runners')
    verify.add_argument('--out', type=Path, required=True)

    device = sub.add_parser('device')
    device.add_argument('--out', type=Path, required=True)
    device.add_argument('--device', required=True)

    post = sub.add_parser('post-build')
    post.add_argument('--apk', type=Path, required=True)
    post.add_argument('--device', required=True)
    post.add_argument('--package', default='app.archium.android')

    args = parser.parse_args()
    if args.gate == 'host':
        host_gate(args.android_jar, args.out)
    elif args.gate == 'verify-device-runners':
        verify_device_runners(args.out)
    elif args.gate == 'device':
        device_gate(args.out, args.device)
    elif args.gate == 'post-build':
        post_build_gate(args.apk, args.device, args.package)


if __name__ == '__main__':
    main()
