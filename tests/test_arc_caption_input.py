"""Execute pinned native caption/input methods, with only Android storage doubled.

Original SHA-256 is tied to Chromium cfd94726b7b5fb48aedcc32662f2f3fbdbadec35.
These probes establish reversible app-side ownership, not Samsung DeX minimize behavior.
"""
from pathlib import Path
import hashlib
import os
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body

REL = 'chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarControlContainer.java'
ORIGINAL = ROOT / '.source-reference' / REL
MODIFIED = ROOT / '.source-modified' / REL
PINNED_SHA256 = '9502ad91d5e87e23fd4753061d6792cf7c8f6058d766d5b642137ee44ed00050'


def methods(source):
    signatures = [
        'public boolean isToolbarInAppHeader()',
        'public void setSystemGestureExclusionRects(List<Rect> rects)',
        'private void updateSystemGestureExclusions()',
        'public boolean onTouchEvent(MotionEvent event)',
        'public boolean onInterceptTouchEvent(MotionEvent event)',
        'private void updateTopLeftCornerOverlay()',
        'public void onAppHeaderStateChanged(AppHeaderState newState)',
        'public void onDesktopWindowingModeChanged(boolean isInDesktopWindow)',
    ]
    optional = [
        'public void setArcToolbarSuppressed(boolean suppressed)',
        'private void applySystemGestureExclusions()',
        'protected void onAttachedToWindow()',
        'protected void onDetachedFromWindow()',
    ]
    signatures += [signature for signature in optional if signature in source]
    return '\n'.join(signature + ' ' + method_body(source, re.escape(signature)) for signature in signatures)


