"""Native progress remains authoritative; only phone drawing changes."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method,run_probe
ROOT=Path(__file__).resolve().parents[1]
class PhonePerimeterProgressTests(unittest.TestCase):
 def test_composited_line_is_suppressed_only_while_phone_owns_perimeter(self):
  s=(ROOT/'.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/ToolbarProgressBar.java').read_text()
  code='''@interface Nullable {}class View{int invalidations;void invalidate(){invalidations++;}}class DrawingInfo {boolean visible;int progressBarColor,progressBarBackgroundColor,progressBarStaticBackgroundColor;}class Color{static final int TRANSPARENT=0;}class NativeProgress {public void getDrawingInfo(DrawingInfo d){d.visible=true;d.progressBarColor=0xff0000ff;d.progressBarBackgroundColor=5;d.progressBarStaticBackgroundColor=6;}}
public class ProgressProbe extends NativeProgress {View mArcPhonePerimeterTarget;
'''+method(s,'public void setArcPhonePerimeterTarget(')+method(s,'public void getDrawingInfo(')+'''
static void check(boolean b){if(!b)throw new AssertionError("native progress / one visible rendering");}
public static void main(String[] args){ProgressProbe p=new ProgressProbe();DrawingInfo d=new DrawingInfo();p.getDrawingInfo(d);check(d.visible&&d.progressBarColor==0xff0000ff);View target=new View();p.setArcPhonePerimeterTarget(target);p.getDrawingInfo(d);check(!d.visible&&d.progressBarColor==0&&d.progressBarBackgroundColor==0&&d.progressBarStaticBackgroundColor==0);p.setArcPhonePerimeterTarget(null);p.getDrawingInfo(d);check(d.visible&&d.progressBarColor==0xff0000ff);}}
'''
  run_probe(self,{'ProgressProbe.java':code},'ProgressProbe')
