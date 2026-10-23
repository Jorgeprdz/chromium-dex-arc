"""Approved Mobile uses Chromium's sole bottom slot; never a second root overlay."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
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

    def test_toolbar_host_field_compiles_with_type_use_nullable(self):
        # Compile the delivered integration field, not a corrected copy or string assertion.
        javac=shutil.which('javac')
        self.assertIsNotNone(javac,'JDK required for the native field syntax regression')
        source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        declarations=re.findall(r'^    private [^;\n]+ mArcPhone(?:Host|ModeObserver|TopGlass|BottomGlass);',source,re.MULTILINE)
        self.assertEqual(4,len(declarations),'Mobile Host/observer integration field missing')
        with tempfile.TemporaryDirectory(prefix='archium-host-nullable-') as tmp:
            path=Path(tmp)/'ToolbarHostProbe.java'
            path.write_text('import java.lang.annotation.*;\n'
                '@Target(ElementType.TYPE_USE) @interface Nullable {}\n'
                'class ArcPhoneNavigation { interface Host {} }\n'
                'class ArcPhoneGlass { static class Backdrop {} }\n'
                'interface SharedPreferences { interface OnSharedPreferenceChangeListener {} }\n'
                'class ToolbarHostProbe {\n'+'\n'.join(declarations)+'\n}\n')
            result=subprocess.run([javac,'-d',tmp,str(path)],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)
