"""R3.3 R-05: observer lifecycle tied to currently selected native tab."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
COORD = (ROOT / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java").read_text()


class NativeNavigationContract(unittest.TestCase):
    def test_navigation_buttons_are_live_objects(self):
        for v in ("mBackButton = navigationButton(", "mForwardButton = navigationButton(",
                  "mReloadButton = navigationButton(", "mBackButton.setEnabled(back)",
                  "mForwardButton.setEnabled(forward)", "mReloadButton.setEnabled(tab != null)"):
            self.assertIn(v, COORD)

    def test_observers_are_swapped_and_disposed(self):
        self.assertIn("mObservedNavigationTab.removeObserver(mNavigationObserver);", COORD)
        self.assertIn("tab.addObserver(mNavigationObserver);", COORD)
        self.assertIn("bindNavigationTab(desktop);", COORD)
        self.assertIn("public void onUrlUpdated(Tab tab)", COORD)
        self.assertIn("public void onNavigationEntriesDeleted(Tab tab)", COORD)


if __name__ == "__main__":
    unittest.main()
