#!/usr/bin/env python3
"""Install Archium Portal in Chromium's existing launcher resource slots.

No new package, manifest icon alias, resource target or GN source list is needed:
chrome_base_module_resources already owns these exact mipmap and drawable names.
This is deliberately a binary overlay outside the UTF-8-only Chromium patch.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REVISION = "cfd94726b7b5fb48aedcc32662f2f3fbdbadec35"
ICON_ROOT = ROOT / "assets/branding/archium"
BASE = "chrome/android/java/res_chromium_base"
# These are pinned Git blob IDs from the user-approved Portal commit.
SOURCE_BLOBS = {
    "archium-dark-48.png": "a55dbdf135f0701c2d62231dafc81e9b9ba98c58",
    "archium-dark-64.png": "564ddcb2517f46b4472668a63caeb3de0c0a23af",
    "archium-dark-128.png": "dd08cf3495ed9f8d43686ff0ed3dc88088fa6b16",
    "archium-dark-192.png": "2d9352d82545e54815bc52680c1748c9d833d85f",
    "archium-adaptive-foreground-432.png": "d5dcb024720fdc40da5cd18e1bb23b7590885f04",
    "archium-adaptive-foreground-512.png": "49c312f420c4ffaf253ad9caa42ab66e7e42456e",
    "archium-adaptive-background-432.png": "a9e2c0a9a7af2d6db1febaaf6ccc1e486a491303",
    "archium-adaptive-background-512.png": "1939222624e0da72216080bc1e8f5fb58c340f23",
    "archium-monochrome-light.svg": "3914ec740d25201707d718d32d1e587f1f6a8483",
}
DENSITIES = {
    "mdpi": ("archium-dark-48.png", "archium-adaptive-foreground-432.png",
             "archium-adaptive-background-432.png"),
    "hdpi": ("archium-dark-64.png", "archium-adaptive-foreground-432.png",
             "archium-adaptive-background-432.png"),
    "xhdpi": ("archium-dark-128.png", "archium-adaptive-foreground-432.png",
              "archium-adaptive-background-432.png"),
    "xxhdpi": ("archium-dark-128.png", "archium-adaptive-foreground-512.png",
               "archium-adaptive-background-512.png"),
    "xxxhdpi": ("archium-dark-192.png", "archium-adaptive-foreground-512.png",
                "archium-adaptive-background-512.png"),
}
APP_XML = """<?xml version="1.0" encoding="utf-8"?>
<!-- Archium Portal. Both default and round launchers resolve to these same layers. -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/layered_app_icon_background"/>
    <foreground android:drawable="@mipmap/layered_app_icon"/>
    <monochrome android:drawable="@drawable/themed_app_icon"/>
</adaptive-icon>
"""


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def png_size(data):
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Invalid PNG signature/header")
    width, height = struct.unpack(">II", data[16:24])
    if not 16 <= width <= 1024 or width != height:
        raise ValueError("Portal icons must be square PNGs in the approved size range")
    if data[25] != 6:  # RGBA: transparency for the adaptive foreground.
        raise ValueError("Portal artwork must preserve RGBA transparency")
    return width


def approved_assets():
    files = {}
    for name, expected_blob in SOURCE_BLOBS.items():
        data = (ICON_ROOT / name).read_bytes()
        if git_blob(data) != expected_blob:
            raise ValueError("Unapproved or corrupted Portal asset: " + name)
        if name.endswith(".png"):
            actual = png_size(data)
            desired = int(name.removesuffix(".png").rsplit("-", 1)[-1])
            if actual != desired:
                raise ValueError("Portal PNG dimensions changed: " + name)
        files[name] = data
    return files


def make_themed_vector(svg):
    namespace = {"s": "http://www.w3.org/2000/svg"}
    root = ET.fromstring(svg)
    paths = [node.attrib["d"] for node in root.findall(".//s:path", namespace)
             if node.get("fill") == "#FFFFFF"]
    if len(paths) != 1 or not paths[0].strip().startswith("M 177 760"):
        raise ValueError("Approved Archium monochrome outline was not found")
    path = re.sub(r"\s+", " ", paths[0]).strip()
    return ("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="1024" android:viewportHeight="1024">
    <path android:fillColor="#000000" android:pathData=""""
            + '"' + path + '"/>\n</vector>\n').encode("utf-8")


def expected_resources():
    assets = approved_assets()
    resources = {}
    for density, (flat, foreground, background) in DENSITIES.items():
        prefix = f"{BASE}/mipmap-{density}"
        resources[f"{prefix}/app_icon.png"] = assets[flat]
        resources[f"{prefix}/layered_app_icon.png"] = assets[foreground]
        resources[f"{prefix}/layered_app_icon_background.png"] = assets[background]
    # The original AndroidManifest.xml already references these official Chromium
    # drawable aliases. Do not modify the manifest or the app ID.
    resources["chrome/android/java/res_base/drawable/ic_launcher.xml"] = APP_XML.encode()
    resources["chrome/android/java/res_base/drawable/ic_launcher_round.xml"] = APP_XML.encode()
    resources[f"{BASE}/drawable/themed_app_icon.xml"] = make_themed_vector(
        assets["archium-monochrome-light.svg"])
    return resources


def safe_target(checkout, relative):
    target = checkout / relative
    if any((checkout / Path(*Path(relative).parts[:i])).is_symlink()
           for i in range(1, len(Path(relative).parts) + 1)):
        raise ValueError("Refusing symlink resource: " + relative)
    if not target.is_file() or not target.resolve().is_relative_to(checkout):
        raise ValueError("Missing/unsafe Chromium launcher resource: " + relative)
    return target


def overlay(checkout, *, check=False, verify=False):
    checkout = Path(checkout).resolve()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(checkout), *args],
                                       stderr=subprocess.STDOUT).strip()
    if Path(os.fsdecode(git("rev-parse", "--show-toplevel"))).resolve() != checkout:
        raise ValueError("Not a Chromium checkout root")
    if git("rev-parse", "HEAD").decode() != REVISION:
        raise ValueError("Launcher overlay requires pinned Chromium revision")
    resources = expected_resources()
    previous = {}
    for relative, desired in resources.items():
        path = safe_target(checkout, relative)
        original = git("show", REVISION + ":" + relative)
        actual = path.read_bytes()
        if actual not in (original, desired):
            raise ValueError("Unrecognized checkout resource; preserving it: " + relative)
        if verify and actual != desired:
            raise ValueError("Archium Portal not installed: " + relative)
        previous[relative] = actual
    if not check and not verify:
        changed = []
        try:
            for relative, desired in resources.items():
                path = checkout / relative
                if previous[relative] == desired:
                    continue
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".archium-icon-",
                                                 delete=False) as staging:
                    staging.write(desired)
                    tmp = Path(staging.name)
                try:
                    os.chmod(tmp, path.stat().st_mode & 0o777)
                    os.replace(tmp, path)
                finally:
                    if tmp.exists():
                        tmp.unlink()
                changed.append(relative)
        except BaseException:
            for relative in reversed(changed):
                (checkout / relative).write_bytes(previous[relative])
            raise
        overlay(checkout, verify=True)
    print("ARCHIUM_PORTAL_RESOURCES=" + ("VERIFIED" if verify else "PREFLIGHT" if check else "INSTALLED")
          + f" paths={len(resources)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    overlay(args.checkout, check=args.check, verify=args.verify)


if __name__ == "__main__":
    main()
