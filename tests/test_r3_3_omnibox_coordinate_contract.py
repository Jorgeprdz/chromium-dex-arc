"""R3.3 R-02: pinned native embedder protects reparented Arc omnibox alignment."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ("chrome/browser/ui/android/omnibox/java/src/org/chromium/"
        "chrome/browser/omnibox/OmniboxSuggestionsDropdownEmbedderImpl.java")
UPSTREAM = (ROOT / ".source-reference" / PATH).read_text()
PATCHED = (ROOT / ".source-modified" / PATH).read_text()


class ReparentedOmniboxContract(unittest.TestCase):
    def test_preserves_native_descendant_path(self):
        self.assertIn("ViewUtils.getRelativeLayoutPosition(mAnchorView, mAlignmentView, mPositionArray);", PATCHED)
        self.assertIn("if (ancestor == mAnchorView)", PATCHED)

    def test_detached_and_foreign_host_not_positioned(self):
        self.assertIn("mAnchorView.isAttachedToWindow()", PATCHED)
        self.assertIn("mAnchorView.getRootView() == mAlignmentView.getRootView()", PATCHED)
        self.assertIn("new OmniboxAlignment(0, 0, 0, 0, 0, 0, 0, 0)", PATCHED)

    def test_alignment_uses_window_coordinates_outside_native_toolbar(self):
        self.assertIn("mAnchorView.getLocationInWindow(anchorInWindow);", PATCHED)
        self.assertIn("mAlignmentView.getLocationInWindow(mPositionArray);", PATCHED)
        self.assertIn("mPositionArray[0] -= anchorInWindow[0];", PATCHED)
        self.assertNotIn("mAnchorView.getLocationInWindow(anchorInWindow);", UPSTREAM)


if __name__ == "__main__":
    unittest.main()
