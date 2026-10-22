"""Approved Mobile uses Chromium's sole bottom slot; never a second root overlay."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class MobileBottomOwnershipTests(unittest.TestCase):
    def test_mobile_replaces_native_bottom_delegate(self):
        s=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        self.assertTrue('ArcPhoneNavigation' in s,'Native replacement delegate missing')
        self.assertIn('bottomBarContainerOneshotSupplier.set(mArcPhoneNavigation)',s)
        self.assertIn('configureArcPhoneNavigation',s)
    def test_only_native_container_owns_insets(self):
        p=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneNavigation.java'
        self.assertTrue(p.is_file(),'Approved Mobile delegate missing')
        s=p.read_text()
        for forbidden in ['params.bottomMargin','android.R.id.content','setOnApplyWindowInsetsListener','setPaddingRelative','ArcMobileHomeView']:
            self.assertNotIn(forbidden,s)
        self.assertIn('implements BottomControlsContentDelegate',s)
    def test_bottom_sheet_has_no_omnibar_fallback(self):
        p=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneNavigation.java'
        self.assertTrue(p.is_file(),'Approved sheet missing')
        s=p.read_text()
        self.assertIn('implements BottomSheetContent',s)
        self.assertIn('getToolbarView()',s)
        self.assertNotIn('EditText',s)
        self.assertTrue('new Dialog(' not in s and 'new android.app.Dialog(' not in s,'Custom dialog must not replace the native sheet')
        self.assertNotIn('Summarize',s)
    def test_no_mobile_ntp_or_spaces_replacement(self):
        s=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java').read_text()
        self.assertNotIn('ArcMobileHomeView',s)
        self.assertNotIn('showArcMobileSpaces',s)
        self.assertNotIn('initializeArcMobileControls',s)
