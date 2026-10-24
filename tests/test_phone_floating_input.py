"""Delivered phone input dispatch at simulated native boundaries; not device acceptance."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method, run_probe
ROOT=Path(__file__).resolve().parents[1]
CONTAINER=ROOT/'.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarControlContainer.java'
class FloatingInputTests(unittest.TestCase):
 def test_web_surface_keeps_full_window_during_phone_compaction(self):
  toolbar=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  self.assertNotIn('setArcPhoneContentInsets(',toolbar,'Phone controls must never cut the web surface into reserved solid-color bands')
  self.assertNotIn('updateArcPhoneContentInsets()',toolbar)
 def test_container_rejects_transparent_down_without_forwarding_or_stealing_native_gestures(self):
  self.assertTrue(CONTAINER.exists(),'Native toolbar container needs an explicit floating input opt-in')
  src=CONTAINER.read_text();body=method(src,'public boolean dispatchTouchEvent(MotionEvent event)')
  code='''class Parent {int nativeEvents;public boolean dispatchTouchEvent(ContainerProbe.MotionEvent e){nativeEvents++;return true;}}
public class ContainerProbe extends Parent {
static final int VISIBLE=0;static class MotionEvent {static final int ACTION_DOWN=0,ACTION_MOVE=2,ACTION_UP=1;int action;float x,y;MotionEvent(int a,float x,float y){action=a;this.x=x;this.y=y;}int getActionMasked(){return action;}float getRawX(){return x;}float getRawY(){return y;}}
static class Rect {int l,t,r,b;boolean contains(int x,int y){return x>=l&&x<r&&y>=t&&y<b;}}
static class View {boolean shown;boolean isShown(){return shown;}void getLocationOnScreen(int[] p){p[0]=0;p[1]=200;}int getWidth(){return 900;}int getHeight(){return 60;}}
static class R {static class id {static final int find_toolbar=1;}}
View find;View findViewById(int id){return find;}
java.util.function.Predicate<MotionEvent> mArcPhoneFloatingTouchFilter;
'''+body+'''
static void check(boolean v){if(!v)throw new AssertionError("floating/native gesture ownership");}
public static void main(String[] a){ContainerProbe p=new ContainerProbe();
p.mArcPhoneFloatingTouchFilter=e->e.y>=107&&e.y<212;
check(!p.dispatchTouchEvent(new MotionEvent(0,450,94)));check(p.nativeEvents==0);
check(p.dispatchTouchEvent(new MotionEvent(0,450,160)));
check(p.dispatchTouchEvent(new MotionEvent(2,450,94)));check(p.dispatchTouchEvent(new MotionEvent(1,450,94)));
p.mArcPhoneFloatingTouchFilter=e->false;check(!p.dispatchTouchEvent(new MotionEvent(0,450,160)));
p.find=new View();p.find.shown=true;check(p.dispatchTouchEvent(new MotionEvent(0,450,230)));
check(!p.dispatchTouchEvent(new MotionEvent(0,450,94)));
p.mArcPhoneFloatingTouchFilter=null;check(p.dispatchTouchEvent(new MotionEvent(0,450,94)));
}}
'''
  run_probe(self,{'ContainerProbe.java':code},'ContainerProbe')

 def test_capsule_geometry_tracks_translation_visibility_and_transparent_corners(self):
  src=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  body=method(src,'private boolean isArcPhoneFloatingTouch(')
  code='public class TouchGeometryProbe {\nstatic class ToolbarPhone {boolean shown=true;float alpha=1;int x,y=86;boolean isShown(){return shown;}float getAlpha(){return alpha;}void getLocationOnScreen(int[] out){out[0]=x;out[1]=y;}void getArcPhoneGlassBounds(android.graphics.Rect r){r.left=21;r.top=21;r.right=883;r.bottom=126;}}\nObject mToolbarLayout=new ToolbarPhone();\n'+body+'\nstatic void check(boolean v){if(!v)throw new AssertionError("visible pill mask, not invisible native parent");}\npublic static void main(String[] a){TouchGeometryProbe p=new TouchGeometryProbe();ToolbarPhone phone=(ToolbarPhone)p.mToolbarLayout;\ncheck(!p.isArcPhoneFloatingTouch(new android.view.MotionEvent(450,94)));\ncheck(p.isArcPhoneFloatingTouch(new android.view.MotionEvent(450,160)));\ncheck(!p.isArcPhoneFloatingTouch(new android.view.MotionEvent(23,109)));\ncheck(!p.isArcPhoneFloatingTouch(new android.view.MotionEvent(450,213)));\nphone.alpha=0;check(!p.isArcPhoneFloatingTouch(new android.view.MotionEvent(450,160)));\nphone.alpha=1;phone.x=200;phone.y=300;check(p.isArcPhoneFloatingTouch(new android.view.MotionEvent(650,360)));\nphone.shown=false;check(!p.isArcPhoneFloatingTouch(new android.view.MotionEvent(650,360)));}}\n'
  run_probe(self,{'TouchGeometryProbe.java':code,'android/view/MotionEvent.java':'package android.view;public class MotionEvent {float x,y;public MotionEvent(float x,float y){this.x=x;this.y=y;}public float getRawX(){return x;}public float getRawY(){return y;}}','android/graphics/Rect.java':'package android.graphics;public class Rect {public int left,top,right,bottom;public int height(){return bottom-top;}}'},'TouchGeometryProbe')