HARNESS = r'''
import java.util.*;
class Rect {
    int left,top,right,bottom;Rect(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}
    Rect(Rect r){this(r.left,r.top,r.right,r.bottom);}
    public boolean equals(Object o){return o instanceof Rect r&&left==r.left&&top==r.top&&right==r.right&&bottom==r.bottom;}
    public String toString(){return left+","+top+","+right+","+bottom;}
}
class View {static final int VISIBLE=0,GONE=8;int visibility=VISIBLE;void setVisibility(int n){visibility=n;}void bringToFront(){}int getVisibility(){return visibility;}}
class MotionEvent {static final int ACTION_DOWN=0;int action;MotionEvent(int a){action=a;}int getActionMasked(){return action;}}
class AppHeaderState {boolean desktop=true;int right=120,top=0,height=40;int getRightPadding(){return right;}int getCaptionControlsTopOffset(){return top;}int getCaptionControlsHeight(){return height;}}
class TouchEventObserver {int calls;boolean onInterceptTouchEvent(MotionEvent e){calls++;return false;}}
class SwipeListener {int calls;boolean onTouchEvent(MotionEvent e){calls++;return false;}}
class Base {
    List<Rect> actual=List.of();int width=1382,cancels;boolean attached;
    void setSystemGestureExclusionRects(List<Rect> rects){actual=List.copyOf(rects);}int getWidth(){return width;}
    void cancelPendingInputEvents(){cancels++;}void cancelLongPress(){}
    protected void onAttachedToWindow(){attached=true;}protected void onDetachedFromWindow(){attached=false;}
    // The absent production API is a no-op at baseline, so tests exercise unchanged native methods.
    public void setArcToolbarSuppressed(boolean suppressed){}
}
class CaptionInputProbe extends Base {
    boolean mArcToolbarSuppressed,vertical=true;int mTabStripHeight;List<Rect> mLastRequestedSystemGestureExclusionRects=List.of();
    View mToolbarView=new View(),mTopLeftCornerOverlayView=new View(),mToolbarContainer=new View();
    AppHeaderState header=new AppHeaderState();SwipeListener mSwipeGestureListener=new SwipeListener();
    List<TouchEventObserver> mTouchEventObservers=new ArrayList<>(List.of(new TouchEventObserver()));
    static <T>T assertNonNull(T t){return Objects.requireNonNull(t);}
    AppHeaderState getAppHeaderState(){return header;}
    boolean isVerticalTabsInDesktopWindow(){return vertical&&header!=null&&header.desktop;}
    boolean isToolbarContainerFullyVisible(){return mToolbarContainer.getVisibility()==View.VISIBLE;}
    boolean isBelowToolbarContainer(MotionEvent e){return false;}boolean isOnTabStrip(MotionEvent e){return false;}
    void updateToolbarRightOffset(){}void updateToolbarContainerTopMargin(){}
    METHODS
    static void check(boolean b,String reason){if(!b)throw new AssertionError(reason);}
    static void rect(CaptionInputProbe p,int l,int t,int r,int b,String reason){check(p.actual.equals(List.of(new Rect(l,t,r,b))),reason+": "+p.actual);}
    public static void main(String[]args){CaptionInputProbe p=new CaptionInputProbe();
        switch(args[0]){
            case "caption":
                p.mToolbarView.setVisibility(View.GONE);p.mArcToolbarSuppressed=true;p.setSystemGestureExclusionRects(List.of());
                check(p.actual.isEmpty(),"Arc's hidden native toolbar must release the full caption drag region");
                check(!p.isToolbarInAppHeader(),"hidden Arc toolbar no longer claims native caption row");break;
            case "setter":
                p.setSystemGestureExclusionRects(List.of());rect(p,0,0,1262,40,"native desktop toolbar initially owns caption");
                p.mToolbarView.setVisibility(View.GONE);p.setArcToolbarSuppressed(true);
                check(p.actual.isEmpty()&&p.mTopLeftCornerOverlayView.visibility==View.GONE,"suppression immediately releases native exclusion and corner drawable");
                p.header.right=180;p.header.top=24;p.header.height=48;p.onAppHeaderStateChanged(p.header);
                check(p.actual.isEmpty(),"native header refresh cannot reclaim Arc's caption");
                p.setArcToolbarSuppressed(false);rect(p,0,24,1202,72,"MOBILE restores CURRENT native caption, not entry snapshot");
                check(p.mTopLeftCornerOverlayView.visibility==View.VISIBLE,"native corner drawable restored");break;
            case "requests":
                p.vertical=false;Rect original=new Rect(3,4,30,40);p.setSystemGestureExclusionRects(List.of(original));
                p.setArcToolbarSuppressed(true);original.left=777;
                p.header=null;p.onDesktopWindowingModeChanged(false);check(p.actual.isEmpty(),"desktop exit while Arc keeps exclusions cleared");
                p.setArcToolbarSuppressed(false);rect(p,3,4,30,40,"MOBILE restores caller snapshot after native header disappears");
                p.setArcToolbarSuppressed(true);Rect latest=new Rect(7,8,70,80);p.setSystemGestureExclusionRects(List.of(latest));latest.right=888;
                check(p.actual.isEmpty(),"new external exclusion request cannot reassert hidden Arc toolbar");
                p.onAppHeaderStateChanged(new AppHeaderState());p.setArcToolbarSuppressed(false);
                rect(p,7,8,70,80,"MOBILE adopts latest external request despite internal header updates");break;
            case "input":
                p.setArcToolbarSuppressed(true);p.mToolbarContainer.setVisibility(View.GONE);
                check(!p.onInterceptTouchEvent(new MotionEvent(0))&&!p.onTouchEvent(new MotionEvent(0)),"hidden native toolbar cannot intercept Arc controls");
                p.mToolbarContainer.setVisibility(View.VISIBLE);
                check(!p.onTouchEvent(new MotionEvent(1))&&p.mSwipeGestureListener.calls==0&&p.mTouchEventObservers.get(0).calls==0,"suppressed empty toolbar doesn't dispatch old swipe/input observers");
                p.setArcToolbarSuppressed(false);check(p.onTouchEvent(new MotionEvent(0)),"MOBILE retains native unhandled-down ownership");
                p.mToolbarContainer.setVisibility(View.GONE);check(p.onInterceptTouchEvent(new MotionEvent(0)),"MOBILE restores native invisible-toolbar interception");break;
            case "detach":
                p.vertical=false;p.setSystemGestureExclusionRects(List.of(new Rect(1,2,10,20)));
                p.onAttachedToWindow();p.onDetachedFromWindow();check(p.actual.isEmpty(),"detached container releases input exclusions");
                p.onAttachedToWindow();rect(p,1,2,10,20,"reattach restores caller native input ownership");
                p.setArcToolbarSuppressed(true);p.onDetachedFromWindow();p.onAttachedToWindow();
                check(p.actual.isEmpty(),"reattach while Arc active cannot reclaim caption");
                p.setArcToolbarSuppressed(false);rect(p,1,2,10,20,"detach never loses saved caller request");break;
            default:throw new AssertionError(args[0]);
        }
    }
}
'''


