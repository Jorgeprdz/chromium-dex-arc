#!/usr/bin/env python3
"""Negative regressions for compiled APK icon-content verification."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("gate", "archium_portal_content_gate.py")
portal = load("portal", "integrate-archium-portal.py")
IDS = {
    "mipmap/app_icon": 0x7f010001,
    "mipmap/layered_app_icon": 0x7f010002,
    "mipmap/layered_app_icon_background": 0x7f010003,
    "drawable/ic_launcher": 0x7f020001,
    "drawable/ic_launcher_round": 0x7f020002,
    "drawable/themed_app_icon": 0x7f020003,
}


def fixture(tamper=None, remove=None):
    expected = portal.expected_resources()
    inputs = {}
    rows = []
    for name, id_ in IDS.items():
        leaf = name.split("/")[1]
        ext = ".png" if name.startswith("mipmap/") else ".xml"
        packed = "res/verify/" + leaf + ext
        if ext == ".png":
            source = f"{portal.BASE}/mipmap-mdpi/{leaf}.png"
        elif leaf == "themed_app_icon":
            source = f"{portal.BASE}/drawable/themed_app_icon.xml"
        else:
            source = "chrome/android/java/res_base/drawable/" + leaf + ".xml"
        if name != remove:
            data = expected[source]
            if name == tamper:
                data = (expected[f"{portal.BASE}/mipmap-mdpi/app_icon.png"]
                        if leaf != "app_icon"
                        else expected[f"{portal.BASE}/mipmap-mdpi/layered_app_icon.png"])
            inputs[packed] = data
            rows.append(f"resource 0x{id_:08x} app.archium.android:{name}\n"
                        f"  (mdpi) (file) {packed}\n")
    return inputs, "\n".join(rows)


def xmltree(path):
    if "themed_app_icon" in path:
        return "E: vector\nE: group scaleX scaleY\nE: path android:pathData=\"M 177 760\""
    return ("E: adaptive-icon\nE: foreground android:drawable=@0x7f010002"
            "\nE: background android:drawable=@0x7f010003"
            "\nE: monochrome android:drawable=@0x7f020003")


class ApkPixelGateTest(unittest.TestCase):
    def run_gate(self, tamper=None, remove=None, broken_xml=False):
        files, table = fixture(tamper=tamper, remove=remove)
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp) / "fake.apk"
            with zipfile.ZipFile(apk, "w") as z:
                for path, value in files.items():
                    z.writestr(path, value)
            return gate.check_content(apk, table, (lambda path: "E: wrong")
                                      if broken_xml else xmltree)

    def test_approved_content_all_links_pass(self):
        self.assertEqual("PASS", self.run_gate()["status"])

    def test_foreign_foreground_under_correct_alias_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Wrong Portal pixels"):
            self.run_gate(tamper="mipmap/layered_app_icon")

    def test_foreign_background_under_correct_alias_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Wrong Portal pixels"):
            self.run_gate(tamper="mipmap/layered_app_icon_background")

    def test_no_compiled_layer_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Missing compiled Portal resource"):
            self.run_gate(remove="mipmap/layered_app_icon")

    def test_wrong_adaptive_xml_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "not adaptive"):
            self.run_gate(broken_xml=True)

    def test_unknown_resource_file_rejected(self):
        files, table = fixture()
        table = table.replace("res/verify/layered_app_icon.png",
                              "res/verify/missing.png")
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp) / "bad.apk"
            with zipfile.ZipFile(apk, "w") as z:
                for p, value in files.items():
                    z.writestr(p, value)
            with self.assertRaisesRegex(ValueError, "missing ZIP entry"):
                gate.check_content(apk, table, xmltree)


if __name__ == "__main__":
    unittest.main()
