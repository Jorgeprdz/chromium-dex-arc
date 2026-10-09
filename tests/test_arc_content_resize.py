"""Execute Chromium's shipped resize callbacks with explicit platform boundaries.

The probe exercises native WebContents sizing and input offsets, not Android
transition rendering, DeX frame timing, or any site's desktop viewport policy.
"""
from pathlib import Path
import hashlib
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body

PATH = "chrome/android/java/src/org/chromium/chrome/browser/compositor/CompositorViewHolder.java"
SIDE_PATH = "chrome/browser/ui/side_ui/internal/android/java/src/org/chromium/chrome/browser/ui/side_ui/SideUiCoordinatorImpl.java"
ARC = ROOT / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java"
PINNED_HASHES = {
    PATH: "d97a75b795091ef8d4535c758d42ecd43d9a989049c26cc3502ec11747e6dac4",
    SIDE_PATH: "839d90432bfa48e68e7431fe34aa267dce1af1b7a557384cc9cad29bd327c69a",
}

TRANSITION_JAVA = r"""
import java.util.*;
class SideUiTransitionProbe {
    @java.lang.annotation.Target(java.lang.annotation.ElementType.TYPE_USE)
    @interface AnchorSide { int LEFT=0; } @interface Px {}
    interface Callback<T> { void onResult(T value); }
    static class ViewGroup {}
    static class View extends ViewGroup {}
    static class Activity {}
    static class ArcDesktopAppearance { static boolean desktop=true; static boolean isDesktopWindow(Activity a){return desktop;} }
    static class SideUiSize { int mReservedWidth,mRenderedWidth; SideUiSize(int w){mReservedWidth=w;mRenderedWidth=w;} }
    static class SideUiSpecs {
        final int width; SideUiSpecs(int w){width=w;}
        int getRenderedWidth(int s){return width;} int getReservedWidth(int s){return width;}
        Set<Map.Entry<Integer,SideUiSize>> entrySet(){return Map.of(0,new SideUiSize(width)).entrySet();}
    }
    static class UpdateReason { static final int SIDE_UI_REQUEST=0,RESIZE_LIVE=5,RESIZE_COMMITTED=6; }
    static class UiUpdateRequest { int mUpdateReason; }
    static class SideUiUpdateSpecs {
        SideUiSpecs mNewSpecs=new SideUiSpecs(52),mSpecsDiff=mNewSpecs,mCurrentSpecs=new SideUiSpecs(334);
        UiUpdateRequest mRequest=new UiUpdateRequest();
    }
    static class SideUiContainer {
        final SideUiTransitionProbe owner; SideUiContainer(SideUiTransitionProbe p){owner=p;}
        void setRenderedWidth(int w){owner.railLayout();}
    }
    static class TransitionSet { void addListener(Object o){} }
    static class ViewUtils { static void triggerSynchronousMeasureAndLayout(Object v){} }
    static class TransitionManager { static void beginDelayedTransition(Object root,Object set){} }
    static class SideUiContainerTransition {
        static void triggerContainerTransition(Object anchor,SideUiContainer container,int side,int oldw,int neww){container.setRenderedWidth(neww);}
    }
    static class TransitionListener {
        Callback<SideUiUpdateSpecs> callback; SideUiUpdateSpecs specs;
        void startListening(Object root,SideUiUpdateSpecs s,Callback<SideUiUpdateSpecs> c){specs=s;callback=c;}
        void end(){callback.onResult(specs);}
    }
    static class SideUiObserver {
        public void onTransitionBegun(SideUiSpecs s,UiUpdateRequest r){onSideUiSpecsChanged(s,r);}
        public void onTransitionEnded(SideUiSpecs s,UiUpdateRequest r){}
        public void onSideUiSpecsChanged(SideUiSpecs s,UiUpdateRequest r){}
    }
    class Notifier {
        void notifyTransitionBegun(SideUiSpecs s,UiUpdateRequest r){mSideUiObserver.onTransitionBegun(s,r);}
        void notifyTransitionEnded(SideUiSpecs s,UiUpdateRequest r){mSideUiObserver.onTransitionEnded(s,r);}
    }
    final Activity mActivity=new Activity(); boolean mDestroyed,mArcToolbarCompositionActive=true;
    final ViewGroup mAnchorContainerParent=new ViewGroup();
    final Map<Integer,ViewGroup> mAnchorContainers=Map.of(0,new ViewGroup());
    final SideUiContainer container=new SideUiContainer(this);
    final TransitionListener mSideUiTransitionListener=new TransitionListener();
    final Notifier mSideUiObserverNotifier=new Notifier();
    SideUiSpecs mCurrentSideUiSpecs=new SideUiSpecs(334);
    int clipLeft=334,railLayoutReserved=-1,geometryUpdates;
    final SideUiObserver mSideUiObserver=new SideUiObserver() OBSERVER;
    void applyFrameGeometry(){geometryUpdates++;clipLeft=mCurrentSideUiSpecs.width;}
    void updateSidebarControls(){applyFrameGeometry();}
    HELPER
    void railLayout(){railLayoutReserved=mCurrentSideUiSpecs.width;applyFrameGeometry();}
    ViewGroup getRootView(){return mAnchorContainerParent;}
    SideUiContainer getSideUiContainerBySide(int side){return container;}
    void attachSideUiContainerView(SideUiContainer c,int side){}
    void detachSideUiContainerView(SideUiContainer c){}
    void notifyContainersOnUiUpdateCompleted(SideUiSpecs a,SideUiSpecs b){}
    static <T> T assumeNonNull(T t){return Objects.requireNonNull(t);}
    METHOD
    static void check(boolean b,String msg){if(!b)throw new AssertionError(msg);}
    public static void main(String[] args){
        SideUiTransitionProbe p=new SideUiTransitionProbe();
        if(args[0].equals("order")){
            p.commitNewSpecsForAnimatedResize(new SideUiUpdateSpecs(),new TransitionSet());
            check(p.railLayoutReserved==334,"native final layout must reproduce old reserved width");
            check(p.clipLeft==334,"before commit the root supplier still reports expanded width");
            p.mSideUiTransitionListener.end();
            check(p.mCurrentSideUiSpecs.width==52,"native transition end must commit collapsed specs");
            check(p.clipLeft==52,"Arc clip must refresh after native specs commit: actual "+p.clipLeft);
        }else if(args[0].equals("static")){
            p.mCurrentSideUiSpecs=new SideUiSpecs(370);
            p.mSideUiObserver.onSideUiSpecsChanged(p.mCurrentSideUiSpecs,new UiUpdateRequest());
            check(p.clipLeft==370,"static/manual SideUi update must refresh clip");
        }else if(args[0].equals("destroyed")){
            p.mDestroyed=true;p.mCurrentSideUiSpecs=new SideUiSpecs(52);
            p.mSideUiObserver.onTransitionEnded(p.mCurrentSideUiSpecs,new UiUpdateRequest());
            p.mSideUiObserver.onSideUiSpecsChanged(p.mCurrentSideUiSpecs,new UiUpdateRequest());
            check(p.geometryUpdates==0,"destroyed observer callbacks must do no geometry work");
        }else if(args[0].equals("mobile")){
            p.mArcToolbarCompositionActive=false;ArcDesktopAppearance.desktop=false;
            p.mCurrentSideUiSpecs=new SideUiSpecs(0);
            p.mSideUiObserver.onTransitionEnded(p.mCurrentSideUiSpecs,new UiUpdateRequest());
            p.mSideUiObserver.onSideUiSpecsChanged(p.mCurrentSideUiSpecs,new UiUpdateRequest());
            check(p.geometryUpdates==0,"MOBILE callbacks must not restore Arc geometry");
        }
    }
}
"""

