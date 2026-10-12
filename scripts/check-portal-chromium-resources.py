#!/usr/bin/env python3
"""Verify Chromium's genuine resource compile/link output before native fanout.

Requires the pinned, restored Chromium tree and its actual GN resource target.
The minimal Portal AAPT2 fixture does not satisfy this gate.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from archium_portal_content_gate import resource_entry
import importlib.util

PIN = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'
TARGET = '//chrome/android:chrome_public_apk__compile_resources'
OPTIMIZE_TARGET = '//chrome/android:chrome_public_apk__optimize_resources'


def optimization_args(action, archive, aapt2, destination):
    """Use the actual GN optimizer args, replacing only isolated probe outputs.

    R.txt and resource configs remain exactly those of the APK action. Never
    overwrite its Siso/Ninja-tracked outputs or require its final-dex dependency.
    """
    if not action.get('script', '').endswith('/build/android/gyp/optimize_resources.py'):
        raise ValueError('Unexpected Chromium resource optimizer script')
    replacements = {
        '--input-path': str(archive), '--aapt2-path': str(aapt2),
        '--optimized-output-path': str(destination / 'portal-optimized.ap_'),
        '--resources-path-map-out-path': str(destination / 'portal-path-map.txt'),
    }
    args = list(action.get('args', []))
    seen = set()
    index = 0
    while index < len(args):
        key = args[index].split('=', 1)[0]
        if key in replacements:
            if key in seen:
                raise ValueError('Duplicate Chromium optimizer argument: ' + key)
            seen.add(key)
            if '=' in args[index]:
                args[index] = key + '=' + replacements[key]
            else:
                if index + 1 >= len(args):
                    raise ValueError('Missing Chromium optimizer argument: ' + key)
                args[index + 1] = replacements[key]
                index += 1
        index += 1
    required = {'--input-path', '--aapt2-path', '--optimized-output-path'}
    if not required <= seen or not any(a.startswith('--resources-config-paths') for a in args) \
            or '--r-text-in' not in args:
        raise ValueError('Incomplete real Chromium resource optimizer arguments')
    return args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--aapt2', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    checkout = out.parent.parent
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != PIN:
        raise ValueError('Resource gate requires exact pinned Chromium checkout')
    output = subprocess.check_output(['gn', 'desc', str(out), TARGET, 'outputs'], cwd=checkout, text=True)
    archives = []
    for line in output.splitlines():
        value = line.strip()
        if not value.endswith('.ap_') or value.endswith('.proto.ap_'):
            continue
        path = (checkout / value[2:]) if value.startswith('//') else (out / value)
        path = path.resolve()
        if not path.is_relative_to(out) or not path.is_file() or path.stat().st_size == 0:
            raise ValueError('Missing or unsafe real resource output: ' + value)
        archives.append(path)
    if len(archives) != 1:
        raise ValueError('Expected exactly one real GN resource archive, got ' + str(archives))
    inventory = []
    names = ('ic_launcher', 'ic_launcher_round', 'layered_app_icon',
             'layered_app_icon_background', 'layered_app_icon_foreground', 'app_icon')
    for path in sorted((checkout / 'chrome/android/java').glob('res*/**/*')):
        if not path.is_file():
            continue
        if path.stem in names:
            inventory.append(str(path.relative_to(checkout)))
        elif path.parent.name.startswith('values') and path.suffix == '.xml':
            for item in ET.parse(path).getroot():
                if item.get('name') in names:
                    inventory.append(str(path.relative_to(checkout)) + '#' + item.get('name'))
    manifest = out / 'gen/chrome/android/chrome_public_apk/AndroidManifest.merged.xml'
    if not manifest.is_file():
        raise ValueError('Actual merged Chromium manifest missing')
    application = ET.parse(manifest).getroot().find('application')
    android = '{http://schemas.android.com/apk/res/android}'
    if application is None or application.get(android + 'icon') != '@drawable/ic_launcher' \
            or application.get(android + 'roundIcon') != '@drawable/ic_launcher_round':
        raise ValueError('Actual Chromium manifest shadows Portal aliases')
    spec = importlib.util.spec_from_file_location('portal_apk', Path(__file__).with_name('verify-archium-portal-apk.py'))
    verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
    result = verifier.inspect(archives[0], args.aapt2, 'app.archium.android')
    # Release additionally collapses names and shortens paths. Run the pinned
    # optimizer with the actual GN args before Java/native fanout. This does
    # not cover R8 resource shrinking; final APK verification remains mandatory.
    graph = json.loads(subprocess.check_output(
        ['gn', 'desc', str(out), OPTIMIZE_TARGET, '--format=json'], cwd=checkout, text=True))
    if len(graph) != 1:
        raise ValueError('Expected exactly one genuine Chromium resource optimizer action')
    action = next(iter(graph.values()))
    script = checkout / 'build/android/gyp/optimize_resources.py'
    if not script.is_file():
        raise ValueError('Pinned Chromium optimizer missing')
    with tempfile.TemporaryDirectory(prefix='archium-portal-optimize-', dir=out) as directory:
        destination = Path(directory)
        command = optimization_args(action, archives[0], args.aapt2.resolve(), destination)
        subprocess.run([sys.executable, str(script), *command], cwd=out, check=True)
        optimized = verifier.inspect(destination / 'portal-optimized.ap_', args.aapt2, 'app.archium.android')
        result['release_optimization'] = {
            'status': optimized['status'], 'target': OPTIMIZE_TARGET,
            'scope': 'pinned optimizer + actual GN R.txt/configs, before R8 shrinking',
        }
    result.update(scope='Chromium real AAPT2 compile/link, GN target and merged manifest',
                  chromium_pin=revision, target=TARGET, resource_inventory=inventory,
                  archive=str(archives[0]), manifest=str(manifest))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('AAPT2_REAL_RESOURCES=PASS scope=Chromium_merged_manifest_resource_target_and_release_optimization')


if __name__ == '__main__':
    main()
