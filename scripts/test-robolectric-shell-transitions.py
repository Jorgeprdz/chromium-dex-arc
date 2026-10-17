#!/usr/bin/env python3
"""Delivered native transition method bodies on Android views; Tab/JNI boundaries explicit."""
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
p=argparse.ArgumentParser();p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
a.work.mkdir(parents=True,exist_ok=True);classes=a.work/'classes';classes.mkdir(exist_ok=True)
arc=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
shell=(arc/'ArcDesktopCoordinator.java').read_text()
root=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java').read_text()
compositor=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/compositor/CompositorViewHolder.java').read_text()
fixture=r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.os.Looper;
import android.view.*;
import android.graphics.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.ui.vertical_tabs.*;
import org.chromium.chrome.browser.arc.*;
import org.chromium.chrome.browser.tab.*;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ShellTransitionsProbe {
    java.util.List<org.robolectric.android.controller.ActivityController<? extends Activity>> activities=new java.util.ArrayList<>();
    Activity activity(){var c=Robolectric.buildActivity(Activity.class).setup();activities.add(c);return c.get();}
    @After public void close(){for(var c:activities)c.pause().stop().destroy();Shadows.shadowOf(Looper.getMainLooper()).idle();}
    public static class RecreationActivity extends Activity {int recreations;@Override public void recreate(){recreations++;}}
    @Test public void mobileControlsKeepFontAfterActivityModeTransitionAndDestroyCancelsWork() {
        var controller=Robolectric.buildActivity(RecreationActivity.class).setup();activities.add(controller);
        var window=controller.get();android.widget.TextView controls=new android.widget.TextView(window);window.setContentView(controls);
        ArcDesktopAppearance.setUiMode(window,ArcDesktopPolicy.MODE_ARC);
        var dispatcher=new org.chromium.chrome.browser.lifecycle.ActivityLifecycleDispatcher();
        int[] prepared={0};
        ArcDesktopWindowObserver observer=new ArcDesktopWindowObserver(window,dispatcher,
                ()->prepared[0]++,()->ArcDesktopAppearance.applyUiFont(controls));
        ArcDesktopAppearance.setUiFont(window,3);Shadows.shadowOf(Looper.getMainLooper()).idle();
        assertEquals(Typeface.MONOSPACE,controls.getTypeface());
        ArcDesktopAppearance.setUiMode(window,ArcDesktopPolicy.MODE_MOBILE);Shadows.shadowOf(Looper.getMainLooper()).idle();
        assertEquals(1,prepared[0]);assertEquals(1,window.recreations);
        observer.destroy();ArcDesktopAppearance.setUiFont(window,2);Shadows.shadowOf(Looper.getMainLooper()).idle();
        assertEquals(Typeface.MONOSPACE,controls.getTypeface());assertEquals(1,window.recreations);
    }
    static class Shell {
        final View mRail; final java.util.function.Supplier<Integer> mReservedLeftWidth;
        boolean mRailViewportTransition; int mTransitionOtherInset;
        final Compositor mCompositorViewHolder = new Compositor();
        Shell(Activity a,int reserve){mRail=new View(a);mReservedLeftWidth=()->reserve;}
        void scheduleAppearance(){} // full queue helper is tested separately.
        int reservedLeftWidth() RESERVE
        void onSideUiTransition(int reservedWidth,int renderedWidth) TRANSITION
        void onSideUiChanged() CHANGED
    }
    static class ContentView {int offset;void setContentOffsetXPix(int n){offset=n;}}
    static class LayoutManager {int offset;void setContentOffsetX(int n){offset=n;}}
    static class Compositor {
        LayoutManager mLayoutManager=new LayoutManager();ContentView content=new ContentView();int resizes;
        void updateWebContentsSize(){resizes++;}
        void beginArcRailViewportResize(int currentInset) BEGIN_RESIZE
        ContentView getContentView(){return content;}
        void setArcContentOffsetForRail(int leftWidth) OFFSET
    }
    static class Model {Tab[] tabs;Model(Tab...t){tabs=t;}int getCount(){return tabs.length;}Tab getTabAt(int i){return tabs[i];}}
    static class Selector {Model regular,privateModel;Selector(Model r,Model p){regular=r;privateModel=p;}Model getModel(boolean p){return p?privateModel:regular;}}
    static class Root {
        Activity mActivity;java.util.function.Supplier<Selector> mTabModelSelectorSupplier;
        void prepareArcMobileNavigation() MOBILE
    }
    @Test public void railResizeMovesRendererAndInputTogetherThroughoutCollapse() {
        Shell s=new Shell(activity(),216);s.mRail.layout(0,0,216,800);s.onSideUiTransition(52,52);
        Compositor c=s.mCompositorViewHolder;assertEquals(1,c.resizes);
        for(int width:new int[]{216,172,120,80,52}){
            s.mRail.layout(0,0,width,800);c.setArcContentOffsetForRail(s.reservedLeftWidth());
            assertEquals(width,c.mLayoutManager.offset);assertEquals(width,c.content.offset);
        }
    }
    @Test public void hoverExpansionNeverMovesThePage() {
        Shell s=new Shell(activity(),52);s.mRail.layout(0,0,52,800);s.onSideUiTransition(52,216);
        s.mRail.layout(0,0,216,800);assertEquals(52,s.reservedLeftWidth());
    }
    @Test public void sidePanelReserveSurvivesRailAnimation() {
        Shell s=new Shell(activity(),316);s.mRail.layout(0,0,216,800);s.onSideUiTransition(152,152);
        s.mRail.layout(0,0,52,800);assertEquals(152,s.reservedLeftWidth());
        s.onSideUiChanged();assertEquals(316,s.reservedLeftWidth());
    }
    @Test public void mobileUpdatesLoadedAndFrozenTabsWithoutOpeningOrClosingTabs() {
        Root r=new Root();r.mActivity=activity();ArcDesktopAppearance.setUiMode(r.mActivity,ArcDesktopPolicy.MODE_MOBILE);
        Tab loaded=new Tab(true), frozen=new Tab(false), secret=new Tab(true), destroyed=new Tab(true);destroyed.destroyed=true;
        r.mTabModelSelectorSupplier=()->new Selector(new Model(loaded,frozen,destroyed),new Model(secret));
        r.prepareArcMobileNavigation();
        assertEquals(TabUserAgent.MOBILE,loaded.ua);assertEquals(TabUserAgent.MOBILE,frozen.ua);assertEquals(TabUserAgent.MOBILE,secret.ua);
        assertEquals(1,loaded.reloads);assertEquals(1,secret.reloads);assertEquals(0,frozen.reloads);assertEquals(0,destroyed.reloads);
        r.prepareArcMobileNavigation();assertEquals("Already mobile must not reload",1,loaded.reloads);
    }
    @Test public void compositorCanLoseItsSurfaceOrLayoutManagerDuringTeardown() {
        Compositor c=new Compositor();c.content=null;c.setArcContentOffsetForRail(-1);assertEquals(0,c.mLayoutManager.offset);
        c.mLayoutManager=null;c.setArcContentOffsetForRail(52);
    }
}
'''
for marker,src,pattern in [('RESERVE',shell,r'private int reservedLeftWidth\('),('TRANSITION',shell,r'public void onSideUiTransition\('),('CHANGED',shell,r'public void onSideUiChanged\('),('BEGIN_RESIZE',compositor,r'public void beginArcRailViewportResize\('),('OFFSET',compositor,r'public void setArcContentOffsetForRail\('),('MOBILE',root,r'private void prepareArcMobileNavigation\(')]:
 fixture=fixture.replace(' '+marker+'\n',' '+method_body(src,pattern)+'\n')
paths=[]
for name,body in {
 'ShellTransitionsProbe.java':fixture,
 'ConfigurationChangedObserver.java':'package org.chromium.chrome.browser.lifecycle; public interface ConfigurationChangedObserver {void onConfigurationChanged(android.content.res.Configuration c);}',
 'ActivityLifecycleDispatcher.java':'package org.chromium.chrome.browser.lifecycle; public class ActivityLifecycleDispatcher {public void register(ConfigurationChangedObserver o){}public void unregister(ConfigurationChangedObserver o){}}',
 'Tab.java':'package org.chromium.chrome.browser.tab; public class Tab {public boolean destroyed, desktop=true;public int ua=2,reloads;public Object web;public Tab(boolean loaded){web=loaded?this:null;}public boolean isDestroyed(){return destroyed;}public void setUserAgent(int v){ua=v;}public Object getWebContents(){return web;}}',
 'TabUtils.java':'package org.chromium.chrome.browser.tab; public class TabUtils {public static boolean isUsingDesktopUserAgent(Object w){return ((Tab)w).desktop;}public static void switchUserAgent(Tab t,boolean desktop){t.desktop=desktop;t.reloads++;}}',
 'TabUserAgent.java':'package org.chromium.chrome.browser.tab; public class TabUserAgent {public static final int MOBILE=1;}',
 'ArchiumWindowMetrics.java':'package org.chromium.chrome.browser.desktop_policy; public class ArchiumWindowMetrics {public static int currentWidthDp(android.content.Context c){return 1100;}}',
}.items():
 f=a.work/name;f.write_text(body);paths.append(f)
paths += list(ROOT.glob('chromium/**/ArcDesktopAppearance.java'))+list(ROOT.glob('chromium/**/ArcDesktopPolicy.java'))+list(ROOT.glob('chromium/**/ArchiumWindowClass.java'))+[arc/'ArcFrameDispatch.java',arc/'ArcDesktopWindowObserver.java']
cp=a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,paths)],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','ShellTransitionsProbe'])
print('SCOPE=delivered_transition_methods_Android_views_Tab_JNI_adapters_NOT_APK_RUNTIME')
raise SystemExit(r.returncode)
