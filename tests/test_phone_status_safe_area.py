"""Execute native safe-area routing with synthetic window-inset dependencies."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method,run_probe
ROOT=Path(__file__).resolve().parents[1]
class PhoneStatusSafeAreaTests(unittest.TestCase):
 def test_top_safe_area_coexists_with_bottom_and_resets(self):
  file=ROOT/'.source-modified/ui/android/java/src/org/chromium/ui/insets/InsetObserver.java'
  self.assertTrue(file.exists(),'Native top inset routing missing')
  s=file.read_text()
  code='''import java.util.*;public class SafeAreaProbe {
static class Context{}static class Insets{int left,top,right,bottom;static final Insets NONE=new Insets();}
static class Rect {int left,top,right,bottom;Rect(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}Rect(Rect r){this(r.left,r.top,r.right,r.bottom);}void set(Rect r){left=r.left;top=r.top;right=r.right;bottom=r.bottom;}public boolean equals(Object v){if(!(v instanceof Rect r))return false;return left==r.left&&top==r.top&&right==r.right&&bottom==r.bottom;}}
static class Raw {Insets getInsets(int t){Insets i=new Insets();i.top=86;return i;}}
static class WindowInsetsUtils {static boolean shouldPadDisplayCutout(Object i,Context c){return true;}}
static class ThreadUtils {static void assertOnUiThread(){}}
interface WindowInsetObserver{void onSafeAreaChanged(Rect r);}
int mBottomInsetsForEdgeToEdge=24,mTopInsetsForEdgeToEdge;java.lang.ref.WeakReference<Context> mContextReference=new java.lang.ref.WeakReference<>(new Context());Rect mDisplayCutoutRect=new Rect(0,86,0,0),mCurrentSafeArea=new Rect(0,0,0,0);ArrayList<WindowInsetObserver> mObservers=new ArrayList<>();Raw getLastRawWindowInsets(){return new Raw();}static int systemBars(){return 1;}static int displayCutout(){return 2;}
'''+method(s,'private void updateCurrentSafeArea()')+method(s,'public void updateTopInsetForEdgeToEdge(')+'''
public static void main(String[] args){SafeAreaProbe p=new SafeAreaProbe();p.updateCurrentSafeArea();if(p.mCurrentSafeArea.top!=0||p.mCurrentSafeArea.bottom!=24)throw new AssertionError();p.updateTopInsetForEdgeToEdge(86);if(p.mCurrentSafeArea.top!=86||p.mCurrentSafeArea.bottom!=24)throw new AssertionError("status safe area must reach native observers");p.updateTopInsetForEdgeToEdge(0);if(p.mCurrentSafeArea.top!=0||p.mCurrentSafeArea.bottom!=24)throw new AssertionError("Desktop/native reset");}}
'''
  run_probe(self,{'SafeAreaProbe.java':code},'SafeAreaProbe')
