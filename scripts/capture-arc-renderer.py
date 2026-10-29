#!/usr/bin/env python3
"""Read-only F06 evidence on the existing device. Output may contain private data: never publish raw.
Run on a synthetic test page before/after resize/click; correlate UTC and device uptime.
No GPU settings, cache clearing, page scale, profile changes or app restarts.
"""
import argparse, datetime, json, pathlib, subprocess, time

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial', required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--samples', type=int, default=5)
    p.add_argument('--interval', type=float, default=1)
    p.add_argument('--screenshot', action='store_true', help='Private PNG per sample; use synthetic tabs')
    a = p.parse_args()
    if not 1 <= a.samples <= 30 or not .5 <= a.interval <= 10:
        p.error('Use 1..30 samples at .5..10 seconds')
    a.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    adb = ['adb', '-s', a.serial]
    for i in range(a.samples):
        stem = a.output / f'{i:02}'
        metadata = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'monotonic_ns': time.monotonic_ns(), 'sample': i, 'status': 'PENDING_REPRO'}
        for label, cmd in {
            'uptime': ['shell', 'cat', '/proc/uptime'],
            'window': ['shell', 'dumpsys', 'window', 'windows'],
            'surface': ['shell', 'dumpsys', 'SurfaceFlinger'],
            'graphics': ['shell', 'dumpsys', 'gfxinfo', 'app.archium.android', 'framestats'],
            'display': ['shell', 'dumpsys', 'display'],
            'renderer': ['logcat', '-d', '-t', '300', '-v', 'epoch',
                         'chromium:I', 'cr_CompositorView:I', 'SurfaceView:I', '*:S'],
        }.items():
            result = subprocess.run(adb + cmd, capture_output=True, timeout=20)
            stem.with_suffix('.' + label + '.txt').write_bytes(result.stdout + result.stderr)
            metadata[label + '_exit'] = result.returncode
        if a.screenshot:
            result = subprocess.run(adb + ['exec-out', 'screencap', '-p'], capture_output=True, timeout=20)
            if result.returncode == 0: stem.with_suffix('.png').write_bytes(result.stdout)
        stem.with_suffix('.json').write_text(json.dumps(metadata, indent=2) + '\n')
        if i + 1 < a.samples: time.sleep(a.interval)
    print('CAPTURED_PRIVATE_EVIDENCE; F06=PENDING_REPRO (capture alone is not acceptance)')
if __name__ == '__main__': main()
