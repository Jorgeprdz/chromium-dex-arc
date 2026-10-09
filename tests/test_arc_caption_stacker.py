"""Characterize Arc caption through pinned native stacker and bookmark callbacks.

The fixtures are unmodified Chromium cfd94726b7b5fb48aedcc32662f2f3fbdbadec35:
chrome/browser/browser_controls/android/java/src/org/chromium/chrome/browser/browser_controls/TopControlsStacker.java
chrome/browser/bookmarks/android/java/src/org/chromium/chrome/browser/bookmarks/bar/BookmarkBarCoordinator.java
Fixture SHA-256:
  TopControlsStacker: 969b2bb53e31c75027b33a7c7a6e7889dffc61ce58336cafb32ec2ce616eff11
  BookmarkBarCoordinator: f823c292a7e1cbce6d76905927d8717ab80d938ac49fcdfdcc4c26bdfd7a0e3c
Only Android view storage and unrelated stacker logging are doubled. This is a host
contract test, not evidence of Android SurfaceView/scene-layer rendering.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body, window_core_jar

FIXTURES = ROOT / 'tests/fixtures/arc-caption'
COORD = ROOT / '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java'


def method(source, signature):
    body = method_body(source, re.escape(signature))
    return re.sub(r'@(TopControlType|TopControlVisibility|Nullable)\s+', '', signature + ' ' + body)


JAVA = r'''
import java.util.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class CaptionStackerContract {
    static class TopControlType {static final int STATUS_INDICATOR=0,TABSTRIP=1,TOOLBAR=2,BOOKMARK_BAR=3,HAIRLINE=4,TAB_SHARING_TOOLBAR=6,PROGRESS_BAR=5;}
    static class TopControlVisibility {static final int VISIBLE=0,HIDDEN=1,SHOWING_TOP_ANCHOR=3,SHOWING_BOTTOM_ANCHOR=4,HIDING_TOP_ANCHOR=5,HIDING_BOTTOM_ANCHOR=6;}
    static class ScrollBehavior {static final int DEFAULT_SCROLLABLE=0,NEVER_SCROLLABLE=1;}
    static class BrowserControlsState {static final int SHOWN=1,BOTH=2;}
    static class SparseIntArray {
        Map<Integer,Integer> data=new HashMap<>();
        int get(int k){return get(k,0);}int get(int k,int fallback){return data.getOrDefault(k,fallback);}
        void put(int k,int v){data.put(k,v);}void delete(int k){data.remove(k);}
    }
    interface TopControlLayer {
        int getTopControlType();int getTopControlHeight();int getTopControlVisibility();
        default int getScrollBehavior(){return ScrollBehavior.DEFAULT_SCROLLABLE;}
        default boolean contributesToTotalHeight(){return true;}
        default void updateOffsetTag(Object tag){}
        default void onBrowserControlsOffsetUpdate(int y,boolean rest){}
    }
    static class Stacker {
        static final int INVALID_HEIGHT=-1;
        static final int[] STACK_ORDER={0,1,2,3,4,6,5};
        final Map<Integer,TopControlLayer> mControls=new HashMap<>();
        final SparseIntArray mLayerRestingOffsets=new SparseIntArray(),mLayerYOffset=new SparseIntArray();
        boolean mScrollingDisabled,mHasAnimationLayer,mIsMinHeightShrinking;
        int mBrowserControlsState=BrowserControlsState.BOTH,mTotalHeight,mMinHeight;
        Object mTopControlsOffsetTagInfo;
        static final boolean sDumpStatusLogs=false;static final String TAG="test";
        static class Log {static void i(String tag,String message){}}
        void dumpLayerStatus(TopControlLayer layer,int offset){}
        static void logIfHeightMismatch(int h,int m,int actual,int min){check(h==actual&&m==min,"native stacker height consistency");}
        STACK_METHODS
        void update(int scrollOffset){
            recalculateHeights();recalculateLayerRestingOffsets();
            repositionLayers(scrollOffset,mMinHeight,true);
        }
    }
    static class AppHeaderState {boolean desktop=true;int height=40;boolean isInDesktopWindow(){return desktop;}int getAppHeaderHeight(){return height;}}
    static class DesktopWindowStateManager {AppHeaderState state=new AppHeaderState();AppHeaderState getAppHeaderState(){return state;}}
    static class FullscreenManager {boolean fullscreen;boolean getPersistentFullscreenMode(){return fullscreen;}}
    static class Arc {
        DesktopWindowStateManager manager=new DesktopWindowStateManager();
        final FullscreenManager mFullscreenManager=new FullscreenManager();
        final Stacker mTopControlsStacker;
        Arc(Stacker s){mTopControlsStacker=s;}
        DesktopWindowStateManager getDesktopWindowStateManager(){return manager;}
        CAPTION_LAYER
    }
    static class BookmarkBarProperties {static final int TOP_MARGIN=1;}
    static class Model {int margin;int get(int key){return margin;}}
    static class View {int translation;void setTranslationY(int y){translation=y;}}
    static class Bookmarks implements TopControlLayer {
        final Model mModel=new Model();final View mView=new View();
        final Mediator mMediator=new Mediator();
        class Mediator {void setTopMargin(int y){mModel.margin=y;}}
        public int getTopControlType(){return TopControlType.BOOKMARK_BAR;}
        public int getTopControlHeight(){return 42;}
        public int getTopControlVisibility(){return TopControlVisibility.VISIBLE;}
        BOOKMARK_OFFSET
        int screenTop(){return mModel.margin+mView.translation;}
    }
    static class Layer implements TopControlLayer {
        int height,visibility;final int type;
        Layer(int type,int height,int visibility){this.type=type;this.height=height;this.visibility=visibility;}
        public int getTopControlType(){return type;}public int getTopControlHeight(){return height;}
        public int getTopControlVisibility(){return visibility;}
    }
    static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
    public static void main(String[] args){
        Stacker s=new Stacker();Arc arc=new Arc(s);Bookmarks bookmarks=new Bookmarks();
        // Native vertical-tab suppression publishes targetHeight=0 before updating the stack.
        Layer nativeStrip=new Layer(TopControlType.TABSTRIP,0,TopControlVisibility.HIDDEN);
        s.mControls.put(TopControlType.TABSTRIP,nativeStrip);
        s.mControls.put(TopControlType.TOOLBAR,arc.mArcCaptionLayer);
        s.mControls.put(TopControlType.BOOKMARK_BAR,bookmarks);
        for(int visibility:new int[]{TopControlVisibility.HIDDEN,TopControlVisibility.HIDING_TOP_ANCHOR,TopControlVisibility.HIDING_BOTTOM_ANCHOR}){
            nativeStrip.visibility=visibility;s.mHasAnimationLayer=visibility!=TopControlVisibility.HIDDEN;
            s.update(0);
            check(s.mTotalHeight==82&&s.mMinHeight==40,"40px caption is reserved once before 42px bookmarks");
            check(bookmarks.screenTop()==40,"native bookmarks must begin below caption, including strip suppression");
        }
        nativeStrip.visibility=TopControlVisibility.HIDDEN;s.mHasAnimationLayer=false;
        s.update(-42);
        check(s.mMinHeight==40&&bookmarks.screenTop()+42==40,"scrolling bookmarks away cannot consume system caption");
        arc.manager.state.height=24;s.update(0);
        check(s.mTotalHeight==66&&s.mMinHeight==24&&bookmarks.screenTop()==24,"live caption resize updates native bookmark layout");
        arc.mFullscreenManager.fullscreen=true;s.update(0);
        check(s.mMinHeight==0&&bookmarks.screenTop()==0,"fullscreen releases caption without waiting for desktop state");
        arc.mFullscreenManager.fullscreen=false;arc.manager.state.desktop=false;s.update(0);
        check(s.mMinHeight==0&&bookmarks.screenTop()==0,"non-desktop state has no caption");
        arc.manager.state=null;s.update(0);check(bookmarks.screenTop()==0,"null header has no caption");
        arc.manager=null;s.update(0);check(bookmarks.screenTop()==0,"null desktop manager has no caption");
        System.out.println("PASS native caption/bookmark stacker contract");
    }
}
'''


class ArcCaptionStackerTest(unittest.TestCase):
    def test_native_bookmark_offset_and_caption_minimum_through_suppression(self):
        stacker = (FIXTURES / 'TopControlsStacker.java').read_text()
        methods = '\n'.join(method(stacker, signature) for signature in (
            'public int getHeightFromLayerToTop(@TopControlType int stopLayer)',
            'private void recalculateHeights()',
            'private void recalculateLayerRestingOffsets()',
            'private void calculateStackLayersOffsets(',
            'private void repositionLayers(',
            'private static boolean isLayerHidden(@Nullable TopControlLayer layer)',
            'private static boolean isLayerHiding(TopControlLayer layer)',
            'private boolean doesLayerHasMinHeight(TopControlLayer layer)',
        ))
        # Multiline signatures are completed from the source; method_body returns only braces.
        for prefix in ('private void calculateStackLayersOffsets(', 'private void repositionLayers('):
            start = stacker.index(prefix)
            signature = stacker[start:stacker.index('{', start)].strip()
            methods = methods.replace(prefix + ' {', signature + ' {')
        source = COORD.read_text()
        start = source.index('private final TopControlLayer mArcCaptionLayer =')
        end = source.index('\n    };', start) + len('\n    };')
        caption = re.sub(r'@(TopControlType|TopControlVisibility|ScrollBehavior)\s+', '', source[start:end])
        bookmark = method((FIXTURES / 'BookmarkBarCoordinator.java').read_text(),
                          'public void onBrowserControlsOffsetUpdate(int layerYOffset, boolean reachRestingPosition)')
        program = JAVA.replace('STACK_METHODS', methods).replace('CAPTION_LAYER', caption).replace('BOOKMARK_OFFSET', bookmark)
        with tempfile.TemporaryDirectory(prefix='arc-caption-stacker-') as tmp:
            java = Path(tmp) / 'CaptionStackerContract.java'
            java.write_text(program)
            jar = window_core_jar()
            sources = list((ROOT / 'chromium').rglob('ArcDesktopPolicy.java')) + list((ROOT / 'chromium').rglob('ArchiumWindowClass.java'))
            result = subprocess.run(['javac', '--release', '17', '-cp', str(jar), '-d', tmp, *map(str, sources), str(java)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(['java', '-ea', '-cp', tmp + ':' + str(jar), 'CaptionStackerContract'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
