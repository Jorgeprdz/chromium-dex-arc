"""Execute delivered native refresh routing; JNI/widget delivery is an explicit boundary."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method, run_probe
ROOT=Path(__file__).resolve().parents[1]
class PullRevealIntegrationTests(unittest.TestCase):
 def test_short_pull_never_reaches_refresh_but_long_pull_uses_existing_native_handler(self):
  src=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/SwipeRefreshHandler.java').read_text()
  bodies='\n'.join(method(src,s) for s in ['public boolean start(', 'public void pull(', 'public void release(', 'public void reset()'])
  code='''import org.chromium.chrome.browser.arc.ArcPhonePullReveal;
public class RefreshProbe {
@interface OverscrollAction {int NONE=0,PULL_TO_REFRESH=1,HISTORY_NAVIGATION=2,PULL_FROM_BOTTOM_EDGE=3;}
@interface OverscrollActivationStatus {int ALLOW_ACTIVATION=1,FORCE_ACTIVATION=2;}
@interface BackGestureEventSwipeEdge {}
static class TraceEvent {static void begin(String s){}static void end(String s){}}
static void assumeNonNull(Object o){if(o==null)throw new AssertionError();}
static class Tab {Object getContext(){return this;}}Tab mTab=new Tab();
static class Widget {boolean accepted=true,allowed;int starts,pulls,attached;float distance;
boolean start(){starts++;return accepted;}void pull(float d){pulls++;distance+=d;}void release(boolean allow){allowed=allow;}void reset(){distance=0;}}
Widget mSwipeRefreshLayout=new Widget();void initSwipeRefreshLayout(Object c){}void attachSwipeRefreshLayoutIfNecessary(){mSwipeRefreshLayout.attached++;}
static class Navigation {void startGesture(){}boolean triggerUi(int e){return true;}void pull(float x,float y){}void release(int s){}void reset(){}}
Navigation mNavigationCoordinator;static class Bottom {boolean start(){return true;}void pull(float d){}void release(boolean b){}void reset(){}}Bottom mBottomOverscrollHandler;
void cancelStopRefreshingRunnable(){}int mSwipeType;boolean mArcPhonePullActive;
ArcPhonePullReveal mArcPhonePullReveal;
'''+bodies+'''
static void check(boolean v){if(!v)throw new AssertionError("phone reveal must consume short pull before native refresh");}
public static void main(String[] a){RefreshProbe p=new RefreshProbe();
p.mArcPhonePullReveal=new ArcPhonePullReveal();check(p.start(1,0));p.pull(0,80);p.release(1);
check(p.mArcPhonePullReveal.starts==1&&p.mArcPhonePullReveal.releases==1);
check(p.mSwipeRefreshLayout.starts==1&&p.mSwipeRefreshLayout.pulls==0&&!p.mSwipeRefreshLayout.allowed);
check(p.mSwipeRefreshLayout.attached==0);
p.mArcPhonePullReveal.excess=28;p.mArcPhonePullReveal.refresh=true;
check(p.start(1,0));p.pull(0,140);p.release(1);
check(p.mSwipeRefreshLayout.distance==28&&p.mSwipeRefreshLayout.allowed&&p.mSwipeRefreshLayout.attached>0);
p.start(1,0);p.pull(0,140);p.release(0);check(!p.mSwipeRefreshLayout.allowed);
p.reset();check(p.mArcPhonePullReveal.resets==1&&!p.mArcPhonePullActive);
RefreshProbe nativePath=new RefreshProbe();nativePath.start(1,0);nativePath.pull(0,80);nativePath.release(1);
check(nativePath.mSwipeRefreshLayout.distance==80&&nativePath.mSwipeRefreshLayout.allowed);
RefreshProbe rejected=new RefreshProbe();rejected.mArcPhonePullReveal=new ArcPhonePullReveal();rejected.mSwipeRefreshLayout.accepted=false;
check(!rejected.start(1,0));check(rejected.mArcPhonePullReveal.starts==0);
}}
'''
  reveal='''package org.chromium.chrome.browser.arc;public class ArcPhonePullReveal {
public int starts,releases,resets;public float excess;public boolean refresh;
public boolean start(){starts++;return true;}public float pull(float d){return excess;}
public boolean release(boolean allow){releases++;return refresh&&allow;}public void reset(boolean animate){resets++;}}
'''
  run_probe(self,{'RefreshProbe.java':code,'org/chromium/chrome/browser/arc/ArcPhonePullReveal.java':reveal},'RefreshProbe')

 def test_native_scroll_signals_dismiss_gap_and_preserve_compaction_direction(self):
  src=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  listener=src[src.index('private final GestureStateListener mArcPhoneGestureListener'):]
  body=method(listener,'public void onScrollStarted(')+method(listener,'public void onVerticalScrollDirectionChanged(')
  code='''public class ScrollProbe {
static class Reveal {int scrolls;void onPageScroll(){scrolls++;}}Reveal mArcPhonePullReveal=new Reveal();
static class Focus {boolean focused;boolean get(){return focused;}}Focus mFormFieldFocusedSupplier=new Focus();
boolean compact;void setArcPhoneCompact(boolean value){compact=value;}
'''+body+'''
public static void main(String[] a){ScrollProbe p=new ScrollProbe();
p.onScrollStarted(0,200,true);if(p.mArcPhonePullReveal.scrolls!=1||p.compact)throw new AssertionError("ordinary scroll must dismiss revealed gap");
p.onVerticalScrollDirectionChanged(false,1);if(p.mArcPhonePullReveal.scrolls!=2||!p.compact)throw new AssertionError("direction policy changed");
p.mFormFieldFocusedSupplier.focused=true;p.onScrollStarted(0,200,true);
if(p.mArcPhonePullReveal.scrolls!=3||!p.compact)throw new AssertionError("form controls must remain clear");
p.mArcPhonePullReveal=null;p.onScrollStarted(0,200,true);}}
'''
  run_probe(self,{'ScrollProbe.java':code},'ScrollProbe')

 def test_context_identity_comes_from_current_native_tab_and_clears_on_unbind(self):
  src=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  body=method(src,'private void updateArcPhoneRevealIdentity(')
  code='''public class IdentityProbe {
@interface Nullable {} static class Url {String getSpec(){return "https://www.github.com/Jorgeprdz/chromium-dex-arc";}}
static class Tab {Url getUrl(){return new Url();}String getTitle(){return "chromium-dex-arc";}}
static class TabFavicon {static final Object ICON=new Object();static Object getBitmap(Tab tab){return ICON;}}
static class Reveal {Object icon;String site,title;void setIdentity(Object i,String s,String t){icon=i;site=s;title=t;}}
Reveal mArcPhonePullReveal=new Reveal();
'''+body+'''
public static void main(String[] args){IdentityProbe p=new IdentityProbe();p.updateArcPhoneRevealIdentity(new Tab());
if(p.mArcPhonePullReveal.icon!=TabFavicon.ICON||!p.mArcPhonePullReveal.site.equals("github.com")||!p.mArcPhonePullReveal.title.equals("chromium-dex-arc"))throw new AssertionError("native tab identity");
p.updateArcPhoneRevealIdentity(null);if(p.mArcPhonePullReveal.icon!=null||!p.mArcPhonePullReveal.site.isEmpty()||!p.mArcPhonePullReveal.title.isEmpty())throw new AssertionError("old tab leaked");
p.mArcPhonePullReveal=null;p.updateArcPhoneRevealIdentity(new Tab());}}
'''
  # URI parsing is the explicit Android boundary; the delivered ToolbarManager body runs verbatim.
  uri='package android.net;public class Uri {java.net.URI value;Uri(String s){value=java.net.URI.create(s);}public static Uri parse(String s){return new Uri(s);}public String getHost(){return value.getHost();}}'
  run_probe(self,{'IdentityProbe.java':code,'android/net/Uri.java':uri},'IdentityProbe')

 def test_identity_action_restores_controls_and_reuses_native_address_focus(self):
  src=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  action=method(src,'mArcPhonePullReveal.setOpenAddressAction(')
  code='''public class AddressActionProbe {
static class Reveal {Runnable action;void setOpenAddressAction(Runnable r){action=r;}}
static class OmniboxFocusReason {static final int MENU_OR_KEYBOARD_ACTION=7;}
Reveal mArcPhonePullReveal=new Reveal();boolean compact=true;int reason=-1;
void setArcPhoneCompact(boolean c){compact=c;}void focusAndSelectAllUrlBarText(int value){reason=value;}
void bind(){'''+action+''');}
public static void main(String[] args){var p=new AddressActionProbe();p.bind();p.mArcPhonePullReveal.action.run();if(p.compact||p.reason!=7)throw new AssertionError("must restore controls and focus the same native editor");}}
'''
  run_probe(self,{'AddressActionProbe.java':code},'AddressActionProbe')
