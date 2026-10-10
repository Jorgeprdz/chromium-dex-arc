"""Isolated JVM regression for display-less Context; NOT a Robolectric substitute."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopAppearance.java'
STUBS = {
'android/content/Context.java': """package android.content;
import android.content.pm.PackageManager; import android.content.res.Resources;
public class Context {
 public static final int MODE_PRIVATE=0;
 public final Resources res=new Resources();
 public final PackageManager pm=new PackageManager();
 public final SharedPreferences prefs=new SharedPreferences();
 public Resources getResources(){return res;}
 public PackageManager getPackageManager(){return pm;}
 public Context getApplicationContext(){return this;}
 public SharedPreferences getSharedPreferences(String name,int flags){return prefs;}
}""",
'android/content/SharedPreferences.java': """package android.content;
public class SharedPreferences {
 public int mode;
 public int getInt(String key,int fallback){return key.equals("ui_mode")?mode:fallback;}
 public Editor edit(){return new Editor(this);}
 public static class Editor {
  private SharedPreferences p;
  public Editor(SharedPreferences p){this.p=p;}
  public Editor putInt(String key,int value){if(key.equals("ui_mode"))p.mode=value;return this;}
  public void apply(){}
 }
}""",
'android/content/pm/PackageManager.java': """package android.content.pm;
public class PackageManager {
 public static final String FEATURE_PC="android.hardware.type.pc";
 public boolean pc;
 public boolean hasSystemFeature(String name){return pc;}
}""",
'android/content/res/Resources.java': """package android.content.res;
public class Resources {
 public final Configuration config=new Configuration();
 public Configuration getConfiguration(){return config;}
}""",
'android/content/res/Configuration.java': """package android.content.res;
public class Configuration {
 public static final int UI_MODE_TYPE_MASK=15,UI_MODE_TYPE_DESK=2;
 public static final int UI_MODE_NIGHT_MASK=48,UI_MODE_NIGHT_YES=32;
 public int screenWidthDp,smallestScreenWidthDp,uiMode;
}""",
'android/view/Display.java': """package android.view;
public class Display {
 public static final int DEFAULT_DISPLAY=0;
 private int id;
 public Display(int id){this.id=id;}
 public int getDisplayId(){return id;}
}""",
'android/view/View.java': """package android.view;
public class View {
 public Display display;
 public boolean attached;
 public boolean isAttachedToWindow(){return attached;}
 public Display getDisplay(){
  if(!attached)throw new UnsupportedOperationException("detached view display");
  return display;
 }
}""",
'android/view/Window.java': """package android.view;
public class Window {
 public final View decor=new View();
 public View getDecorView(){return decor;}
}""",
'android/app/Activity.java': """package android.app;
import android.content.Context;import android.view.Window;
public class Activity extends Context {
 public Window window=new Window();
 public boolean multiWindow;
 public Window getWindow(){return window;}
 public boolean isInMultiWindowMode(){return multiWindow;}
 public android.view.Display getDisplay(){throw new UnsupportedOperationException("detached context");}
}""",
'org/chromium/chrome/browser/desktop_policy/ArchiumWindowMetrics.java': """package org.chromium.chrome.browser.desktop_policy;
import android.content.Context;import android.app.Activity;
public class ArchiumWindowMetrics {
 public static int currentWidthDp(Context c){
  return c instanceof Activity ? c.getResources().getConfiguration().screenWidthDp : 0;
 }
}""",
'org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java': """package org.chromium.chrome.browser.ui.vertical_tabs;
public class ArcDesktopPolicy {
 public static final int MODE_AUTO=0,MODE_ARC=1,MODE_MOBILE=2;
 public static boolean isArcWindow(int pref,int width,boolean large) {
  return pref==MODE_ARC || pref!=MODE_MOBILE && large && width>=800;
 }
 public static int surface(int c,boolean dark){return c;}
 public static int foreground(int c){return c;}
 public static int selection(int c){return c;}
}""",
'ArchiumDesktopContextProbe.java': """import android.app.Activity;import android.content.Context;
import android.view.Display;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
public class ArchiumDesktopContextProbe {
 static int count;
 static void check(boolean got,boolean want,String scenario) {
  if(got!=want)throw new AssertionError(scenario+" expected "+want+" got "+got);
  count++;
 }
 public static void main(String[] args) {
  Context plain=new Context();
  plain.res.config.screenWidthDp=1200;plain.res.config.smallestScreenWidthDp=700;
  check(ArcDesktopAppearance.isDesktopWindow(plain),false,"nonvisual context");
  Context app=new Context();
  app.res.config.screenWidthDp=1200;app.res.config.smallestScreenWidthDp=700;
  check(ArcDesktopAppearance.isDesktopWindow(app),false,"application context");
  Activity detached=new Activity();
  detached.res.config.screenWidthDp=1100;detached.res.config.smallestScreenWidthDp=700;
  check(ArcDesktopAppearance.isDesktopWindow(detached),true,"Robolectric detached tablet");
  Activity external=new Activity();
  external.res.config.screenWidthDp=1100;external.window.decor.display=new Display(4);external.window.decor.attached=true;
  check(ArcDesktopAppearance.isDesktopWindow(external),true,"external display");
  Activity unbound=new Activity();
  unbound.res.config.screenWidthDp=1100;unbound.window.decor.display=new Display(6);
  check(ArcDesktopAppearance.isDesktopWindow(unbound),false,"display is not attached");
  Activity multi=new Activity();
  multi.res.config.screenWidthDp=1100;multi.multiWindow=true;
  check(ArcDesktopAppearance.isDesktopWindow(multi),true,"desktop multiwindow");
  Activity mobile=new Activity();
  mobile.res.config.screenWidthDp=420;mobile.window.decor.display=new Display(0);mobile.window.decor.attached=true;
  check(ArcDesktopAppearance.isDesktopWindow(mobile),false,"mobile window");
  Activity tablet=new Activity();
  tablet.res.config.screenWidthDp=1100;tablet.res.config.smallestScreenWidthDp=700;
  tablet.window.decor.display=new Display(0);tablet.window.decor.attached=true;
  check(ArcDesktopAppearance.isDesktopWindow(tablet),true,"tablet");
  Activity noWindow=new Activity();
  noWindow.window=null;noWindow.res.config.screenWidthDp=420;
  check(ArcDesktopAppearance.isDesktopWindow(noWindow),false,"missing window");
  mobile.prefs.mode=ArcDesktopPolicy.MODE_ARC;
  check(ArcDesktopAppearance.isDesktopWindow(mobile),true,"manual Arc");
  external.prefs.mode=ArcDesktopPolicy.MODE_MOBILE;
  check(ArcDesktopAppearance.isDesktopWindow(external),false,"manual mobile");
  System.out.println("ARCHIUM_DISPLAY_CONTEXT_SCENARIOS=PASS "+count);
 }
}"""
}
class ContextGuardTest(unittest.TestCase):
 def test_production_java_against_display_less_contexts(self):
  self.assertTrue(SOURCE.is_file())
  if not shutil.which('javac') or not shutil.which('java'):
   self.fail('Java toolchain is required for Gate B')
  with tempfile.TemporaryDirectory(prefix='archium-context-') as d:
   root=Path(d);files=[]
   for name,body in STUBS.items():
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(body);files.append(str(path))
   src=root/'org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopAppearance.java'
   src.parent.mkdir(parents=True,exist_ok=True)
   src.write_bytes(SOURCE.read_bytes());files.append(str(src))
   classes=root/'classes';classes.mkdir()
   subprocess.run(['javac','-d',str(classes),*files],check=True,timeout=90,capture_output=True,text=True)
   proc=subprocess.run(['java','-cp',str(classes),'ArchiumDesktopContextProbe'],
     check=True,timeout=45,capture_output=True,text=True)
   self.assertIn('ARCHIUM_DISPLAY_CONTEXT_SCENARIOS=PASS 11',proc.stdout)
if __name__=='__main__':unittest.main()
