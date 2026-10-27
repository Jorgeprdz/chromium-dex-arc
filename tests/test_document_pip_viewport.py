"""Delivered child-only viewport policy; value-type seams, not device PiP acceptance."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]

class DocumentPipViewportTests(unittest.TestCase):
 def test_only_document_pip_gets_desktop_viewport(self):
  source=(ROOT/'.source-modified/chrome/browser/chrome_content_browser_client.cc').read_text()
  needle='if (web_contents->GetPictureInPictureOptions().has_value()) {'
  self.assertTrue(needle in source,'Document PiP still inherits mobile shrink-to-fit preferences')
  start=source.index(needle);opened=source.index('{',start);depth=1;end=opened+1
  while depth:
   if source[end]=='{':depth+=1
   elif source[end]=='}':depth-=1
   end+=1
  body=source[start:end]
  code='''#include <cassert>
#include <optional>
namespace blink::mojom {enum class ViewportStyle {kMobile,kDefault};}
struct Contents {bool pip;std::optional<int> GetPictureInPictureOptions(){return pip?std::optional<int>(1):std::nullopt;}};
struct Preferences {bool viewport_enabled=true,viewport_meta_enabled=true,shrinks_viewport_contents_to_fit=true,main_frame_resizes_are_orientation_changes=true;blink::mojom::ViewportStyle viewport_style=blink::mojom::ViewportStyle::kMobile;float default_minimum_page_scale_factor=.25f,default_maximum_page_scale_factor=5.f;};
void apply(Contents* web_contents,Preferences* web_prefs){'''+body+'''}
int main(){
 Contents ordinary{false},pip{true};Preferences native;
 apply(&ordinary,&native);
 assert(native.viewport_enabled&&native.viewport_meta_enabled&&native.shrinks_viewport_contents_to_fit&&native.main_frame_resizes_are_orientation_changes);
 assert(native.viewport_style==blink::mojom::ViewportStyle::kMobile&&native.default_minimum_page_scale_factor==.25f&&native.default_maximum_page_scale_factor==5.f);
 Preferences child;apply(&pip,&child);
 assert(!child.viewport_enabled&&!child.viewport_meta_enabled&&!child.shrinks_viewport_contents_to_fit&&!child.main_frame_resizes_are_orientation_changes);
 assert(child.viewport_style==blink::mojom::ViewportStyle::kDefault);
 assert(child.default_minimum_page_scale_factor==1.f&&child.default_maximum_page_scale_factor==4.f);
 apply(&ordinary,&native);assert(native.viewport_enabled&&native.default_minimum_page_scale_factor==.25f);
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'case.cc';p.write_text(code)
   subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(p),'-o',d+'/case'],check=True,capture_output=True)
   subprocess.run([d+'/case'],check=True)

if __name__=='__main__':unittest.main()
