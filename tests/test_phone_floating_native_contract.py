"""Phone-only surface boundaries; runtime drawing/focus/insets still require device acceptance."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
TOP=ROOT/'.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarPhone.java'
STATUS=ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ui/system/StatusBarColorController.java'
class PhoneFloatingNativeContractTests(unittest.TestCase):
    def test_toolbar_surface_changes_preserve_native_geometry(self):
        self.assertTrue(TOP.is_file(),'Native phone surface hook missing')
        text=TOP.read_text()
        start=text.index('public void setArcPhoneFloatingSurfaceEnabled(')
        end=text.index('private @ColorInt int getArcPhoneSurfaceColor()',start)
        for forbidden in ['setLayoutParams','setPadding','setMinimumHeight','setTextSize','setOnTouchListener','setOnClickListener','new EditText']:
            self.assertNotIn(forbidden,text[start:end])
        self.assertIn('return !mArcPhoneFloatingSurface && super.shouldDrawHairline();',text)
    def test_activation_stays_under_existing_phone_guard(self):
        activity=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java').read_text()
        start=activity.index('private void configureArcPhoneNavigation(')
        end=activity.index('private void maybeCreateIncognitoTabSnapshotController()',start)
        self.assertIn('ArcDesktopAppearance.isDesktopWindow(this)) return;',activity[start:end])
        toolbar=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        self.assertTrue('phone.setArcPhoneFloatingSurfaceEnabled(enabled);' in toolbar, 'Phone activation missing')
        self.assertIn('if (mArcPhoneHost != null) updateArcPhoneFloatingSurfaces();',toolbar)
        self.assertIn('mArcPhoneNavigation.setPhoneModeActive(enabled)',toolbar)
        self.assertEqual(2,toolbar.count('ArcPhoneNavigation.getReservedHeight(mActivity)'))
    def test_transparent_status_bar_keeps_native_overlays_and_icon_contrast(self):
        self.assertTrue(STATUS.is_file(),'Native status surface hook missing')
        text=STATUS.read_text()
        self.assertIn('statusBarColor == getArcPhoneSurfaceColor()',text)
        self.assertIn('setStatusBarColor(Color.TRANSPARENT, false)',text)
        self.assertIn('setStatusBarIconContrastColorOverride(',text)
        self.assertIn('floatingPhoneSurface ? Integer.valueOf(statusBarColor) : null',text)
        self.assertIn('UiUtils.setStatusBarIconColor(',text)
        for preserved in ['applyStatusBarIndicatorColor(', 'applyCurrentScrimToColor(', 'applyTabStripOverlay(']:
            self.assertIn(preserved,text)
