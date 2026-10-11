#!/usr/bin/env python3
"""Negative regressions for compiled APK icon-content verification."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import zipfile
import io
import xml.etree.ElementTree as ET
from PIL import Image

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


def fixture(tamper=None, remove=None, webp=False, exact=True, pixel_mutation=None):
    expected = portal.expected_resources()
    inputs = {}
    rows = []
    for name, id_ in IDS.items():
        leaf = name.split("/")[1]
        ext = ".png" if name.startswith("mipmap/") else ".xml"
        packed = "res/verify/" + leaf + ("" if webp and ext == ".png" else ext)
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
            if webp and ext == '.png':
                output = io.BytesIO()
                image = Image.open(io.BytesIO(data)).convert('RGBA')
                if name == 'mipmap/app_icon' and pixel_mutation:
                    pixels = bytearray(image.tobytes())
                    if pixel_mutation == 'transparent_alpha':
                        index = next(i for i in range(0, len(pixels), 4) if pixels[i+3] == 0)
                        pixels[index+3] = 1
                    else:
                        index = next(i for i in range(0, len(pixels), 4) if 0 < pixels[i+3] < 255)
                        if pixel_mutation == 'visible_rgb':
                            pixels[index] = (pixels[index]+1) % 256
                        else:
                            pixels[index+3] = 0
                    image = Image.frombytes('RGBA', image.size, bytes(pixels))
                image.save(output, format='WEBP', lossless=True, method=6, quality=100, exact=exact)
                data = output.getvalue()
            inputs[packed] = data
            rows.append(f"resource 0x{id_:08x} app.archium.android:{name}\n"
                        f"  (mdpi) (file) {packed}\n")
    return inputs, "\n".join(rows)


def xmltree(path):
    if "themed_app_icon" in path:
        source = portal.expected_resources()[f'{portal.BASE}/drawable/themed_app_icon.xml']
        vector = ET.fromstring(source)
        group = vector.find('group'); outline = group.find('path')
        android = '{http://schemas.android.com/apk/res/android}'
        rows = ['E: vector']
        for name in ('width', 'height', 'viewportWidth', 'viewportHeight'):
            rows.append(f'  A: android:{name}(0x1)={vector.get(android+name)}')
        rows.append('  E: group')
        for name in ('scaleX', 'scaleY', 'translateX', 'translateY'):
            rows.append(f'    A: android:{name}(0x1)={group.get(android+name)}')
        rows += ['    E: path', '      A: android:fillColor(0x1)=#ff000000',
                 f'      A: android:pathData(0x1)="{outline.get(android+"pathData")}"']
        return '\n'.join(rows)
    return ("E: adaptive-icon\nE: foreground android:drawable=@0x7f010002"
            "\nE: background android:drawable=@0x7f010003"
            "\nE: monochrome android:drawable=@0x7f020003")


class ApkPixelGateTest(unittest.TestCase):
    def run_gate(self, tamper=None, remove=None, broken_xml=False, webp=False, exact=True, pixel_mutation=None):
        files, table = fixture(tamper=tamper, remove=remove, webp=webp,
                               exact=exact, pixel_mutation=pixel_mutation)
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp) / "fake.apk"
            with zipfile.ZipFile(apk, "w") as z:
                for path, value in files.items():
                    z.writestr(path, value)
            return gate.check_content(apk, table, (lambda path: "E: wrong")
                                      if broken_xml else xmltree)

    def test_approved_content_all_links_pass(self):
        self.assertEqual("PASS", self.run_gate()["status"])

    def test_chromium_extensionless_lossless_webp_preserves_pixels(self):
        self.assertEqual('PASS', self.run_gate(webp=True)['status'])

    def test_foreign_pixels_in_extensionless_webp_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Wrong Portal pixels'):
            self.run_gate(tamper='mipmap/layered_app_icon', webp=True)

    def test_chromium_lossless_webp_without_exact_preserves_visible_pixels(self):
        self.assertEqual('PASS', self.run_gate(webp=True, exact=False)['status'])

    def test_semitransparent_rgb_change_is_rejected_without_exact(self):
        with self.assertRaisesRegex(ValueError, 'Wrong Portal pixels'):
            self.run_gate(webp=True, exact=False, pixel_mutation='visible_rgb')

    def test_semitransparent_alpha_change_is_rejected_without_exact(self):
        with self.assertRaisesRegex(ValueError, 'Wrong Portal pixels'):
            self.run_gate(webp=True, exact=False, pixel_mutation='visible_alpha')

    def test_transparent_pixel_becoming_visible_is_rejected_without_exact(self):
        with self.assertRaisesRegex(ValueError, 'Wrong Portal pixels'):
            self.run_gate(webp=True, exact=False, pixel_mutation='transparent_alpha')

    def test_replaced_monochrome_path_is_rejected(self):
        self.reject_vector(lambda x: x.split('android:pathData')[0] + 'android:pathData(0x1)="M 177 760 L 0 0 Z"')

    def test_changed_monochrome_scale_is_rejected(self):
        self.reject_vector(lambda x: x.replace('scaleX(0x1)=0.65', 'scaleX(0x1)=1.0'))

    def test_changed_monochrome_translation_is_rejected(self):
        self.reject_vector(lambda x: x.replace('translateX(0x1)=179.2', 'translateX(0x1)=0'))

    def test_changed_monochrome_viewport_is_rejected(self):
        self.reject_vector(lambda x: x.replace('viewportWidth(0x1)=1024', 'viewportWidth(0x1)=512'))

    def test_changed_monochrome_fill_is_rejected(self):
        self.reject_vector(lambda x: x.replace('#ff000000', '#ff00ff00'))

    def test_extra_monochrome_element_is_rejected(self):
        self.reject_vector(lambda x: x + '\n    E: path\n      A: android:pathData(0x1)="M 177 760 L 0 0 Z"')

    def reject_vector(self, mutation):
        files, table = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            apk = Path(tmp)/'bad-vector.apk'
            with zipfile.ZipFile(apk, 'w') as z:
                for path, data in files.items():
                    z.writestr(path, data)
            with self.assertRaisesRegex(ValueError, 'Themed glyph'):
                gate.check_content(apk, table, lambda p: mutation(xmltree(p))
                                   if 'themed_app_icon' in p else xmltree(p))

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
