#!/usr/bin/env python3
"""Execute delivered sidebar binder title logic and appearance helpers on Android views.

Chromium resources/model construction are fixture boundaries; not an APK or GPU test.
"""
import argparse, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import method_body
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file',type=Path,required=True)
p.add_argument('--java-home',type=Path,required=True)
p.add_argument('--work',type=Path,required=True)
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
classes=a.work/'classes';classes.mkdir(exist_ok=True)
binder=(ROOT/'.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java').read_text()
test=r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.content.res.ColorStateList;
import android.graphics.*;
import android.graphics.drawable.*;
import android.view.*;
import android.text.TextUtils;
import android.widget.*;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36},qualifiers="mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class SidebarAppearanceProbe {
 org.robolectric.android.controller.ActivityController<Activity> controller;
 Activity a;
 @Before public void setup(){controller=Robolectric.buildActivity(Activity.class).setup();a=controller.get();ArcDesktopAppearance.setUiMode(a,ArcDesktopPolicy.MODE_ARC);}
 @After public void close(){if(controller!=null)controller.pause().stop().destroy();}
 public static void main(String[] args){
  org.junit.runner.JUnitCore junit=new org.junit.runner.JUnitCore();
  junit.addListener(new org.junit.internal.TextListener(System.out));
  junit.addListener(new org.junit.runner.notification.RunListener(){
   @Override public void testStarted(org.junit.runner.Description d){System.out.println("START "+d.getDisplayName());}
   @Override public void testFinished(org.junit.runner.Description d){System.out.println("END "+d.getDisplayName());}
  });
  System.exit(junit.run(SidebarAppearanceProbe.class).wasSuccessful()?0:1);
 }
 static class R {static class id {static final int tab_title=0x7f010001,action_button=0x7f010002;}}
 static class TabProperties {static final Object TITLE=new Object(),ARC_SPLIT_PAIR=new Object();static class ArcSplitPair{}}
 static class PropertyModel {
  String title;PropertyModel(String t){title=t;}
  @SuppressWarnings("unchecked") <T>T get(Object key){return (T)(key==TabProperties.TITLE?title:null);}
 }
 static class TabListViewBinderUtils {static void updateActionButtonContentDescription(PropertyModel m,View v){}}
 // Pair formatting is exercised by test-robolectric-split-pair-visuals.py, not this normal-row fixture.
 static void updatePairTitle(PropertyModel m,ViewGroup v,TextView t,TabProperties.ArcSplitPair p){throw new AssertionError("Unexpected pair in normal-row fixture");}
 static boolean collapsed;
 static boolean shouldShowIconOnly(PropertyModel m,View v){return collapsed;}
 static void updateContentDescription(PropertyModel m,View v){}
 TITLE_METHOD
 void row(View v,boolean active,boolean multi,boolean hover) throws Exception {
  ArcDesktopAppearance.class.getMethod("applySidebarRowState",View.class,boolean.class,boolean.class,boolean.class,boolean.class)
   .invoke(null,v,active,multi,false,hover);
 }
 int fill(View v){return v.getBackgroundTintList().getDefaultColor();}
 @Test public void sidebarTitleGrowsOnceAndRestoresWhenLeavingDesktop() throws Exception {
  TextView text=new TextView(a);text.setTextSize(12);
  var method=ArcDesktopAppearance.class.getMethod("styleSidebarTitle",TextView.class);
  method.invoke(null,text);method.invoke(null,text);
  assertEquals(13,text.getTextSize()/a.getResources().getDisplayMetrics().scaledDensity,.01f);
  ArcDesktopAppearance.setUiMode(a,ArcDesktopPolicy.MODE_MOBILE);method.invoke(null,text);
  assertEquals(12,text.getTextSize()/a.getResources().getDisplayMetrics().scaledDensity,.01f);
 }
 @Test public void pairedFaviconsHaveIndependentOpticalSpaceAndRestoreNativeBox() throws Exception {
  ImageView icon=new ImageView(a);icon.setLayoutParams(new LinearLayout.LayoutParams(16,16));
  var size=ArcDesktopAppearance.class.getMethod("sizeSidebarFavicon",ImageView.class,boolean.class,boolean.class);
  size.invoke(null,icon,true,false);assertEquals(41,icon.getLayoutParams().width);assertEquals(20,icon.getLayoutParams().height);
  size.invoke(null,icon,true,true);assertEquals(32,icon.getLayoutParams().width);assertEquals(20,icon.getLayoutParams().height);
  size.invoke(null,icon,false,false);assertEquals(20,icon.getLayoutParams().width);
  ArcDesktopAppearance.class.getMethod("restoreSidebarFaviconSize",ImageView.class).invoke(null,icon);
  assertEquals(16,icon.getLayoutParams().width);assertEquals(16,icon.getLayoutParams().height);
 }
 @Test public void defaultLavenderAndVioletSelectionHaveReadableForegroundAndCustomColorsPersist(){
  var prefs=ArcDesktopAppearance.preferences(a);prefs.edit().remove(ArcDesktopAppearance.COLOR_KEY).commit();
  assertEquals(0xffdccdf7,ArcDesktopAppearance.surface(a,false));
  int selected=ArcDesktopAppearance.activeTabSurface(a,false);assertEquals(0xff7365d8,selected);
  assertTrue(ArcDesktopPolicy.contrast(selected,ArcDesktopPolicy.foreground(selected))>=4.5);
  prefs.edit().putInt(ArcDesktopAppearance.COLOR_KEY,0xffee4400).commit();
  assertEquals(0xfffce0d5,ArcDesktopAppearance.activeTabSurface(a,false));
  assertNotEquals(ArcDesktopAppearance.surface(a,false),ArcDesktopAppearance.surface(a,true));
 }
 @Test public void selectedCollapsedTitleSurvivesRecycleAndClearsEmptyTooltip(){
  LinearLayout v=new LinearLayout(a);TextView title=new TextView(a);title.setId(123);v.addView(title);v.setSelected(true);
  View.OnLayoutChangeListener oldPairListener=(changed,l,t,r,b,ol,ot,or,ob)->{};
  title.addOnLayoutChangeListener(oldPairListener);title.setTag(R.id.tab_title,oldPairListener);
  View close=new View(a);close.setId(R.id.action_button);close.setTooltipText("Close pair member");v.addView(close);
  collapsed=true;PropertyModel m=new PropertyModel("First selected title");updateTitle(123,m,v);
  assertNull(title.getTag(R.id.tab_title));assertNull(close.getTooltipText());
  assertEquals("First selected title",v.getTooltipText());assertEquals("First selected title",title.getText().toString());
  m.title="Recycled title";updateTitle(123,m,v);assertEquals("Recycled title",v.getTooltipText());
  assertEquals("Recycled title",title.getText().toString());assertEquals(View.GONE,title.getVisibility());
  collapsed=false;updateTitle(123,m,v);assertEquals(View.VISIBLE,title.getVisibility());
  m.title="";updateTitle(123,m,v);assertNull(v.getTooltipText());assertEquals("",title.getText().toString());
 }
 @Test public void activeSurfacePersistsThroughHoverAndMultiSelectionIsDistinct() throws Exception {
  View v=new View(a);GradientDrawable bg=new GradientDrawable();bg.setCornerRadius(12);v.setBackground(bg);
  row(v,true,false,false);int selected=fill(v);assertEquals(ArcDesktopAppearance.activeTabSurface(a,false),selected);
  row(v,true,false,true);assertEquals(selected,fill(v));assertSame(bg,v.getBackground());
  row(v,false,true,true);assertEquals(ArcDesktopAppearance.selection(a,false),fill(v));
  row(v,false,false,true);assertEquals(ArcDesktopAppearance.selection(a,false),fill(v));
  row(v,false,false,false);assertEquals(Color.TRANSPARENT,fill(v));
  assertEquals(12,bg.getCornerRadius(),0);assertNull(v.getLayoutParams());
 }
 @Test public void disabledRowsAttenuateTheSameFillAndSuppressFocusHighlight() throws Exception {
  View v=new View(a);row(v,true,false,true);
  int enabled=fill(v);
  int disabled=v.getBackgroundTintList().getColorForState(new int[]{-android.R.attr.state_enabled},enabled);
  assertEquals(enabled&0x00ffffff,disabled&0x00ffffff);
  assertEquals(Math.round(Color.alpha(enabled)*.4f),Color.alpha(disabled));
  var enabledFocus=outline(v,new int[]{android.R.attr.state_enabled,android.R.attr.state_focused});
  v.setEnabled(false);
  var disabledFocus=outline(v,new int[]{-android.R.attr.state_enabled,android.R.attr.state_focused});
  assertTrue(disabledFocus.paint.getAlpha()<enabledFocus.paint.getAlpha());
  assertEquals(Math.round(64*.4f),disabledFocus.paint.getAlpha());
  assertEquals(1f,v.getAlpha(),0);
  row(v,false,false,false);
  assertEquals(Color.TRANSPARENT,v.getBackgroundTintList().getColorForState(new int[]{-android.R.attr.state_enabled},Color.RED));
 }
 org.robolectric.shadows.ShadowCanvas.RoundRectPaintHistoryEvent outline(View v,int[] states){
  Drawable d=v.getForeground();assertNotNull(d);d.setBounds(0,0,80,40);d.setState(states);
  Canvas canvas=new Canvas();d.draw(canvas);
  org.robolectric.shadows.ShadowCanvas shadow=org.robolectric.Shadows.shadowOf(canvas);
  return shadow.getRoundRectPaintHistoryCount()==0 ? null : shadow.getLastDrawnRoundRect();
 }
 @Test public void selectedAndKeyboardFocusHaveInsideOutlineWithoutChangingPadding() throws Exception {
  View v=new View(a);GradientDrawable bg=new GradientDrawable();bg.setCornerRadius(12);v.setBackground(bg);v.setPadding(7,8,9,10);
  row(v,true,false,true);
  var selected=outline(v,new int[]{android.R.attr.state_selected});
  var focused=outline(v,new int[]{android.R.attr.state_selected,android.R.attr.state_focused});
  assertTrue(selected.paint.getAlpha()>0);assertTrue(focused.paint.getAlpha()>selected.paint.getAlpha());
  assertEquals(1f,focused.paint.getStrokeWidth(),0);assertEquals(Paint.Style.STROKE,focused.paint.getStyle());
  assertEquals(.5f,focused.left,0);assertEquals(.5f,focused.top,0);assertEquals(79.5f,focused.right,0);assertEquals(39.5f,focused.bottom,0);
  assertEquals(11.5f,focused.rx,0);assertEquals(11.5f,focused.ry,0);
  row(v,false,false,false);assertNull(outline(v,new int[]{}));
  assertEquals(7,v.getPaddingLeft());assertEquals(8,v.getPaddingTop());assertEquals(9,v.getPaddingRight());assertEquals(10,v.getPaddingBottom());
 }
 @Test public void outlineFollowsExistingNativeInsetsAndClearsForMobile() throws Exception {
  View v=new View(a);GradientDrawable shape=new GradientDrawable();shape.setCornerRadius(12);
  InsetDrawable bg=new InsetDrawable(shape,0,4,0,4);v.setBackground(bg);bg.setBounds(0,0,80,40);
  row(v,true,false,false);var drawn=outline(v,new int[]{});
  assertEquals(4.5f,drawn.top,0);assertEquals(35.5f,drawn.bottom,0);
  ArcDesktopAppearance.class.getMethod("clearSidebarRowState",View.class).invoke(null,v);
  assertNull(v.getForeground());assertSame(bg,v.getBackground());
 }
 @Test public void faviconContainmentKeepsDrawableTintBoundsAndBox() throws Exception {
  ImageView v=new ImageView(a);v.setLayoutParams(new LinearLayout.LayoutParams(24,24));
  ColorDrawable fallback=new ColorDrawable(Color.BLUE);v.setImageDrawable(fallback);v.setScaleType(ImageView.ScaleType.CENTER_CROP);
  ArcDesktopAppearance.class.getMethod("normalizeSidebarFavicon",ImageView.class).invoke(null,v);
  assertEquals(ImageView.ScaleType.FIT_CENTER,v.getScaleType());assertSame(fallback,v.getDrawable());
  assertNull(v.getImageTintList());assertEquals(24,v.getLayoutParams().width);assertEquals(24,v.getLayoutParams().height);
  v.setImageDrawable(new ColorDrawable(Color.RED));ArcDesktopAppearance.class.getMethod("normalizeSidebarFavicon",ImageView.class).invoke(null,v);
  assertEquals(ImageView.ScaleType.FIT_CENTER,v.getScaleType());assertNull(v.getImageTintList());
 }
 View attachedRow(){
  LinearLayout host=new LinearLayout(a);View v=new View(a);host.addView(v,new LinearLayout.LayoutParams(80,40));
  a.setContentView(host);org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
  assertTrue(v.isAttachedToWindow());return v;
 }
 @Test public void selectionOutlineAnimatesOnlyItsPaintAndRebindCancelsOldSelection() throws Exception {
  View v=attachedRow();row(v,false,false,false);int baseline=android.animation.ValueAnimator.getCurrentAnimationsCount();
  row(v,true,false,false);
  assertTrue("Selection should start its bounded paint animation",android.animation.ValueAnimator.getCurrentAnimationsCount()>baseline);
  assertNull("Animation starts from the old outline alpha",outline(v,new int[]{}));
  row(v,false,false,false);
  assertEquals("Rebind cancels previous selection animation",baseline,android.animation.ValueAnimator.getCurrentAnimationsCount());
  org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(200));
  assertNull(outline(v,new int[]{}));assertEquals(1f,v.getAlpha(),0);assertEquals(80,v.getLayoutParams().width);assertEquals(40,v.getLayoutParams().height);
  row(v,true,false,false);assertTrue(android.animation.ValueAnimator.getCurrentAnimationsCount()>baseline);
  ArcDesktopAppearance.clearSidebarRowState(v);
  assertEquals(baseline,android.animation.ValueAnimator.getCurrentAnimationsCount());assertNull(v.getForeground());
 }
 @Test public void detachCancelsOutlineAnimationAndSettlesItsTarget() throws Exception {
  View v=attachedRow();row(v,false,false,false);int baseline=android.animation.ValueAnimator.getCurrentAnimationsCount();
  row(v,true,false,false);
  assertTrue(android.animation.ValueAnimator.getCurrentAnimationsCount()>baseline);
  ((ViewGroup)v.getParent()).removeView(v);
  assertEquals("Detached recycled rows cannot retain animation callbacks",baseline,android.animation.ValueAnimator.getCurrentAnimationsCount());
  assertEquals(64,outline(v,new int[]{}).paint.getAlpha());
 }
 @Test public void selectionPaintFadeFinishesWithinItsShortBudget() throws Exception {
  // Default Robolectric vsync eagerly advances time and drains every animation frame.
  org.robolectric.shadows.ShadowChoreographer.setPaused(true);
  org.robolectric.shadows.ShadowChoreographer.setFrameDelay(java.time.Duration.ofMillis(16));
  View v=attachedRow();row(v,false,false,false);int baseline=android.animation.ValueAnimator.getCurrentAnimationsCount();
  row(v,true,false,false);
  // Commit the initial frame before measuring the 100ms animation timeline.
  org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(16));
  org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(50));
  int intermediate=outline(v,new int[]{}).paint.getAlpha();assertTrue("Intermediate alpha="+intermediate,intermediate>0);assertTrue("Intermediate alpha="+intermediate,intermediate<64);
  org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(100));
  assertEquals(64,outline(v,new int[]{}).paint.getAlpha());
  assertEquals(baseline,android.animation.ValueAnimator.getCurrentAnimationsCount());
 }
 @Test public void disabledSystemAnimationsSettleOutlineImmediately() throws Exception {
  View v=attachedRow();row(v,false,false,false);int baseline=android.animation.ValueAnimator.getCurrentAnimationsCount();
  float scale=android.animation.ValueAnimator.getDurationScale();
  try {
   android.animation.ValueAnimator.setDurationScale(0);
   assertFalse(android.animation.ValueAnimator.areAnimatorsEnabled());
   row(v,true,false,false);
   assertEquals(baseline,android.animation.ValueAnimator.getCurrentAnimationsCount());
   assertEquals(64,outline(v,new int[]{}).paint.getAlpha());
  } finally {android.animation.ValueAnimator.setDurationScale(scale);}
 }
}
'''.replace('TITLE_METHOD','static void updateTitle(int titleViewId, PropertyModel model, ViewGroup view) '+method_body(binder,r'private static void updateTitle\('))
java=a.work/'SidebarAppearanceProbe.java';java.write_text(test)
metrics=a.work/'ArchiumWindowMetrics.java';metrics.write_text('package org.chromium.chrome.browser.desktop_policy; public class ArchiumWindowMetrics {public static int currentWidthDp(android.content.Context c){return c.getResources().getConfiguration().screenWidthDp;}}')
import importlib.util
spec=importlib.util.spec_from_file_location('window_core',ROOT/'scripts/fetch-window-core.py')
window=importlib.util.module_from_spec(spec);spec.loader.exec_module(window)
cp=a.classpath_file.read_text().strip()+':'+str(window.ensure_jar())
sources=[java,metrics,*ROOT.glob('chromium/**/ArcDesktopAppearance.java'),*ROOT.glob('chromium/**/ArcDesktopPolicy.java'),*ROOT.glob('chromium/**/ArchiumWindowClass.java')]
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,sources)],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Xmx512m','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'SidebarAppearanceProbe'])
print('SCOPE=real_Android_views_drawables_delivered_title_method_and_appearance_helpers_NOT_APK_GPU')
raise SystemExit(r.returncode)
