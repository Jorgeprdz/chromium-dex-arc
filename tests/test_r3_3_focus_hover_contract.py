"""R3.3 R-06 focus/hover contracts in real source; runtime input validation still pending."""
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1] / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc"
VIEW = (BASE / "ArcCollectionsView.java").read_text()
COORDINATOR = (BASE / "ArcDesktopCoordinator.java").read_text()


class FocusHoverContract(unittest.TestCase):
    def test_both_dynamic_regions_restore_focus_by_stable_tags(self):
        for fragment in ("mFavorites.findFocus()", "mEntries.findFocus()",
                         "mFavorites.findViewWithTag(favoriteFocusId)",
                         "mEntries.findViewWithTag(entryFocusId)",
                         'folderRow.setTag("arc-folder:" + folder.id)',
                         'newFolder.setTag("arc-new-folder:'):
            self.assertIn(fragment, VIEW)

    def test_no_constant_background_for_owned_buttons(self):
        self.assertIn("private StateListDrawable arcButtonStates(", COORDINATOR)
        self.assertIn("android.R.attr.state_pressed", COORDINATOR)
        self.assertIn("android.R.attr.state_focused", COORDINATOR)
        self.assertIn("android.R.attr.state_hovered", COORDINATOR)
        self.assertIn("mArcNewTabRow.setBackground(arcButtonStates(", COORDINATOR)
        self.assertIn('((String) tag).startsWith("arc-entry:")', COORDINATOR)


if __name__ == "__main__":
    unittest.main()
