"""Opt-in native menu bridge; synthetic Activity/View boundary, no visual acceptance."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method, run_probe
ROOT=Path(__file__).resolve().parents[1]
class NativeMenuGlassTests(unittest.TestCase):
 def test_native_default_and_phone_attachment(self):
  p=ROOT/'.source-modified/ui/android/java/src/org/chromium/ui/base/ViewUtils.java'
  self.assertTrue(p.exists(),'Native menu backdrop bridge missing')
  s=p.read_text()
  code='''public class MenuBridgeProbe {
static class Context{} static class Activity extends Context {Window window=new Window();Window getWindow(){return window;}}
static class ContextUtils {static Activity activityFromContext(Context c){return c instanceof Activity?(Activity)c:null;}}
static class Window {View decor=new View(null);View getDecorView(){return decor;}}
static class R {static class id {static int arc_phone_surface_decorator=1,arc_phone_surface_layers=2;}}
static class View {Context context;Object tag,layers;boolean attached;OnAttachStateChangeListener listener;
View(Context c){context=c;}Context getContext(){return context;}Object getTag(int id){return tag;}void setTag(int id,Object v){layers=v;}boolean isAttachedToWindow(){return attached;}void addOnAttachStateChangeListener(OnAttachStateChangeListener l){listener=l;}
interface OnAttachStateChangeListener {void onViewAttachedToWindow(View v);void onViewDetachedFromWindow(View v);}}
'''+method(s,'public static boolean attachArcPhoneSurface(').replace('org.chromium.ui.R.id','R.id')+'''
public static void main(String[] args){Activity a=new Activity();View owner=new View(a),surface=new View(a);if(attachArcPhoneSurface(owner,surface)||surface.listener!=null)throw new AssertionError("native/Desktop default changed");int[] calls={0};View.OnAttachStateChangeListener l=new View.OnAttachStateChangeListener(){public void onViewAttachedToWindow(View v){calls[0]++;}public void onViewDetachedFromWindow(View v){calls[0]--;}};a.window.decor.tag=l;if(!attachArcPhoneSurface(owner,surface)||surface.listener!=l||calls[0]!=0)throw new AssertionError();surface.listener.onViewAttachedToWindow(surface);surface.listener.onViewDetachedFromWindow(surface);if(calls[0]!=0)throw new AssertionError("lifecycle");surface.attached=true;attachArcPhoneSurface(owner,surface);if(calls[0]!=1)throw new AssertionError("attached surface");if(attachArcPhoneSurface(new View(new Context()),surface))throw new AssertionError("non Activity");}}
'''
  run_probe(self,{'MenuBridgeProbe.java':code},'MenuBridgeProbe')
 def test_native_owners_opt_in(self):
  files={
   'chrome/browser/ui/android/appmenu/internal/java/src/org/chromium/chrome/browser/ui/appmenu/AppMenu.java':['attachArcPhoneSurface(anchorView, contentView,','attachArcPhoneSurface(view, contentView,'],
   'components/page_info/android/java/src/org/chromium/components/page_info/PageInfoDialog.java':['attachArcPhoneSurface(containerView, mScrollView,'],
  }
  files['components/browser_ui/widget/android/java/src/org/chromium/components/browser_ui/widget/ContextMenuDialog.java']=['attachArcPhoneSurface(', 'ownerActivity.getWindow().getDecorView(), contentView)']
  for path,needles in files.items():
   file=ROOT/'.source-modified'/path
   self.assertTrue(file.exists(),path)
   for needle in needles:self.assertIn(needle,file.read_text())
