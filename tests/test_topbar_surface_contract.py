"""Execute delivered native glass/background hooks at synthetic drawable boundaries."""
from pathlib import Path
import subprocess, tempfile, unittest
from arc_toolbar_probe import method_body
ROOT=Path(__file__).resolve().parents[1]
TABLET=ROOT/'.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarTablet.java'
class TopbarSurfaceContractTest(unittest.TestCase):
 def test_top_and_command_surfaces_survive_glass_refresh_and_restore_sidebar(self):
  source=TABLET.read_text()
  setter=method_body(source,r'public void setArcGlassBackground\(').replace('android.graphics.Color.TRANSPARENT','0')
  mode=method_body(source,r'public void setArcTopBar\(')
  command=method_body(source,r'public void setArcCommandBar\(')
  java='''class Rect {}
class Drawable {boolean getPadding(Rect r){return true;}}
class LayerDrawable extends Drawable {LayerDrawable(Drawable[] d){}void setLayerInset(int n,int l,int t,int r,int b){}}
class MarginLayoutParams {}
class FrameLayout {static class LayoutParams extends MarginLayoutParams {LayoutParams(LayoutParams p){}}}
class NativeEditor {
 Object command;Object params;
 Object getArcCommandResults(){return command;}
 public void setArcCommandBar(Rect results,boolean actions,Runnable before,Runnable end){command=results;}
 Object getLayoutParams(){return params;}void setLayoutParams(Object p){params=p;}
 int getPaddingLeft(){return 0;}int getPaddingTop(){return 0;}int getPaddingRight(){return 0;}int getPaddingBottom(){return 0;}
 void setPadding(int l,int t,int r,int b){}
}
public class Probe extends NativeEditor {
 boolean mArcTopBar;Drawable background;
 MarginLayoutParams mArcCommandOriginalChildParams;int mArcCommandOriginalPaddingBottom;
 Drawable mArcGlassBackground,mArcGlassLayers,mLocationBarBackground=new Drawable(),mFocusedPopupDrawable=new Drawable();
 int mModernToolbarBackgroundVerticalOffset=4;
 Drawable getBackground(){return background;}
 void setBackground(Drawable d){background=d;}
 void setBackgroundColor(int c){background=null;}
 void updateBackgroundColor(){}
 void updateForegroundAndGlifAnimation(){}
 void updateLayoutAndBackground(){if(mArcTopBar||command!=null)setBackgroundColor(0);else setBackground(mArcGlassLayers==null?mLocationBarBackground:mArcGlassLayers);}
 public void setArcGlassBackground(Drawable surface) SETTER
 public void setArcTopBar(boolean active) MODE
 public void setArcCommandBar(Rect results,boolean actions,Runnable beforeNavigation,Runnable inputEnd) COMMAND
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 public static void main(String[] args){
  Probe p=new Probe();Drawable glass=new Drawable();p.setArcTopBar(true);p.setArcGlassBackground(glass);
  check(p.background==null,"Top bar regained detached capsule after material refresh");
  p.setArcGlassBackground(new Drawable());check(p.background==null,"Changed palette repainted top capsule");
  p.setArcTopBar(false);check(p.background instanceof LayerDrawable,"Sidebar glass lost after top->sidebar");
  p.setArcCommandBar(new Rect(),false,null,null);p.background=null;p.setArcGlassBackground(new Drawable());
  check(p.background==null,"Command editor regained nested pill after refresh");
  p.setArcCommandBar(null,false,null,null);check(p.background instanceof LayerDrawable,"Native command exit must rebuild sidebar glass without another appearance event");
  p.background=p.mFocusedPopupDrawable;p.setArcGlassBackground(new Drawable());check(p.background==p.mFocusedPopupDrawable,"Native focused popup replaced outside integrated mode");
 }
}'''.replace('SETTER',setter).replace('MODE',mode).replace('COMMAND',command)
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'Probe.java';f.write_text(java)
   p=subprocess.run(['javac',str(f)],capture_output=True,text=True);self.assertEqual(0,p.returncode,p.stderr)
   p=subprocess.run(['java','-ea','-cp',d,'Probe'],capture_output=True,text=True);self.assertEqual(0,p.returncode,p.stderr)
