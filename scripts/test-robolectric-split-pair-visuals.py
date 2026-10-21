#!/usr/bin/env python3
"""Run delivered pair title/icon helpers on Android drawables; not APK/GPU validation."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file', type=Path, required=True)
p.add_argument('--java-home', type=Path, required=True)
p.add_argument('--work', type=Path, required=True)
p.add_argument('--native-graphics', action='store_true', help='Require native font/ellipsis rendering support')
a = p.parse_args()
a.work.mkdir(parents=True, exist_ok=True)
classes = a.work / 'classes'
classes.mkdir(exist_ok=True)
java = a.work / 'SplitPairVisualsProbe.java'
java.write_text(r'''
import static org.junit.Assert.*;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.text.TextPaint;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36},qualifiers="mdpi")
@GraphicsMode(GraphicsMode.Mode.GRAPHICS_MODE)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class SplitPairVisualsProbe {
 static Class<?> visuals() throws Exception {
  try{return Class.forName("org.chromium.chrome.browser.ui.vertical_tabs.ArcSplitPairVisuals");}
  catch(ClassNotFoundException e){throw new AssertionError("Pair visual helper is missing",e);}
 }
 static Drawable icons(Drawable left,Drawable right,int color) throws Exception {
  return (Drawable)visuals().getMethod("icons",Drawable.class,Drawable.class,int.class).invoke(null,left,right,color);
 }
 static CharSequence title(String left,String right,TextPaint paint,float width) throws Exception {
  return (CharSequence)visuals().getMethod("title",CharSequence.class,CharSequence.class,TextPaint.class,float.class).invoke(null,left,right,paint,width);
 }
 static class Logo extends Drawable {
  final int width,height;Rect drawn;int draws,tints;
  Logo(int w,int h){width=w;height=h;}
  @Override public int getIntrinsicWidth(){return width;}
  @Override public int getIntrinsicHeight(){return height;}
  @Override public void draw(Canvas c){drawn=new Rect(getBounds());draws++;}
  @Override public void setAlpha(int alpha){}
  @Override public void setColorFilter(ColorFilter f){tints++;}
  @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
 }
 static class RecordingCanvas extends Canvas {
  RectF divider;int color;
  @Override public void drawRect(float l,float t,float r,float b,Paint p){divider=new RectF(l,t,r,b);color=p.getColor();}
  @Override public void drawRect(RectF r,Paint p){drawRect(r.left,r.top,r.right,r.bottom,p);}
  @Override public void drawRect(Rect r,Paint p){drawRect(r.left,r.top,r.right,r.bottom,p);}
  @Override public void drawLine(float x,float y,float endX,float endY,Paint p){
   assertEquals(x,endX,0);divider=new RectF(x-p.getStrokeWidth()/2,y,endX+p.getStrokeWidth()/2,endY);color=p.getColor();
  }
 }
 @Test public void bothLogosFitIndependentHalvesAndRestoreTheirBounds() throws Exception {
  Logo left=new Logo(40,20),right=new Logo(20,40);
  left.setBounds(2,3,4,5);right.setBounds(6,7,8,9);
  Drawable pair=icons(left,right,Color.MAGENTA);pair.setBounds(0,0,41,24);
  RecordingCanvas canvas=new RecordingCanvas();pair.draw(canvas);
  assertEquals(1,left.draws);assertEquals(1,right.draws);
  assertEquals(new Rect(0,7,20,17),left.drawn);assertEquals(new Rect(25,0,37,24),right.drawn);
  assertEquals(new Rect(2,3,4,5),left.getBounds());assertEquals(new Rect(6,7,8,9),right.getBounds());
  assertEquals(0,left.tints);assertEquals(0,right.tints);
  assertNotNull("Both native logos need a visible divider",canvas.divider);
  assertEquals(1f,canvas.divider.width(),0);assertEquals(20f,canvas.divider.left,0);
  assertEquals(Color.MAGENTA,canvas.color);
 }
 @Test public void independentEllipsisPreservesSecondTitleAndSeparator() throws Exception {
  TextPaint paint=new TextPaint();paint.setTextSize(18);
  // Exceed each half under native fonts and Robolectric legacy's unit-width metric.
  String result=title("LEFT "+"W".repeat(800),"RIGHT "+"W".repeat(800),paint,200).toString();
  String[] parts=result.split(" \\| ",-1);
  assertEquals("Separator must survive long titles",2,parts.length);
  assertTrue(parts[0],parts[0].startsWith("LEFT"));assertTrue(parts[1],parts[1].startsWith("RIGHT"));
  // LEGACY ShadowTextUtils truncates without a glyph. Native mode verifies Android's ellipsis.
  if (NATIVE_GRAPHICS) {
   assertTrue(parts[0],parts[0].contains("\u2026"));assertTrue(parts[1],parts[1].contains("\u2026"));
  }
  assertTrue(parts[0].length()<805);assertTrue(parts[1].length()<806);
  float half=(200-paint.measureText(" | "))/2;
  assertTrue(paint.measureText(parts[0])<=half+.1f);assertTrue(paint.measureText(parts[1])<=half+.1f);
  assertTrue("Title must fit allocated row width",paint.measureText(result)<=200.1f);
  assertEquals("A | B",title("A","B",paint,200).toString());
 }
}
'''.replace('GRAPHICS_MODE', 'NATIVE' if a.native_graphics else 'LEGACY').replace('NATIVE_GRAPHICS',str(a.native_graphics).lower()))
cp = a.classpath_file.read_text().strip()
helper = ROOT / 'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcSplitPairVisuals.java'
sources = [java] + ([helper] if helper.exists() else [])
subprocess.run([str(a.java_home / 'bin/javac'), '-cp', cp, '-d', str(classes), *map(str, sources)], check=True)
result = subprocess.run([str(a.java_home / 'bin/java'), '-ea', '-Xmx512m',
    '-Drobolectric.conscryptMode=OFF', '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
    '-cp', str(classes) + ':' + cp, 'org.junit.runner.JUnitCore', 'SplitPairVisualsProbe'])
print('SCOPE=delivered_pair_title_and_drawable_helpers_real_Android_NOT_APK_GPU')
if not a.native_graphics:
    print('LIMIT=LEGACY_TextUtils_truncation_metrics_no_native_ellipsis_glyph_validation')
raise SystemExit(result.returncode)
