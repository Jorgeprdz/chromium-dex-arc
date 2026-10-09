#!/usr/bin/env python3
"""Fail-closed structural Android APK icon gate (not a visual device acceptance)."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import zipfile

from archium_portal_content_gate import check_content


def inspect(apk, aapt2, package):
    apk, aapt2 = Path(apk), Path(aapt2)
    if not apk.is_file() or not aapt2.is_file():
        raise ValueError("Missing APK or pinned aapt2")
    def dump(what):
        return subprocess.check_output([str(aapt2), "dump", what, str(apk)],
                                       text=True, stderr=subprocess.STDOUT)
    badging = dump("badging")
    resources = dump("resources")
    if not re.search(r"package:\s+name='" + re.escape(package) + r"'", badging):
        raise ValueError("Unexpected Archium applicationId in final APK")
    app = next((line for line in badging.splitlines() if line.startswith("application: ")), "")
    if "Archium" not in app or "Chromium" in app:
        raise ValueError("APK launcher app label does not resolve to Archium")
    icon_line = re.search(r"\bicon='([^']+)'", app)
    if not icon_line:
        raise ValueError("APK application icon is missing")
    icon_name = icon_line.group(1)
    if not icon_name.endswith(".xml") or "ic_launcher" not in icon_name:
        raise ValueError("APK launcher does not use the native adaptive icon alias")
    required = ("drawable/ic_launcher", "drawable/ic_launcher_round",
                "drawable/themed_app_icon", "mipmap/app_icon",
                "mipmap/layered_app_icon", "mipmap/layered_app_icon_background")
    missing = [name for name in required
               if re.search(r"(?<![A-Za-z0-9_/])" + re.escape(name) + r"\b", resources) is None]
    if missing:
        raise ValueError("APK is missing registered launcher resources: " + ", ".join(missing))
    with zipfile.ZipFile(apk) as archive:
        names = set(archive.namelist())
        if "AndroidManifest.xml" not in names or "resources.arsc" not in names:
            raise ValueError("Invalid Android APK resource archive")
        if icon_name not in names:
            raise ValueError("Android manifest icon XML missing from packaged archive")
        if not any(name.startswith("res/") and name.endswith(".png") for name in names):
            raise ValueError("Missing packed PNG resources")
    content = check_content(apk, resources, lambda path: subprocess.check_output(
        [str(aapt2), "dump", "xmltree", str(apk), "--file", path],
        text=True, stderr=subprocess.STDOUT))
    return {"status": "PASS", "scope": content["scope"], "content": content,
            "package": package, "application": app, "icon_path": icon_name,
            "resources": list(required),
            "limit": "PNG pixels and launcher presentation require real device validation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--aapt2", required=True, type=Path)
    parser.add_argument("--package", default="app.archium.android")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    data = inspect(args.apk, args.aapt2, args.package)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(data, indent=2) + "\n")
    print("ARCHIUM_PORTAL_APK_STRUCTURE=PASS package=" + data["package"])


if __name__ == "__main__":
    main()
