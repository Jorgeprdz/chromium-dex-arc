"""Delivered Desktop geometry/contrast; phone overlay regression is in test_phone_floating_input."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method, run_probe
ROOT=Path(__file__).resolve().parents[1]
class ContentSafeGeometryTests(unittest.TestCase):
 def test_desktop_retains_thin_frame_and_original_native_margin(self):
  src=(ROOT/'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java').read_text()
  body=method(src,'public static int contentTopMargin(')
  code='public class CaptionProbe {'+body+'''public static void main(String[] a){
if(contentTopMargin(0,8)!=8||contentTopMargin(32,8)!=40||contentTopMargin(7,8)!=15)throw new AssertionError("Desktop frame grew beyond its original margin + 8dp");}}
'''
  run_probe(self,{'CaptionProbe.java':code},'CaptionProbe')
 def test_desktop_frame_does_not_reserve_a_second_title_row(self):
  src=(ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java').read_text()
  body=method(src,'private void applyFrameGeometry(')
  self.assertIn('contentTopMargin(mOriginalContentMarginTop, outer)',body)
  self.assertNotIn('WindowInsets.Type.captionBar()',body)
  # The native window controls and sidebar caption spacer keep their existing owner.
  self.assertIn('setDesktopWindowSpacerHost(captionSpacer)',src)
 def test_header_tile_text_uses_its_actual_idle_surface(self):
  policy=ROOT/'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java'
  window=next((ROOT/'chromium').rglob('ArchiumWindowClass.java'))
  src=(ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java').read_text()
  body=method(src,'private void styleInteraction(')
  code='import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;\npublic class TileProbe {\nint mPaletteSurface;\nint dp(int n){return n;}\nstatic class android {static class R {static class attr {static final int state_pressed=1,state_focused=2,state_hovered=3,state_enabled=4;}}}\nstatic class Color {static final int TRANSPARENT=0;}\nstatic class GradientDrawable {void setColor(int c){}void setCornerRadius(int n){}void setStroke(int a,int c){}}\nstatic class StateListDrawable {void addState(int[] a,GradientDrawable b){}}\nstatic class ColorStateList {int[] colors;ColorStateList(int[][] states,int[] c){colors=c;}}\nstatic class View {Object getTag(){return "arc-header-tile";}void setBackground(StateListDrawable s){}}\nstatic class TextView extends View {int idle;void setTextColor(int c){idle=c;}void setTextColor(ColorStateList c){idle=c.colors[c.colors.length-1];}}\n'+body+'public static void main(String[] args){TileProbe p=new TileProbe();\nfor(int seed=0;seed<0xffffff;seed+=7919)for(boolean dark:new boolean[]{false,true}){\np.mPaletteSurface=ArcDesktopPolicy.surface(seed,dark);TextView tile=new TextView();\np.styleInteraction(tile,ArcDesktopPolicy.foreground(p.mPaletteSurface),ArcDesktopPolicy.selection(p.mPaletteSurface));\nif(ArcDesktopPolicy.contrast(ArcDesktopPolicy.activeTabSurface(p.mPaletteSurface),tile.idle)<4.5)throw new AssertionError("caption contrast below AA on actual idle tile");}}\n}\n'
  run_probe(self,{'TileProbe.java':code,'org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java':policy.read_text(),'org/chromium/chrome/browser/desktop_policy/ArchiumWindowClass.java':window.read_text(),'androidx/window/core/layout/WindowSizeClass.java':'package androidx.window.core.layout;public class WindowSizeClass {public static final int WIDTH_DP_EXPANDED_LOWER_BOUND=840,WIDTH_DP_MEDIUM_LOWER_BOUND=600;}'},'TileProbe')
