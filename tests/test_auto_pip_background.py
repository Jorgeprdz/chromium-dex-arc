"""Protect the native tab-selection PiP path restored after the device regression."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('chrome/browser/picture_in_picture')

class AutoPipBackgroundTests(unittest.TestCase):
 def test_native_observer_matches_the_pre_regression_owner(self):
  for name in ('BUILD.gn','auto_picture_in_picture_tab_model_observer_helper.cc','auto_picture_in_picture_tab_model_observer_helper.h','auto_picture_in_picture_tab_model_observer_helper_unittest.cc'):
   with self.subTest(source=name):
    self.assertEqual((ROOT/'.source-reference'/BASE/name).read_bytes(),(ROOT/'.source-modified'/BASE/name).read_bytes())

 def test_native_selection_delivers_one_activation_change(self):
  source=(ROOT/'.source-modified'/BASE/'auto_picture_in_picture_tab_model_observer_helper.cc').read_text()
  signature='void AutoPictureInPictureTabModelObserverHelper::UpdateIsTabActivated()'
  start=source.index(signature);body=source[start:]
  # This is the final method in the pinned source.
  code='''#include <cassert>
#include <vector>
class AutoPictureInPictureTabModelObserverHelper {
 public: bool is_tab_activated_=false,is_observing_=true;int model=1;int* observed_tab_model_=&model;
 int own=1,other=2;int* active=&own;std::vector<bool> events;
 int* GetActiveWebContents(){return active;}int* GetObservedWebContents(){return &own;}
 void RunCallback(bool a){events.push_back(a);}void UpdateIsTabActivated();
};
'''+body+'''
int main(){AutoPictureInPictureTabModelObserverHelper h;
 h.UpdateIsTabActivated();assert(h.is_tab_activated_&&h.events.size()==1);
 h.active=&h.other;h.UpdateIsTabActivated();assert(!h.is_tab_activated_&&h.events.size()==2);
 h.UpdateIsTabActivated();assert(h.events.size()==2);
 h.active=&h.own;h.UpdateIsTabActivated();assert(h.is_tab_activated_&&h.events.size()==3);
 h.is_observing_=false;h.active=&h.other;h.UpdateIsTabActivated();assert(h.events.size()==3);
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'case.cc';p.write_text(code)
   subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(p),'-o',d+'/case'],check=True,capture_output=True)
   subprocess.run([d+'/case'],check=True)
