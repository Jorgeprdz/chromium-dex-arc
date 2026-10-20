"""Split gates must opt into Chromium's local Robolectric discovery."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SplitDiscoveryTest(unittest.TestCase):
    def test_every_split_gate_has_explicit_robolectric_runner(self):
        for p in (ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc').glob('ArcSplit*Test.java'):
            with self.subTest(suite=p.name):
                text=p.read_text()
                self.assertIn('@RunWith(RobolectricTestRunner.class)',text)
                self.assertRegex(text,r'@Config\(manifest\s*=\s*Config.NONE,\s*sdk\s*=\s*\{30,\s*36\}\)')
