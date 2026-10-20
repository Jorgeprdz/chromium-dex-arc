"""Execute delivered native navigation/activation/icon branches with explicit Java boundaries."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import method_body
ROOT=Path(__file__).resolve().parents[1]
MED=ROOT/'.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarMediator.java'
BINDER=ROOT/'.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java'
class AddressSemanticsTests(unittest.TestCase):
    def execute(self,assertions):
        source=MED.read_text();start=source.index('if (mLocationBarLayout.getArcCommandResults() != null)');load=method_body(source[start:],r'if \(')
        start=source.index('if (activateNewSession && mLocationBarLayout.getArcCommandResults() != null)') if 'if (activateNewSession && mLocationBarLayout.getArcCommandResults() != null)' in source else source.index('if (activateNewSession && mLocationBarLayout.getArcCommandResults() != null')
        initial=source[start:source.index('{',start)]+method_body(source[start:],r'if \(')
        action=re.search(r'boolean actionWanted\s*=\s*(.*?);',BINDER.read_text(),re.S)[1]
        code=r'''
class NativeAddressProbe {
 static class Layout {boolean editing,actions,showing=true;int closed;Object getArcCommandResults(){return showing?this:null;}boolean isArcCommandActions(){return actions;}boolean isArcCommandEditingAddress(){return editing;}void finishArcCommandNavigation(){closed++;showing=false;editing=false;}}
 static class OmniboxLoadUrlParams {String url;int transitionType;long inputStartTimestamp;boolean openInNewTab,openInNewWindow,openInBackground;byte[] postData;Object extraHeaders,callback;
  static class Builder {OmniboxLoadUrlParams p=new OmniboxLoadUrlParams();Builder(String u,int t){p.url=u;p.transitionType=t;}Builder setInputStartTimestamp(long v){p.inputStartTimestamp=v;return this;}Builder setOpenInNewTab(boolean v){p.openInNewTab=v;return this;}Builder setOpenInNewWindow(boolean v){p.openInNewWindow=v;return this;}Builder setOpenInBackground(boolean v){p.openInBackground=v;return this;}Builder setPostData(byte[] v){p.postData=v;return this;}Builder setExtraHeaders(Object v){p.extraHeaders=v;return this;}Builder setAutocompleteLoadCallback(Object v){p.callback=v;return this;}OmniboxLoadUrlParams build(){return p;}}
 }
 Layout mLocationBarLayout=new Layout();OmniboxLoadUrlParams delivered;
 void load(OmniboxLoadUrlParams omniboxLoadUrlParams){if(mLocationBarLayout.getArcCommandResults()!=null) LOAD;delivered=omniboxLoadUrlParams;}
 static class Input {String text="https://page.test/",initial=text;Object preview=new Object();Input setInitialInput(String s,Object o){initial=s;return this;}Input setUserText(String s){text=s;return this;}void setPreviewMatchUrl(Object o){preview=o;}}
 Input mCurrentInput=new Input();void activate(boolean activateNewSession){INITIAL}
 static class DeviceInfo {static boolean desktop;static boolean isDesktop(){return desktop;}}
 static class ArcDesktopAppearance {static boolean desktop;static boolean isDesktopWindow(Object context){return desktop;}}
 static class V {Object getContext(){return this;}}
 static boolean action(boolean showIconOnly,boolean isSelected,boolean isHovered,boolean deviceDesktop,boolean arcDesktop,boolean isPinned){DeviceInfo.desktop=deviceDesktop;ArcDesktopAppearance.desktop=arcDesktop;Object actionButton=new Object(),actionData=new Object();V view=new V();return ACTION;}
 static void check(boolean yes,String message){if(!yes)throw new AssertionError(message);}
 public static void main(String[] args){ASSERTIONS}
}
'''.replace('LOAD',load).replace('INITIAL',initial).replace('ACTION',action).replace('ASSERTIONS',assertions)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d);(path/'NativeAddressProbe.java').write_text(code)
            compiled=subprocess.run(['javac','-d',d,str(path/'NativeAddressProbe.java')],text=True,capture_output=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run(['java','-ea','-cp',d,'NativeAddressProbe'],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
    def test_edit_address_retains_page_url_during_native_activation(self):
        self.execute('NativeAddressProbe p=new NativeAddressProbe();p.mLocationBarLayout.editing=true;p.activate(true);check(p.mCurrentInput.text.equals("https://page.test/"),"current URL erased by new-command activation");')
    def test_edit_address_navigates_current_tab_and_preserves_parameters(self):
        self.execute('NativeAddressProbe p=new NativeAddressProbe();p.mLocationBarLayout.editing=true;OmniboxLoadUrlParams v=new OmniboxLoadUrlParams.Builder("https://next.test/",4).setPostData(new byte[]{1}).setExtraHeaders(new Object()).setAutocompleteLoadCallback(new Object()).build();p.load(v);check(p.delivered==v,"editing current tab changed native disposition or parameters");check(!p.delivered.openInNewTab,"editing created a tab");check(p.mLocationBarLayout.closed==1,"panel not restored before navigation");')
    def test_ctrl_t_still_starts_empty_and_opens_new_tab(self):
        self.execute('NativeAddressProbe p=new NativeAddressProbe();p.activate(true);check(p.mCurrentInput.text.isEmpty(),"CtrlT not empty");OmniboxLoadUrlParams v=new OmniboxLoadUrlParams.Builder("https://new.test/",4).build();p.load(v);check(p.delivered.openInNewTab,"CtrlT no longer creates a tab");check(!v.openInNewTab,"native input mutated");')
    def test_explicit_new_window_and_background_dispositions_survive_edit(self):
        self.execute('NativeAddressProbe p=new NativeAddressProbe();p.mLocationBarLayout.editing=true;OmniboxLoadUrlParams v=new OmniboxLoadUrlParams.Builder("https://new.test/",4).setOpenInNewWindow(true).setOpenInBackground(true).build();p.load(v);check(p.delivered==v&&p.delivered.openInNewWindow&&p.delivered.openInBackground,"explicit native dispositions changed");')
    def test_actions_never_navigate(self):
        self.execute('NativeAddressProbe p=new NativeAddressProbe();p.mLocationBarLayout.actions=true;p.load(new OmniboxLoadUrlParams.Builder("x",0).build());check(p.delivered==null&&p.mLocationBarLayout.closed==1,"actions navigated");')
    def test_compact_desktop_window_keeps_favicon_until_hover(self):
        self.execute('check(!action(true,true,false,false,true,false),"desktop window classified as phone; close replaces favicon");check(action(true,true,true,false,true,false),"desktop hover close unavailable");check(action(true,true,false,false,false,false),"phone behavior changed");check(action(false,true,false,false,true,false),"expanded close removed");check(!action(true,true,true,false,true,true),"pinned close exposed");')
