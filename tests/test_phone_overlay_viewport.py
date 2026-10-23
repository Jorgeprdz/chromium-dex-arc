"""Compile delivered viewport getters: defaults stay native, phone overlay reserves no controls."""
from pathlib import Path
import re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/fullscreen/BrowserControlsManager.java'
class PhoneOverlayViewportTests(unittest.TestCase):
    def test_delivered_getters_preserve_native_state_and_remove_only_phone_reservation(self):
        text=SOURCE.read_text();methods=[]
        names=['getTopControlsHeight','getTopControlsMinHeight','getBottomControlsHeight','getBottomControlsMinHeight','getContentOffset','getTopControlOffset','getBottomControlOffset','getTopVisibleContentOffset','getTopControlsMinHeightOffset','getBottomControlsMinHeightOffset','getBrowserControlHiddenRatio','getTopControlHiddenRatio','getBottomControlHiddenRatio']
        for name in names:
            matches=list(re.finditer(r'public (?:int|float) '+name+r'\(\)\s*\{',text));self.assertEqual(1,len(matches),name)
            m=matches[0];end=m.end();depth=1
            while depth:depth+=(text[end]=='{')-(text[end]=='}');end+=1
            methods.append(text[m.start():end])
        code='''public class OverlayProbe {
boolean mArcPhoneOverlay;
static class ControlsPosition {static final int TOP=0,BOTTOM=1;}
int mControlsPosition=ControlsPosition.TOP;
int mTopControlsHeight=56,mTopControlsMinHeight=8,mBottomControlsHeight=76,mBottomControlsMinHeight=10;
int mRendererTopContentOffset=56,mRendererTopControlOffset=0,mRendererBottomControlOffset=0,mRendererTopControlsMinHeightOffset=8,mRendererBottomControlsMinHeightOffset=10;
'''+ '\n'.join(methods)+'''
static void check(boolean v){if(!v)throw new AssertionError("phone overlay viewport reservation");}
public static void main(String[] args){OverlayProbe p=new OverlayProbe();
check(p.getTopControlsHeight()==56&&p.getBottomControlsHeight()==76&&p.getContentOffset()==56);
p.mArcPhoneOverlay=true;
check(p.getBrowserControlHiddenRatio()==0&&p.getTopControlHiddenRatio()==0&&p.getBottomControlHiddenRatio()==0);
check(p.getTopControlsHeight()==0&&p.getTopControlsMinHeight()==0&&p.getBottomControlsHeight()==0&&p.getBottomControlsMinHeight()==0&&p.getContentOffset()==0&&p.getTopVisibleContentOffset()==0);
p.mRendererTopControlOffset=-24;p.mRendererBottomControlOffset=30;
check(p.getTopControlOffset()==0&&p.getBottomControlOffset()==0&&p.getTopControlsMinHeightOffset()==0&&p.getBottomControlsMinHeightOffset()==0);
p.mTopControlsHeight=88;p.mBottomControlsHeight=92;check(p.getTopControlsHeight()==0&&p.getBottomControlsHeight()==0);
p.mArcPhoneOverlay=false;
check(p.getTopControlsHeight()==88&&p.getBottomControlsHeight()==92&&p.getTopControlsMinHeight()==8&&p.getBottomControlsMinHeight()==10&&p.getContentOffset()==56&&p.getTopVisibleContentOffset()==64&&p.getTopControlOffset()==-24&&p.getBottomControlOffset()==30);
}}
'''
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'OverlayProbe.java';f.write_text(code)
            r=subprocess.run([shutil.which('javac'),'-d',tmp,str(f)],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)
            r=subprocess.run([shutil.which('java'),'-cp',tmp,'OverlayProbe'],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)

    def test_glass_is_wired_to_native_phone_controls_and_content_overlay(self):
        toolbar=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        self.assertIn('mCompositorViewHolder.setArcPhoneControlsOverlay(glass)',toolbar)
        self.assertIn('phone.setArcPhoneGlassBackground(',toolbar)
        self.assertIn('mArcPhoneNavigation.setGlassBackdrop(',toolbar)
