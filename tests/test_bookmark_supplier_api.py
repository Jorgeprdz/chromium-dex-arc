"""Compile the actual bookmark registration against declarations from pinned Chromium.
Only supplier declarations are extracted; coordinator dependencies are boundaries.
This is an API gate, not a full TabbedRootUiCoordinator or native build.
"""
from pathlib import Path
import hashlib, re, shutil, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
PIN=ROOT/'tests/pinned/MonotonicObservableSupplier.java'
SOURCE=ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java'
class BookmarkSupplierApiTest(unittest.TestCase):
 def test_native_bookmark_registration_compiles_against_pinned_declarations(self):
  pinned=PIN.read_text()
  self.assertEqual('02f233bae730761b161960cba69a9f0935ad35907db56272b37835df29d48b00',hashlib.sha256(PIN.read_bytes()).hexdigest())
  declarations=re.findall(r'default @Nullable T (addSyncObserver\w*)\(Callback<T> obs\)',pinned)
  self.assertTrue(declarations)
  source=SOURCE.read_text();start=source.index('mTabBookmarkerSupplier.',source.index('mArcDesktopCoordinator.configureCommands('));end=source.index('mToolbarManager.setVerticalTabsAutoHiddenSupplier(',start)
  registration=source[start:end]
  api='interface MonotonicObservableSupplier<T>{'+''.join('T '+name+'(Callback<T> obs);' for name in declarations)+'}'
  probe='interface Callback<T>{void onResult(T v);}'+api+"""
class Probe {
 static class TabBookmarker {}
 static class Desktop {void configureNativeBookmarks(TabBookmarker b){}}
 static class Controller {<T> Callback<T> makeCancelable(Callback<T> cb){return cb;}}
 MonotonicObservableSupplier<TabBookmarker> mTabBookmarkerSupplier;
 Desktop mArcDesktopCoordinator;Controller mCallbackController;
 void register(){REGISTRATION}
}
""".replace('REGISTRATION',registration)
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'Probe.java';path.write_text(probe)
   result=subprocess.run([shutil.which('javac'),str(path)],capture_output=True,text=True)
   self.assertEqual(0,result.returncode,result.stderr)
  self.assertIn('mCallbackController.makeCancelable(',registration)
