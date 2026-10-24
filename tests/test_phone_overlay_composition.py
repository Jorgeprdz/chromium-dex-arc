"""Regression for the native texture under a live floating capsule; no device acceptance."""
from pathlib import Path
import re,shutil,subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class OverlayCompositionTests(unittest.TestCase):
    def test_bottom_native_texture_is_suppressed_only_for_phone_overlay(self):
        p=ROOT/'.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/bottom/ScrollingBottomViewSceneLayer.java'
        source=p.read_text();m=re.search(r'public boolean isSceneOverlayTreeShowing\(\)\s*\{',source);self.assertIsNotNone(m)
        end=m.end();depth=1
        while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
        code='''public class SceneProbe {
boolean mArcPhoneControlsOverlay,mIsVisible=true;int mCurrentYOffsetPx,mTopShadowHeightPx=8;
static class Bottom {int getHeight(){return 84;}} Bottom mBottomView=new Bottom();
'''+source[m.start():end]+'''
static void check(boolean value){if(!value)throw new AssertionError("native texture behind live phone glass");}
public static void main(String[] args){SceneProbe p=new SceneProbe();check(p.isSceneOverlayTreeShowing());
p.mArcPhoneControlsOverlay=true;check(!p.isSceneOverlayTreeShowing());
p.mArcPhoneControlsOverlay=false;check(p.isSceneOverlayTreeShowing());
p.mIsVisible=false;check(!p.isSceneOverlayTreeShowing());p.mIsVisible=true;p.mCurrentYOffsetPx=90;check(!p.isSceneOverlayTreeShowing());}}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'SceneProbe.java';path.write_text(code)
            r=subprocess.run([shutil.which('javac'),'-d',tmp,str(path)],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)
            r=subprocess.run([shutil.which('java'),'-cp',tmp,'SceneProbe'],capture_output=True,text=True);self.assertEqual(0,r.returncode,r.stderr)

    def test_integration_suppresses_both_textures_and_preserves_other_suppression_reasons(self):
        toolbar=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        start=toolbar.index('private void updateToolbarSceneLayerSuppression()')
        end=toolbar.index('@VisibleForTesting',start)
        for reason in ('mIsXrFsm','mIsVerticalTabsHiddenDueToNarrow','mIsArcToolbarSuppressed','mArcPhoneOverlayActive'):
            self.assertIn(reason,toolbar[start:end])
        self.assertIn('phoneBottom.setArcPhoneControlsOverlay(floating)',toolbar)
        self.assertIn('edgeController.setArcPhoneControlsOverlay(glass)',toolbar)
        self.assertIn('mBottomControlsStacker.requestLayerUpdate(false)',toolbar)

    def test_native_pages_keep_one_floating_bottom_scene_without_web_inset_override(self):
        from test_phone_overlay_insets import run_probe
        toolbar=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
        floating=re.search(r'boolean floating = [^;]+;',toolbar).group(0)
        glass=re.search(r'boolean glass = [^;]+;',toolbar).group(0)
        bottom=re.search(r'phoneBottom.setArcPhoneControlsOverlay\((\w+)\)',toolbar).group(1)
        web=re.search(r'mCompositorViewHolder.setArcPhoneControlsOverlay\((\w+)\)',toolbar).group(1)
        code='public class NativeSceneProbe {static class Tab {boolean nativePage;boolean isNativePage(){return nativePage;}} static int actual(boolean enabled,boolean mArcPhoneResumed,boolean mArcPhoneFullscreen,Tab glassTab){'+floating+glass+'return ('+bottom+'?1:0)|('+web+'?2:0);}' + '\npublic static void main(String[] a){\nfor(boolean enabled:new boolean[]{false,true})for(boolean resumed:new boolean[]{false,true})for(boolean fullscreen:new boolean[]{false,true}){\nboolean live=enabled&&resumed&&!fullscreen;\nTab nativeTab=new Tab();nativeTab.nativePage=true;Tab webTab=new Tab();\nif(actual(enabled,resumed,fullscreen,nativeTab)!=(live?1:0)||actual(enabled,resumed,fullscreen,null)!=(live?1:0)||actual(enabled,resumed,fullscreen,webTab)!=(live?3:0))throw new AssertionError("NTP/native bottom scene or web viewport ownership");}}}\n'
        run_probe(self,{'NativeSceneProbe.java':code},'NativeSceneProbe')
