"""Guard the physically failing SurfaceView source; not physical blur acceptance."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PhoneBackdropReadbackTests(unittest.TestCase):
 def test_capture_reads_existing_chromium_surface_region_without_changing_gpu_path(self):
  glass=(ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneGlass.java').read_text()
  toolbar=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  native=ROOT/'.source-modified/chrome/browser/android/compositor/compositor_view.cc'
  self.assertNotIn('PixelCopy.request(',glass)
  self.assertIn('ArcPhoneGlass.contentSource(',toolbar)
  self.assertTrue(native.exists())
  code=native.read_text();start=code.index('void CompositorView::CopyArcPhoneBackdrop(');end=code.index('\nvoid ',start+5);body=code[start:end]
  self.assertIn('IsSurfaceAvailableForCopy()',body)
  self.assertIn('CopyFromSurface(region,',body)
  self.assertIn('Contains(region)',body)
  self.assertIn('width > 256',body);self.assertIn('height > 128',body)
  self.assertNotIn('IncrementCapturerCount',body)
  self.assertNotIn('SetSurface',body)
 def test_root_owner_removes_top_padding_and_paint_only_for_opted_phone(self):
  path=ROOT/'.source-modified/ui/edge_to_edge/android/java/src/org/chromium/ui/edge_to_edge/layout'
  base=(path/'EdgeToEdgeBaseLayout.java').read_text() if (path/'EdgeToEdgeBaseLayout.java').exists() else ''
  owner=(path/'EdgeToEdgeLayoutCoordinator.java').read_text() if (path/'EdgeToEdgeLayoutCoordinator.java').exists() else ''
  self.assertIn('isArcPhoneControlsOverlay()',base)
  self.assertIn('mView.isArcPhoneControlsOverlay()',owner)
  self.assertIn('overallInsets.left, captionBarInsets.top, overallInsets.right, overallInsets.bottom',owner)
  self.assertIn('mView.setStatusBarInsets(Insets.NONE)',owner)
 def test_actual_root_inset_consumer_preserves_ime_sides_and_native_restore(self):
  import os
  from test_phone_overlay_insets import method,run_probe
  default=ROOT/'.source-modified/ui/edge_to_edge/android/java/src/org/chromium/ui/edge_to_edge/layout/EdgeToEdgeLayoutCoordinator.java'
  text=Path(os.environ.get('ARCHIUM_ROOT_LAYOUT_SOURCE',str(default))).read_text()
  body=method(text,'public WindowInsetsCompat onApplyWindowInsets(')
  code='''public class RootInsetProbe {
static class Insets {int left,top,right,bottom;static final Insets NONE=of(0,0,0,0);static Insets of(int l,int t,int r,int b){Insets i=new Insets();i.left=l;i.top=t;i.right=r;i.bottom=b;return i;}static Insets max(Insets a,Insets b){return of(Math.max(a.left,b.left),Math.max(a.top,b.top),Math.max(a.right,b.right),Math.max(a.bottom,b.bottom));}}
static class View {boolean overlay;Insets status,cutout,padding;boolean isArcPhoneControlsOverlay(){return overlay;}void setStatusBarInsets(Insets i){status=i;}void setNavigationBarInsets(Insets i){}void setCaptionBarInsets(Insets i){}void setDisplayCutoutTop(Insets i){cutout=i;}void setDisplayCutoutInsetLeft(Insets i){}void setDisplayCutoutInsetRight(Insets i){}void setPadding(int l,int t,int r,int b){padding=Insets.of(l,t,r,b);}void updateCachedRects(){}void invalidate(){}}
static class Type {static int statusBars(){return 1;}static int navigationBars(){return 2;}static int captionBar(){return 4;}static int displayCutout(){return 8;}static int ime(){return 16;}static int systemBars(){return 7;}static int tappableElement(){return 32;}static int mandatorySystemGestures(){return 64;}}
static class WindowInsetsCompat {int keyboard=24,caption;Insets getInsets(int types){Insets r=Insets.NONE;if((types&1)!=0)r=Insets.max(r,Insets.of(0,86,0,0));if((types&2)!=0)r=Insets.max(r,Insets.of(0,0,0,24));if((types&4)!=0)r=Insets.max(r,Insets.of(0,caption,0,0));if((types&8)!=0)r=Insets.max(r,Insets.of(30,86,12,0));if((types&16)!=0)r=Insets.max(r,Insets.of(0,0,0,keyboard));return r;}static class Builder {WindowInsetsCompat value;Builder(WindowInsetsCompat v){value=v;}Builder setInsets(int t,Insets i){return this;}WindowInsetsCompat build(){return value;}}}
static class WindowInsetsUtils {static boolean shouldPadDisplayCutout(Object w,Object c){return true;}}
View mView=new View();Object mContext=new Object();static void assumeNonNull(Object v){}Insets getNavigationBarInsets(WindowInsetsCompat w){return w.getInsets(Type.navigationBars());}
'''+body+'''
static void check(boolean v){if(!v)throw new AssertionError("root phone top / IME / restoration");}
public static void main(String[] args){RootInsetProbe p=new RootInsetProbe();WindowInsetsCompat w=new WindowInsetsCompat();
p.onApplyWindowInsets(p.mView,w);check(p.mView.padding.top==86&&p.mView.status.top==86);
p.mView.overlay=true;p.onApplyWindowInsets(p.mView,w);check(p.mView.padding.top==0&&p.mView.status.top==0&&p.mView.cutout.top==0);check(p.mView.padding.left==30&&p.mView.padding.right==12&&p.mView.padding.bottom==24);
w.keyboard=600;p.onApplyWindowInsets(p.mView,w);check(p.mView.padding.top==0&&p.mView.padding.bottom==600);w.caption=20;p.onApplyWindowInsets(p.mView,w);check(p.mView.padding.top==20);
p.mView.overlay=false;p.onApplyWindowInsets(p.mView,w);check(p.mView.padding.top==86&&p.mView.status.top==86&&p.mView.padding.bottom==600);}}
'''
  run_probe(self,{'RootInsetProbe.java':code},'RootInsetProbe')
