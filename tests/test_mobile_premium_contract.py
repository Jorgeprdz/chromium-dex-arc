"""Exact ownership/color source contracts. No Samsung visual acceptance is inferred."""
import pathlib, subprocess, unittest
from arc_toolbar_probe import method_body
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='677c73fcebd14d37b52ec68e2dffba627282c0bf'
class MobilePremiumContracts(unittest.TestCase):
 def original(self,path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
 def test_approved_pull_and_native_owners_are_byte_identical(self):
  paths=['chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhonePullReveal.java',
   '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/SwipeRefreshHandler.java',
   '.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarPhone.java',
   'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCameraControls.java']
  for path in paths:
   with self.subTest(path=path):self.assertEqual(self.original(path),(ROOT/path).read_bytes())
 def test_color_resolver_and_reveal_binding_are_unchanged(self):
  path='.source-modified/chrome/browser/ui/android/theme/java/src/org/chromium/chrome/browser/theme/ToolbarThemeColorProvider.java'
  pattern=r'public @ColorInt int getArcPhonePageColor\('
  self.assertEqual(method_body(self.original(path).decode(),pattern),method_body((ROOT/path).read_text(),pattern))
  path='.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java'
  for pattern in [r'private void bindArcPhonePullReveal\(',r'private void updateArcPhoneRevealIdentity\(',r'private void bindArcPhoneGestures\(',r'private void updateArcPhoneTopInset\(']:
   self.assertEqual(method_body(self.original(path).decode(),pattern),method_body((ROOT/path).read_text(),pattern))
 def test_status_visibility_and_capture_schedule_are_unchanged(self):
  path='chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneStatusFade.java'
  pattern=r'public void update\(boolean compact, boolean nativeFullscreen\)'
  self.assertEqual(method_body(self.original(path).decode(),pattern),method_body((ROOT/path).read_text(),pattern))
  path='chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcPhoneGlass.java'
  for pattern in [r'public void setInMotion\(',r'void sampleNow\(',r'private void schedule\(',r'public static Capture contentSource\(']:
   self.assertEqual(method_body(self.original(path).decode(),pattern),method_body((ROOT/path).read_text(),pattern))
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
