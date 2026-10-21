"""Split gates must opt into Chromium's local Robolectric discovery."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SplitDiscoveryTest(unittest.TestCase):
    def test_every_split_gate_has_explicit_robolectric_runner(self):
        for p in (ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc').glob('ArcSplit*Test.java'):
            with self.subTest(suite=p.name):
                text=p.read_text()
                # GURL needs Chromium context/native setup; view-only suites use generic Robolectric.
                runner=('BaseRobolectricTestRunner' if p.stem=='ArcSplitViewCoordinatorTest'
                        else 'RobolectricTestRunner')
                self.assertIn('@RunWith('+runner+'.class)',text)
                if runner=='BaseRobolectricTestRunner':
                    self.assertIn('import org.chromium.base.test.BaseRobolectricTestRunner;',text)
                self.assertRegex(text,r'@Config\(manifest\s*=\s*Config.NONE,\s*sdk\s*=\s*\{30,\s*36\}\)')
