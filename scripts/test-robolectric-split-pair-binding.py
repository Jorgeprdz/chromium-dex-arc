#!/usr/bin/env python3
"""Run delivered pair favicon callbacks and compact icon policy on Android views.

Only model keys, native fetch scheduling and surrounding row/palette APIs are fixtures.
The binder methods, pair metadata and pair drawable composition are extracted verbatim.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import method_body

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file', type=Path)
p.add_argument('--java-home', type=Path)
p.add_argument('--work', type=Path)
p.add_argument('--check-source-only', action='store_true')
a = p.parse_args()
binder = (ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java').read_text()
properties = (ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/TabProperties.java').read_text()
if 'private static void bindArcSplitPairIcons(' not in binder:
    sys.exit('RED: delivered binder has no bindArcSplitPairIcons helper')
if 'Drawable defaultIcon' not in properties:
    sys.exit('RED: delivered pair metadata has no native defaultIcon fallback')
if a.check_source_only:
    print('PAIR_BINDING_SOURCE_CONTRACT_PRESENT; callback behavior still requires Android runner')
    sys.exit(0)
if not all((a.classpath_file, a.java_home, a.work)):
    p.error('--classpath-file, --java-home and --work required for Android execution')
a.work.mkdir(parents=True, exist_ok=True)
classes = a.work / 'classes'
classes.mkdir(exist_ok=True)
java = r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.*;
import android.view.*;
import android.widget.*;
import java.util.*;
import java.lang.annotation.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.tab_ui.TabListFaviconProvider;
import org.chromium.chrome.browser.tab_ui.TabListFaviconProvider.TabFavicon;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcSplitPairVisuals;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36},qualifiers="mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class SplitPairBindingProbe {
 @Target({ElementType.TYPE_USE,ElementType.LOCAL_VARIABLE,ElementType.PARAMETER}) @interface Nullable {}
 @interface ColorInt {}
 static class Key<T> {}
 static class PropertyModel {
  final Map<Key<?>,Object> values=new HashMap<>();
  @SuppressWarnings("unchecked") <T> T get(Key<T> key){return (T)values.get(key);}
  <T> void set(Key<T> key,T value){values.put(key,value);}
  boolean containsKey(Key<?> key){return values.containsKey(key);}
 }
 static class TabProperties {
  static final Key<ArcSplitPair> ARC_SPLIT_PAIR=new Key<>();
  static final Key<Integer> TAB_ID=new Key<>(),ALERT_STATE=new Key<>();
  static final Key<Boolean> IS_SELECTED=new Key<>(),IS_LOADING=new Key<>(),IS_INCOGNITO=new Key<>();
  static final Key<TabActionButtonData> TAB_ACTION_BUTTON_DATA=new Key<>();
  static final Key<TabListFaviconProvider.TabFaviconFetcher> FAVICON_FETCHER=new Key<>();
  public static final class ArcSplitPair PAIR_BODY
 }
 static class TabActionButtonData {}
 @interface TabAlert {int NONE=0,ACTOR_ACCESSING=1;}
 static class DeviceInfo {static boolean isDesktop(){return true;}}
 static class R {static class id {static final int tab_favicon=1,action_button=2,alert_indicator_icon=3,tab_loading_spinner=4;}}
 static class ArcDesktopAppearance {
  static boolean isDesktopWindow(Context context){return true;}
  static int foreground(Context context,boolean incognito){return incognito?Color.WHITE:Color.BLACK;}
  static void normalizeSidebarFavicon(ImageView view){view.setScaleType(ImageView.ScaleType.FIT_CENTER);view.setImageTintList(null);}
 }
 static class TabListViewBinderUtils {
  static final Drawable ordinary=new ColorDrawable(Color.GRAY);
  // Native Utils stamps fetcher before asynchronous delivery; palette/delivery remain fixtures.
  static void updateFaviconImage(PropertyModel model,ImageView view){view.setTag(model.get(TabProperties.FAVICON_FETCHER));view.setImageDrawable(ordinary);}
 }
 static class VerticalTabItemLayout extends LinearLayout {
  final ImageView icon;
  boolean showAction,showAlert,showLoading,showFavicon;
  VerticalTabItemLayout(Context context){super(context);icon=new ImageView(context);icon.setId(R.id.tab_favicon);addView(icon);
   for(int id:new int[]{R.id.action_button,R.id.alert_indicator_icon,R.id.tab_loading_spinner}){View child=new View(context);child.setId(id);addView(child);}}
  void updateIconDisplay(boolean only,boolean action,boolean alert,boolean actor,boolean loading,int color,boolean favicon){
   showAction=action;showAlert=alert;showLoading=loading;showFavicon=favicon;
   icon.setVisibility(favicon?View.VISIBLE:View.GONE);
  }
 }
 static boolean compact;
 static boolean shouldShowIconOnly(PropertyModel model,View view){return compact;}
 static boolean isPinned(PropertyModel model,View view){return false;}
 static boolean isIncognito(PropertyModel model){return model.get(TabProperties.IS_INCOGNITO);}
 static int getLoadingSpinnerColor(PropertyModel model,Context context){return Color.BLACK;}
 static void updateIcons(PropertyModel model,VerticalTabItemLayout view){updateIcons(model,view,view.isHovered());}
 private static void updateFaviconImage(PropertyModel model,VerticalTabItemLayout view) FAVICON_BODY
 private static void bindArcSplitPairIcons(PropertyModel model,ImageView faviconView,TabProperties.ArcSplitPair pair) PAIR_ICONS_BODY
 private static void updateIcons(PropertyModel model,VerticalTabItemLayout view,boolean isHovered) ICON_POLICY_BODY
 static class DeferredFetcher extends TabListFaviconProvider.TabFaviconFetcher {
  final List<org.chromium.base.Callback<TabFavicon>> callbacks=new ArrayList<>();
  @Override public void fetch(org.chromium.base.Callback<TabFavicon> callback){callbacks.add(callback);}
  void deliver(int request,Drawable icon){callbacks.get(request).onResult(icon==null?null:new TabFavicon(icon));}
  void deliverNullDrawable(int request){callbacks.get(request).onResult(new TabFavicon(null));}
 }
 static class TrackedIcon extends ColorDrawable {
  int draws;
  TrackedIcon(int color){super(color);}
  @Override public void draw(Canvas canvas){draws++;super.draw(canvas);}
 }
 org.robolectric.android.controller.ActivityController<Activity> controller;
 Activity a;
 @Before public void setup(){controller=Robolectric.buildActivity(Activity.class).setup();a=controller.get();compact=false;}
 @After public void close(){controller.pause().stop().destroy();}
 PropertyModel model(int id,TabProperties.ArcSplitPair pair,boolean incognito){
  PropertyModel m=new PropertyModel();m.set(TabProperties.TAB_ID,id);m.set(TabProperties.ARC_SPLIT_PAIR,pair);
  m.set(TabProperties.IS_SELECTED,true);m.set(TabProperties.IS_LOADING,false);m.set(TabProperties.IS_INCOGNITO,incognito);
  m.set(TabProperties.FAVICON_FETCHER,new DeferredFetcher());m.set(TabProperties.TAB_ACTION_BUTTON_DATA,new TabActionButtonData());return m;
 }
 TabProperties.ArcSplitPair pair(DeferredFetcher left,DeferredFetcher right,Drawable fallback){
  return new TabProperties.ArcSplitPair(17,18,17,"Left","Right",left,right,fallback);
 }
 void draw(ImageView view){Drawable d=view.getDrawable();assertNotNull(d);d.setBounds(0,0,48,24);d.draw(new Canvas());}
 @Test public void nativeFetchersPopulateBothIconsAndNullCallbacksKeepFallback(){
  DeferredFetcher left=new DeferredFetcher(),right=new DeferredFetcher();TrackedIcon fallback=new TrackedIcon(Color.GRAY),l=new TrackedIcon(Color.RED),r=new TrackedIcon(Color.BLUE);
  VerticalTabItemLayout row=new VerticalTabItemLayout(a);PropertyModel m=model(17,pair(left,right,fallback),false);
  updateFaviconImage(m,row);assertEquals(1,left.callbacks.size());assertEquals(1,right.callbacks.size());
  draw(row.icon);assertEquals(2,fallback.draws);
  left.deliver(0,l);right.deliver(0,null);draw(row.icon);assertEquals(1,l.draws);assertEquals(3,fallback.draws);
  right.deliverNullDrawable(0);draw(row.icon);assertEquals(2,l.draws);assertEquals(4,fallback.draws);
  right.deliver(0,r);draw(row.icon);assertEquals(3,l.draws);assertEquals(1,r.draws);
 }
 @Test public void recycledProfileAndDifferentPairRejectOldNativeCallbacks(){
  DeferredFetcher left=new DeferredFetcher(),right=new DeferredFetcher();TrackedIcon fallback=new TrackedIcon(Color.GRAY),stale=new TrackedIcon(Color.MAGENTA);
  VerticalTabItemLayout row=new VerticalTabItemLayout(a);PropertyModel normal=model(17,pair(left,right,fallback),false);
  updateFaviconImage(normal,row);
  DeferredFetcher privateLeft=new DeferredFetcher(),privateRight=new DeferredFetcher();TrackedIcon a=new TrackedIcon(Color.RED),b=new TrackedIcon(Color.BLUE);
  PropertyModel privateModel=model(17,pair(privateLeft,privateRight,fallback),true);updateFaviconImage(privateModel,row);
  privateLeft.deliver(0,a);privateRight.deliver(0,b);Drawable current=row.icon.getDrawable();
  left.deliver(0,stale);right.deliver(0,stale);assertSame(current,row.icon.getDrawable());draw(row.icon);
  assertEquals(0,stale.draws);assertEquals(1,a.draws);assertEquals(1,b.draws);
 }
 @Test public void changedPairIdentityAndRowIdRejectCallbacksBeforeRebind(){
  DeferredFetcher left=new DeferredFetcher(),right=new DeferredFetcher();TrackedIcon fallback=new TrackedIcon(Color.GRAY),stale=new TrackedIcon(Color.RED);
  VerticalTabItemLayout row=new VerticalTabItemLayout(a);PropertyModel m=model(17,pair(left,right,fallback),false);updateFaviconImage(m,row);
  Drawable current=row.icon.getDrawable();m.set(TabProperties.ARC_SPLIT_PAIR,pair(new DeferredFetcher(),new DeferredFetcher(),fallback));
  left.deliver(0,stale);assertSame(current,row.icon.getDrawable());
  m.set(TabProperties.ARC_SPLIT_PAIR,null);right.deliver(0,stale);assertSame(current,row.icon.getDrawable());
  DeferredFetcher l2=new DeferredFetcher(),r2=new DeferredFetcher();m.set(TabProperties.ARC_SPLIT_PAIR,pair(l2,r2,fallback));updateFaviconImage(m,row);
  current=row.icon.getDrawable();m.set(TabProperties.TAB_ID,99);l2.deliver(0,stale);r2.deliver(0,stale);
  assertSame(current,row.icon.getDrawable());draw(row.icon);assertEquals(0,stale.draws);
 }
 @Test public void repeatedBindingOfSamePairInvalidatesPreviousGeneration(){
  DeferredFetcher left=new DeferredFetcher(),right=new DeferredFetcher();TrackedIcon fallback=new TrackedIcon(Color.GRAY),stale=new TrackedIcon(Color.RED),live=new TrackedIcon(Color.BLUE);
  VerticalTabItemLayout row=new VerticalTabItemLayout(a);PropertyModel m=model(17,pair(left,right,fallback),false);
  updateFaviconImage(m,row);updateFaviconImage(m,row);left.deliver(1,live);right.deliver(1,live);
  Drawable current=row.icon.getDrawable();left.deliver(0,stale);right.deliver(0,stale);
  assertSame(current,row.icon.getDrawable());draw(row.icon);assertEquals(0,stale.draws);assertEquals(2,live.draws);
 }
 @Test public void ordinaryRecycledRowCancelsPreviousPairCallbacks(){
  DeferredFetcher left=new DeferredFetcher(),right=new DeferredFetcher();TrackedIcon fallback=new TrackedIcon(Color.GRAY),stale=new TrackedIcon(Color.RED);
  VerticalTabItemLayout row=new VerticalTabItemLayout(a);PropertyModel paired=model(17,pair(left,right,fallback),false);updateFaviconImage(paired,row);
  PropertyModel normal=model(22,null,false);updateFaviconImage(normal,row);Drawable current=row.icon.getDrawable();
  left.deliver(0,stale);right.deliver(0,stale);assertSame(current,row.icon.getDrawable());
  draw(row.icon);assertEquals(0,stale.draws);
 }
 @Test public void compactSelectedHoveredPairKeepsBothLogosInsteadOfCloseSpinnerOrAlert(){
  DeferredFetcher left=new DeferredFetcher(),right=new DeferredFetcher();TrackedIcon fallback=new TrackedIcon(Color.GRAY),l=new TrackedIcon(Color.RED),r=new TrackedIcon(Color.BLUE);
  VerticalTabItemLayout row=new VerticalTabItemLayout(a);PropertyModel m=model(17,pair(left,right,fallback),false);
  compact=true;m.set(TabProperties.IS_LOADING,true);m.set(TabProperties.ALERT_STATE,TabAlert.ACTOR_ACCESSING);
  updateFaviconImage(m,row);left.deliver(0,l);right.deliver(0,r);updateIcons(m,row,true);
  assertFalse(row.showAction);assertFalse(row.showAlert);assertFalse(row.showLoading);assertTrue(row.showFavicon);
  assertEquals(View.VISIBLE,row.icon.getVisibility());draw(row.icon);assertEquals(1,l.draws);assertEquals(1,r.draws);
  compact=false;updateIcons(m,row,true);assertTrue("Expanded pair retains native close action",row.showAction);
 }
}
'''
java = java.replace('PAIR_BODY', method_body(properties, r'public static final class ArcSplitPair'))
java = java.replace('FAVICON_BODY', method_body(binder, r'private static void updateFaviconImage\('))
java = java.replace('PAIR_ICONS_BODY', method_body(binder, r'private static void bindArcSplitPairIcons\('))
java = java.replace('ICON_POLICY_BODY', method_body(binder, r'private static void updateIcons\(\s*PropertyModel model, VerticalTabItemLayout view, boolean isHovered\)'))
sources = []
for name, content in {
    'SplitPairBindingProbe.java': java,
    'Callback.java': 'package org.chromium.base; public interface Callback<T>{void onResult(T value);}',
    'TabListFaviconProvider.java': '''package org.chromium.chrome.browser.tab_ui;
public class TabListFaviconProvider {
 public abstract static class TabFaviconFetcher {public abstract void fetch(org.chromium.base.Callback<TabFavicon> callback);}
 public static class TabFavicon {private final android.graphics.drawable.Drawable icon;
  public TabFavicon(android.graphics.drawable.Drawable value){icon=value;}
  public android.graphics.drawable.Drawable getDefaultDrawable(){return icon;}}
}''',
}.items():
    path = a.work / name
    path.write_text(content)
    sources.append(path)
sources += list(ROOT.glob('chromium/**/ArcSplitPairVisuals.java'))
cp = a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home / 'bin/javac'), '-cp', cp, '-d', str(classes), *map(str, sources)], check=True)
r = subprocess.run([str(a.java_home / 'bin/java'), '-ea', '-Xmx512m', '-XX:ActiveProcessorCount=2', '-Drobolectric.conscryptMode=OFF', '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2', '-cp', str(classes) + ':' + cp, 'org.junit.runner.JUnitCore', 'SplitPairBindingProbe'])
print('SCOPE=DELIVERED_BINDER_CALLBACKS_AND_COMPACT_ICON_POLICY_REAL_ANDROID_VIEWS_NATIVE_FETCH_MODEL_PALETTE_FIXTURES_NOT_APK_GPU')
sys.exit(r.returncode)
