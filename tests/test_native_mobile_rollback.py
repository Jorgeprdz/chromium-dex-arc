"""Phone presentation must remain owned by native Chromium after selective rollback."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
ARC=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
class NativeMobileRollbackTests(unittest.TestCase):
    def test_custom_mobile_classes_and_tests_are_removed(self):
        for name in ['ArcMobileControls.java','ArcMobileHomeView.java']:
            self.assertFalse((ARC/name).exists(),name)
        self.assertFalse((ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcMobileControlsTest.java').exists())
        self.assertFalse((ROOT/'scripts/test-robolectric-mobile.py').exists())
    def test_native_activity_has_no_custom_mobile_ownership(self):
        s=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java').read_text()
        for forbidden in ['ArcMobile','arcMobileSession','initializeArcMobile','buildArcMobileHome','showArcMobileSpaces']:
            self.assertNotIn(forbidden,s)
    def test_no_orphaned_source_resource_or_gate_registrations(self):
        for name in ['.source-modified/chrome/android/chrome_java_sources.gni','.source-modified/chrome/android/junit/BUILD.gn',
                     'scripts/archium-test-gates.py','scripts/build-archium-r5.sh','tests/test_host_gate_coverage.py']:
            self.assertNotIn('ArcMobile', (ROOT/name).read_text(),name)
        self.assertNotIn('arc_mobile_', (ROOT/'chromium/chrome/android/java/res/values/arc_strings.xml').read_text())
    def test_root_does_not_override_native_phone_navigation(self):
        s=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java').read_text()
        self.assertNotIn('prepareArcMobileNavigation',s)
        self.assertNotIn('TabUtils.switchUserAgent',s)
        self.assertNotIn('.setUserAgent(',s)
    def test_shared_desktop_session_and_profile_store_survive(self):
        for name in ['ArcNativeTabSession','ArcSidebarProfiles','ArcSidebarState','ArcCollectionsView','ArcSplitViewCoordinator','ArcDesktopCoordinator']:
            self.assertTrue((ARC/(name+'.java')).is_file(),name)
        self.assertNotIn('restoreSpaceSelection',(ARC/'ArcNativeTabSession.java').read_text())
