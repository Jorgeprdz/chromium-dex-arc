"""Run shipped coordinator geometry/lifecycle bodies with explicit view-boundary doubles.

These tests prove arithmetic and mutations, never Android SurfaceView rendering.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body

COORD = ROOT / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java"
JAVA = r"""
import java.util.*;
import java.util.function.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class FrameRegression {
    static class Rect {
        int left,top,right,bottom;
        Rect(){} Rect(int l,int t,int r,int b){set(l,t,r,b);}
        void set(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}
        boolean isEmpty(){return right<=left||bottom<=top;}
        void setEmpty(){set(0,0,0,0);}
        public boolean equals(Object o){if(!(o instanceof Rect))return false;Rect v=(Rect)o;return left==v.left&&top==v.top&&right==v.right&&bottom==v.bottom;}
    }
    static class ViewOutlineProvider {}
    static class Drawable {}
    static class Metrics {float density=1f;}
    static class Resources {Metrics getDisplayMetrics(){return new Metrics();}}
    static class Activity {Resources getResources(){return new Resources();}}
    static class View {
        int width=1382,height=863,x,y,paddingLeft,paddingTop,paddingRight,paddingBottom,layouts,invalidations,listeners;
        ViewGroup.LayoutParams params=new ViewGroup.MarginLayoutParams();
        ViewOutlineProvider outline=new ViewOutlineProvider();boolean clip;Rect clipBounds;
        int getWidth(){return width;}int getHeight(){return height;}
        int getPaddingLeft(){return paddingLeft;}int getPaddingTop(){return paddingTop;}
        int getPaddingRight(){return paddingRight;}int getPaddingBottom(){return paddingBottom;}
        float getX(){return x;}float getY(){return y;}
        void getLocationInWindow(int[] a){a[0]=x;a[1]=y;}
        void setPadding(int l,int t,int r,int b){paddingLeft=l;paddingTop=t;paddingRight=r;paddingBottom=b;}
        ViewGroup.LayoutParams getLayoutParams(){return params;}
        void setLayoutParams(ViewGroup.LayoutParams p){params=p;layouts++;}
        void setOutlineProvider(ViewOutlineProvider p){outline=p;}
        ViewOutlineProvider getOutlineProvider(){return outline;}
        boolean getClipToOutline(){return clip;}void setClipToOutline(boolean b){clip=b;}
        Rect getClipBounds(){return clipBounds;}void setClipBounds(Rect r){clipBounds=r;}
        void invalidateOutline(){invalidations++;}
        void setBackgroundColor(int c){}void setBackground(Drawable d){}
        void addOnAttachStateChangeListener(Object o){listeners++;}void removeOnAttachStateChangeListener(Object o){listeners--;}
        void removeCallbacks(Runnable r){}
    }
    static class ViewGroup extends View {
        static class LayoutParams {}
        static class MarginLayoutParams extends LayoutParams {int leftMargin,topMargin,rightMargin,bottomMargin;}
    }
    static class FullscreenManager {boolean fullscreen;boolean getPersistentFullscreenMode(){return fullscreen;}}
    static class CompositorViewHolder extends ViewGroup {View active;FullscreenManager fullscreen=new FullscreenManager();FullscreenManager getFullscreenManager(){return fullscreen;}View getActiveSurfaceView(){return active;}}
    static class SurfaceHolder {
        interface Callback {void surfaceCreated(SurfaceHolder h);void surfaceChanged(SurfaceHolder h,int f,int w,int t);void surfaceDestroyed(SurfaceHolder h);}
        int callbacks;void addCallback(Callback c){callbacks++;}void removeCallback(Callback c){callbacks--;}
    }
    static class SurfaceView extends View {SurfaceHolder holder=new SurfaceHolder();SurfaceHolder getHolder(){return holder;}}
    static class ArcDesktopAppearance {static int surface(Activity a,boolean b){return 0;}}
    static class Incognito {boolean isIncognitoSelected(){return false;}}
    final Activity mActivity=new Activity();final View mRail=new View();final View mFrameRoot=new View();
    final CompositorViewHolder mCompositorViewHolder=new CompositorViewHolder();
    final Supplier<Integer> mReservedLeftWidth=()->334;final Incognito mIncognitoStateProvider=new Incognito();
    final ViewOutlineProvider mArcContentOutlineProvider=new ViewOutlineProvider();
    final ViewOutlineProvider mOriginalContentOutlineProvider=mCompositorViewHolder.outline;
    final ViewOutlineProvider mArcFrameOutlineProvider=new ViewOutlineProvider();
    final ViewOutlineProvider mOriginalFrameOutlineProvider=mFrameRoot.outline;
    final boolean mOriginalFrameClipToOutline=false;
    final Drawable mOriginalFrameBackground=new Drawable(); final boolean mOriginalContentClipToOutline=false;
    final int mOriginalContentMarginLeft=0,mOriginalContentMarginTop=0,mOriginalContentMarginRight=0,mOriginalContentMarginBottom=0;
    final int mOriginalRailPaddingLeft=0,mOriginalRailPaddingTop=0,mOriginalRailPaddingRight=0,mOriginalRailPaddingBottom=0;
    final Object mSurfaceAttachStateListener=new Object();
    final SurfaceHolder.Callback mSurfaceCallback=null;
    final Runnable mGeometryUpdate=()->{};
    boolean mDestroyed,mArcToolbarCompositionActive=true,mArcFrameActive,mRejectingRoundedCornerGesture;
    View mClippedSurface;ViewOutlineProvider mClippedSurfaceOriginalOutlineProvider;boolean mClippedSurfaceOriginalClipToOutline;
    Rect mClippedSurfaceOriginalClipBounds;
    ArcDesktopPolicy.Geometry mFrameGeometry;
    int dp(int n){return n;}
    METHODS
    static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    public static void main(String[]args) {
        FrameRegression r=new FrameRegression();String scenario=args[0];
        if(scenario.equals("frame")) {
            r.applyFrameGeometry();var p=(ViewGroup.MarginLayoutParams)r.mCompositorViewHolder.params;
            check(p.leftMargin==0,"sidebar/content edge must not gain an artificial8dp gap");
            check(p.topMargin==12&&p.rightMargin==11&&p.bottomMargin==11,"reference insets are12/11/11");
            check(r.mRail.paddingTop==0&&r.mRail.paddingBottom==0,"sidebar must reach full window height");
            check(r.mFrameRoot.clip,"outer frame must respect reference rounding");
            int layouts=r.mCompositorViewHolder.layouts;r.applyFrameGeometry();
            check(r.mCompositorViewHolder.layouts==layouts,"stable geometry must not request repeated layouts");
            r.clearFrameGeometry();check(!r.mFrameRoot.clip,"MOBILE restores frame outline clipping");check(p.topMargin==0&&p.rightMargin==0&&p.bottomMargin==0,"MOBILE restores all original margins");
        } else if(scenario.equals("inactive")) {
            r.mArcToolbarCompositionActive=false;r.applyFrameGeometry();
            check(!r.mArcFrameActive&&r.mCompositorViewHolder.layouts==0,"queued geometry must not resurrect Arc after MOBILE");
        } else if(scenario.equals("surface")) {
            SurfaceView first=new SurfaceView();ViewOutlineProvider original=first.outline;
            r.mCompositorViewHolder.active=first;r.applyFrameGeometry();check(first.clip,"live surface must be clipped");
            SurfaceView next=new SurfaceView();r.mCompositorViewHolder.active=next;r.applyActiveSurfaceClip();
            check(first.outline==original&&!first.clip&&first.listeners==0,"surface swap releases old outline and listener");
            check(next.clip&&next.listeners==1,"same-size surface swap clips the replacement");
            r.clearFrameGeometry();check(!next.clip&&next.listeners==0,"MOBILE releases active-surface decoration");
        } else if(scenario.equals("fullscreen")) {
            r.applyFrameGeometry();r.mCompositorViewHolder.fullscreen.fullscreen=true;r.applyFrameGeometry();
            check(!r.mArcFrameActive,"fullscreen must release Arc frame insets/radii");
            r.mCompositorViewHolder.fullscreen.fullscreen=false;r.applyFrameGeometry();
            check(r.mArcFrameActive,"exiting fullscreen restores Arc frame");
        } else if(scenario.equals("destroyed")) {
            r.mDestroyed=true;r.applyFrameGeometry();check(!r.mArcFrameActive,"destroyed callback cannot mutate frame");
        } else if(scenario.equals("hit")) {
            r.applyFrameGeometry();check(!r.isInsideArcContent(334,0),"rounded invisible corner must reject touch");
            check(r.isInsideArcContent(500,300),"web center must remain interactive");
        }
        System.out.println("PASS "+scenario);
    }
}
"""

class ArcFrameRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=COORD.read_text()
        signatures={
            "applyFrameGeometry":"private void applyFrameGeometry()",
            "clearFrameGeometry":"private void clearFrameGeometry()",
            "restoreClippedSurface":"private void restoreClippedSurface()",
            "applyActiveSurfaceClip":"private void applyActiveSurfaceClip()",
            "reservedLeftWidth":"private int reservedLeftWidth()",
            "arcClipLeftForView":"private int arcClipLeftForView(View view)",
            "isInsideArcContent":"private boolean isInsideArcContent(float x, float y)",
        }
        for name,signature in {
            "currentFrameGeometry":"private ArcDesktopPolicy.Geometry currentFrameGeometry()",
            "arcClipBoundsForView":"private Rect arcClipBoundsForView(View view)",
        }.items():
            if name+"(" in source:signatures[name]=signature
        import re
        methods="\n".join(sig+" "+method_body(source,re.escape(sig)) for sig in signatures.values())
        cls.tmp=tempfile.TemporaryDirectory(prefix="arc-frame-regression-")
        cls.work=Path(cls.tmp.name)
        test=cls.work/"FrameRegression.java";test.write_text(JAVA.replace("METHODS",methods))
        jar=ROOT/".sync-audit/androidx-window-core.jar"
        sources=list((ROOT/"chromium").rglob("ArcDesktopPolicy.java"))+list((ROOT/"chromium").rglob("ArchiumWindowClass.java"))
        result=subprocess.run(["javac","--release","17","-cp",str(jar),"-d",str(cls.work),*map(str,sources),str(test)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)
        cls.cp=str(cls.work)+":"+str(jar)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def run_case(self,name):
        result=subprocess.run(["java","-ea","-cp",self.cp,"FrameRegression",name],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_reference_frame_and_mobile_restore(self):self.run_case("frame")
    def test_inactive_posted_callback(self):self.run_case("inactive")
    def test_surface_swap_and_cleanup(self):self.run_case("surface")
    def test_destroyed_callback(self):self.run_case("destroyed")
    def test_hit_bounds(self):self.run_case("hit")
    def test_fullscreen_frame_round_trip(self):self.run_case("fullscreen")

class ArcCaptionGeometryTest(unittest.TestCase):
    def test_caption_bookmarks_fullscreen_and_nullable_state(self):
        import re
        source=(ROOT/".source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java").read_text()
        caption=source[source.index("private final TopControlLayer mArcCaptionLayer"):]
        body=method_body(caption,r"public int getTopControlHeight\(\)")
        program=r"""
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class CaptionGeometry {
    static class TopControlType {static final int TOOLBAR=2;}
    static class AppHeaderState {boolean desktop=true;int height=40;boolean isInDesktopWindow(){return desktop;}int getAppHeaderHeight(){return height;}}
    static class DesktopWindowStateManager {AppHeaderState state=new AppHeaderState();AppHeaderState getAppHeaderState(){return state;}}
    static class FullscreenManager {boolean fullscreen;boolean getPersistentFullscreenMode(){return fullscreen;}}
    static class Stacker {int previous;int getHeightFromLayerToTop(int stop){return previous;}}
    DesktopWindowStateManager manager=new DesktopWindowStateManager();
    final FullscreenManager mFullscreenManager=new FullscreenManager();final Stacker mTopControlsStacker=new Stacker();
    DesktopWindowStateManager getDesktopWindowStateManager(){return manager;}
    public int getTopControlHeight() BODY
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[]args){CaptionGeometry r=new CaptionGeometry();
        check(r.getTopControlHeight()+42==82,"bookmarks must begin under40px caption");
        r.mTopControlsStacker.previous=16;check(r.getTopControlHeight()==24,"preceding layer16 must not duplicate caption40");
        r.manager.state.height=24;r.mTopControlsStacker.previous=0;check(r.getTopControlHeight()==24,"caption resize40to24");
        r.mFullscreenManager.fullscreen=true;check(r.getTopControlHeight()==0,"fullscreen must release caption even while AppHeaderState remains desktop");
        r.mFullscreenManager.fullscreen=false;r.manager.state=null;check(r.getTopControlHeight()==0,"nullable header state cannot crash");
        r.manager=null;check(r.getTopControlHeight()==0,"nullable desktop manager cannot crash");
    }
}
""".replace("BODY",body)
        with tempfile.TemporaryDirectory(prefix="arc-caption-geometry-") as tmp:
            p=Path(tmp)/"CaptionGeometry.java";p.write_text(program)
            jar=ROOT/".sync-audit/androidx-window-core.jar"
            sources=list((ROOT/"chromium").rglob("ArcDesktopPolicy.java"))+list((ROOT/"chromium").rglob("ArchiumWindowClass.java"))
            compiled=subprocess.run(["javac","--release","17","-cp",str(jar),"-d",tmp,*map(str,sources),str(p)],text=True,capture_output=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run(["java","-ea","-cp",tmp+":"+str(jar),"CaptionGeometry"],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

class ArcNativeCaptionInsetTest(unittest.TestCase):
    def test_native_spacer_tracks_caption_height_and_null(self):
        source=(ROOT/".source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListCoordinator.java").read_text()
        body=method_body(source,r"private void updateSpacerVisibility\(")
        java=r"""
