"""Run delivered teardown/write paths at explicit native/JNI boundaries."""
import subprocess
import tempfile
from pathlib import Path
import unittest
from test_group_projection import method
ROOT=Path(__file__).resolve().parents[1]
class ReviewLifecycleTests(unittest.TestCase):
    def test_top_strip_removal_cannot_reenter_a_dead_scene_layer(self):
        src=(ROOT/'.source-modified/chrome/browser/ui/android/tabstrip/java/src/org/chromium/chrome/browser/tabstrip/TabStripTopControlLayer.java').read_text()
        destroy=method(src,'public void destroy()')
        code='''public class TeardownProbe {
Object mTabStrip=new Object(),mTransitionState=new Object(),mTransitionFinishedCallback=new Object();
int mLockTopControlsToken=0;static class TokenHolder {static int INVALID_TOKEN=-1;void releaseToken(int t){}}
TokenHolder mLockTopControlsTokenJar=new TokenHolder();
class Stacker {void removeControl(Object o){if(mTabStrip!=null&&mTransitionState!=null)throw new AssertionError("callback uses destroyed scene layer");}}
Stacker mTopControlsStacker=new Stacker();static class Supplier {void destroy(){}}Supplier mSupplier=new Supplier();
'''+destroy+'''public static void main(String[] a){TeardownProbe p=new TeardownProbe();p.destroy();if(p.mLockTopControlsToken!=-1)throw new AssertionError("lock leaked");}}'''
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'TeardownProbe.java';path.write_text(code)
            subprocess.run(['javac',str(path)],check=True,capture_output=True)
            r=subprocess.run(['java','-cp',d,'TeardownProbe'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_collection_metadata_requests_immediate_disk_write_only_for_its_key(self):
        src=(ROOT/'.source-modified/components/prefs/android/pref_service_android.cc').read_text()
        start=src.index('void PrefServiceAndroid::SetString(')
        end=src.index('\nbool PrefServiceAndroid::IsManagedPreference',start)
        body=src[start:end]
        code=r'''#include <string>
#include <cassert>
using jstring=std::string;using JNIEnv=int;
template<class T>using JavaRef=T;
namespace base {namespace android {template<class T>using JavaRef=T;
std::string ConvertJavaStringToUTF8(JNIEnv*,const std::string& s){return s;}}}
struct Prefs {int commits=0;std::string key,value;void SetString(const std::string& k,const std::string& v){key=k;value=v;}void CommitPendingWrite(){commits++;}};
struct PrefServiceAndroid {Prefs* pref_service_;void SetString(JNIEnv*,const std::string&,const std::string&);};
'''+body+r'''
int main(){Prefs prefs;PrefServiceAndroid bridge{&prefs};bridge.SetString(nullptr,"ordinary.preference","a");assert(prefs.commits==0);bridge.SetString(nullptr,"archium.sidebar.state","nested-folder");assert(prefs.value=="nested-folder");assert(prefs.commits==1);}
'''
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'prefs.cc';path.write_text(code)
            subprocess.run(['g++','-std=c++20',str(path),'-o',d+'/probe'],check=True,capture_output=True)
            r=subprocess.run([d+'/probe'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_expanded_desktop_pins_show_titles_while_collapsed_and_phone_stay_native(self):
        src=(ROOT/'.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java').read_text()
        decision=method(src,'private static boolean shouldShowIconOnly(')
        code='''public class PinnedTitleProbe {
static boolean desktop;static class View {Object getContext(){return this;}}
static class TabProperties {static int RAIL_COLLAPSE_STATE=0;}
static class PropertyModel {int state;int get(int k){return state;}}
static boolean isPinned(PropertyModel m,View v){return true;}
static class ArcDesktopAppearance {static boolean isDesktopWindow(Object c){return desktop;}}
static class VerticalTabRailCollapseController {
static boolean shouldShowIconOnly(int state,boolean pin){return pin||state==1;}
}
'''+decision+'''public static void main(String[] a){PropertyModel m=new PropertyModel();View v=new View();
desktop=true;if(shouldShowIconOnly(m,v))throw new AssertionError("expanded Desktop pin title hidden");
m.state=1;if(!shouldShowIconOnly(m,v))throw new AssertionError("collapsed rail changed");
m.state=0;desktop=false;if(!shouldShowIconOnly(m,v))throw new AssertionError("native phone changed");}}'''
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'PinnedTitleProbe.java';path.write_text(code)
            subprocess.run(['javac',str(path)],check=True,capture_output=True)
            r=subprocess.run(['java','-cp',d,'PinnedTitleProbe'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_new_desktop_pin_titles_follow_space_contrast(self):
        src=(ROOT/'.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java').read_text()
        body=method(src,'private static void updatePinnedColors(')
        code='''public class PinContrastProbe {
@interface Nullable {}static boolean desktop=true;static class PropertyModel {boolean get(int k){return false;}}
static class TabProperties {static int IS_SELECTED;}
static class ColorStateList {static ColorStateList valueOf(int c){return new ColorStateList();}}
static class R {static class color {static int gm3_baseline_surface_container_high_dark;}}
static class Context {int getColor(int id){return 0;}}static class Text {int color;void setTextColor(int c){color=c;}}
static class VerticalTabItemLayout {Context context=new Context();Text title=new Text();Context getContext(){return context;}Text getTitleView(){return title;}}
static class ArcDesktopAppearance {static boolean isDesktopWindow(Context c){return desktop;}}
static boolean isIncognito(PropertyModel m){return false;}static int getTextColor(Context c,boolean s,boolean i){return -1;}
static void updateSelectionAndBackground(PropertyModel m,VerticalTabItemLayout v,ColorStateList c){}
'''+body+'''public static void main(String[] a){VerticalTabItemLayout v=new VerticalTabItemLayout();updatePinnedColors(new PropertyModel(),v);if(v.title.color!=-1)throw new AssertionError("dark Space receives unreadable native light-theme title");desktop=false;v.title.color=0;updatePinnedColors(new PropertyModel(),v);if(v.title.color!=0)throw new AssertionError("native phone colors changed");}}
'''
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'PinContrastProbe.java';path.write_text(code)
            subprocess.run(['javac',str(path)],check=True,capture_output=True)
            r=subprocess.run(['java','-cp',d,'PinContrastProbe'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
