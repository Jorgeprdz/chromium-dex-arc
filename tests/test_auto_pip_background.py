"""Compile the native visibility/selection transition methods with value-type seams.

This proves lifecycle routing and suppression, not Android window launch acceptance.
The Chromium unit test overlay covers actual WebContents observer delivery.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.source-modified/chrome/browser/picture_in_picture'


def method(source, signature):
    start = source.find(signature)
    if start < 0:
        raise AssertionError('Missing native background visibility hook: ' + signature)
    opened = source.index('{', start)
    depth, end = 1, opened + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class AutoPipBackgroundTests(unittest.TestCase):
    def test_effective_activation_uses_native_visibility_and_selection(self):
        source = (SOURCE / 'auto_picture_in_picture_tab_model_observer_helper.cc').read_text()
        methods = '\n'.join(method(source, signature) for signature in [
            'void AutoPictureInPictureTabModelObserverHelper::OnVisibilityWillChange(',
            'void AutoPictureInPictureTabModelObserverHelper::UpdateIsTabActivated()',
            'void AutoPictureInPictureTabModelObserverHelper::WillCloseTab(',
            'void AutoPictureInPictureTabModelObserverHelper::WillCloseTabs(',
        ])
        harness = r'''
#include <algorithm>
#include <cassert>
#include <memory>
#include <vector>
namespace content {enum class Visibility {VISIBLE,HIDDEN,OCCLUDED}; struct WebContents {};}
struct TabAndroid {content::WebContents* contents;content::WebContents* web_contents(){return contents;}};
struct Model {};
struct Delegate {bool enabled=true,dragging=false;
 bool ShouldObserveVisibility(content::WebContents*) const{return enabled;}
 bool IsTabDragging(content::WebContents*) const{return dragging;}};
class AutoPictureInPictureTabModelObserverHelper {
 public:
 std::unique_ptr<Delegate> delegate_=std::make_unique<Delegate>();
 Model model;Model* observed_tab_model_=&model;
 content::WebContents own, other;content::WebContents* active=&own;
 bool is_tab_activated_=false,is_observing_=true;
 bool is_web_contents_visible_=true,is_closing_=false;
 std::vector<bool> events;
 content::WebContents* GetObservedWebContents(){return &own;}
 content::WebContents* GetActiveWebContents(){return active;}
 void RunCallback(bool active){events.push_back(active);}
 void OnVisibilityWillChange(content::Visibility visibility);
 void UpdateIsTabActivated();
 void WillCloseTab(TabAndroid* tab);
 void WillCloseTabs(const std::vector<TabAndroid*>& tabs,bool is_all_tabs,bool allow_undo);
 void ReevaluateObservedModelAndState(bool){}
};
''' + methods + r'''
int main(){
 using V=content::Visibility;
 AutoPictureInPictureTabModelObserverHelper h;
 h.UpdateIsTabActivated();assert(h.is_tab_activated_&&h.events.size()==1);
 // Direct minimize and repeated background notification enter only once.
 h.OnVisibilityWillChange(V::HIDDEN);
 assert(!h.is_tab_activated_&&h.events.size()==2&&!h.events.back());
 h.OnVisibilityWillChange(V::HIDDEN);assert(h.events.size()==2);
 // The asynchronous PiP acknowledgement must still see an inactive opener.
 h.UpdateIsTabActivated();assert(!h.is_tab_activated_&&h.events.size()==2);
 h.OnVisibilityWillChange(V::VISIBLE);assert(h.is_tab_activated_&&h.events.size()==3);
 // A covered window uses the same transition and restoration.
 h.OnVisibilityWillChange(V::OCCLUDED);assert(!h.is_tab_activated_);
 h.OnVisibilityWillChange(V::VISIBLE);assert(h.is_tab_activated_);
 // A background tab stays inactive across window visibility changes.
 h.active=&h.other;h.UpdateIsTabActivated();auto count=h.events.size();
 h.OnVisibilityWillChange(V::HIDDEN);h.OnVisibilityWillChange(V::VISIBLE);
 assert(!h.is_tab_activated_&&h.events.size()==count);
 h.active=&h.own;h.UpdateIsTabActivated();assert(h.is_tab_activated_);
 // Closing and dragging must not start PiP via visibility side effects.
 count=h.events.size();TabAndroid own_tab{&h.own},other_tab{&h.other};
 h.WillCloseTab(&other_tab);assert(!h.is_closing_);
 h.WillCloseTabs({&other_tab},false,true);assert(!h.is_closing_);
 h.WillCloseTabs({&other_tab,&own_tab},false,true);assert(h.is_closing_);
 h.OnVisibilityWillChange(V::HIDDEN);
 assert(h.events.size()==count);h.is_closing_=false;
 h.delegate_->dragging=true;h.OnVisibilityWillChange(V::HIDDEN);
 assert(h.events.size()==count);h.delegate_->dragging=false;
 // Phone / unsupported Android and stopped observers preserve selection semantics.
 h.delegate_->enabled=false;h.OnVisibilityWillChange(V::HIDDEN);
 assert(h.events.size()==count&&h.is_tab_activated_);
 h.delegate_->enabled=true;h.is_observing_=false;h.OnVisibilityWillChange(V::HIDDEN);
 assert(h.events.size()==count);
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'case.cc'
            path.write_text(harness)
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-Wno-unused-parameter',str(path),'-o',tmp+'/case'],check=True,capture_output=True)
            subprocess.run([tmp+'/case'],check=True)


if __name__ == '__main__':
    unittest.main()
