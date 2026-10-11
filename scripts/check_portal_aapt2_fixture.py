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


def load(portal_path):
    spec = importlib.util.spec_from_file_location("portal_probed", portal_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_aapt2_fixture(android_jar, aapt2, *, optimize=False, verify_negative=False):
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
        run(str(aapt2), "link", "-o", str(apk), "-I", str(android_jar),
            "--manifest", str(manifest), "--auto-add-overlay",
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
                "--manifest", str(manifest), "--auto-add-overlay", str(output))
            try:
                verifier.inspect(poisoned, aapt2, "app.archium.android")
            except ValueError as error:
                if 'native adaptive icon alias' not in str(error):
                    raise
            else:
                raise AssertionError('Foreign manifest icon must be rejected')
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
