"""Run production geometry policy on a real JVM; no device/viewport rendering claim."""
import importlib.util,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RecoveryGeometryTests(unittest.TestCase):
 def test_native_tab_reserve_and_square_bottom_left_hit_region(self):
  spec=importlib.util.spec_from_file_location('window_core',ROOT/'scripts/fetch-window-core.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  jar=module.ensure_jar()
  with tempfile.TemporaryDirectory() as d:
   work=Path(d);src=work/'GeometryProbe.java'
   src.write_text("""import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
public class GeometryProbe {
 static void eq(int a,int b){if(a!=b)throw new AssertionError(a+" != "+b);}
 public static void main(String[] args){
  eq(ArcDesktopPolicy.collectionScrollBudgetPx(800,1f,20),240);
  eq(ArcDesktopPolicy.collectionScrollBudgetPx(600,1f,20),72);
  eq(ArcDesktopPolicy.collectionScrollBudgetPx(400,1f,0),0);
  eq(ArcDesktopPolicy.collectionScrollBudgetPx(800,0f,0),0);
  if(!ArcDesktopPolicy.containsArcContentPoint(0,99,0,0,100,100,16))throw new AssertionError("bottom left corner must be square");
  if(!ArcDesktopPolicy.containsArcContentPoint(99,99,0,0,100,100,16))throw new AssertionError("lower crop has square corners and accepts input");
  if(ArcDesktopPolicy.containsArcContentPoint(0,0,0,0,100,100,16))throw new AssertionError("top left corner must remain round");
  if(ArcDesktopPolicy.containsArcContentPoint(99,0,0,0,100,100,16))throw new AssertionError("right corner must be round");
  if(ArcDesktopPolicy.containsArcContentPoint(100,50,0,0,100,100,16))throw new AssertionError("outside must reject");
 }
}""")
   sources=list((ROOT/'chromium').rglob('ArcDesktopPolicy.java'))+list((ROOT/'chromium').rglob('ArchiumWindowClass.java'))+[src]
   c=subprocess.run([shutil.which('javac'),'-cp',str(jar),'-d',str(work),*map(str,sources)],capture_output=True,text=True)
   self.assertEqual(c.returncode,0,c.stderr)
   r=subprocess.run([shutil.which('java'),'-ea','-cp',str(work),'GeometryProbe'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
