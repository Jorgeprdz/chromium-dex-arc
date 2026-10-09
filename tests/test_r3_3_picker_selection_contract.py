"""R3.3: picker swatches share the same parsed draft value as HEX and RGB."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java").read_text()


class PickerSelectionContract(unittest.TestCase):
    def test_preset_state_follows_valid_hex_and_clears_on_invalid(self):
        self.assertIn("updatePresetSelection(swatches, swatchBackgrounds, presetColors, chosen);", SOURCE)
        self.assertIn("updatePresetSelection(swatches, swatchBackgrounds, presetColors, -1);", SOURCE)
        self.assertIn("updatePresetSelection(swatches, swatchBackgrounds, presetColors, selected);", SOURCE)

    def test_android_accessibility_selected_state(self):
        self.assertIn("swatches[i].setSelected(selected);", SOURCE)
        self.assertIn("selected ? ArcDesktopPolicy.foreground(presets[i])", SOURCE)

    def test_cancel_does_not_persist_draft(self):
        self.assertIn(".setNegativeButton(android.R.string.cancel, null)", SOURCE)
        self.assertIn('mPreferences.edit().putInt(ArcDesktopAppearance.COLOR_KEY,', SOURCE)


if __name__ == "__main__":
    unittest.main()
