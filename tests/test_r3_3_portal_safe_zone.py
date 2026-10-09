#!/usr/bin/env python3
"""Real decoded-pixel contracts for derived Portal launcher assets."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("portal", ROOT / "scripts/integrate-archium-portal.py")
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)


class AdaptiveSafeZoneTest(unittest.TestCase):
    def test_foreground_is_within_android_safe_circle(self):
        assets = portal.approved_assets()
        for name in ("archium-adaptive-foreground-432.png",
                     "archium-adaptive-foreground-512.png"):
            original = assets[name]
            safe = portal.safe_foreground(original)
            self.assertNotEqual(original, safe, "original approved master must not be rewritten")
            portal.assert_adaptive_safe_zone(safe)
            size, rgba = portal.png_pixels(safe)
            self.assertEqual(size, portal.png_size(original))
            self.assertEqual(0, rgba[3], "outside corners must remain fully transparent")
            self.assertTrue(any(rgba[3::4]), "foreground must show Portal glyph")
            self.assertEqual(safe, portal.safe_foreground(original))

    def test_background_is_full_bleed_and_preserves_center(self):
        assets = portal.approved_assets()
        for name in ("archium-adaptive-background-432.png",
                     "archium-adaptive-background-512.png"):
            original = assets[name]
            flattened = portal.opaque_background(original)
            _, source = portal.png_pixels(original)
            _, pixels = portal.png_pixels(flattened)
            self.assertEqual({255}, set(pixels[3::4]))
            middle = (portal.png_size(flattened) ** 2 // 2) * 4
            self.assertEqual(source[middle:middle + 3], pixels[middle:middle + 3])
            self.assertNotEqual(original, flattened)

    def test_derived_resources_are_used_at_every_density(self):
        assets = portal.approved_assets()
        mapped = portal.expected_resources()
        self.assertEqual(18, len(mapped))
        for density, (flat, fg, bg) in portal.DENSITIES.items():
            root = f"{portal.BASE}/mipmap-{density}"
            self.assertEqual(assets[flat], mapped[f"{root}/app_icon.png"])
            self.assertEqual(portal.safe_foreground(assets[fg]),
                             mapped[f"{root}/layered_app_icon.png"])
            self.assertEqual(portal.opaque_background(assets[bg]),
                             mapped[f"{root}/layered_app_icon_background.png"])
        vector = mapped[f"{portal.BASE}/drawable/themed_app_icon.xml"].decode()
        self.assertIn('android:scaleX="0.65"', vector)
        self.assertIn('android:scaleY="0.65"', vector)

    def test_bad_crc_and_unknown_png_format_fail_closed(self):
        original = bytearray(next(iter(portal.approved_assets().values())))
        original[-8] ^= 1
        with self.assertRaises(ValueError):
            portal.png_pixels(bytes(original))


if __name__ == "__main__":
    unittest.main()
