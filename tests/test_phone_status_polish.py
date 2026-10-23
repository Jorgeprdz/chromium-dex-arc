"""Integration contracts for phone status protection; Android drawing tested separately."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PhoneStatusPolishTests(unittest.TestCase):
    def test_native_status_owner_installs_and_destroys_visual_fade(self):
        source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ui/system/StatusBarColorController.java').read_text()
        self.assertIn('mArcPhoneStatusFade.update(floatingPhoneSurface, statusBarColor)',source,
                      'Transparent status icons have no matching visual protection')
        self.assertIn('mArcPhoneStatusFade.destroy()',source)
    def test_fullscreen_and_pause_do_not_leave_status_overlay_opted_in(self):
        source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        self.assertIn('mStatusBarColorController.setArcPhoneFloatingSurfaceEnabled(floating)',source,
                      'Status treatment must follow fullscreen/resume, not only phone mode')
    def test_focused_native_editor_keeps_contrast_after_delegate_refresh(self):
        import re
        from test_phone_overlay_insets import run_probe
        source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ui/system/StatusBarColorController.java').read_text()
        expression=re.search(r'setStatusBarIconContrastColorOverride\(\s*(.*?)\);',source,re.S).group(1)
        code='''public class FocusStatusProbe {public static void main(String[] a){
boolean mArcPhoneFloatingSurface=true,floatingPhoneSurface=false;int statusBarColor=0xffffffff;
Integer contrast='''+expression+''';
if(contrast==null||contrast!=statusBarColor)throw new AssertionError("focused editor loses contrast to transparent native owner");
mArcPhoneFloatingSurface=false;contrast='''+expression+''';
if(contrast!=null)throw new AssertionError("Desktop must release override");}}
'''
        run_probe(self,{'FocusStatusProbe.java':code},'FocusStatusProbe')
    def test_phone_visual_protection_does_not_stack_platform_opaque_contrast_scrim(self):
        source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        self.assertNotIn('mActivity.getWindow().setStatusBarContrastEnforced(true)',source)
        self.assertIn('mActivity.getWindow().setStatusBarContrastEnforced(false)',source)
        self.assertIn('mActivity.getWindow().setStatusBarContrastEnforced(mArcPhoneOriginalStatusContrast)',source)
