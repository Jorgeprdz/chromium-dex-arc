"""Native focus presentation opt-in; synthetic probes are not APK acceptance."""
from pathlib import Path
import unittest
from test_phone_overlay_insets import method,run_probe
ROOT=Path(__file__).resolve().parents[1]
class PhoneFocusGlassTests(unittest.TestCase):
 def test_container_keeps_latest_native_color_and_editor_untouched(self):
  source=(ROOT/'.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/suggestions/OmniboxSuggestionsContainer.java').read_text()
  code='''@interface Nullable {} class Drawable {} class Color {static final int TRANSPARENT=0;}class Parent {Drawable background;int color;void setBackground(Drawable d){background=d;}public void setBackgroundColor(int c){color=c;}void invalidate(){}}
public class FocusProbe extends Parent {
Drawable mArcPhoneGlassBackground;int mArcNativeBackgroundColor;
static class Dropdown {boolean enabled;void setArcPhoneGlassEnabled(boolean v){enabled=v;}}
Dropdown mDropdown=new Dropdown();
'''+method(source,'public void setArcPhoneGlassBackground(')+method(source,'public void setBackgroundColor(')+'''
static void check(boolean b){if(!b)throw new AssertionError("focus glass/native background restoration");}
public static void main(String[] args){FocusProbe p=new FocusProbe();p.setBackgroundColor(7);check(p.color==7);Drawable glass=new Drawable();p.setArcPhoneGlassBackground(glass);check(p.background==glass&&p.mDropdown.enabled);p.setBackgroundColor(9);check(p.background==glass);p.setArcPhoneGlassBackground(null);check(p.color==9&&!p.mDropdown.enabled);}}
'''
  run_probe(self,{'FocusProbe.java':code},'FocusProbe')
 def test_phone_focus_retains_overlay_without_touching_desktop(self):
  s=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java').read_text()
  body=method(s,'private void updateArcPhoneFloatingSurfaces()')
  import re
  definition=body[body.index('boolean floating ='):body.index('bindArcPhoneGestures(')]
  pull=re.search(r'bindArcPhonePullReveal\((.*?)\);',body,re.S).group(1)
  code='''public class FocusPolicyProbe {
static boolean focus;static boolean isUrlBarFocused(){return focus;}
static class Tab {boolean nativePage;boolean isNativePage(){return nativePage;}}
public static void main(String[] a){
// enabled,resumed,fullscreen,hasTab,nativePage,editorFocus,wantGlass,wantPull
int[][] cases={{1,1,0,1,0,0,1,1},{1,1,0,1,0,1,1,0},
{0,1,0,1,0,0,0,0},{1,0,0,1,0,0,0,0},{1,1,1,1,0,0,0,0},
{1,1,0,0,0,0,0,0},{1,1,0,1,1,0,0,0}};
for(int[] row:cases){boolean enabled=row[0]==1,mArcPhoneResumed=row[1]==1,mArcPhoneFullscreen=row[2]==1;
Tab glassTab=row[3]==1?new Tab():null;if(glassTab!=null)glassTab.nativePage=row[4]==1;focus=row[5]==1;
'''+definition+'''
Tab pullTarget='''+pull+''';
if(glass!=(row[6]==1)||(pullTarget!=null)!=(row[7]==1))throw new AssertionError("editor keeps glass, releases only phone pull gesture");
}}}
'''
  run_probe(self,{'FocusPolicyProbe.java':code},'FocusPolicyProbe')
  self.assertIn('ArcDesktopAppearance.isDesktopWindow',body)
  self.assertIn('setArcPhoneGlassBackground',body)
