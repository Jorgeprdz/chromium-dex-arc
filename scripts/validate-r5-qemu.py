#!/usr/bin/env python3
"""Validate current-run ARM64 APK provenance and report honest QEMU coverage.

Never selects an attached device. Native ARM64/KVM + existing API36 ARM64 AVD
can run a bounded launch smoke; visual matrix cases require observed evidence.
No x86 APK or system-image fallback is permitted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time
import zipfile

APK_NAME = 'Archium-for-Android-arm64.apk'
PACKAGE = 'app.archium.android'
CASES = [
    ('launch', 'Install, launch, activity foreground and screenshot'),
    ('local_fixture', 'Open deterministic local compositor fixture'),
    ('scroll', 'Five scroll cycles; inspect image/text/canvas tiles'),
    ('dialogs', 'Alert, confirm, prompt, HTML dialog; scrim/focus restoration'),
    ('keyboard', 'Keyboard and pointer/touch input; focus restoration'),
    ('window_resize', 'Narrow/maximized resize, sidebar collapse/expand'),
    ('lifecycle', 'Minimize/restore, switch tabs, lock/unlock'),
    ('incognito', 'Repeat fixture and viewport transitions in incognito'),
    ('renderer', 'Inspect compositor/renderer output and crash diagnostics'),
    ('high_resolution', 'Continuous scroll with high-resolution images'),
    ('dynamic_lists', 'Long lists and dynamic page updates'),
    ('sticky_fixed', 'CSS sticky and fixed elements during scroll'),
    ('transforms', 'CSS transforms and animations'),
    ('canvas_acceleration', 'Canvas and accelerated content'),
    ('resize_scrolling', 'Resize the window while scrolling'),
    ('surface_recovery', 'Suspend and restore the rendering surface'),
    ('visual_artifacts', 'Inspect black blocks, tearing and duplicated content'),
    ('native_dialog', 'Native Chromium dialogs and actions'),
    ('scrim_z_order', 'Scrim visibility and window stacking order'),
    ('dialog_tab_switch', 'Switch tabs while a dialog is open'),
    ('hover_selection', 'Sidebar hover, focus and selected tab'),
    ('omnibox', 'Omnibox focus, typing, navigation and cancellation'),
    ('navigation_controls', 'Native back, forward and reload controls'),
    ('footer_clipping', 'Footer geometry and residual lower clipping'),
    ('tab_persistence', 'Tab and navigation-state persistence'),
    ('viewport_scaling', 'Viewport CSS dimensions, device scale and zoom'),
    ('multi_tab', 'Open and close multiple tabs without losing state'),
    ('history', 'Back and forward navigation preserves content'),
    ('background_foreground', 'Background and foreground lifecycle'),
    ('activity_recreation', 'Activity recreation with retained state'),
    ('orientation_density', 'Orientation, density and display-size changes'),
    ('controlled_memory', 'Controlled memory pressure and recovery'),
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_identity(root, source_sha, run_id):
    report = json.loads((root / 'BUILD_REPORT.json').read_text())
    if report.get('source_sha') != source_sha or str(report.get('run_id')) != str(run_id):
        raise ValueError('BUILD_REPORT source_sha/run_id differs from current workflow run')
    apk = root / APK_NAME
    actual = sha256(apk)
    entries = [line.split() for line in (root / 'SHA256SUMS').read_text().splitlines() if line.strip()]
    if len(entries) != 1 or len(entries[0]) != 2 or entries[0][1].lstrip('*') != APK_NAME or entries[0][0] != actual:
        raise ValueError('SHA256SUMS does not match exact current-run APK bytes')
    with zipfile.ZipFile(apk) as archive:
        abis = {name.split('/')[1] for name in archive.namelist() if re.match(r'^lib/[^/]+/.+\.so$', name)}
    if abis != {'arm64-v8a'}:
        raise ValueError(f'APK native ABI must exclusively be arm64-v8a; observed {sorted(abis)}')
    return {'source_sha': source_sha, 'run_id': str(run_id), 'apk_sha256': actual}


def command(argv, timeout=30):
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    output = result.stdout.decode(errors='replace')
    if result.returncode:
        raise ValueError(f'Command failed ({result.returncode}): {argv!r}\n{output[-6000:]}')
    return output


def tool(name):
    found = shutil.which(name)
    if found:
        return found
    sdk = Path(os.environ.get('ANDROID_SDK_ROOT', os.environ.get('ANDROID_HOME', '/opt/android-sdk')))
    candidates = list((sdk / 'build-tools').glob(f'*/{name}'))
    candidates += [sdk / 'emulator' / name, sdk / 'platform-tools' / name]
    return str(next((path for path in sorted(candidates, reverse=True) if path.is_file()), '')) or None


def package_identity(badging):
    fields = dict(re.findall(r"(name|versionCode|versionName)='([^']*)'", badging.splitlines()[0]))
    if set(fields) != {'name', 'versionCode', 'versionName'}:
        raise ValueError('Incomplete package identity')
    return fields


def verify_android(root, output):
    aapt, signer = tool('aapt2'), tool('apksigner')
    if not aapt or not signer:
        raise ValueError('aapt2 and apksigner required for independent APK verification')
    badging = command([aapt, 'dump', 'badging', str(root / APK_NAME)])
    signature = command([signer, 'verify', '--verbose', '--print-certs', str(root / APK_NAME)])
    (output / 'actual-badging.txt').write_text(badging)
    (output / 'actual-signature.txt').write_text(signature)
    for label, observed in [('APK_BADGING.txt', badging), ('SIGNATURE.txt', signature)]:
        expected = (root / label).read_text()
        if label == 'APK_BADGING.txt':
            for content in [expected, observed]:
                if not re.search(r"^package: name='app\.archium\.android' ", content, re.M) or not re.search(r"^native-code: 'arm64-v8a'\s*$", content, re.M):
                    raise ValueError('APK package or badging ABI mismatch')
            if package_identity(expected) != package_identity(observed):
                raise ValueError('Package/version metadata differs from native build artifact')
        else:
            certs = lambda content: set(re.findall(r'certificate SHA-256 digest: ([0-9a-fA-F]{64})', content))
            if not certs(expected) or certs(expected) != certs(observed):
                raise ValueError('APK signing certificate differs from native build artifact')
    return {'package': PACKAGE, 'abi': 'arm64-v8a', 'signature': 'VERIFIED', 'package_version': badging.splitlines()[0]}


def capable_avd(machine, kvm, avds):
    if machine not in ('aarch64', 'arm64') or not kvm:
        return None
    return next((item['name'] for item in avds if item['abi'] == 'arm64-v8a' and item['api'] == '36'), None)


def matrix_status(cases):
    if any(case['status'] == 'FAIL' for case in cases):
        return 'FAIL'
    complete = {case.get('id') for case in cases} == {key for key, _ in CASES}
    return 'QEMU_TESTS_PASS' if complete and all(case['status'] == 'PASS' for case in cases) else 'NOT_TESTED'


def probe():
    avds = []
    home = Path(os.environ.get('ANDROID_AVD_HOME', str(Path.home() / '.android/avd')))
    for config in home.glob('*.avd/config.ini'):
        props = dict(line.split('=', 1) for line in config.read_text().splitlines() if '=' in line)
        image = props.get('image.sysdir.1', '')
        api = re.search(r'android-(\d+)', image)
        avds.append({'name': config.parent.stem, 'abi': props.get('abi.type', ''), 'api': api.group(1) if api else 'unknown', 'config': str(config)})
    emulator = tool('emulator')
    environment = {'host_arch': platform.machine(), 'host': platform.platform(), 'kvm_accessible': os.access('/dev/kvm', os.R_OK | os.W_OK), 'emulator': emulator, 'emulator_version': 'UNAVAILABLE', 'qemu_system_aarch64': tool('qemu-system-aarch64'), 'avds': avds, 'api': 'NOT_EXECUTED', 'abi': 'NOT_EXECUTED', 'renderer': 'NOT_EXECUTED', 'display': 'NOT_EXECUTED'}
    environment['acceleration_usable'] = False
    if emulator:
        try:
            environment['emulator_version'] = command([emulator, '-version']).strip()
            environment['accel_check'] = command([emulator, '-accel-check']).strip()
            environment['acceleration_usable'] = True
        except (ValueError, OSError, subprocess.TimeoutExpired) as error:
            environment['probe_error'] = str(error)
    return environment


def smoke(root, output, environment, avd, cases):
    adb = tool('adb')
    if not adb:
        raise ValueError('adb unavailable for isolated QEMU serial')
    serial = 'emulator-5580'
    if any(line.split()[0] == serial for line in command([adb, 'devices']).splitlines()[1:] if line.split()):
        raise ValueError('Reserved QEMU serial already exists; refusing to target an existing device')
    def bridge(*args, timeout=30):
        return command([adb, '-s', serial, *args], timeout)
    # Only the emulator started here is addressed, never an attached Galaxy/USB device.
    log = (output / 'emulator.log').open('wb')
    process = subprocess.Popen([environment['emulator'], '-avd', avd, '-port', '5580', '-no-window', '-no-audio', '-no-snapshot', '-data', str(output / 'qemu-userdata.img'), '-cache', str(output / 'qemu-cache.img'), '-gpu', 'swiftshader', '-accel', 'on'], stdout=log, stderr=subprocess.STDOUT)
    try:
        bridge('wait-for-device', timeout=180)
        deadline = time.monotonic() + 180
        while bridge('shell', 'getprop', 'sys.boot_completed').strip() != '1':
            if time.monotonic() > deadline or process.poll() is not None:
                raise ValueError('QEMU boot timeout; see emulator.log')
            time.sleep(2)
        if bridge('shell', 'getprop', 'ro.kernel.qemu').strip() != '1':
            raise ValueError('Selected serial is not QEMU; refusing Android execution')
        environment.update({'avd': avd, 'api': bridge('shell', 'getprop', 'ro.build.version.sdk').strip(), 'abi': bridge('shell', 'getprop', 'ro.product.cpu.abi').strip(), 'renderer': bridge('shell', 'dumpsys', 'SurfaceFlinger'), 'display': bridge('shell', 'wm', 'size') + bridge('shell', 'wm', 'density')})
        if environment['api'] != '36' or environment['abi'] != 'arm64-v8a':
            raise ValueError('Running QEMU guest differs from required API36/ARM64 configuration')
        bridge('install', '-r', str(root / APK_NAME), timeout=120)
        bridge('shell', 'monkey', '-p', PACKAGE, '-c', 'android.intent.category.LAUNCHER', '1')
        time.sleep(5)
        activity = bridge('shell', 'dumpsys', 'activity', 'activities')
        (output / 'activities.txt').write_text(activity)
        (output / 'logcat.txt').write_text(bridge('logcat', '-d', '-v', 'threadtime', timeout=45))
        screenshot = subprocess.run([adb, '-s', serial, 'exec-out', 'screencap', '-p'], capture_output=True, timeout=30, check=True).stdout
        if not screenshot.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('QEMU screenshot is missing/invalid')
        (output / 'launch.png').write_bytes(screenshot)
        if not any(PACKAGE in line and ('mResumedActivity' in line or 'topResumedActivity' in line) for line in activity.splitlines()):
            raise ValueError('Archium did not become the resumed QEMU activity')
        cases[0].update(status='PASS', evidence='activities.txt, launch.png, logcat.txt; launch only, no visual correctness assertion')
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        log.close()


def write_report(receipt, output):
    (output / 'qemu-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    lines = ['# Archium R5 QEMU validation', '', f"Status: **{receipt['status']}**", '', 'Hardware-specific validation: **PENDING_DEVICE_VALIDATION** (Galaxy GPU, Samsung Internet comparison, physical input and phone/DeX transitions).', '', '```json', json.dumps({key: value for key, value in receipt.items() if key != 'cases'}, indent=2), '```', '', '| Case | Status | Evidence / reproduction |', '| --- | --- | --- |']
    for case in receipt['cases']:
        lines.append(f"| {case['description']} | {case['status']} | {case['evidence']} |")
    lines += ['', 'Reproduce: download the same run’s `Archium-for-Android-arm64` artifact, then run', '`python3 scripts/validate-r5-qemu.py --artifact-dir ARTIFACT --source-sha SOURCE_SHA --run-id RUN_ID --output-dir QEMU_OUTPUT`.', '', 'The existing local fixture is `tests/fixtures/rendering/r5-compositor.html`. Fixture, scroll, dialog, keyboard, window/lifecycle and incognito cases remain NOT_TESTED until exercised with observable evidence. Startup and a screenshot cannot establish visual correctness. No screenshot is claimed for a blocked run.', '', 'Infrastructure references: [Android emulator acceleration](https://developer.android.com/studio/run/emulator-acceleration), [emulator release notes](https://developer.android.com/studio/releases/emulator). ARM64 host support depends on the actual emulator/image distribution; absence here does not prove universal impossibility.', '']
    (output / 'R5_QEMU_REPORT.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {'schema_version': 1, 'status': 'FAIL', 'source_sha': args.source_sha, 'run_id': str(args.run_id), 'apk_sha256': None, 'device_validation': 'PENDING_DEVICE_VALIDATION', 'artifact_verification': 'FAIL', 'cases': [{'id': key, 'description': description, 'status': 'NOT_TESTED', 'evidence': 'Not exercised'} for key, description in CASES]}
    try:
        receipt.update(verify_identity(args.artifact_dir, args.source_sha, args.run_id))
        receipt['apk'] = verify_android(args.artifact_dir, args.output_dir)
        receipt['artifact_verification'] = 'PASS'
        receipt['environment'] = probe()
        env = receipt['environment']
        avd = capable_avd(env['host_arch'], env['kvm_accessible'], env['avds'])
        if not avd or not env['emulator'] or not env['acceleration_usable']:
            receipt['status'] = 'QEMU_ABI_BLOCKED'
            receipt['reason'] = 'No usable native ARM64 host + accessible KVM + existing API36 ARM64 AVD/emulator. x86_64 acceleration does not execute ARM64 guests; no x86 substitute or slow unbounded software boot attempted.'
            for case in receipt['cases']:
                case.update(status='BLOCKED', evidence='QEMU_ABI_BLOCKED; no Android execution, logs or screenshots')
        else:
            try:
                smoke(args.artifact_dir, args.output_dir, env, avd, receipt['cases'])
            except Exception as error:
                receipt['cases'][0].update(status='FAIL', evidence=str(error))
                raise
            receipt['status'] = matrix_status(receipt['cases'])
    except Exception as error:
        receipt['status'] = 'FAIL'
        receipt['reason'] = str(error)
    write_report(receipt, args.output_dir)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            stream.write(f"status={receipt['status']}\n")
    print(json.dumps({key: receipt[key] for key in ['status', 'source_sha', 'run_id', 'apk_sha256', 'device_validation']}))
    return 1 if receipt['status'] == 'FAIL' else 0


if __name__ == '__main__':
    raise SystemExit(main())
