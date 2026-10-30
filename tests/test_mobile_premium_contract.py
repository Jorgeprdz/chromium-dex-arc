"""Exact ownership/color source contracts. No Samsung visual acceptance is inferred."""
import hashlib, json, pathlib, subprocess, unittest
from arc_toolbar_probe import method_body
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='677c73fcebd14d37b52ec68e2dffba627282c0bf'
class MobilePremiumContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.baseline=json.loads((ROOT/'tests/pinned/mobile-premium-baseline.json').read_text())
  if cls.baseline['schema']!=1 or cls.baseline['source_commit']!=BASE or cls.baseline['algorithm']!='sha256':
   raise AssertionError('Unexpected immutable mobile baseline')
 def assert_original_method(self,path,pattern):
  actual=method_body((ROOT/path).read_text(),pattern).encode()
  self.assertEqual(self.baseline['methods'][path][pattern],hashlib.sha256(actual).hexdigest())
 def test_approved_pull_and_native_owners_are_byte_identical(self):
  paths=['chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhonePullReveal.java',
   '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/SwipeRefreshHandler.java']
  # Desktop camera menu labels/choices are an approved UI-only exception.
  # The approved phone capsule inset is also presentation-only. Native phone
  # input/layout methods and capture/reveal owners remain protected below.
  for path in paths:
   with self.subTest(path=path):self.assertEqual(self.baseline['files'][path],hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
 def test_native_phone_input_and_layout_survive_the_capsule_presentation_change(self):
  path='.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarPhone.java'
  # Pinned from 0f5de40 before the authorized background-only height adjustment.
  expected={
   'public boolean onInterceptTouchEvent\\(': '7b6485cb4ff6d86292cb4bdaf2d0543a156c0a642ad95ff187489fb7e94a1db3',
   'public boolean onTouchEvent\\(': '357dcebeba62591b215dbea4a9b0b5f04a3b5a330481e764cd8ddecdf7ca9737',
   'protected void onMeasure\\(': '5d48d56e6041929416b13e119dbca43c0e243b819749d0d3773460e05e297f96',
   'private boolean updateUnfocusedLocationBarLayoutParams\\(': '157d85e7b2e3e715a0d9bf063083aeda85a6b8fa9154a41c7577715cbbc2c699',
   'private int getFocusedLocationBarWidth\\(': '5ac588192e845a3f0fe1121a6ac11ddcbf5935b57b60598f497ef28d35b1c04a',
   'private int getFocusedLocationBarLeftMargin\\(': '8aba1b9157ff7508c52db391be2380d8e167fd9d036eebcca7e9c9436e630888',
   'private void updateLocationBarLayoutForExpansionAnimation\\(': '120d451c08b5ec0f8385b669dffb73f3332f1f4bb69763f0f5ae6e79535b888d',
   'public void onUrlFocusChange\\(': '2695bba4301a3b5cb196ea8a512dbd8d40db3be99d595df9e498c0dc46e26a6b',
   'private void updateLayoutParamsForMultiline\\(': '8b6fbfa9f954c6166c816ca9bdf6e65dcfb5c0dc3fd17d99055f102042d7512d',
   'private int calculateOnFocusHeightIncrease\\(': '8e6c7af7279485f3e2de4327a37c8b0bf6cba95b2f13fb64e4e241b853f8f55b',
  }
  source=(ROOT/path).read_text()
  for pattern,digest in expected.items():
   with self.subTest(method=pattern):
    self.assertEqual(digest,hashlib.sha256(method_body(source,pattern).encode()).hexdigest())
 def test_color_resolver_and_reveal_binding_are_unchanged(self):
  path='.source-modified/chrome/browser/ui/android/theme/java/src/org/chromium/chrome/browser/theme/ToolbarThemeColorProvider.java'
  pattern=r'public @ColorInt int getArcPhonePageColor\('
  self.assert_original_method(path,pattern)
  path='.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java'
  for pattern in [r'private void bindArcPhonePullReveal\(',r'private void updateArcPhoneRevealIdentity\(',r'private void bindArcPhoneGestures\(',r'private void updateArcPhoneTopInset\(']:
   self.assert_original_method(path,pattern)
 def test_status_visibility_and_capture_schedule_are_unchanged(self):
  path='chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneStatusFade.java'
  pattern=r'public void update\(boolean compact, boolean nativeFullscreen\)'
  self.assert_original_method(path,pattern)
  path='chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneGlass.java'
  for pattern in [r'public void setInMotion\(',r'void sampleNow\(',r'private void schedule\(',r'public static Capture contentSource\(']:
   self.assert_original_method(path,pattern)
 def test_external_homepage_no_longer_implies_archium_home(self):
  path='.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java'
  body=method_body((ROOT/path).read_text(),r'public boolean homePage\(')
  # Execute the production predicate on a JVM with only native URL/tab boundaries adapted.
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);source='''public class HomeProbe {
String current="https://google.com/";static class Tab{String url;Tab(String u){url=u;}String getUrl(){return url;}}
Tab getActivityTab(){return current==null?null:new Tab(current);} static class UrlUtilities{static boolean isNtpUrl(String s){return s.equals("chrome://newtab/");}}
boolean homePage() BODY
public static void main(String[] args){HomeProbe p=new HomeProbe();if(p.homePage())throw new AssertionError("Google is not Archium home");p.current="chrome://newtab/";if(!p.homePage())throw new AssertionError("Native home lost");p.current=null;if(p.homePage())throw new AssertionError("Null tab selected");}}
'''.replace('BODY',body)
   (p/'HomeProbe.java').write_text(source)
   subprocess.run(['javac',str(p/'HomeProbe.java')],check=True,capture_output=True)
   subprocess.run(['java','-ea','-cp',str(p),'HomeProbe'],check=True,capture_output=True)

 def test_favorite_state_does_not_query_a_destroyed_tab(self):
  path='.source-modified/chrome/android/java/src/org/chromium/chrome/browser/ChromeTabbedActivity.java'
  body=method_body((ROOT/path).read_text(),r'public boolean favorite\(')
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);source='''public class FavoriteProbe {
static class Tab{boolean destroyed;boolean isDestroyed(){return destroyed;}}
static class BookmarkModel{int queries;boolean isBookmarkModelLoaded(){return true;}Object getUserBookmarkIdForTab(Tab t){queries++;return new Object();}}
Tab tab=new Tab();Tab getActivityTab(){return tab;}BookmarkModel model=new BookmarkModel();java.util.function.Supplier<BookmarkModel> mBookmarkModelSupplier=()->model;
boolean favorite() BODY
public static void main(String[] args){FavoriteProbe p=new FavoriteProbe();if(!p.favorite())throw new AssertionError("Native favorite state lost");p.tab.destroyed=true;if(p.favorite()||p.model.queries!=1)throw new AssertionError("Destroyed tab queried");p.tab=null;if(p.favorite())throw new AssertionError("Null tab queried");}}
'''.replace('BODY',body)
   (p/'FavoriteProbe.java').write_text(source)
   subprocess.run(['javac',str(p/'FavoriteProbe.java')],check=True,capture_output=True)
   result=subprocess.run(['java','-ea','-cp',str(p),'FavoriteProbe'],capture_output=True,text=True)
   self.assertEqual(0,result.returncode,result.stderr)
