"""Execute delivered toolbar frame hooks; synthetic native colors/widgets, not device drawing."""
from pathlib import Path
import subprocess,tempfile,unittest
from arc_toolbar_probe import method_body
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarTablet.java'
class DesktopToolbarSurfaceTest(unittest.TestCase):
 def test_theme_and_fusebox_updates_keep_shared_frame_and_mobile_restores_native(self):
  source=SOURCE.read_text()
  setter=method_body(source,r'public void setArcFrameBackground\(')
  apply=method_body(source,r'private boolean applyArcFrameBackground\(')
  theme=method_body(source,r'public void onThemeColorChanged\(')
  self.assertIn('applyArcFrameBackground();',method_body(source,r'private void onFuseboxStateChanged\('))
  java='''class Drawable {}
class Color {static final int TRANSPARENT=0;}
class ColorStateList {static ColorStateList valueOf(int color){return new ColorStateList();}}
class View {Drawable background;int color;void setBackground(Drawable d){background=d;}void setBackgroundColor(int c){background=null;color=c;}}
class NativeTheme {int getThemeColor(){return 77;}}
class SemanticColorUtils {static int getDefaultBgColor(Object context){return 88;}}
class ImageViewCompat {static void setImageTintList(Object view,Object tint){}}
class ArcDesktopAppearance {static boolean desktop=true;static boolean isDesktopWindow(Object c){return desktop;}static int surface(Object c,boolean i){return 55;}static int foreground(Object c,boolean i){return 0;}}
class Forward {Object getButton(){return this;}}
class Location {void updateVisualsForState(){}}
public class Probe extends View {
 Drawable mArcFrameBackground;View mFixedHeightBackground=new View();NativeTheme mThemeColorProvider=new NativeTheme();
 Object mHomeButton,mBackButton,mReloadButton;Forward mForwardButtonCoordinator=new Forward();Location mLocationBar=new Location();int hairline;
 Object getContext(){return this;}boolean isIncognitoBranded(){return false;}
 void setToolbarHairlineColor(int c){hairline=c;}void notifyToolbarColorChanged(int c){}
 public void setArcFrameBackground(Drawable background) SETTER
 private boolean applyArcFrameBackground() APPLY
 public void onThemeColorChanged(int color,boolean shouldAnimate) THEME
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 public static void main(String[] args){
  Probe p=new Probe();Drawable shared=new Drawable();p.setArcFrameBackground(shared);p.onThemeColorChanged(123,false);
  check(p.background==shared,"Theme callback detached shared frame");check(p.mFixedHeightBackground.color==0,"Fixed native background masks gradient");check(p.hairline==0,"White/native divider survived");
  p.setBackgroundColor(456);p.applyArcFrameBackground();check(p.background==shared,"Fusebox transition failed to restore material");
  ArcDesktopAppearance.desktop=false;p.setArcFrameBackground(null);check(p.background==null&&p.color==77,"Mobile native background not restored");check(p.mFixedHeightBackground.color==77&&p.hairline==77,"Mobile hairline/colors changed");
 }
}'''.replace('SETTER',setter).replace('APPLY',apply).replace('THEME',theme)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'Probe.java';f.write_text(java)
   r=subprocess.run(['javac',str(f)],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)
   r=subprocess.run(['java','-ea','-cp',d,'Probe'],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)
