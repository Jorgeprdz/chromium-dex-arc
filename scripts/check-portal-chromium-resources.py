#!/usr/bin/env python3
"""Verify Chromium's genuine resource compile/link output before native fanout.

Requires the pinned, restored Chromium tree and its actual GN resource target.
The minimal Portal AAPT2 fixture does not satisfy this gate.
"""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from archium_portal_content_gate import resource_entry
import importlib.util

PIN = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'
TARGET = '//chrome/android:chrome_public_apk__compile_resources'


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
    result.update(scope='Chromium real AAPT2 compile/link, GN target and merged manifest',
                  chromium_pin=revision, target=TARGET, resource_inventory=inventory,
                  archive=str(archives[0]), manifest=str(manifest))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('AAPT2_REAL_RESOURCES=PASS scope=Chromium_merged_manifest_resource_target')


if __name__ == '__main__':
    main()
