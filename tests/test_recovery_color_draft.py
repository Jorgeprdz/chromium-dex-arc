"""Execute production color draft on a genuine JVM; not Chromium/Robolectric."""
import os, shutil, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcColorDraft.java'
class ColorDraftTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
  cls.work=Path(cls.tmp.name)
  cls.java=shutil.which('java');javac=shutil.which('javac')
  if not cls.java or not javac:raise AssertionError('Real JDK required, no skip')
  runner=cls.work/'ColorProbe.java'
  runner.write_text("""import org.chromium.chrome.browser.arc.ArcColorDraft;
public class ColorProbe {
 static void eq(Object a,Object b){if(!a.equals(b))throw new AssertionError(a+" != "+b);}
 public static void main(String[] args){
  ArcColorDraft d=new ArcColorDraft(0xff123456,0xff53657b);
  switch(args[0]){
   case "hex":eq(d.setHex(" #aBcDeF "),true);eq(d.color(),0xffabcdef);eq(d.hex(),"#ABCDEF");break;
   case "invalid":eq(d.setHex("#12345"),false);eq(d.isValid(),false);eq(d.color(),0xff123456);break;
   case "rgb":d.setRgb(255,0,128);eq(d.color(),0xffff0080);eq(d.hex(),"#FF0080");break;
   case "range":try{d.setRgb(-1,0,0);throw new AssertionError("negative RGB accepted");}catch(IllegalArgumentException expected){}break;
   case "alpha":eq(d.setHex("#00123456"),false);break;
   case "cancel":d.setRgb(3,4,5);d.cancel();eq(d.color(),0xff123456);eq(d.shouldClearPreference(),false);break;
   case "reset":d.reset();eq(d.color(),0xff53657b);eq(d.shouldClearPreference(),true);break;
   case "resetCancel":d.reset();d.cancel();eq(d.color(),0xff123456);eq(d.shouldClearPreference(),false);break;
   case "resetEdit":d.reset();d.setHex("#ABCDEF");eq(d.shouldClearPreference(),false);break;
   case "presets":eq(ArcColorDraft.presetCount(),8);eq(ArcColorDraft.presetAt(0),0xff53657b);eq(ArcColorDraft.presetAt(7),0xffda886b);break;
   case "selection":d.setHex("#998AC3");eq(d.selectedPreset(),1);d.setHex("wrong");eq(d.selectedPreset(),-1);d.setRgb(153,138,195);eq(d.selectedPreset(),1);break;
   default:throw new AssertionError("unknown case");
  }
 }
}""")
  cls.env=dict(os.environ);cls.env.pop('JAVA_TOOL_OPTIONS',None)
  result=subprocess.run([javac,'-d',str(cls.work),str(SOURCE),str(runner)],env=cls.env,capture_output=True,text=True)
  if result.returncode:raise AssertionError(result.stderr)
 def probe(self,name):
  r=subprocess.run([self.java,'-ea','-cp',str(self.work),'ColorProbe',name],env=self.env,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr)
 def test_hex_round_trip(self):self.probe('hex')
 def test_invalid_hex_keeps_last_value_and_blocks_apply(self):self.probe('invalid')
 def test_rgb_hex_share_one_value(self):self.probe('rgb')
 def test_rgb_out_of_range_is_rejected(self):self.probe('range')
 def test_alpha_hex_is_rejected(self):self.probe('alpha')
 def test_cancel_restores_original_draft(self):self.probe('cancel')
 def test_reset_marks_preference_removal(self):self.probe('reset')
 def test_cancel_after_reset_restores_original(self):self.probe('resetCancel')
 def test_edit_after_reset_becomes_custom(self):self.probe('resetEdit')
 def test_eight_approved_presets(self):self.probe('presets')
 def test_selection_tracks_valid_hex_and_rgb(self):self.probe('selection')
