"""Execute delivered inset policy; synthetic dependencies are not device acceptance."""
import os,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def method(text,signature):
    start=text.index(signature);opening=text.index('{',start);end=opening+1;depth=1
    while depth:depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
def run_probe(case,files,main):
    with tempfile.TemporaryDirectory() as tmp:
        paths=[]
        for name,code in files.items():
            p=Path(tmp)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(code);paths.append(str(p))
        r=subprocess.run([shutil.which('javac'),'-d',tmp,*paths],capture_output=True,text=True);case.assertEqual(0,r.returncode,r.stderr)
        r=subprocess.run([shutil.which('java'),'-cp',tmp,main],capture_output=True,text=True);case.assertEqual(0,r.returncode,r.stderr)
class OverlayInsetTests(unittest.TestCase):
    def test_edge_owner_consumes_top_only_for_live_phone_web_and_preserves_native_paths(self):
        default=ROOT/'.source-modified/chrome/browser/ui/android/edge_to_edge/internal/java/src/org/chromium/chrome/browser/ui/edge_to_edge/EdgeToEdgeControllerImpl.java'
        source=Path(os.environ.get('ARCHIUM_EDGE_POLICY_SOURCE',str(default))).read_text()
        body=method(source,'private boolean shouldDrawTopEdgeToEdge(')
        code='''@interface Nullable {} public class EdgeProbe {
boolean mArcPhoneControlsOverlay,mStatusIndicatorVisible;Object mActivity=new Object();
static class Tab {boolean nativePage;boolean isNativePage(){return nativePage;}}
static class EdgeToEdgeUtils {static boolean supported,nativeOptIn;static boolean isEdgelessTopInsetSupported(Object a){return supported;}static boolean tabSupportsTopEdgeToEdge(Tab t){return nativeOptIn;}static boolean isRegularNtp(Tab t){return false;}}
static class NtpBackgroundType {static final int DEFAULT=0;}
static class NtpCustomizationConfigManager {static NtpCustomizationConfigManager getInstance(){return new NtpCustomizationConfigManager();}int getBackgroundType(){return 0;}}
'''+body+'''
static void check(boolean v){if(!v)throw new AssertionError("web beneath status bar policy");}
public static void main(String[] args){EdgeProbe p=new EdgeProbe();Tab tab=new Tab();check(!p.shouldDrawTopEdgeToEdge(tab));
p.mArcPhoneControlsOverlay=true;check(p.shouldDrawTopEdgeToEdge(tab));tab.nativePage=true;check(!p.shouldDrawTopEdgeToEdge(tab));tab.nativePage=false;check(!p.shouldDrawTopEdgeToEdge(null));p.mStatusIndicatorVisible=true;check(!p.shouldDrawTopEdgeToEdge(tab));
p.mArcPhoneControlsOverlay=false;p.mStatusIndicatorVisible=false;check(!p.shouldDrawTopEdgeToEdge(tab));EdgeToEdgeUtils.supported=true;EdgeToEdgeUtils.nativeOptIn=true;check(p.shouldDrawTopEdgeToEdge(tab));}}
'''
        run_probe(self,{'EdgeProbe.java':code},'EdgeProbe')
    def test_legacy_margins_clear_cutout_without_resizing_and_restore_on_editor_or_desktop(self):
        s=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        body=method(s,'private void updateArcPhoneTopInset()')
        code='''public class InsetProbe {
boolean mArcPhoneOverlayActive,mArcPhoneMarginOwned;int mArcPhoneOriginalTopMargin,mArcPhoneOriginalProgressMargin;
static class ViewGroup {static class MarginLayoutParams {int topMargin,height=147,width=904;}}
static class View {ViewGroup.MarginLayoutParams params=new ViewGroup.MarginLayoutParams();android.view.WindowInsets raw=new android.view.WindowInsets();Object getLayoutParams(){return params;}void setLayoutParams(Object p){params=(ViewGroup.MarginLayoutParams)p;}android.view.WindowInsets getRootWindowInsets(){return raw;}}
static class Controls {View view=new View();View getView(){return view;}}
static class Window {View decor=new View();View getDecorView(){return decor;}}
static class Activity {Window window=new Window();Window getWindow(){return window;}}
Controls mControlContainer=new Controls();View mProgressBarContainer=new View();Activity mActivity=new Activity();
'''+body+'''
static void check(boolean v){if(!v)throw new AssertionError("phone cutout/restoration");}
public static void main(String[] args){InsetProbe p=new InsetProbe();ViewGroup.MarginLayoutParams top=p.mControlContainer.view.params,progress=p.mProgressBarContainer.params;top.topMargin=7;progress.topMargin=148;
p.mArcPhoneOverlayActive=true;p.updateArcPhoneTopInset();check(top.topMargin==107&&progress.topMargin==248&&top.height==147&&top.width==904);p.updateArcPhoneTopInset();check(top.topMargin==107);
p.mActivity.window.decor.raw.top=0;p.mActivity.window.decor.raw.cutout.safe=0;p.updateArcPhoneTopInset();check(top.topMargin==7&&progress.topMargin==148);
p.mArcPhoneOverlayActive=false;p.updateArcPhoneTopInset();check(!p.mArcPhoneMarginOwned&&top.topMargin==7&&progress.topMargin==148);
org.chromium.chrome.browser.ui.edge_to_edge.EdgeToEdgeUtils.refactor=true;p.mArcPhoneOverlayActive=true;p.updateArcPhoneTopInset();check(!p.mArcPhoneMarginOwned&&top.topMargin==7);}}
'''
        files={'InsetProbe.java':code,
        'org/chromium/chrome/browser/arc/ArcPhoneStatusFade.java':'package org.chromium.chrome.browser.arc;public class ArcPhoneStatusFade {public static int toolbarTopInset(android.view.WindowInsets raw){return Math.max(raw.getSystemWindowInsetTop(),raw.getDisplayCutout().getSafeInsetTop());}}',
        'android/view/WindowInsets.java':'package android.view;public class WindowInsets {public int top=86;public DisplayCutout cutout=new DisplayCutout();public int getSystemWindowInsetTop(){return top;}public DisplayCutout getDisplayCutout(){return cutout;}}',
        'android/view/DisplayCutout.java':'package android.view;public class DisplayCutout {public int safe=100;public int getSafeInsetTop(){return safe;}}',
        'org/chromium/chrome/browser/ui/edge_to_edge/EdgeToEdgeUtils.java':'package org.chromium.chrome.browser.ui.edge_to_edge;public class EdgeToEdgeUtils {public static boolean refactor;public static boolean isEdgeToEdgeRefactorEnabled(){return refactor;}}'}
        run_probe(self,files,'InsetProbe')
