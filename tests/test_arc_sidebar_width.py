"""Execute native saved-width/feature defaults and the real Arc width allocator.

Preferences, field trials and dp conversion are explicit host boundaries. This
does not establish the values an installed APK receives from DeX window metrics.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body, window_core_jar

UTILS = ROOT / ".source-modified/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/VerticalTabUtils.java"
SIDE = ROOT / ".source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabsSideUiCoordinator.java"
ROOT_UI = ROOT / ".source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java"

JAVA = r"""
import java.util.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class SidebarWidthProbe {
    @interface Px {} @interface WindowWidthBoundary {
        int NOT_SHOWABLE=0,FORCED_COLLAPSED=1,DYNAMIC_EXPANDABLE=2,FULLY_EXPANDABLE=3;
    }
    @interface RailCollapseState { int COLLAPSED=0,EXPANDED_FOR_HOVERING=1,EXPANDED=2; }
    static class Metrics { float density=1; }
    static class Resources { final Metrics metrics=new Metrics(); Metrics getDisplayMetrics(){return metrics;} }
    static class Context { final Resources resources=new Resources(); Resources getResources(){return resources;} }
    static class View { final Context context=new Context(); Context getContext(){return context;} }
    static class ViewUtils {
        static int dpToPx(Context c,int dp){return Math.round(dp*c.resources.metrics.density);}
    }
    static class MathUtils { static int clamp(int v,int lo,int hi){return Math.max(lo,Math.min(hi,v));} }
    static class ArcDesktopAppearance { static boolean arc=true; static boolean isDesktopWindow(Context c){return arc;} }
    static class ChromeFeatureList {
        static final String ANDROID_VERTICAL_TABS="AndroidVerticalTabs";
        static Boolean manual;
        static boolean getFieldTrialParamByFeatureAsBoolean(String f,String p,boolean d){return manual==null?d:manual;}
    }
    static class ChromePreferenceKeys { static final String VERTICAL_TABS_USER_RESIZED_WIDTH_DP="Chrome.VerticalTabs.UserResizedWidthDp"; }
    static class ChromeSharedPreferences {
        static final ChromeSharedPreferences INSTANCE=new ChromeSharedPreferences();
        final Map<String,Integer> values=new HashMap<>();
        static ChromeSharedPreferences getInstance(){return INSTANCE;}
        int readInt(String k,int d){return values.getOrDefault(k,d);}
        void writeInt(String k,int v){values.put(k,v);} void removeKey(String k){values.remove(k);}
    }
    static class VerticalTabUtils {
        CONSTANTS
        UTILS_METHODS
    }
    final View mRootView=new View(); int mExpandedViewWidth,mCollapsedViewWidth,mMinManualWidth,mMaxManualWidth,mLiveResizeWidth;
    SidebarWidthProbe(float density){
        mRootView.context.resources.metrics.density=density;
        mExpandedViewWidth=ViewUtils.dpToPx(mRootView.context,VerticalTabUtils.SIDE_UI_CONTAINER_WIDTH_DP);
        mCollapsedViewWidth=ViewUtils.dpToPx(mRootView.context,VerticalTabUtils.SIDE_UI_CONTAINER_COLLAPSED_WIDTH_DP);
        mMinManualWidth=ViewUtils.dpToPx(mRootView.context,VerticalTabUtils.MIN_EXPANDED_WIDTH_DP);
        mMaxManualWidth=ViewUtils.dpToPx(mRootView.context,VerticalTabUtils.MAX_EXPANDED_WIDTH_DP);
    }
    ALLOCATOR
    static class SideUiCoordinator {
        static class SideUiId {static final int VERTICAL_TABS=1;}
        static class UiUpdateRequest {final int id; final boolean suppressAnimations;
            UiUpdateRequest(int id,boolean suppressAnimations){this.id=id;this.suppressAnimations=suppressAnimations;}}
        int updates;void updateUi(UiUpdateRequest request){
            check(request.id==1&&request.suppressAnimations,"automatic width must reallocate native rail synchronously");updates++;}
    }
    SideUiCoordinator mSideUiCoordinator=new SideUiCoordinator();
    RESET_ACTION
    int width(int state,int window,int available){return calculateRenderedWidthPx(3,state,window,available);}
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    public static void main(String[] args){
        SidebarWidthProbe p=new SidebarWidthProbe(1);
        if(args[0].equals("defaults")){
            check(!VerticalTabUtils.isManualResizeEnabled(),"manual flag defaults false");
            check(VerticalTabUtils.getUserResizedWidthDp()==0,"absent preference must denote no user resize");
            check(p.width(2,1628,1216)==393,"fresh ARC at measured window1628 must allocate393px");
            check(ChromeSharedPreferences.INSTANCE.values.isEmpty(),"default allocation must not write a manual preference");
        }else if(args[0].equals("enabled_no_preference")){
            ChromeFeatureList.manual=true;
            check(p.width(2,1628,1216)==393,"manual feature enabled without saved resize must use reference ratio");
        }else if(args[0].equals("intentional")){
            ChromeFeatureList.manual=true;VerticalTabUtils.setUserResizedWidthDp(206);
            check(p.width(2,1628,1216)==206,"intentional user206dp width must remain authoritative");
            p.mLiveResizeWidth=370;check(p.width(2,1628,1216)==370,"live manual width must override persisted width");
            p.mLiveResizeWidth=0;ChromeFeatureList.manual=false;
            check(p.width(2,1628,1216)==393,"disabled manual feature must use automatic ARC width");
            check(VerticalTabUtils.getUserResizedWidthDp()==206,"automatic allocation must preserve intentional width for later reenable");
        }else if(args[0].equals("clear")){
            ChromeFeatureList.manual=true;VerticalTabUtils.setUserResizedWidthDp(206);
            VerticalTabUtils.setUserResizedWidthDp(0);
            check(p.width(2,1628,1216)==393,"explicitly cleared preference returns to adaptive width");
        }else if(args[0].equals("action")){
            ChromeFeatureList.manual=true;VerticalTabUtils.setUserResizedWidthDp(206);
            check(p.width(2,1628,1216)==206,"explicit user width remains unchanged until reset action");
            p.resetArcSidebarWidth();
            check(p.width(2,1628,1216)==393,"automatic width action returns to reference ratio");
            check(p.mSideUiCoordinator.updates==1,"automatic action must notify native SideUi");
            p.mSideUiCoordinator=null;p.resetArcSidebarWidth();
            check(p.width(2,1628,1216)==393,"early or detached reset does not crash or corrupt default");
        }else if(args[0].equals("clamps")){
            check(p.width(2,1628,180)==180,"automatic width cannot consume native minimum content allocation");
            ChromeFeatureList.manual=true;VerticalTabUtils.setUserResizedWidthDp(600);
            check(p.width(2,1628,1216)==500,"manual width respects native max500dp");
            check(p.width(2,1628,180)==180,"manual width cannot consume native minimum content allocation");
            VerticalTabUtils.setUserResizedWidthDp(20);
            check(p.width(2,1628,1216)==92,"manual width respects native minimum92dp");
        }else if(args[0].equals("collapse_hover")){
            ChromeFeatureList.manual=true;VerticalTabUtils.setUserResizedWidthDp(400);
            check(p.width(0,1628,1216)==52,"compact width remains52dp despite manual preference");
            check(p.width(1,1628,1216)==240,"hover renders native overlay without applying automatic ratio");
        }else if(args[0].equals("mobile")){
            ArcDesktopAppearance.arc=false;
            check(p.width(2,1628,1216)==240,"MOBILE retains native240dp expanded width");
        }else if(args[0].equals("density")){
            SidebarWidthProbe high=new SidebarWidthProbe(2);
            check(high.width(2,1628,804)==420,"navigation minimum scales with density and stays within available width");
            ChromeFeatureList.manual=true;VerticalTabUtils.setUserResizedWidthDp(206);
            check(high.width(2,1628,804)==412,"saved width is dp and converts to current display pixels");
            check(high.width(0,1628,804)==104,"compact52dp scales with display density");
        }else if(args[0].equals("input")){
            check(p.width(2,852,440)==210,"852px window uses centralized navigation minimum210px");
            check(p.width(2,1628,1216)==393,"larger actual window is required for measured reference ratio");
        }
    }
}
"""


class ArcSidebarWidthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        utils = UTILS.read_text()
        names = ["SIDE_UI_CONTAINER_WIDTH_DP", "SIDE_UI_CONTAINER_COLLAPSED_WIDTH_DP",
                 "MIN_EXPANDED_WIDTH_DP", "MAX_EXPANDED_WIDTH_DP", "EXPANDED_WINDOW_WIDTH_RATIO"]
        constants = "\n".join(re.search(r"public static final (?:int|float) " + name + r"\s*=.*?;", utils).group()
                              for name in names)
        signatures = ["public static boolean isManualResizeEnabled()",
                      "public static int getUserResizedWidthDp()",
                      "public static void setUserResizedWidthDp(int widthDp)"]
        methods = "\n".join(s + " " + method_body(utils, re.escape(s)) for s in signatures)
        signature = "private @Px int calculateRenderedWidthPx("
        allocator = ("private int calculateRenderedWidthPx(int boundary, int effectiveState, int windowWidthPx, int availableWidthPx) "
                     + method_body(SIDE.read_text(), re.escape(signature)))
        cls.tmp = tempfile.TemporaryDirectory(prefix="arc-native-width-")
        cls.work = Path(cls.tmp.name)
        java = cls.work / "SidebarWidthProbe.java"
        root=ROOT_UI.read_text();signature='private void resetArcSidebarWidth()'
        action=signature+' '+(method_body(root,re.escape(signature)) if signature in root else '{}')
        java.write_text(JAVA.replace("CONSTANTS", constants).replace("UTILS_METHODS", methods).replace("ALLOCATOR", allocator).replace("RESET_ACTION", action))
        cls.jar = window_core_jar()
        sources = list((ROOT / "chromium").rglob("ArcDesktopPolicy.java"))
        sources += list((ROOT / "chromium").rglob("ArchiumWindowClass.java"))
        result = subprocess.run(["javac", "--release", "17", "-cp", str(cls.jar), "-d", str(cls.work),
                                 *map(str, sources), str(java)], capture_output=True, text=True)
        if result.returncode: raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def run_case(self, case):
        result = subprocess.run(["java", "-ea", "-cp", str(self.work) + ":" + str(self.jar),
                                 "SidebarWidthProbe", case], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_saved_width_uses_measured_reference_ratio(self): self.run_case("defaults")
    def test_enabled_manual_flag_without_preference_uses_reference_ratio(self): self.run_case("enabled_no_preference")
    def test_intentional_manual_width_and_live_drag_remain_authoritative(self): self.run_case("intentional")
    def test_explicit_clear_returns_to_automatic_width(self): self.run_case("clear")
    def test_sidebar_automatic_width_action_updates_native_geometry(self): self.run_case("action")
    def test_native_content_and_manual_width_bounds(self): self.run_case("clamps")
    def test_collapse_and_hover_preserve_native_sizes(self): self.run_case("collapse_hover")
    def test_mobile_native_default_width(self): self.run_case("mobile")
    def test_saved_width_uses_display_density(self): self.run_case("density")
    def test_allocator_follows_received_window_width(self): self.run_case("input")
