#!/usr/bin/env python3
"""Execute delivered native extension width allocation with explicit width-consumer adapters."""
import argparse,subprocess,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
p=argparse.ArgumentParser();p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
s=(ROOT/'.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/top/ToolbarTablet.java').read_text()
f=r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.view.View;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
class ToolbarComponentId {static final int POPPED_EXTENSION_ACTION=1,EXTENSIONS_MENU_BUTTON=2,EXTENSIONS_REQUEST_ACCESS_BUTTON=3,EXTENSION_ACTION_LIST=4;}
class ToolbarUtils {static int[] RANKED_TOOLBAR_COMPONENTS={0,1,2,3,4};static boolean isToolbarTabletResizeRefactorEnabled(){return true;}}
class ToolbarWidthConsumer {int latest;int cost;ToolbarWidthConsumer(int c){cost=c;}int updateVisibility(int available,int w,int h){latest=available;return Math.min(cost,available);}}
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcExtensionsProbe {
 static class Toolbar extends View {
  boolean mIsDestroyed,mAllocatingArcExtensions;int mArcExtensionsWidth=-1;
  Object mExtensionsToolbarCoordinator=new Object();
  ToolbarWidthConsumer[] mToolbarWidthConsumers=new ToolbarWidthConsumer[5];
  Toolbar(android.content.Context c){super(c);mToolbarWidthConsumers[0]=new ToolbarWidthConsumer(700);mToolbarWidthConsumers[1]=new ToolbarWidthConsumer(20);}
  int getControlContainerMargin(){return 0;}
  void updateArcExtensionsWidth(int widthPx) SETWIDTH
  void onWidthConsumerVisibilityChanged() CALLBACK
  static void allocateAvailableToolbarWidth(ToolbarWidthConsumer[] toolbarWidthConsumer,int availableWidthDp,int widthMeasureSpec,int heightMeasureSpec) ALLOCATE
 }
 @Test public void asynchronousExtensionVisibilityRetainsSidebarBudget() {
  Activity a=Robolectric.buildActivity(Activity.class).setup().get();
  Toolbar t=new Toolbar(a);t.layout(0,0,800,56);t.updateArcExtensionsWidth(84);
  assertEquals(84,t.mToolbarWidthConsumers[1].latest);
  t.onWidthConsumerVisibilityChanged();
  assertEquals("Native load callback must not replace sidebar width with whole toolbar width",84,t.mToolbarWidthConsumers[1].latest);
  a.finish();
 }
}
'''
for marker,pattern in [('SETWIDTH',r'public void updateArcExtensionsWidth\('),('CALLBACK',r'public void onWidthConsumerVisibilityChanged\('),('ALLOCATE',r'static void allocateAvailableToolbarWidth\(')]:
 body=method_body(s,pattern);body=re.sub(r'@(?:Nullable|ToolbarComponentId)\s+','',body);f=f.replace(' '+marker+'\n',' '+body+'\n')
source=a.work/'ArcExtensionsProbe.java';source.write_text(f);classes=a.work/'classes';classes.mkdir(exist_ok=True);cp=a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),str(source)],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','ArcExtensionsProbe']);raise SystemExit(r.returncode)
