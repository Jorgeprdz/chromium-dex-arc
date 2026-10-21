#!/usr/bin/env python3
"""Delivered command bar and touch routing on Android Views; native focus callback is adapted.

Baseline fallback models the existing empty Ctrl+T entry and unmodified touch dispatcher.
This is not installed-APK autocomplete, WindowManager, GPU or device validation.
"""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
revisions=p.add_mutually_exclusive_group()
revisions.add_argument('--baseline',action='store_true',help='Run against immutable pre-change commit 5b8694a')
revisions.add_argument('--source-ref',help='Compare current regression cases against an explicit Git revision')
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
baseline='5b8694a07f328128e1267262780e6996b0ba4509'
revision=a.source_ref or (baseline if a.baseline else None)
def delivered(path):
 if revision:
  return subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT,text=True)
 return (ROOT/path).read_text()
source=delivered('.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarLayout.java')
if 'setArcAddressPopupOpener(' in source:
 start=source.index('    private @Nullable BooleanSupplier mArcAddressPopupOpener;')
 end=source.index('    private @Nullable Rect mArcCommandResults;',start)
 touch=source[start:end]
else:
 # Existing LocationBar has no popup opener; keep native dispatch through the superclass.
 touch='public void setArcAddressPopupOpener(java.util.function.BooleanSupplier opener) {}'
