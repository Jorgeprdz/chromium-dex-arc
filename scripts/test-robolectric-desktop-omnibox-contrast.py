#!/usr/bin/env python3
"""Delivered desktop hint method on real TextViews; native theme scheduling is a boundary."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);classes=a.work/'classes';classes.mkdir(exist_ok=True)
s=(ROOT/'.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarTablet.java').read_text()
try:body=method_body(s,r'private void updateArcHintContrast\(')
except (ValueError,AssertionError,AttributeError):body='{}'
source='''import static org.junit.Assert.*;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.widget.EditText;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class DesktopHintTest {
 static class NativeTablet {
  Integer mArcSurfaceColor;ColorStateList mArcNativeHintColors,mArcAppliedHintColors;
  EditText mUrlBar=new EditText(RuntimeEnvironment.getApplication());Object command;
  Object getArcCommandResults(){return command;}
  private void updateArcHintContrast() BODY
 }
 @Test public void desktopHintHasContrastAndNativeEditorGeometryAndSpansRemainOwned() {
  NativeTablet v=new NativeTablet();v.mUrlBar.setPadding(12,3,14,5);v.mUrlBar.setText("https://example.test/path");
  v.mUrlBar.setHintTextColor(Color.LTGRAY);float size=v.mUrlBar.getTextSize();int text=v.mUrlBar.getCurrentTextColor();
  for(int surface:new int[]{0xffdccdf7,0xff202124,0xff777777,0xfffbcaea}) {
   v.mArcSurfaceColor=surface;v.updateArcHintContrast();
   double a=Color.luminance(v.mUrlBar.getCurrentHintTextColor()),b=Color.luminance(surface);
   assertTrue("Readable placeholder",(Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5);
   assertEquals(text,v.mUrlBar.getCurrentTextColor());assertEquals(size,v.mUrlBar.getTextSize(),0);
   assertEquals(12,v.mUrlBar.getPaddingLeft());assertEquals(14,v.mUrlBar.getPaddingRight());
   assertEquals("https://example.test/path",v.mUrlBar.getText().toString());
  }
  v.mArcSurfaceColor=null;v.updateArcHintContrast();assertEquals(Color.LTGRAY,v.mUrlBar.getCurrentHintTextColor());
  assertNull(v.mArcNativeHintColors);assertNull(v.mArcAppliedHintColors);
 }
 @Test public void nativeHintUpdatesAndCommandThemeSurviveDesktopExit() {
  NativeTablet v=new NativeTablet();v.mUrlBar.setHintTextColor(Color.MAGENTA);
  v.updateArcHintContrast();assertEquals(Color.MAGENTA,v.mUrlBar.getCurrentHintTextColor());
  v.mArcSurfaceColor=0xffdccdf7;v.updateArcHintContrast();
  v.mUrlBar.setHintTextColor(Color.GREEN);v.updateArcHintContrast();
  v.command=new Object();v.mUrlBar.setHintTextColor(Color.BLUE);v.updateArcHintContrast();
  assertEquals(Color.BLUE,v.mUrlBar.getCurrentHintTextColor());v.command=null;
  v.mArcSurfaceColor=null;v.updateArcHintContrast();assertEquals(Color.BLUE,v.mUrlBar.getCurrentHintTextColor());
 }
}'''.replace('BODY',body)
f=a.work/'DesktopHintTest.java';f.write_text(source);cp=a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),str(f)],check=True)
raise SystemExit(subprocess.run([str(a.java_home/'bin/java'),'-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','DesktopHintTest']).returncode)
