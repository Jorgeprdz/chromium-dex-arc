"""Phone-only surface boundaries; runtime drawing/focus/insets still require device acceptance."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
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
        self.assertIn('if (mArcPhoneFloatingSurface) return false;',text)
    def test_legacy_omnibar_shadow_matches_background_bounds_and_stays_subtle(self):
        from test_phone_overlay_insets import method,run_probe
        text=TOP.read_text();start=text.index('public void setArcPhoneFloatingSurfaceEnabled(')
        body=method(text[start:],'public void getOutline(')
        code='''public class ShadowProbe {
static class Rect {int l,t,r,b;Rect(int a,int c,int d,int e){l=a;t=c;r=d;b=e;}void offset(int x,int y){l+=x;r+=x;t+=y;b+=y;}int height(){return b-t;}}
static class View {int getLeft(){return 21;}int getTop(){return 0;}int getWidth(){return 862;}int getHeight(){return 147;}}
interface ViewOutlineProvider {void getOutline(View v,Outline o);}
Object mArcPhoneGlassBackground=new Object();ViewOutlineProvider mArcOriginalLocationBarOutline;
static class Outline {void setEmpty(){bounds=null;}Rect bounds;float radius,alpha=1;void setRoundRect(int l,int t,int r,int b,float rad){bounds=new Rect(l,t,r,b);radius=rad;}void setRoundRect(Rect r,float rad){bounds=r;radius=rad;}void setAlpha(float a){alpha=a;}}
Rect getLocationBarBackgroundRect(){return new Rect(21,21,883,126);}boolean urlHasFocus(){return false;}boolean isLocationBarShownInNtp(){return false;}
'''+body+'''
public static void main(String[] args){Outline o=new Outline();ShadowProbe p=new ShadowProbe();p.getOutline(new View(),o);if(o.bounds.l!=0||o.bounds.t!=21||o.bounds.r!=862||o.bounds.b!=126||Math.abs(o.radius-52.5f)>.01||o.alpha>.12f)throw new AssertionError("shadow must match pill, not whole editor, with low opacity");p.mArcPhoneGlassBackground=null;p.mArcOriginalLocationBarOutline=(v,nativeOutline)->nativeOutline.setRoundRect(1,2,30,40,0);p.getOutline(new View(),o);if(o.bounds.l!=1||o.bounds.t!=2||o.bounds.b!=40)throw new AssertionError("native focus/NTP outline restored");}}
'''
        run_probe(self,{'ShadowProbe.java':code},'ShadowProbe')

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
    def test_night_configuration_refresh_does_not_depend_on_orientation_change(self):
        toolbar=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        start=toolbar.index('public void onConfigurationChanged(Configuration configuration)')
        end=toolbar.index('public void onLowMemory()',start)
        callback=toolbar[start:end]
        self.assertLess(callback.index('updateArcPhoneFloatingSurfaces()'),callback.index('newOrientation == mCurrentOrientation'))
        start=toolbar.index('public void onThemeColorChanged(int color, boolean shouldAnimate)')
        end=toolbar.index('if (!mShouldUpdateToolbarPrimaryColor)',start)
        self.assertIn('mArcPhoneTopGlass.setSurface(color)',toolbar[start:end])
        self.assertIn('mArcPhoneNavigation.refresh()',toolbar[start:end])

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

    def test_delivered_hairline_methods_compile_and_preserve_native_conditions(self):
        text = TOP.read_text()
        methods = []
        for match in re.finditer(r'protected boolean shouldDrawHairline\(\)\s*\{', text):
            start = match.start()
            end = match.end()
            depth = 1
            while depth:
                depth += (text[end] == '{') - (text[end] == '}')
                end += 1
            methods.append(text[start:end])
        self.assertTrue(methods, 'Native hairline method missing')
        # Compile every delivered declaration: the old duplicate must fail javac.
        source = """
class View { static final int VISIBLE=0; }
class HairlineBase { boolean base=true; protected boolean shouldDrawHairline(){return base;} }
public class ToolbarPhoneProbe extends HairlineBase {
 boolean mArcPhoneFloatingSurface, incognito, interstitial;
 static final int STATIC_TAB=0; int mTabSwitcherState, visibility;
 boolean hideHairlineForIncognitoNtp(){return incognito;}
 boolean hideHairlineForInterstitial(){return interstitial;}
 int getVisibility(){return visibility;}
""" + '\n'.join(methods) + """
 static void expect(ToolbarPhoneProbe p,boolean value){if(p.shouldDrawHairline()!=value)throw new AssertionError("hairline state");}
 public static void main(String[] args){
  ToolbarPhoneProbe p=new ToolbarPhoneProbe();expect(p,true);
  p.mArcPhoneFloatingSurface=true;expect(p,false);p.mArcPhoneFloatingSurface=false;expect(p,true);
  p.incognito=true;expect(p,false);p.incognito=false;
  p.interstitial=true;expect(p,false);p.interstitial=false;
  p.mTabSwitcherState=1;expect(p,false);p.mTabSwitcherState=STATIC_TAB;
  p.visibility=4;expect(p,false);p.visibility=View.VISIBLE;
  p.base=false;expect(p,false);p.base=true;expect(p,true);
 }
}
"""
        javac, java = shutil.which('javac'), shutil.which('java')
        self.assertIsNotNone(javac); self.assertIsNotNone(java)
        with tempfile.TemporaryDirectory(prefix='archium-hairline-') as temp:
            probe=Path(temp)/'ToolbarPhoneProbe.java';probe.write_text(source)
            result=subprocess.run([javac,'-d',temp,str(probe)],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)
            result=subprocess.run([java,'-cp',temp,'ToolbarPhoneProbe'],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)
