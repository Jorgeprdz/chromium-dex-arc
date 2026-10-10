"""Protect Chromium's TabListMediator non-flat thumbnail contract."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/TabListMediator.java"

class ThumbnailSpinnerLayoutGateTest(unittest.TestCase):
    def test_grouped_layout_throws_explicit_assertion_even_when_jvm_ea_is_off(self):
        source = SOURCE.read_text()
        method = source.split("void setThumbnailSpinnerVisibility(Tab tab, boolean isVisible) {", 1)[1].split("void updateThumbnailFetcher(", 1)[0]
        self.assertIn("if (mLayoutType != TabListLayoutType.FLAT)", method)
        self.assertIn("throw new AssertionError(", method)
        self.assertLess(method.index("throw new AssertionError("), method.index("getIndexFromTabId("))
        self.assertNotIn("assert mLayoutType == TabListLayoutType.FLAT;", method)

if __name__ == "__main__":
    unittest.main()
