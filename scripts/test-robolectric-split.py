#!/usr/bin/env python3
"""Actual split controls/animator Android Views; native Tab/compositor execution is separate."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--controller',action='store_true');p.add_argument('--host',action='store_true');p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);cp=a.classpath_file.read_text().strip();classes=a.work/'classes';classes.mkdir(exist_ok=True)
arc=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc';test=ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc'
sources=[arc/'ArcSplitViewportPolicy.java',test/'ArcSplitViewportPolicyTest.java',arc/'ArcSplitDividerView.java',arc/'ArcSplitSwapAnimator.java',test/'ArcSplitControlsTest.java']
tests=['org.chromium.chrome.browser.arc.ArcSplitControlsTest','org.chromium.chrome.browser.arc.ArcSplitViewportPolicyTest']
nav=a.work/'NavigationController.java';nav.write_text('package org.chromium.content_public.browser; public interface NavigationController {boolean getUseDesktopUserAgent(); void setUseDesktopUserAgent(boolean override,boolean reloadOnChange,boolean skipOnInitialNavigation);}')
sources.append(nav)
if a.host or a.controller:
 sources += [arc/'ArcSplitContentHost.java',test/'ArcSplitContentHostTest.java']
 tests += ['org.chromium.chrome.browser.arc.ArcSplitContentHostTest']
 adapters={'ContentView.java':'package org.chromium.components.embedder_support.view; public class ContentView extends android.widget.FrameLayout {public static ContentView createContentView(android.content.Context c,Object wc){return new ContentView(c);} private int offset; public ContentView(android.content.Context c){super(c);} public void setContentOffsetXPix(int x){offset=x;} public int getContentOffsetXPix(){return offset;}}', 'Tab.java':'package org.chromium.chrome.browser.tab; public interface Tab {int INVALID_TAB_ID=-1; int getId(); boolean isDestroyed(); org.chromium.components.embedder_support.view.ContentView getContentView(); android.view.View getView();}'}
 for name,text in adapters.items():
  path=a.work/name;path.write_text(text);sources.append(path)
if a.controller:
 sources += [arc/'ArcSplitState.java',test/'ArcSplitStateTest.java',arc/'ArcSplitViewCoordinator.java',test/'ArcSplitViewCoordinatorTest.java']
 tests += ['org.chromium.chrome.browser.arc.ArcSplitStateTest','org.chromium.chrome.browser.arc.ArcSplitViewCoordinatorTest']
 extra={
 'R.java':'package org.chromium.chrome; public class R {public static class id {public static final int tab_modal_dialog_container=2001,tab_modal_dialog_container_stub=2002;}}',
 'Profile.java':'package org.chromium.chrome.browser.profiles; public class Profile {}',
 'GURL.java':'package org.chromium.url; public class GURL {public String getSpec(){return "https://example.test/";}}',
 'WindowAndroid.java':'package org.chromium.ui.base; public class WindowAndroid {public java.lang.ref.WeakReference<android.app.Activity> getActivity(){return null;}}',
 'Tab.java':'package org.chromium.chrome.browser.tab; public interface Tab {int INVALID_TAB_ID=-1; int getId(); boolean isDestroyed(); org.chromium.content_public.browser.WebContents getWebContents(); boolean isClosing(); boolean isNativePage(); boolean isHidden(); boolean isIncognito(); org.chromium.chrome.browser.profiles.Profile getProfile(); org.chromium.ui.base.WindowAndroid getWindowAndroid(); org.chromium.components.embedder_support.view.ContentView getContentView(); android.view.View getView(); String getTitle(); org.chromium.url.GURL getUrl(); void show(int type); void hide(int type); void reload(); void addObserver(TabObserver o); void removeObserver(TabObserver o);}',
 'TabObserver.java':'package org.chromium.chrome.browser.tab; public interface TabObserver {default void onShown(Tab t,int type){} default void onHidden(Tab t,int type){} default void onDestroyed(Tab t){} default void onContentChanged(Tab t){} default void onActivityAttachmentChanged(Tab t,org.chromium.ui.base.WindowAndroid w){} }',
 'TabModel.java':'package org.chromium.chrome.browser.tabmodel; public interface TabModel {org.chromium.chrome.browser.profiles.Profile getProfile(); int getCount(); org.chromium.chrome.browser.tab.Tab getTabAt(int index); org.chromium.chrome.browser.tab.Tab getTabById(int id); void setIndex(int index,int type); boolean isTabModelRestored(); void addObserver(TabModelObserver o); void removeObserver(TabModelObserver o);}',
 'TabModelObserver.java':'package org.chromium.chrome.browser.tabmodel; import org.chromium.chrome.browser.tab.Tab; public interface TabModelObserver {default void didSelectTab(Tab t,int type,int last){} default void willCloseTabs(java.util.List<Tab> tabs,boolean all,boolean undo){} default void willCloseTab(Tab t,boolean alone){} default void tabRemoved(Tab t){} default void restoreCompleted(){} default void onDidActiveStateChange(TabModel model,boolean active){} }',
 'TabCreator.java':'package org.chromium.chrome.browser.tabmodel; public interface TabCreator {org.chromium.chrome.browser.tab.Tab createNewTab(org.chromium.content_public.browser.LoadUrlParams params,int type,org.chromium.chrome.browser.tab.Tab parent);}',
 'WebContents.java':'package org.chromium.content_public.browser; public interface WebContents {boolean isDestroyed(); int getVirtualKeyboardMode(); NavigationController getNavigationController();}',
 'LoadUrlParams.java':'package org.chromium.content_public.browser; public class LoadUrlParams {public LoadUrlParams(String url){}}',
 'TabLaunchType.java':'package org.chromium.chrome.browser.tab; public class TabLaunchType {public static final int FROM_CHROME_UI=0;}',
 'TabSelectionType.java':'package org.chromium.chrome.browser.tab; public class TabSelectionType {public static final int FROM_USER=1;}',
 'TabHidingType.java':'package org.chromium.chrome.browser.tab; public class TabHidingType {public static final int CHANGED_TABS=0,ACTIVITY_HIDDEN=1;}',
 'CompositorViewHolder.java':'package org.chromium.chrome.browser.compositor; import org.chromium.chrome.browser.tab.Tab; public class CompositorViewHolder extends android.widget.FrameLayout {public interface FrameRequestObserver {void onFrameRequested();} public void addFrameRequestObserver(FrameRequestObserver o){} public void removeFrameRequestObserver(FrameRequestObserver o){} public CompositorViewHolder(android.content.Context c){super(c);} public boolean canPresentArcSplit(){return true;} public android.graphics.Rect getArcSplitViewport(){return new android.graphics.Rect(0,0,1100,800);} public boolean setArcSplitTabs(Tab a,Tab b,float r,int active){return true;} public void clearArcSplitTabs(){} public void setArcSplitSwapProgress(float p){} public void setArcSplitInputBlocked(boolean b){} public void setArcSplitActivation(java.util.function.IntConsumer c){} public void onContentChanged(){} }'
 }
 for name,text in extra.items():
  path=a.work/name;path.write_text(text)
  if path not in sources:sources.append(path)
if a.controller:
 sys.path.insert(0,str(ROOT/'tests'))
 from arc_toolbar_probe import method_body
 scene=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/compositor/scene_layer/StaticTabSceneLayer.java').read_text()
 holder_source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/compositor/CompositorViewHolder.java').read_text()
 layout=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/compositor/layouts/StaticLayout.java').read_text()
 natives=method_body(scene,r'public interface Natives').replace('@Nullable ','')
 # Run delivered JNI Java forwarding and onShown body with explicit model/JNI boundaries.
 code="""package org.chromium.chrome.browser.compositor.scene_layer;
 import android.graphics.RectF; import org.chromium.chrome.browser.tab.Tab;
 import org.chromium.chrome.browser.tab_ui.TabContentManager;
 import org.chromium.cc.input.OffsetTag;
 public class StaticTabSceneLayer {
 long mNativePtr;void initializeNative(){mNativePtr=7;}
 public interface Natives NATIVES
 public void setArcSplitTabs(int leftId,int rightId,RectF left,RectF right) SETTER
 public void clearArcSplitTabs() CLEAR
 }
 """.replace('NATIVES',natives).replace('SETTER',method_body(scene,r'public void setArcSplitTabs\(')).replace('CLEAR',method_body(scene,r'public void clearArcSplitTabs\('))
 path=a.work/'StaticTabSceneLayer.java';path.write_text(code);sources.append(path)
 bridge="""package org.chromium.chrome.browser.compositor.scene_layer;
 public class StaticTabSceneLayerJni {public static StaticTabSceneLayer.Natives instance; public static StaticTabSceneLayer.Natives get(){return instance;}}
 """
 path=a.work/'StaticTabSceneLayerJni.java';path.write_text(bridge);sources.append(path)
 for name,text in {'TabContentManager.java':'package org.chromium.chrome.browser.tab_ui; public class TabContentManager {}', 'OffsetTag.java':'package org.chromium.cc.input; public class OffsetTag {}'}.items():
  path=a.work/name;path.write_text(text);sources.append(path)
 code="""package org.chromium.chrome.browser.arc;
 import static org.junit.Assert.*; import static org.mockito.Mockito.*;
 import org.junit.Test; import org.junit.runner.RunWith; import org.robolectric.RobolectricTestRunner;
 import org.robolectric.annotation.Config; import android.graphics.RectF;
 import org.chromium.chrome.browser.tab.Tab;
 import org.chromium.content_public.browser.WebContents;
 import org.chromium.chrome.browser.compositor.scene_layer.*;
 import android.app.Activity; import android.view.View; import android.view.ViewGroup; import android.widget.FrameLayout;
 import org.chromium.chrome.R; import org.chromium.components.embedder_support.view.ContentView;
 @RunWith(RobolectricTestRunner.class) @Config(manifest=Config.NONE,sdk={30,36})
 @org.robolectric.annotation.GraphicsMode(org.robolectric.annotation.GraphicsMode.Mode.LEGACY)
 @org.robolectric.annotation.SQLiteMode(org.robolectric.annotation.SQLiteMode.Mode.LEGACY)
 public class NativeSplitBridgeTest {
  static class FocusHolder extends FrameLayout {
   Activity mActivity;ArcSplitContentHost mArcSplitHost;View mUrlBar;boolean window=true;int focusUpdates;
   FocusHolder(Activity a){super(a);mActivity=a;mArcSplitHost=new ArcSplitContentHost(this);}
   @Override public boolean hasWindowFocus(){return window;}
   void updateFocusability(boolean focusable,boolean block){focusUpdates++;}
   private void focusArcSplitTab(Tab tab) FOCUS
  }
  @Test public void nativeFocusHelperPreservesAddressModalAndOtherWindowFocus(){
   Activity a=org.robolectric.Robolectric.buildActivity(Activity.class).setup().get();FrameLayout root=new FrameLayout(a);a.setContentView(root);
   FocusHolder h=new FocusHolder(a);root.addView(h);Tab left=mock(Tab.class),right=mock(Tab.class);
   ContentView l=ContentView.createContentView(a,null),r=ContentView.createContentView(a,null);l.setFocusableInTouchMode(true);r.setFocusableInTouchMode(true);
   when(left.getId()).thenReturn(17);when(right.getId()).thenReturn(18);when(left.getView()).thenReturn(l);when(right.getView()).thenReturn(r);
   when(left.getContentView()).thenReturn(l);when(right.getContentView()).thenReturn(r);
   assertTrue(h.mArcSplitHost.show(left,right,new android.graphics.Rect(0,0,1000,800),.5f));
   h.focusArcSplitTab(left);h.focusArcSplitTab(right);assertTrue(r.hasFocus());assertFalse(l.hasFocus());
   var address=new android.widget.EditText(a);root.addView(address);h.mUrlBar=address;address.requestFocus();
   h.focusArcSplitTab(left);assertTrue(address.hasFocus());address.clearFocus();h.focusArcSplitTab(right);
   FrameLayout modal=new FrameLayout(a);modal.setId(R.id.tab_modal_dialog_container);modal.addView(new View(a));root.addView(modal);
   h.focusArcSplitTab(left);assertFalse(l.hasFocus());modal.setVisibility(View.GONE);h.window=false;
   h.focusArcSplitTab(left);assertFalse(l.hasFocus());h.window=true;h.focusArcSplitTab(left);assertTrue(l.hasFocus());a.finish();
  }
  static class HolderProbe {
   Tab mArcSplitLeft,current;int mode;boolean mControlsResizeView;
   android.view.View mCompositorView=new android.view.View(org.robolectric.RuntimeEnvironment.getApplication());
   Tab getCurrentTab(){return current;}void updateVirtualKeyboardMode(int m){mode=m;}
   void onPhysicalBackingSizeChanged(WebContents w,int x,int y){}void onControlsResizeViewChanged(WebContents w,boolean b){}
   void updateWebContentsSize(Tab t){}
   static class VirtualKeyboardMode {static final int UNSET=0;}
   private void initializeTab(Tab tab) INITIALIZE
  }
  @Test public void inactiveInitializationCannotOverwriteActiveKeyboardPolicy(){
   HolderProbe p=new HolderProbe();Tab a=mock(Tab.class),b=mock(Tab.class);WebContents wa=mock(WebContents.class),wb=mock(WebContents.class);
   when(a.getWebContents()).thenReturn(wa);when(b.getWebContents()).thenReturn(wb);
   when(wa.getVirtualKeyboardMode()).thenReturn(1);when(wb.getVirtualKeyboardMode()).thenReturn(2);
   p.mArcSplitLeft=a;p.current=a;p.initializeTab(a);p.initializeTab(b);assertEquals(1,p.mode);
   p.current=b;p.initializeTab(b);p.initializeTab(a);assertEquals(2,p.mode);
  }
  static class LayoutTab {static final int TAB_ID=1;}
  static class Model {int id;int get(int key){return id;}}
  static class Selector {Tab active;Tab getCurrentTab(){return active;}}
  static class LayoutProbe {
   int mArcSplitLeftId=17,mArcSplitRightId=18;Model mModel=new Model();Selector mTabModelSelector=new Selector();int changes,updates;
   void setStaticTab(Tab t){mModel.id=t.getId();changes++;}void updateStaticTab(Tab t,boolean b){updates++;}
   void onShown(Tab tab,int type) SHOWN
  }
  @Test public void secondaryOnShownCannotRetargetPrimaryScene(){
   LayoutProbe p=new LayoutProbe();Tab a=mock(Tab.class),b=mock(Tab.class);when(a.getId()).thenReturn(17);when(b.getId()).thenReturn(18);
   p.mTabModelSelector.active=a;p.mModel.id=17;p.onShown(b,0);assertEquals(17,p.mModel.id);assertEquals(0,p.changes);
   p.mTabModelSelector.active=b;p.onShown(b,0);assertEquals(18,p.mModel.id);assertEquals(1,p.changes);
   p.onShown(b,0);assertEquals(1,p.updates);
  }
  @Test public void nativeForwardingUsesDistinctIdsAndExactPhysicalRects(){
   var tap=mock(StaticTabSceneLayer.Natives.class);StaticTabSceneLayerJni.instance=tap;
   var layer=new StaticTabSceneLayer();layer.setArcSplitTabs(17,18,new RectF(216,0,716,800),new RectF(716,0,1216,800));
   verify(tap).setArcSplitTabs(7L,17,18,216f,0f,500f,800f,716f,0f,500f,800f);
   layer.clearArcSplitTabs();verify(tap).setArcSplitTabs(7L,-1,-1,0f,0f,0f,0f,0f,0f,0f,0f);
  }
 }
 """.replace('SHOWN',method_body(layout,r'public void onShown\(')).replace('INITIALIZE',method_body(holder_source,r'private void initializeTab\(')).replace('FOCUS',method_body(holder_source,r'private void focusArcSplitTab\('))
 path=a.work/'NativeSplitBridgeTest.java';path.write_text(code);sources.append(path)
 assert 'focusArcSplitTab(tab);' in method_body(holder_source,r'private void setTab\('), 'Native rail selection must transfer pane focus'
 assert 'focusArcSplitTab(active);' in method_body(holder_source,r'public boolean setArcSplitTabs\('), 'Initial presentation must transfer pane focus'
 tests.append('org.chromium.chrome.browser.arc.NativeSplitBridgeTest')
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,sources)],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore',*tests])
print('SCOPE=ACTUAL_ANDROID_CONTROLS_AND_ANIMATOR_NOT_WEB_COMPOSITION');raise SystemExit(r.returncode)