class ArcCaptionInputTest(unittest.TestCase):
    def run_case(self, name):
        program = HARNESS.replace('METHODS', methods(MODIFIED.read_text()))
        with tempfile.TemporaryDirectory(prefix='arc-caption-input-') as tmp:
            source = Path(tmp) / 'CaptionInputProbe.java'; source.write_text(program)
            result = subprocess.run(['javac', '--release', '17', '-d', tmp, str(source)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(['java', '-ea', '-cp', tmp, 'CaptionInputProbe', name], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pinned_original_provenance(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), PINNED_SHA256)

    def test_hidden_arc_toolbar_releases_full_caption_exclusions(self):
        self.run_case('caption')

    def test_setter_and_header_events_restore_current_native_geometry(self):
        self.run_case('setter')

    def test_external_requests_survive_arc_and_restore_latest_snapshot(self):
        self.run_case('requests')

    def test_arc_releases_empty_toolbar_touch_interception(self):
        self.run_case('input')


    def test_caption_helper_compiles_against_android_sdk37(self):
        android_jar = Path(os.environ.get('ANDROID_JAR', '/opt/android-sdk/platforms/android-37.0/android.jar'))
        if not android_jar.exists():
            self.skipTest('Android platform jar unavailable for bounded SDK compile')
        source = r'''
import android.content.Context;import android.graphics.Rect;import android.view.MotionEvent;
import android.view.View;import android.widget.FrameLayout;import java.util.*;
class CaptionInputSdk extends FrameLayout {
    boolean mArcToolbarSuppressed,vertical=true;int mTabStripHeight;
    List<Rect> mLastRequestedSystemGestureExclusionRects=List.of();
    View mTopLeftCornerOverlayView,mToolbarContainer;AppHeaderState header;SwipeListener mSwipeGestureListener;
    List<TouchEventObserver> mTouchEventObservers=List.of();
    CaptionInputSdk(Context context){super(context);}
    static <T>T assertNonNull(T value){return Objects.requireNonNull(value);}
    AppHeaderState getAppHeaderState(){return header;}boolean isVerticalTabsInDesktopWindow(){return vertical;}
    boolean isToolbarContainerFullyVisible(){return true;}boolean isBelowToolbarContainer(MotionEvent e){return false;}
    boolean isOnTabStrip(MotionEvent e){return false;}void updateToolbarRightOffset(){}void updateToolbarContainerTopMargin(){}
    static class AppHeaderState {int getRightPadding(){return 0;}int getCaptionControlsTopOffset(){return 0;}int getCaptionControlsHeight(){return 40;}}
    static class SwipeListener {boolean onTouchEvent(MotionEvent e){return false;}}
    static class TouchEventObserver {boolean onInterceptTouchEvent(MotionEvent e){return false;}}
    METHODS
}
'''.replace('METHODS', methods(MODIFIED.read_text()))
        with tempfile.TemporaryDirectory(prefix='arc-caption-sdk-') as tmp:
            path = Path(tmp) / 'CaptionInputSdk.java'; path.write_text(source)
            result = subprocess.run(['javac', '--release', '17', '-cp', str(android_jar), '-d', tmp, str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_detach_reattach_preserves_ownership_and_requests(self):
        self.run_case('detach')


if __name__ == '__main__':
    unittest.main()