class NativeCaptionInset {
    static class AppHeaderState {int height=40;boolean desktop=true;boolean isInDesktopWindow(){return desktop;}int getAppHeaderHeight(){return height;}}
    static class Rail {int height=40;boolean visible;void setDesktopWindowSpacerVisible(boolean b){visible=b;}void setDesktopWindowSpacerHeight(int h){height=h;}}
    final Rail mContainerView=new Rail();
    private void updateSpacerVisibility(AppHeaderState appHeaderState) BODY
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[]args){NativeCaptionInset n=new NativeCaptionInset();AppHeaderState s=new AppHeaderState();
        s.height=24;n.updateSpacerVisibility(s);check(n.mContainerView.height==24&&n.mContainerView.visible,"native sidebar caption cannot retain stale40px after24px resize");
        n.updateSpacerVisibility(null);check(n.mContainerView.height==0&&!n.mContainerView.visible,"null/mobile header must not leave stale caption height");
    }
}
""".replace("BODY",body)
        with tempfile.TemporaryDirectory(prefix="arc-native-caption-") as tmp:
            path=Path(tmp)/"NativeCaptionInset.java";path.write_text(java)
            result=subprocess.run(["javac","--release","17","-d",tmp,str(path)],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(["java","-ea","-cp",tmp,"NativeCaptionInset"],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
