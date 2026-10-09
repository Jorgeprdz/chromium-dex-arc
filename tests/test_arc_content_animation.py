"""Execute Arc's SideUi observer and native canvas/input bridge at explicit boundaries.

Android transition scheduling and GPU performance require the new APK; the probe
checks preparation, intermediate geometry, interruption and MOBILE guards.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body

COORD = ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java'
NATIVE_PATH = 'chrome/android/java/src/org/chromium/chrome/browser/compositor/CompositorViewHolder.java'

JAVA = r'''
import java.util.*;
import java.util.function.IntConsumer;
class AnimationObserverProbe {
    @interface Nullable {}
    interface Transition {void progress(int width);}
    static class ArcViewportTransition implements Transition {
        final int start,end;final IntConsumer update;
        ArcViewportTransition(Object view,int s,int e,IntConsumer c){start=s;end=e;update=c;}
        public void progress(int width){update.accept(width);}
    }
    static class AnchorSide {static final int LEFT=0;}
    static class SideUiSpecs {final int width;SideUiSpecs(int w){width=w;}int getReservedWidth(int side){return width;}}
    static class UiUpdateRequest {}
    interface SideUiObserver {
        default Transition onPreSideUiSpecsChange(SideUiSpecs s,UiUpdateRequest r){return null;}
        default void onTransitionBegun(SideUiSpecs s,UiUpdateRequest r){}
        default void onTransitionEnded(SideUiSpecs s,UiUpdateRequest r){}
        default void onSideUiSpecsChanged(SideUiSpecs s,UiUpdateRequest r){}
    }
    static class Holder {
        int prepares,nativeOffset=321,inputOffset=321,outlines;boolean fullscreen;
        final Holder surface=this;
        Holder getFullscreenManager(){return this;}
        boolean getPersistentFullscreenMode(){return fullscreen;}
        void prepareArcSideUiAnimation(int width,int finalWidth){prepares++;nativeOffset=inputOffset=width;}
        void setArcSideUiContentOffsetX(int width){nativeOffset=inputOffset=width;}
        void invalidateOutline(){outlines++;}
    }
    static class Geometry {}
    final Holder mCompositorViewHolder=new Holder();
    boolean mDestroyed,mArcToolbarCompositionActive=true,mArcFrameActive=true;
    boolean mArcViewportAnimationActive;
    boolean mArcViewportAnimationPending;
    int mArcVisualReservedLeftWidth=-1,mArcViewportAnimationGeneration;
    int committedWidth=321,clipLeft=321,surfaceLeft=321;
    Geometry mFrameGeometry;
    final SideUiObserver mSideUiObserver=new SideUiObserver() OBSERVER;
    int reservedLeftWidth(){return mArcViewportAnimationActive?mArcVisualReservedLeftWidth:committedWidth;}
    Geometry currentFrameGeometry(){return new Geometry();}
    void applyActiveSurfaceClip(){clipLeft=surfaceLeft=reservedLeftWidth();}
    void onSidebarGeometryChanged(){if(!mDestroyed&&mArcToolbarCompositionActive)applyActiveSurfaceClip();}
    HELPERS
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    public static void main(String[]args){
        AnimationObserverProbe p=new AnimationObserverProbe();var request=new UiUpdateRequest();
        var target=new SideUiSpecs(52);
        Transition transition=p.mSideUiObserver.onPreSideUiSpecsChange(target,request);
        if(args[0].equals("start")){
            p.mSideUiObserver.onTransitionBegun(target,request);
            check(p.mCompositorViewHolder.prepares==1,"renderer canvas must be prepared once at animation start");
            check(p.committedWidth==321,"native committed specs remain authoritative until transition end");
        }else if(args[0].equals("intermediate")){
            check(transition!=null,"Arc must join the native transition rather than only refresh after it");
            p.mSideUiObserver.onTransitionBegun(target,request);
            transition.progress(200);
            check(p.clipLeft==200&&p.surfaceLeft==200,"holder and SurfaceView clip advance together at intermediate width");
            check(p.mCompositorViewHolder.nativeOffset==200&&p.mCompositorViewHolder.inputOffset==200,"visual and input offsets share the intermediate width");
            transition.progress(52);
            check(p.mCompositorViewHolder.prepares==1,"intermediate frames never resize renderer again");
            p.committedWidth=52;p.mSideUiObserver.onTransitionEnded(target,request);
            check(p.clipLeft==52&&!p.mArcViewportAnimationActive,"settlement keeps final geometry and releases animation ownership");
        }else if(args[0].equals("interrupt")){
            check(transition!=null,"native transition callback required");
            p.mSideUiObserver.onTransitionBegun(target,request);
            transition.progress(200);
            p.committedWidth=370;p.mSideUiObserver.onSideUiSpecsChanged(new SideUiSpecs(370),request);
            transition.progress(100);
            check(p.clipLeft==370&&!p.mArcViewportAnimationActive,"static resize invalidates stale animation callbacks");
        }else if(args[0].equals("guards")){
            p.mDestroyed=true;
            check(p.mSideUiObserver.onPreSideUiSpecsChange(target,request)==null,"destroyed coordinator registers no transition");
            p.mSideUiObserver.onTransitionBegun(target,request);
            check(p.mCompositorViewHolder.prepares==0,"destroyed callbacks do not resize renderer");
            p.mDestroyed=false;p.mArcToolbarCompositionActive=false;
            check(p.mSideUiObserver.onPreSideUiSpecsChange(target,request)==null,"MOBILE uses unchanged native transition");
            p.mArcToolbarCompositionActive=true;p.mCompositorViewHolder.fullscreen=true;
            check(p.mSideUiObserver.onPreSideUiSpecsChange(target,request)==null,"fullscreen owns no Arc clip transition");
        }else if(args[0].equals("hover")){
            p.committedWidth=52;p.clipLeft=52;
            check(p.mSideUiObserver.onPreSideUiSpecsChange(target,request)==null,"hover overlay does not animate reserved width52");
            p.mSideUiObserver.onTransitionBegun(target,request);
            check(p.mCompositorViewHolder.prepares==0,"hover never resizes renderer");
        }
    }
}
'''


class ArcContentAnimationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=COORD.read_text()
        start=source.index('private final SideUiObserver mSideUiObserver =')
        observer=source[source.index('{',start):source.index('\n    };',start)+6]
        helpers='\n'.join(signature+' '+method_body(source,re.escape(signature))
            for signature in ('private Transition createArcViewportTransition(SideUiSpecs specs)',
                              'private void beginArcViewportAnimation(SideUiSpecs specs)',
                              'private void finishArcViewportAnimation()',
                              'private void updateArcAnimatedViewportWidth(int width)')
            if signature in source)
        program=JAVA.replace('OBSERVER',observer).replace('HELPERS',helpers)
        cls.temp=tempfile.TemporaryDirectory(prefix='arc-content-animation-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work=Path(cls.temp.name)
        (cls.work/'AnimationObserverProbe.java').write_text(program)
        result=subprocess.run(['javac','--release','17','-d',str(cls.work),str(cls.work/'AnimationObserverProbe.java')],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)

    def probe(self,scenario):
        result=subprocess.run(['java','-ea','-cp',str(self.work),'AnimationObserverProbe',scenario],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_prepares_renderer_once_at_animation_start(self):self.probe('start')
    def test_intermediate_clip_compositor_and_input_share_width(self):self.probe('intermediate')
    def test_static_resize_invalidates_old_animation(self):self.probe('interrupt')
    def test_inactive_destroyed_fullscreen_do_not_own_transition(self):self.probe('guards')
    def test_hover_overlay_keeps_collapsed_reservation(self):self.probe('hover')


class ArcNativeAnimationBridgeTest(unittest.TestCase):
    def test_renderer_preparation_restores_start_offset_and_frames_do_not_resize(self):
        path=ROOT/'.source-modified'/NATIVE_PATH
        if not path.exists():path=ROOT/'.source-reference'/NATIVE_PATH
        source=path.read_text()
        signatures=('public void prepareArcSideUiAnimation(int initialLeftWidth, int finalLeftWidth)',
                    'public void setArcSideUiContentOffsetX(int leftWidth)')
        for signature in signatures:
            self.assertIn(signature,source,'Native animation sizing/input bridge is missing')
        methods='\n'.join(s+' '+method_body(source,re.escape(s)) for s in signatures)
        java='''
class NativeAnimationBridge {
    static class LayoutManager {int offset=321;void setContentOffsetX(int width){offset=width;}}
    static class ContentView {int offset=321;void setContentOffsetXPix(int width){offset=width;}}
    final LayoutManager mLayoutManager=new LayoutManager();
    final ContentView view=new ContentView();int resizes,expectedWidth=52,canvasWidth=679,mSideUiSizingGeneration;
    ContentView getContentView(){return view;}
    void updateWebContentsSize(){resizes++;view.offset=expectedWidth;canvasWidth=1000-expectedWidth;}
    METHODS
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    public static void main(String[]args){
        NativeAnimationBridge p=new NativeAnimationBridge();
        p.prepareArcSideUiAnimation(321,52);
        check(p.resizes==1,"renderer resizes once before interpolation");
        check(p.view.offset==321&&p.mLayoutManager.offset==321,"start preparation must undo target input offset from sizing");
        for(int width:new int[]{200,100,52})p.setArcSideUiContentOffsetX(width);
        check(p.resizes==1,"animation frames only update position/input, never renderer sizing");
        check(p.view.offset==52&&p.mLayoutManager.offset==52,"final composited and input positions match");
        p.expectedWidth=321;
        p.prepareArcSideUiAnimation(52,321);
        check(p.resizes==1,"expansion keeps the larger existing canvas until native settlement");
        for(int width:new int[]{52,100,200,321}){
            p.setArcSideUiContentOffsetX(width);
            check(width+p.canvasWidth>=1000,"translated renderer canvas must cover the visible right edge during expansion");
        }
        p.updateWebContentsSize();
        check(p.resizes==2&&p.canvasWidth==679,"native settlement shrinks renderer canvas once to final expanded width");
    }
}
'''.replace('METHODS',methods)
        with tempfile.TemporaryDirectory(prefix='arc-native-animation-') as tmp:
            p=Path(tmp)/'NativeAnimationBridge.java';p.write_text(java)
            result=subprocess.run(['javac','--release','17','-d',tmp,str(p)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(['java','-ea','-cp',tmp,'NativeAnimationBridge'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_interrupted_settlement_cannot_overwrite_new_animation_or_live_resize(self):
        path=ROOT/'.source-modified'/NATIVE_PATH
        if not path.exists():path=ROOT/'.source-reference'/NATIVE_PATH
        source=path.read_text()
        signatures=(
            'private void updateForSideUiSpecs(SideUiSpecs sideUiSpecs, boolean isLiveResize)',
            'public void prepareArcSideUiAnimation(int initialLeftWidth, int finalLeftWidth)',
            'public void setArcSideUiContentOffsetX(int leftWidth)',
            'private void applySideUiContentOffsetX(SideUiSpecs sideUiSpecs)',
            'public void shutDown()',
        )
        methods='\n'.join(s+' '+method_body(source,re.escape(s)) for s in signatures)
        methods=methods.replace('@Px ', '')
        java=r'''
import java.util.*;
class QueuedNativeSizingProbe {
    static class AnchorSide {static final int LEFT=0;}
    static class SideUiSpecs {final int width;SideUiSpecs(int w){width=w;}int getReservedWidth(int s){return width;}}
    static class Dummy {void removeCallbacks(Object o){}void removeObserver(Object o){}Dummy getSupplier(){return this;}void shutDown(){}void destroy(){}}
    static class LayoutManager extends Dummy {int offset=52;void setContentOffsetX(int w){offset=w;}}
    static class ContentView {int offset=52;void setContentOffsetXPix(int w){offset=w;}void removeOnHierarchyChangeListener(Object o){}}
    final LayoutManager mLayoutManager=new LayoutManager();
    final ContentView view=new ContentView();
    final Dummy mCompositorView=new Dummy();
    Dummy mBrowserControlsManager,mApplicationBottomInsetSupplier,mOnscreenContentProvider,mSideUiStateProvider;
    Runnable mSystemUiFullscreenResizeRunnable;
    Object mOnViewportInsetsChanged;
    ContentView mContentView;
    final Queue<Runnable> queue=new ArrayDeque<>();
    int resizes,expectedWidth=321,canvasWidth=948,mSideUiSizingGeneration;
    ContentView getContentView(){return view;}
    void updateWebContentsSize(){resizes++;canvasWidth=1000-expectedWidth;view.offset=expectedWidth;}
    void post(Runnable r){queue.add(r);}void drain(){while(!queue.isEmpty())queue.remove().run();}
    void repositionTabViewForSideUi(SideUiSpecs s){}void onViewportChanged(){}
    void setTab(Object tab){}Dummy getHandler(){return new Dummy();}static <T>T assumeNonNull(T t){return t;}
    METHODS
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    public static void main(String[]args){
        var p=new QueuedNativeSizingProbe();
        // Native endTransitions synchronously settles old collapse, posting its resize.
        p.updateForSideUiSpecs(new SideUiSpecs(52),false);
        p.prepareArcSideUiAnimation(52,321);
        p.setArcSideUiContentOffsetX(100);
        p.drain();
        check(p.resizes==0&&p.canvasWidth==948,"old settlement must not prematurely shrink new expansion canvas");
        check(p.view.offset==100&&p.mLayoutManager.offset==100,"queued old specs must not rewind new visual/input offsets");
        p.updateForSideUiSpecs(new SideUiSpecs(321),false);p.drain();
        check(p.resizes==1&&p.canvasWidth==679&&p.view.offset==321,"replacement transition keeps its eventual native final sizing");
        p.updateForSideUiSpecs(new SideUiSpecs(52),false);
        p.updateForSideUiSpecs(new SideUiSpecs(200),true);p.drain();
        check(p.resizes==1&&p.view.offset==200,"live resize invalidates pending static settlement");
        p.updateForSideUiSpecs(new SideUiSpecs(321),false);
        p.updateForSideUiSpecs(new SideUiSpecs(210),false);p.expectedWidth=210;p.drain();
        check(p.resizes==2&&p.view.offset==210,"only latest static settlement applies");
        p.updateForSideUiSpecs(new SideUiSpecs(321),false);p.shutDown();p.drain();
        check(p.resizes==2&&p.view.offset==210,"shutdown invalidates pending sizing callbacks");
    }
}
'''.replace('METHODS',methods)
        with tempfile.TemporaryDirectory(prefix='arc-native-sizing-queue-') as tmp:
            p=Path(tmp)/'QueuedNativeSizingProbe.java';p.write_text(java)
            result=subprocess.run(['javac','--release','17','-d',tmp,str(p)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(['java','-ea','-cp',tmp,'QueuedNativeSizingProbe'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
