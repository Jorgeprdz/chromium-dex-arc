#!/usr/bin/env python3
"""Execute delivered surface methods with real Android geometry; Chrome owners are boundaries."""
from pathlib import Path
import argparse
import sys
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
TABLET=ROOT/'.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarTablet.java'
PHONE=ROOT/'.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarPhone.java'

def method(source,name):
    match=re.search(r'^    (?:@Override )?(?:public|private|protected).*?\b'+name+r'\(',source,re.M)
    body=method_body(source, re.escape(match.group()))
    return source[match.start():source.index('{',match.start())]+body

def main():
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--classpath-file',type=Path,required=True)
        parser.add_argument('--java-home',type=Path,required=True)
        parser.add_argument('--work',type=Path,required=True)
        args=parser.parse_args()
        tablet=TABLET.read_text();phone=PHONE.read_text()
        tm='\n'.join(method(tablet,n) for n in ['setArcGlassBackground','getArcGlassBounds'])
        pm=method(phone,'updateLocationBarBackgroundBounds')
        for source,name,owner in [(tablet,'getArcBackgroundVerticalInset','tablet'),(phone,'getArcLocationBarVerticalInset','phone')]:
            if re.search(r'\b'+name+r'\(',source):
                if owner=='tablet':tm+='\n'+method(source,name)
                else:pm+='\n'+method(source,name)
        tm=tm.replace('@Nullable ','').replace('@Override public void getArcGlassBounds','public void getArcGlassBounds')
        pm=pm.replace('@VisualState ','')
        code='''package probe;
import static org.junit.Assert.*;
import android.app.Activity;
import android.content.Context;
import android.graphics.Rect;
import android.graphics.drawable.*;
import android.view.View;
import android.widget.FrameLayout;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class CapsuleTest {
 static class Border extends GradientDrawable {int top,bottom;void setInsets(int left,int t,int right,int b){top=t;bottom=b;}}
 static class Tablet extends FrameLayout {
  boolean mArcTopBar;Rect command;Drawable mArcGlassBackground,mArcGlassLayers,mFocusedPopupDrawable=new GradientDrawable();
  Border mLocationBarBackground=new Border();int mModernToolbarBackgroundVerticalOffset=4;
  Tablet(Context c){super(c);mLocationBarBackground.setInsets(0,4,0,4);layout(0,0,100,44);}
  Rect getArcCommandResults(){return command;}void updateBackgroundColor(){}
  TABLET_METHODS
 }
 static class Coordinator {View view;View getPhoneCoordinator(){return view;}}
 static class Phone extends FrameLayout {
  int mLocationBarBackgroundVerticalInset=8,focusIncrease;boolean mArcPhoneFloatingSurface;
  Coordinator mLocationBar=new Coordinator();Rect mLocationBarBackgroundBounds=new Rect();
  Phone(Context c){super(c);mLocationBar.view=new View(c);mLocationBar.view.layout(10,20,110,76);}
  int getLeftPositionOfLocationBarBackground(int state){return 10;}
  int getRightPositionOfLocationBarBackground(int state){return 110;}
  int calculateOnFocusHeightIncrease(){return focusIncrease;}
  void onLocationBarBackgroundViewBoundsChanged(){}
  PHONE_METHODS
  Rect bounds(){updateLocationBarBackgroundBounds(mLocationBarBackgroundBounds,0);return new Rect(mLocationBarBackgroundBounds);}
 }
 @Test public void sidebarFillBorderAndSamplingGrowTogetherWithoutChangingLayout(){
  var activity=Robolectric.buildActivity(Activity.class).setup();
  try {
   Tablet t=new Tablet(activity.get());Drawable glass=new GradientDrawable();t.setArcGlassBackground(glass);
   Rect bounds=new Rect();t.getArcGlassBounds(bounds);assertEquals(new Rect(0,3,100,41),bounds);
   assertEquals(3,((LayerDrawable)t.mArcGlassLayers).getLayerInsetTop(0));assertEquals(3,((LayerDrawable)t.mArcGlassLayers).getLayerInsetBottom(0));
   assertEquals(3,t.mLocationBarBackground.top);assertEquals(3,t.mLocationBarBackground.bottom);assertEquals(44,t.getHeight());
   t.mArcTopBar=true;t.setArcGlassBackground(glass);t.getArcGlassBounds(bounds);assertEquals(new Rect(0,4,100,40),bounds);assertEquals(4,t.mLocationBarBackground.top);assertNull(t.mArcGlassLayers);
   t.mArcTopBar=false;t.command=new Rect(0,0,100,100);t.setArcGlassBackground(glass);t.getArcGlassBounds(bounds);assertEquals(new Rect(0,4,100,40),bounds);assertNull(t.mArcGlassLayers);
   t.command=null;t.setArcGlassBackground(null);t.getArcGlassBounds(bounds);assertEquals(new Rect(0,4,100,40),bounds);assertEquals(4,t.mLocationBarBackground.top);
  }finally{activity.pause().stop().destroy();}
 }
 @Test public void phoneBackgroundGrowsSymmetricallyWithNativeFocusAndEditorBoundsRetained(){
  var activity=Robolectric.buildActivity(Activity.class).setup();
  try {
   Phone p=new Phone(activity.get());assertEquals(new Rect(10,28,110,68),p.bounds());
   p.mArcPhoneFloatingSurface=true;assertEquals(new Rect(10,27,110,69),p.bounds());
   p.focusIncrease=2;assertEquals(new Rect(10,25,110,71),p.bounds());
   assertEquals(20,p.mLocationBar.view.getTop());assertEquals(76,p.mLocationBar.view.getBottom());
   p.mArcPhoneFloatingSurface=false;assertEquals(new Rect(10,26,110,70),p.bounds());
  }finally{activity.pause().stop().destroy();}
 }
}
'''.replace('TABLET_METHODS',tm).replace('PHONE_METHODS',pm)
        cp=args.classpath_file.read_text().strip()
        work=args.work
        work.mkdir(parents=True,exist_ok=True)
        p=work/'probe/CapsuleTest.java';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(code)
        classes=work/'classes';classes.mkdir(exist_ok=True)
        subprocess.run([str(args.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),str(p)],check=True)
        subprocess.run([str(args.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','probe.CapsuleTest'],check=True)

        print('SCOPE=REAL_ANDROID_GEOMETRY_AND_DRAWABLES; DELIVERED_SURFACE_METHODS; CHROME_NATIVE_OWNERS_ARE_BOUNDARIES; NOT_DEVICE_ACCEPTANCE')

if __name__=='__main__':main()
