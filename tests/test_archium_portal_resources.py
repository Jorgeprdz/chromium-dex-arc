#!/usr/bin/env python3
"""Host-side resource gate; not a claim that an APK or desktop was tested."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/integrate-archium-portal.py"
spec = importlib.util.spec_from_file_location("archium_portal", SCRIPT)
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)

ANDROID = "{http://schemas.android.com/apk/res/android}"


class ArchiumPortalResourcesTest(unittest.TestCase):
    def test_assets_have_approved_git_blobs_and_dimensions(self):
        assets = portal.approved_assets()
        self.assertEqual(set(portal.SOURCE_BLOBS), set(assets))
        self.assertEqual(9, len(assets))
        for name in assets:
            self.assertEqual(portal.SOURCE_BLOBS[name], portal.git_blob(assets[name]))

    def test_native_resources_cover_existing_gn_slots(self):
        resources = portal.expected_resources()
        self.assertEqual(18, len(resources))
        gn = (ROOT / ".source-reference/chrome/android/BUILD.gn").read_text()
        for path in resources:
            self.assertIn('"' + path.removeprefix("chrome/android/") + '"', gn)
        self.assertEqual(
            {"mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"},
            set(portal.DENSITIES))

    def test_original_manifest_keeps_chromium_drawable_aliases(self):
        template = (ROOT / ".source-reference/chrome/android/java/AndroidManifest.xml").read_text()
        self.assertIn('android:icon="@drawable/ic_launcher"', template)
        self.assertIn('android:roundIcon="@drawable/ic_launcher_round"', template)
        gn_args = (ROOT / "config/archium-args.gn").read_text()
        self.assertIn('chrome_public_manifest_package = "app.archium.android"', gn_args)

    def test_adaptive_round_and_themed_references_are_valid(self):
        resources = portal.expected_resources()
        for basename in ("ic_launcher.xml", "ic_launcher_round.xml"):
            root = ET.fromstring(resources["chrome/android/java/res_base/drawable/" + basename])
            self.assertTrue(root.tag.endswith("adaptive-icon"))
            values = {child.tag: child.attrib.get(ANDROID + "drawable") for child in root}
            self.assertEqual("@mipmap/layered_app_icon_background", values["background"])
            self.assertEqual("@mipmap/layered_app_icon", values["foreground"])
            self.assertEqual("@drawable/themed_app_icon", values["monochrome"])
        icon = ET.fromstring(resources[
            "chrome/android/java/res_chromium_base/drawable/themed_app_icon.xml"])
        self.assertEqual("vector", icon.tag)
        self.assertEqual("#000000", list(icon)[0].get(ANDROID + "fillColor"))
        self.assertIn("M 177 760", list(icon)[0].get(ANDROID + "pathData"))

    def test_foreground_and_background_remain_distinct_rgba(self):
        resources = portal.expected_resources()
        for density in portal.DENSITIES:
            base = f"{portal.BASE}/mipmap-{density}"
            self.assertNotEqual(
                resources[f"{base}/layered_app_icon.png"],
                resources[f"{base}/layered_app_icon_background.png"])
            for name in ("app_icon.png", "layered_app_icon.png", "layered_app_icon_background.png"):
                self.assertGreaterEqual(portal.png_size(resources[f"{base}/{name}"]), 16)

    def test_installer_is_fail_closed_and_idempotent(self):
        resources = portal.expected_resources()
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp)
            for path in resources:
                p = checkout / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"pinned upstream resource: " + path.encode())
            def fake_git(command, stderr=None):
                assert command[:3] == ["git", "-C", str(checkout)]
                args = command[3:]
                if args == ["rev-parse", "--show-toplevel"]:
                    return str(checkout).encode() + b"\n"
                if args == ["rev-parse", "HEAD"]:
                    return portal.REVISION.encode() + b"\n"
                if args[0] == "show" and args[1].startswith(portal.REVISION + ":"):
                    path = args[1].split(":", 1)[1]
                    return b"pinned upstream resource: " + path.encode()
                raise AssertionError(args)
            with mock.patch.object(portal.subprocess, "check_output", side_effect=fake_git):
                portal.overlay(checkout, check=True)
                portal.overlay(checkout)
                portal.overlay(checkout, verify=True)
                portal.overlay(checkout)
                path = next(iter(resources))
                (checkout / path).write_bytes(b"unknown concurrent change")
                with self.assertRaisesRegex(ValueError, "Unrecognized checkout resource"):
                    portal.overlay(checkout)

    def test_builder_integration_and_no_new_manifest_package(self):
        build = (ROOT / "scripts/build-archium.sh").read_text()
        self.assertIn('scripts/integrate-archium-portal.py', build)
        self.assertIn('scripts/verify-archium-portal-apk.py', build)
        self.assertNotIn(".archium-final-dispatch", build)


if __name__ == "__main__":
    unittest.main()
