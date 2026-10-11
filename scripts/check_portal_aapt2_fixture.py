#!/usr/bin/env python3
"""AAPT2 integration probe: compile the *actual* approved Portal resources.

Uses the pinned Android SDK on the CI host to create an isolated minimal APK.
This does NOT claim that Chromium compiled or that a physical launcher was run.
"""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import zipfile
import os
import shutil
import re


def load(portal_path):
    spec = importlib.util.spec_from_file_location("portal_probed", portal_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_aapt2_fixture(android_jar, aapt2, *, optimize=False, verify_negative=False, chromium_images=False):
    here = Path(__file__).resolve().parent
    portal = load(here / "integrate-archium-portal.py")
    source = portal.expected_resources()
    with tempfile.TemporaryDirectory(prefix="archium-portal-aapt2-") as tmp:
        root = Path(tmp)
        res = root / "res"
        for original, data in source.items():
            if "/res_base/" in original:
                path = original.split("/res_base/", 1)[1]
            elif "/res_chromium_base/" in original:
                path = original.split("/res_chromium_base/", 1)[1]
            else:
                raise ValueError("Unexpected resource path: " + original)
            target = res / path
            if chromium_images and target.suffix == '.png':
                # Match _ConvertToWebPSingle at the exact Chromium pin.
                # Do not add -exact: it conceals discarded transparent RGB.
                cwebp = os.environ.get('ARCHIUM_TEST_CWEBP') or shutil.which('cwebp')
                if not cwebp:
                    raise FileNotFoundError('Genuine cwebp required for Chromium image fixture')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                converted = target.with_suffix('')
                result = subprocess.run([cwebp, str(target), '-o', str(converted),
                                         '-quiet', '-m', '6', '-q', '100', '-lossless'],
                                        capture_output=True, text=True, timeout=120)
                if result.returncode:
                    raise RuntimeError('cwebp failed: ' + result.stdout + result.stderr)
                data = converted.read_bytes()
                target.unlink()
                target = converted
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest = root / "AndroidManifest.xml"
        manifest.write_text("""<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="app.archium.android">
  <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="36"/>
  <application android:label="Archium" android:icon="@drawable/ic_launcher"
               android:roundIcon="@drawable/ic_launcher_round"/>
</manifest>
""", encoding="utf-8")
        output = root / "compiled.zip"
        def run(*args):
            p = subprocess.run(args, cwd=root, text=True, capture_output=True)
            if p.returncode:
                raise RuntimeError("aapt2 failed: " + repr(args) + "\n"
                                   + p.stdout[-4000:] + p.stderr[-4000:])
            return p.stdout
        run(str(aapt2), "compile", "--dir", str(res), "-o", str(output))
        with zipfile.ZipFile(output) as compiled:
            entries = compiled.namelist()
        if len(entries) != len(source):
            raise ValueError(f"aapt2 compiled {len(entries)} vs {len(source)} Portal assets")
        apk = root / "fixture.apk"
        # Exact link flags from compile_resources.py at the Chromium pin.
        # Resource XML loses namespaces; Android attribute IDs remain intact.
        chromium_link_flags = ('--no-version-vectors', '--no-xml-namespaces')
        run(str(aapt2), "link", "-o", str(apk), "-I", str(android_jar),
            "--manifest", str(manifest), "--auto-add-overlay", *chromium_link_flags,
            str(output))
        if optimize:
            optimized = root / "optimized.apk"
            run(str(aapt2), "optimize", "--shorten-resource-paths", "-o", str(optimized), str(apk))
            apk = optimized
        verifier = load(here / "verify-archium-portal-apk.py")
        result = verifier.inspect(apk, aapt2, "app.archium.android")
        if result["status"] != "PASS":
            raise AssertionError("AAPT2 fixture verification did not PASS")
        if verify_negative:
            manifest.write_text(manifest.read_text().replace(
                'android:icon="@drawable/ic_launcher"', 'android:icon="@mipmap/app_icon"'))
            poisoned = root / 'poisoned.apk'
            run(str(aapt2), "link", "-o", str(poisoned), "-I", str(android_jar),
                "--manifest", str(manifest), "--auto-add-overlay", *chromium_link_flags, str(output))
            try:
                verifier.inspect(poisoned, aapt2, "app.archium.android")
            except ValueError as error:
                if 'native adaptive icon alias' not in str(error):
                    raise
            else:
                raise AssertionError('Foreign manifest icon must be rejected')
            if not chromium_images:
                # The vector is identical in PNG/WebP runs; exercise real AAPT2
                # negative manifests once, without duplicating these six links.
                manifest.write_text(manifest.read_text().replace(
                    'android:icon="@mipmap/app_icon"', 'android:icon="@drawable/ic_launcher"'))
                vector = res / 'drawable/themed_app_icon.xml'
                approved = vector.read_text()
                mutations = {
                    'path': re.sub(r'android:pathData="[^"]*"',
                                   'android:pathData="M 177 760 L 0 0 Z"', approved),
                    'scale': approved.replace('android:scaleX="0.65"', 'android:scaleX="1"'),
                    'translation': approved.replace('android:translateX="179.2"', 'android:translateX="0"'),
                    'viewport': approved.replace('android:viewportWidth="1024"', 'android:viewportWidth="512"'),
                    'fill': approved.replace('#000000', '#00FF00'),
                    'extra': approved.replace('</group>', '<path android:fillColor="#000000" '
                                              'android:pathData="M 177 760 L 0 0 Z"/></group>'),
                }
                for name, changed in mutations.items():
                    if changed == approved:
                        raise AssertionError('Vector negative mutation did not apply: ' + name)
                    vector.write_text(changed)
                    poisoned_resources = root / f'vector-{name}.zip'
                    run(str(aapt2), 'compile', '--dir', str(res), '-o', str(poisoned_resources))
                    poisoned_apk = root / f'vector-{name}.apk'
                    run(str(aapt2), 'link', '-o', str(poisoned_apk), '-I', str(android_jar),
                        '--manifest', str(manifest), '--auto-add-overlay', *chromium_link_flags,
                        str(poisoned_resources))
                    try:
                        verifier.inspect(poisoned_apk, aapt2, 'app.archium.android')
                    except ValueError as error:
                        if 'Themed glyph' not in str(error):
                            raise
                    else:
                        raise AssertionError('Altered compiled themed vector accepted: ' + name)
                vector.write_text(approved)
        print("ARCHIUM_PORTAL_AAPT2_FIXTURE=PASS"
              " compiled_resources=" + str(len(entries))
              + " scope=isolated-real-aapt2-not-Chromium")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android-jar", required=True, type=Path)
    parser.add_argument("--aapt2", required=True, type=Path)
    args = parser.parse_args()
    for path in (args.android_jar, args.aapt2):
        if not path.is_file():
            raise FileNotFoundError(path)
    run_aapt2_fixture(args.android_jar, args.aapt2)


if __name__ == "__main__":
    main()