JAVA = r"""
import java.util.*;
class ContentResizeProbe {
    @interface Nullable {} @interface Px {}
    static class Point { int x=1280,y=800; }
    static class View {
        static class MarginLayoutParams { int leftMargin,rightMargin; }
        final MarginLayoutParams params=new MarginLayoutParams();
        int width=1280,height=800; boolean attached=true;
        Object getWindowToken(){return attached?this:null;}
        Object getLayoutParams(){return params;}
        void setLayoutParams(Object p){}
        void measure(int w,int h){width=w;height=h;}
        void layout(int l,int t,int r,int b){width=r-l;height=b-t;}
        int getMeasuredWidth(){return width;} int getMeasuredHeight(){return height;}
    }
    static class MarginLayoutParams extends View.MarginLayoutParams {}
    static class ContentView extends View {
        int offset; final ContentResizeProbe.MarginLayoutParams margins=new ContentResizeProbe.MarginLayoutParams();
        void setContentOffsetXPix(int x){offset=x;}
        @Override Object getLayoutParams(){return margins;}
    }
    static class MeasureSpec { static final int EXACTLY=0; static int makeMeasureSpec(int v,int m){return v;} }
    static class WebContents { int width,height,calls; void setSize(int w,int h){width=w;height=h;calls++;} }
    static class Tab {
        final WebContents web=new WebContents(); final ContentView view=new ContentView();
        boolean nativePage,custom;
        WebContents getWebContents(){return web;} ContentView getContentView(){return view;}
        boolean isNativePage(){return nativePage;} boolean isShowingCustomView(){return custom;}
    }
    static class Flag { boolean isEnabled(){return false;} }
    static class ChromeFeatureList {
        static final Flag sVirtualKeyboardTransientInnerHeightFix=new Flag();
        static final Flag sVirtualKeyboardResizesContentTransientOvershootFix=new Flag();
    }
    static class BaseFeatureList { static final Flag sVirtualKeyboardGeometryAndInsetFixes=new Flag(); }
    static class AndroidSidePanelEnabledFn { static boolean isEnabled(){return false;} }
    static class VerticalTabUtils { static boolean eligible=true; static boolean isVerticalTabsEligible(Object a){return eligible;} }
    static class AnchorSide { static final int LEFT=0,RIGHT=1; }
    static class SideUiSpecs {
        final int left,right,rendered;
        SideUiSpecs(int l,int r,int render){left=l;right=r;rendered=render;}
        int getReservedWidth(int side){return side==AnchorSide.LEFT?left:right;}
    }
    static class SideUiProvider { SideUiSpecs specs; SideUiSpecs getExpectedSideUiSpecsForTab(Tab t){return specs;} }
    static class UpdateReason { static final int RESIZE_LIVE=5,RESIZE_COMMITTED=6,SIDE_UI_REQUEST=0; }
    static class UiUpdateRequest { final int mUpdateReason; UiUpdateRequest(int r){mUpdateReason=r;} }
    static class BrowserControls {
        int getTopControlsMinHeight(){return 0;} int getBottomControlsMinHeight(){return 0;}
        int getTopControlsHeight(){return 0;} int getBottomControlsHeight(){return 0;}
    }
    static class Insets { int webContentsHeightInset; }
    static class BottomInsets { Insets getInsets(){return new Insets();} }
    static class KeyboardVisibilityDelegate {
        static KeyboardVisibilityDelegate getInstance(){return new KeyboardVisibilityDelegate();}
        boolean isKeyboardShowing(Object v){return false;}
    }
    static class VirtualKeyboardMode { static final int OVERLAYS_CONTENT=0,RESIZES_VISUAL=1; }
    static class LayoutManager { int offset; void setContentOffsetX(int x){offset=x;} }
    final Tab tab=new Tab(); ContentView mView=tab.view;
    final Object mActivity=new Object(); final LayoutManager mLayoutManager=new LayoutManager();
    final SideUiProvider mSideUiStateProvider=new SideUiProvider();
    BrowserControls mBrowserControlsManager; BottomInsets mApplicationBottomInsetSupplier;
    Runnable mDeferredWebContentsHeightInsetUpdate;
    Integer mLastViewportHeightForWebContentsSizing,mLastStableOutsetModeWebContentsHeight;
    Integer mKeyboardClosedStableWebContentsHeight,mKeyboardOpenStableWebContentsHeight;
    int mAppliedWebContentsHeightInset,mVirtualKeyboardMode=VirtualKeyboardMode.RESIZES_VISUAL;
    boolean mControlsResizeView; int viewportEvents,clipResets;
    final Point viewport=new Point(); final ArrayDeque<Runnable> queue=new ArrayDeque<>();
    Point getViewportSize(){return viewport;} Tab getCurrentTab(){return tab;}
    ContentView getContentView(){return mView;}
    void updateWebContentsSize(){updateWebContentsSize(getCurrentTab());}
    void post(Runnable r){queue.add(r);} void drain(){while(!queue.isEmpty())queue.remove().run();}
    void onViewportChanged(){viewportEvents++;} void requestRender(){}
    void commitDeferredWebContentsHeightInsetAfterLayout(){}
    boolean virtualKeyboardModeOutsetsWebContentsHeight(){return false;}
    boolean virtualKeyboardModeInsetsWebContentsHeight(){return false;}
    int getEffectiveWebContentsHeightInset(){return 0;}
    void notifyVirtualKeyboardOverlayGeometryChangeEvent(int w,int h,WebContents c){}
    void disableClipToPaddingForCurrentTab(){} void resetClipToPadding(){clipResets++;}
    METHODS
    static void check(boolean b,String msg){if(!b)throw new AssertionError(msg);}
    void specs(int left,int right,int rendered){mSideUiStateProvider.specs=new SideUiSpecs(left,right,rendered);}
    void settle(int left,int right,int rendered,int reason){
        specs(left,right,rendered);
        onSideUiSpecsChanged(mSideUiStateProvider.specs,new UiUpdateRequest(reason));drain();
    }
    public static void main(String[] args){
        ContentResizeProbe p=new ContentResizeProbe();p.settle(334,0,334,UpdateReason.SIDE_UI_REQUEST);
        if(args[0].equals("collapse")){
            SideUiSpecs collapsed=new SideUiSpecs(52,0,52);
            p.onTransitionBegun(collapsed,new UiUpdateRequest(UpdateReason.SIDE_UI_REQUEST));
            p.drain();check(p.tab.web.width==946,"upstream defers Blink resize during transition");
            p.mSideUiStateProvider.specs=collapsed;
            p.onTransitionEnded(collapsed,new UiUpdateRequest(UpdateReason.SIDE_UI_REQUEST));p.drain();
            check(p.tab.web.width==1228,"collapse must widen WebContents by282px");
            check(p.mLayoutManager.offset==52&&p.tab.view.offset==52,"layout and input offsets must collapse");
            check(p.clipResets==1,"transition must restore clipping");
            p.settle(334,0,334,UpdateReason.SIDE_UI_REQUEST);
            check(p.tab.web.width==946&&p.tab.view.offset==334,"expansion must resize and reposition content");
        }else if(args[0].equals("hover")){
            p.settle(52,0,52,UpdateReason.SIDE_UI_REQUEST);int width=p.tab.web.width;
            p.settle(52,0,334,UpdateReason.SIDE_UI_REQUEST);
            check(p.tab.web.width==width&&p.tab.view.offset==52,"hover must reserve collapsed width");
        }else if(args[0].equals("manual")){
            p.settle(370,0,370,UpdateReason.RESIZE_LIVE);
            check(p.tab.web.width==946&&p.tab.view.offset==370,"live drag translates without per-frame Blink layout");
            p.settle(370,0,370,UpdateReason.RESIZE_COMMITTED);
            check(p.tab.web.width==910&&p.tab.view.offset==370,"committed manual width must resize Blink");
        }else if(args[0].equals("mobile")){
            VerticalTabUtils.eligible=false;p.settle(0,0,0,UpdateReason.SIDE_UI_REQUEST);
            check(p.tab.web.width==1280&&p.tab.view.offset==0,"MOBILE must reclaim full viewport");
        }else if(args[0].equals("two_sides")){
            p.settle(52,250,52,UpdateReason.SIDE_UI_REQUEST);
            check(p.tab.web.width==978&&p.tab.view.offset==52,"both reservations affect width, left reservation affects input");
        }else if(args[0].equals("native")){
            p.tab.nativePage=true;p.settle(52,250,52,UpdateReason.SIDE_UI_REQUEST);
            check(p.tab.view.margins.leftMargin==52&&p.tab.view.margins.rightMargin==250,"native pages use side margins");
        }else if(args[0].equals("window")){
            p.viewport.x=900;p.settle(52,0,52,UpdateReason.SIDE_UI_REQUEST);
            check(p.tab.web.width==848,"same rail width still uses changed holder size");
        }
    }
}
"""


class ArcContentResizeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / ".source-modified" / PATH
        if not path.exists():
            path = ROOT / ".source-reference" / PATH
        source = path.read_text()
        signatures = [
            "void updateWebContentsSize(@Nullable Tab tab)",
            "private static boolean isAttachedToWindow(@Nullable View view)",
            "public void onTransitionBegun(SideUiSpecs sideUiSpecs, UiUpdateRequest request)",
            "public void onTransitionEnded(SideUiSpecs sideUiSpecs, UiUpdateRequest request)",
            "public void onSideUiSpecsChanged(SideUiSpecs sideUiSpecs, UiUpdateRequest request)",
            "private void updateForSideUiSpecs(SideUiSpecs sideUiSpecs, boolean isLiveResize)",
            "private void repositionTabViewForSideUi(SideUiSpecs sideUiSpecs)",
            "private void applySideUiContentOffsetX(SideUiSpecs sideUiSpecs)",
        ]
        methods = "\n".join(s + " " + method_body(source, re.escape(s)) for s in signatures)
        cls.tmp = tempfile.TemporaryDirectory(prefix="arc-content-resize-")
        cls.work = Path(cls.tmp.name)
        java = cls.work / "ContentResizeProbe.java"
        java.write_text(JAVA.replace("METHODS", methods))
        result = subprocess.run(["javac", "--release", "17", "-d", str(cls.work), str(java)],
                                capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_case(self, case):
        result = subprocess.run(["java", "-ea", "-cp", str(self.work), "ContentResizeProbe", case],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_collapse_and_expand_resize_native_content(self): self.run_case("collapse")
    def test_hover_keeps_collapsed_viewport(self): self.run_case("hover")
    def test_manual_drag_commits_final_content_size(self): self.run_case("manual")
    def test_mobile_reclaims_full_viewport(self): self.run_case("mobile")
    def test_both_side_reservations_and_input_offset(self): self.run_case("two_sides")
    def test_native_page_margins(self): self.run_case("native")
    def test_window_resize_uses_current_holder_dimensions(self): self.run_case("window")

    def test_test_only_native_references_match_pinned_upstream(self):
        for path, digest in PINNED_HASHES.items():
            with self.subTest(path=path):
                original = ROOT / ".source-reference" / path
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)


class ArcCommittedSideUiGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        side = ROOT / ".source-modified" / SIDE_PATH
        if not side.exists(): side = ROOT / ".source-reference" / SIDE_PATH
        signature = "private void commitNewSpecsForAnimatedResize("
        native_body = method_body(side.read_text(), re.escape(signature))
        arc_source = ARC.read_text()
        # The missing observer is the pre-fix behavior, so this remains executable
        # against the deployed baseline and fails specifically for its stale clip.
        observer = "{}"
        observer_signature = r"mSideUiObserver\s*=\s*new SideUiObserver\(\)"
        if re.search(observer_signature, arc_source):
            observer = method_body(arc_source, observer_signature)
        helper_signature = "private void onSidebarGeometryChanged()"
        helper = helper_signature + " " + method_body(arc_source, re.escape(helper_signature))
        cls.tmp = tempfile.TemporaryDirectory(prefix="arc-sideui-commit-")
        cls.work = Path(cls.tmp.name)
        java = cls.work / "SideUiTransitionProbe.java"
        native_method = "private void commitNewSpecsForAnimatedResize(SideUiUpdateSpecs uiUpdateSpecs, TransitionSet transitionSet) " + native_body
        java.write_text(TRANSITION_JAVA.replace("METHOD", native_method)
                        .replace("OBSERVER", observer).replace("HELPER", helper))
        result = subprocess.run(["javac", "--release", "17", "-d", str(cls.work), str(java)],
                                capture_output=True, text=True)
        if result.returncode: raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def run_case(self, case):
        result = subprocess.run(["java", "-ea", "-cp", str(self.work), "SideUiTransitionProbe", case],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_final_clip_uses_post_transition_reserved_width(self): self.run_case("order")
    def test_static_and_manual_commits_refresh_clip(self): self.run_case("static")
    def test_destroyed_observer_does_no_work(self): self.run_case("destroyed")
    def test_mobile_observer_does_no_arc_work(self): self.run_case("mobile")