fixture=r'''
package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import android.app.Activity;
import android.graphics.Rect;
import android.view.*;
import android.widget.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BooleanSupplier;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.arc.*;
@interface Nullable {}
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class AddressPopupProbe {
 org.robolectric.android.controller.ActivityController<Activity> c;
 Activity activity;
 @Before public void setup(){c=Robolectric.buildActivity(Activity.class).setup();activity=c.get();}
 @After public void close(){c.pause().stop().destroy();}
 static class NativeDispatchFrame extends FrameLayout {
  int nativeDispatches;
  NativeDispatchFrame(Activity a){super(a);}
  @Override public boolean dispatchTouchEvent(MotionEvent e){nativeDispatches++;return super.dispatchTouchEvent(e);}
 }
 static class Location extends NativeDispatchFrame {
  final EditText mUrlBar; final View mLocationBarStatusView,mFocusThief;
  Location(Activity a){super(a);mUrlBar=new EditText(a);mLocationBarStatusView=new View(a);mFocusThief=new View(a);
   addView(mUrlBar);addView(mLocationBarStatusView);addView(mFocusThief);mFocusThief.setVisibility(View.GONE);}
  TOUCH
 }
 Location location(){Location v=new Location(activity);activity.setContentView(v);Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();v.layout(0,0,216,48);
  v.mUrlBar.layout(48,0,168,48);v.mLocationBarStatusView.layout(0,0,48,48);return v;}
 boolean mouseStream;
 void touch(Location v,int action,int buttons,float x,float y){
  if(action==MotionEvent.ACTION_DOWN)mouseStream=buttons!=0;
  MotionEvent.PointerProperties pp=new MotionEvent.PointerProperties();pp.id=0;pp.toolType=mouseStream?MotionEvent.TOOL_TYPE_MOUSE:MotionEvent.TOOL_TYPE_FINGER;
  MotionEvent.PointerCoords pc=new MotionEvent.PointerCoords();pc.x=x;pc.y=y;pc.pressure=1;pc.size=1;
  MotionEvent e=MotionEvent.obtain(1,2,action,1,new MotionEvent.PointerProperties[]{pp},new MotionEvent.PointerCoords[]{pc},0,buttons,1,1,0,0,mouseStream?android.view.InputDevice.SOURCE_MOUSE:android.view.InputDevice.SOURCE_TOUCHSCREEN,0);
  try{v.dispatchTouchEvent(e);Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();}finally{e.recycle();}
 }
 @Test public void primaryClickRoutesToPopupExactlyOnceAndConsumesRelease(){
  Location v=location();AtomicInteger calls=new AtomicInteger();v.setArcAddressPopupOpener(()->{calls.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,0,100,24);touch(v,MotionEvent.ACTION_UP,0,100,24);assertEquals(1,calls.get());}
 @Test public void backgroundClickUsesSameAddressEntry(){
  Location v=location();AtomicInteger calls=new AtomicInteger();v.setArcAddressPopupOpener(()->{calls.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,MotionEvent.BUTTON_PRIMARY,210,24);assertEquals(1,calls.get());}
 @Test public void siteInformationAndOtherNativeButtonsKeepTheirClicks(){
  Location v=location();AtomicInteger opens=new AtomicInteger(),status=new AtomicInteger(),other=new AtomicInteger();
  v.mLocationBarStatusView.setOnClickListener(x->status.incrementAndGet());View button=new View(activity);button.setOnClickListener(x->other.incrementAndGet());v.addView(button);button.layout(168,0,200,48);
  v.setArcAddressPopupOpener(()->{opens.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,0,24,24);touch(v,MotionEvent.ACTION_UP,0,24,24);
  touch(v,MotionEvent.ACTION_DOWN,0,184,24);touch(v,MotionEvent.ACTION_UP,0,184,24);
  assertEquals(0,opens.get());assertEquals(1,status.get());assertEquals(1,other.get());}
 @Test public void nestedNativeActionSegmentKeepsItsButton(){
  Location v=location();AtomicInteger opens=new AtomicInteger(),clicks=new AtomicInteger();
  FrameLayout segment=new FrameLayout(activity);View button=new View(activity);button.setOnClickListener(x->clicks.incrementAndGet());
  segment.addView(button);v.addView(segment);segment.layout(168,0,200,48);button.layout(0,0,32,48);
  v.setArcAddressPopupOpener(()->{opens.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,0,184,24);touch(v,MotionEvent.ACTION_UP,0,184,24);
  assertEquals(0,opens.get());assertEquals(1,clicks.get());}
 @Test public void secondaryClickDoesNotOpenOrReplaceNativeContextMenu(){
  Location v=location();AtomicInteger opens=new AtomicInteger();v.setArcAddressPopupOpener(()->{opens.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,MotionEvent.BUTTON_SECONDARY,100,24);assertEquals(0,opens.get());}
 @Test public void popupAndMobileFallbackKeepNativeEditorInput(){
  Location v=location();AtomicInteger nativeEvents=new AtomicInteger();v.mUrlBar.setOnTouchListener((x,e)->{nativeEvents.incrementAndGet();return true;});
  v.setArcAddressPopupOpener(()->false);touch(v,MotionEvent.ACTION_DOWN,0,100,24);touch(v,MotionEvent.ACTION_UP,0,100,24);assertEquals(2,nativeEvents.get());}
 @Test public void freshDownAfterLostReleaseCanOpenAddressAgain(){
  for(int buttons:new int[]{0,MotionEvent.BUTTON_PRIMARY}){
   Location v=location();AtomicInteger opens=new AtomicInteger();
   v.setArcAddressPopupOpener(()->{opens.incrementAndGet();return true;});
   touch(v,MotionEvent.ACTION_DOWN,buttons,100,24);
   // Reparenting the editor can end its old touch target without another release here.
   touch(v,MotionEvent.ACTION_DOWN,buttons,100,24);
   touch(v,MotionEvent.ACTION_UP,0,100,24);
   assertEquals("A fresh gesture must not be consumed by the old stream",2,opens.get());
  }
 }
 @Test public void popupEditorReceivesFirstNewGestureAfterLostRelease(){
  Location v=location();AtomicInteger nativeEvents=new AtomicInteger();
  v.setArcAddressPopupOpener(()->true);touch(v,MotionEvent.ACTION_DOWN,0,100,24);
  // The same LocationBar is now in the popup, whose opener correctly returns false.
  v.setArcAddressPopupOpener(()->false);
  v.mUrlBar.setOnTouchListener((x,e)->{nativeEvents.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,0,100,24);touch(v,MotionEvent.ACTION_UP,0,100,24);
  assertEquals(2,nativeEvents.get());
 }
 @Test public void interruptedEntryCannotSwallowNextSecondaryClick(){
  Location v=location();AtomicInteger nativeEvents=new AtomicInteger(),opens=new AtomicInteger();
  v.setArcAddressPopupOpener(()->{opens.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,MotionEvent.BUTTON_PRIMARY,100,24);
  v.mUrlBar.setOnTouchListener((x,e)->{nativeEvents.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,MotionEvent.BUTTON_SECONDARY,100,24);
  touch(v,MotionEvent.ACTION_UP,0,100,24);
  // Android may handle a real secondary mouse click before its editor touch listener.
  // Assert the native dispatcher receives the stream rather than prescribing child handling.
  assertEquals(1,opens.get());assertEquals(2,v.nativeDispatches);
 }
 @Test public void teardownDropsOpenerAndCancelledGestureCanStartAgain(){
  Location v=location();AtomicInteger opens=new AtomicInteger();v.setArcAddressPopupOpener(()->{opens.incrementAndGet();return true;});
  touch(v,MotionEvent.ACTION_DOWN,0,100,24);touch(v,MotionEvent.ACTION_CANCEL,0,100,24);
  touch(v,MotionEvent.ACTION_DOWN,0,100,24);assertEquals(2,opens.get());v.setArcAddressPopupOpener(null);
  touch(v,MotionEvent.ACTION_UP,0,100,24);touch(v,MotionEvent.ACTION_DOWN,0,100,24);assertEquals(2,opens.get());}
 static class Session {
  final FrameLayout root,original,holder;final EditText editor;final ArcOmniboxPlacement placement;final ArcCommandBar bar;
  final AtomicInteger blanks=new AtomicInteger(),addresses=new AtomicInteger(),ends=new AtomicInteger();
  final String url="https://example.test/path?a=1#section";
  Session(Activity a){root=new FrameLayout(a);original=new FrameLayout(a);holder=new FrameLayout(a);editor=new EditText(a);
   root.addView(original);original.addView(holder);holder.addView(editor);a.setContentView(root);root.layout(0,0,1000,800);holder.layout(0,0,216,48);
   placement=new ArcOmniboxPlacement(holder);bar=new ArcCommandBar(a,root,holder,editor,placement,()->new Rect(216,0,1000,800),
    ()->{blanks.incrementAndGet();editor.requestFocus();editor.setText("");},()->{ends.incrementAndGet();editor.clearFocus();},placement::restore,x->List.of(),"URL","Actions");}
  void openAddress() throws Exception {
   Runnable nativeFocus=()->{addresses.incrementAndGet();editor.requestFocus();editor.setText(url);editor.selectAll();};
   try{ArcCommandBar.class.getMethod("openAddress",Runnable.class).invoke(bar,nativeFocus);}
   catch(NoSuchMethodException baseline){bar.open(false);}
  }
 }
 @Test public void addressEntryUsesNativeFullUrlAndSelectionInsteadOfBlankInput() throws Exception {
  Session s=new Session(activity);s.openAddress();s.bar.finishAnimationForTesting();
  assertEquals(1,s.addresses.get());assertEquals(0,s.blanks.get());assertEquals(s.url,s.editor.getText().toString());
  assertEquals(0,s.editor.getSelectionStart());assertEquals(s.url.length(),s.editor.getSelectionEnd());
  s.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_ESCAPE));s.bar.finishAnimationForTesting();
  assertFalse(s.bar.isShowing());assertSame(s.original,s.holder.getParent());assertEquals(1,s.ends.get());s.bar.destroy();}
 @Test public void existingCtrlTStaysBlankAndAddressReentryDoesNotClobberEdits() throws Exception {
  Session s=new Session(activity);s.openAddress();s.bar.finishAnimationForTesting();s.editor.setText("edited");s.openAddress();
  assertEquals("edited",s.editor.getText().toString());assertEquals(1,s.addresses.get());s.bar.close(false,null);
  s.bar.open(false);s.bar.finishAnimationForTesting();assertEquals("",s.editor.getText().toString());assertEquals(1,s.blanks.get());s.bar.destroy();}
}
'''.replace('  TOUCH\n','  '+touch+'\n')
f=a.work/'AddressPopupProbe.java';f.write_text(fixture)
cp=a.classpath_file.read_text().strip();classes=a.work/'classes';classes.mkdir(exist_ok=True)
arc=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
command_source=arc/'ArcCommandBar.java'
if revision:
 command_source=a.work/'ArcCommandBar.java'
 command_source.write_text(delivered('chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCommandBar.java'))
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),str(f),str(command_source),str(arc/'ArcOmniboxPlacement.java')],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','org.chromium.chrome.browser.arc.AddressPopupProbe'])
print('SCOPE=DELIVERED_COMMAND_BAR_TOUCH_METHODS_REAL_VIEWS_NATIVE_FOCUS_CALLBACK_ADAPTER_NOT_APK',flush=True)
sys.exit(r.returncode)
