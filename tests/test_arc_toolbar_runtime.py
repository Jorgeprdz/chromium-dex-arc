"""Execute actual toolbar/callback method bodies at controlled Java boundaries.

View/window and Chromium service doubles model the two recorded crash contracts.
These host probes do not claim Android rendering or full Arc activity acceptance.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import toolbar_body, transition_bodies


JAVA = r'''
import java.util.*;

public class ArcToolbarRuntimeBoundaryTest {
    interface Parent { Parent getParent(); }
    static class WindowRoot implements Parent { public Parent getParent() { return null; } }
    static class View implements Parent {
        Parent parent; Object token; int x,y,windowX,windowY;
        public Parent getParent() { return parent; }
        float getX() { return x; } float getY() { return y; }
        int getPaddingLeft() { return 2; } int getPaddingTop() { return 3; }
        int getPaddingRight() { return 1; } int getPaddingBottom() { return 2; }
        int getWidth() { return 80; } int getHeight() { return 30; }
        Object getWindowToken() { return token; }
        void getLocationInWindow(int[] result) { result[0]=windowX; result[1]=windowY; }
    }
    static class ViewGroup extends View {}
    static class Rect {
        int left,top,right,bottom;
        void set(int l,int t,int r,int b) { left=l;top=t;right=r;bottom=b; }
        void setEmpty() { set(0,0,0,0); }
        void offset(int x,int y) { left+=x;right+=x;top+=y;bottom+=y; }
        public String toString() { return left+","+top+","+right+","+bottom; }
    }
    static class LocationBar { View view; View getContainerView() { return view; } }
    static class ViewUtils {
        // Characterize the unmodified upstream ancestor-only contract seen in t7i.e.
        static void getRelativeDrawPosition(ViewGroup root,View view,int[] result) {
            result[0]=result[1]=0;
            while (view!=null && view!=root) {
                result[0]+=(int)view.getX();result[1]+=(int)view.getY();
                if (view.getParent()==root) return;
                view=(View)view.getParent();
            }
        }
    }
    static class Toolbar extends ViewGroup {
        final int[] mTempPosition=new int[2]; final LocationBar bar=new LocationBar();
        LocationBar getLocationBar() { return bar; }
        void getLocationBarContentRect(Rect outRect) __TOOLBAR_BODY__
    }
    interface PauseResumeWithNativeObserver { void onResumeWithNative(); void onPauseWithNative(); }
    static class Transition {
        final List<Boolean> suppressed=new ArrayList<>();
        void suppressTabStrip(boolean value) { suppressed.add(value); }
    }
    static class Manager {
        Transition transition;
        Transition getTabStripTransitionCoordinator() { return transition; }
    }
    static class Dispatcher {
        PauseResumeWithNativeObserver observer;
        int removals;
        void register(PauseResumeWithNativeObserver value) { observer=value; }
        void unregister(PauseResumeWithNativeObserver value) { observer=null;removals++; }
    }
    static class ApplicationStatus { static int state; static int getStateForActivity(Object a) { return state; } }
    static class ActivityState { static final int PAUSED=4,STOPPED=5; }
    static class TextUtils { static boolean equals(String a,String b) { return Objects.equals(a,b); } }
    static class ChromePreferenceKeys { static final String VERTICAL_TABS_ENABLED="vertical"; }
    static class VerticalTabUtils { static boolean enabled; static boolean isVerticalTabsEnabled(Object a) { return enabled; } }
    static class Controls { int updates; void updateToolbarRightOffset() { updates++; } }
    static class SideUi { boolean visible; void setVisible(boolean value,boolean noAnimations) { visible=value; } }
    static class Tabs {
        final Object mActivity=new Object(); final Manager mToolbarManager=new Manager();
        final Dispatcher mActivityLifecycleDispatcher=new Dispatcher();
        final Controls mControlContainer=new Controls(); final SideUi mVerticalTabsSideUiCoordinator=new SideUi();
        PauseResumeWithNativeObserver mPendingUnsuppressTabStripObserver;
        boolean switching=true;
        static <T> T assumeNonNull(T value) { return value; }
        void setTabLayoutSwitchingInProgress(boolean value) { switching=value; }
        void showVerticalTabs(boolean value) { mVerticalTabsSideUiCoordinator.setVisible(value,false); }
        private void onVerticalTabsActiveChanged(boolean active) __ACTIVE_BODY__
        private void maybeClearPendingTabStripUnsuppression() __CLEAR_BODY__
        void preferenceChanged(Object prefs,String key) __PREFERENCE_BODY__
    }
    static void check(boolean okay,String message) { if (!okay) throw new AssertionError(message); }
    public static void main(String[] args) {
        String scenario=args[0];
        if (scenario.startsWith("geometry")) {
            Object window=new Object();
            Toolbar toolbar=new Toolbar();toolbar.parent=new WindowRoot();toolbar.token=window;
            toolbar.windowX=130;toolbar.windowY=240;
            View bar=new View();bar.token=window;bar.x=12;bar.y=14;toolbar.bar.view=bar;
            if (scenario.equals("geometry-descendant")) {
                bar.parent=toolbar;bar.windowX=142;bar.windowY=254;
            } else {
                ViewGroup arcHeader=new ViewGroup();arcHeader.parent=toolbar.parent;
                bar.parent=arcHeader;bar.windowX=115;bar.windowY=286;
                if (scenario.equals("geometry-detached")) { bar.parent=null;bar.token=null; }
                if (scenario.equals("geometry-other-window")) bar.token=new Object();
            }
            Rect rect=new Rect();toolbar.getLocationBarContentRect(rect);
            String expected=scenario.equals("geometry-descendant") ? "14,17,91,42"
                : scenario.equals("geometry-reparented") ? "-13,49,64,74" : "0,0,0,0";
            check(rect.toString().equals(expected),"wrong toolbar-relative rect:"+rect);
        } else {
            Tabs tabs=new Tabs();
            boolean tablet=scenario.startsWith("tablet");
            if (tablet) tabs.mToolbarManager.transition=new Transition();
            if (scenario.endsWith("preference")) {
                VerticalTabUtils.enabled=true;tabs.preferenceChanged(null,"vertical");
                if (tablet) check(tabs.mToolbarManager.transition.suppressed.equals(List.of(true)),"tablet suppression lost");
                else check(tabs.mVerticalTabsSideUiCoordinator.visible && !tabs.switching,"phone shelf never shown/switching stuck");
                check(tabs.mControlContainer.updates==1,"toolbar offset update lost");
            } else if (scenario.equals("tablet-paused")) {
                ApplicationStatus.state=ActivityState.PAUSED;
                tabs.onVerticalTabsActiveChanged(false);
                check(tabs.mToolbarManager.transition.suppressed.isEmpty(),"unsuppressed before resume");
                check(tabs.mPendingUnsuppressTabStripObserver!=null,"resume observer missing");
                tabs.mPendingUnsuppressTabStripObserver.onResumeWithNative();
                check(tabs.mToolbarManager.transition.suppressed.equals(List.of(false)),"resume unsuppression lost");
                check(tabs.mPendingUnsuppressTabStripObserver==null && tabs.mActivityLifecycleDispatcher.removals==1,"stale observer");
            } else {
                boolean active=scenario.equals("phone-active") || scenario.equals("tablet-active");
                if (scenario.equals("phone-pending")) {
                    tabs.mPendingUnsuppressTabStripObserver=new PauseResumeWithNativeObserver() {
                        public void onResumeWithNative() {} public void onPauseWithNative() {}
                    };
                }
                tabs.onVerticalTabsActiveChanged(active);
                check(!tabs.switching && tabs.mPendingUnsuppressTabStripObserver==null,"pending transition state not cleared");
                if (tablet) check(tabs.mToolbarManager.transition.suppressed.equals(List.of(active)),"tablet suppression changed");
                if (scenario.equals("phone-pending")) check(tabs.mActivityLifecycleDispatcher.removals==1,"observer not unregistered");
            }
        }
        System.out.println("PASS "+scenario);
    }
}
'''


class ArcToolbarRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        active, clear, preference = transition_bodies()
        source = JAVA.replace('__TOOLBAR_BODY__', toolbar_body()).replace(
            '__ACTIVE_BODY__', active).replace('__CLEAR_BODY__', clear).replace(
            '__PREFERENCE_BODY__', preference)
        path = cls.work / 'ArcToolbarRuntimeBoundaryTest.java'
        path.write_text(source)
        subprocess.run(['javac', '-d', str(cls.work), str(path)],
                       check=True, capture_output=True, text=True)

    def probe(self, scenario):
        result = subprocess.run(['java', '-ea', '-cp', str(self.work),
                                 'ArcToolbarRuntimeBoundaryTest', scenario],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS ' + scenario, result.stdout)

    def test_reparented_omnibox_uses_toolbar_relative_window_coordinates(self):
        self.probe('geometry-reparented')

    def test_native_descendant_omnibox_keeps_original_draw_coordinates(self):
        self.probe('geometry-descendant')

    def test_detached_or_other_window_omnibox_has_no_capture_rect(self):
        for scenario in ['geometry-detached', 'geometry-other-window']:
            with self.subTest(scenario=scenario): self.probe(scenario)

    def test_phone_vertical_tab_callbacks_allow_absent_horizontal_strip(self):
        for scenario in ['phone-active', 'phone-inactive', 'phone-pending']:
            with self.subTest(scenario=scenario): self.probe(scenario)

    def test_phone_preference_shows_shelf_without_waiting_for_horizontal_transition(self):
        self.probe('phone-preference')

    def test_tablet_horizontal_strip_suppression_survives(self):
        for scenario in ['tablet-active', 'tablet-inactive', 'tablet-preference', 'tablet-paused']:
            with self.subTest(scenario=scenario): self.probe(scenario)
