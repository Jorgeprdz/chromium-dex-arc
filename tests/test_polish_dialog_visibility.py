"""Execute delivered host-visibility transition policy; not Android compositor acceptance."""
from pathlib import Path
import subprocess, tempfile, unittest
from arc_toolbar_probe import method_body
ROOT=Path(__file__).resolve().parents[1]
class BookmarkHostVisibilityTests(unittest.TestCase):
 def test_runtime_desktop_scope_and_transitions(self):
  for name in ('BookmarkEditActivity','BookmarkFolderPickerActivity'):
   source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/app/bookmarks'/(name+'.java')).read_text()
   body=method_body(source,r'private void updateArcHostVisibility\(')
   with self.subTest(activity=name),tempfile.TemporaryDirectory() as d:
    p=Path(d)
    files={
     'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT=30;}public static class VERSION_CODES{public static final int R=30;}}',
     'org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopAppearance.java':'package org.chromium.chrome.browser.ui.vertical_tabs;public class ArcDesktopAppearance{public static boolean desktop;public static boolean isDesktopWindow(Object o){return desktop;}}',
     'DialogProbe.java':'''import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
public class DialogProbe {
 boolean mArcKeepsHostVisible; int calls; boolean latest; boolean succeeds=true;
 boolean setTranslucent(boolean b){calls++;latest=b;return succeeds;}
 void updateArcHostVisibility() BODY
 public static void main(String[] args){
  DialogProbe p=new DialogProbe();p.updateArcHostVisibility();if(p.calls!=0)throw new AssertionError("mobile changed");
  ArcDesktopAppearance.desktop=true;p.updateArcHostVisibility();if(p.calls!=1||!p.latest)throw new AssertionError("desktop not live");
  ArcDesktopAppearance.desktop=false;p.updateArcHostVisibility();if(p.calls!=2||p.latest)throw new AssertionError("mobile transition not restored");
  p.updateArcHostVisibility();if(p.calls!=2)throw new AssertionError("mobile repeatedly changed");
  android.os.Build.VERSION.SDK_INT=29;ArcDesktopAppearance.desktop=true;p.updateArcHostVisibility();if(p.calls!=2)throw new AssertionError("unsupported API called");
 }
}'''.replace('BODY',body)}
    for f,text in files.items():
     dest=p/f;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    result=subprocess.run(['javac','-d',str(p),*[str(p/f) for f in files]],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
    result=subprocess.run(['java','-ea','-cp',str(p),'DialogProbe'],capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
