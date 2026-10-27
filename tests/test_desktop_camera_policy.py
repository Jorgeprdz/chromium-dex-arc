"""Compile the delivered camera policy math; not a Chromium/GPU or device acceptance."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class DesktopCameraPolicyTests(unittest.TestCase):
 def test_delivered_size_calculation_keeps_explicit_aspect_and_bounds(self):
  # Execute the delivered Chromium size algorithm; gfx/settings below are only
  # value-type boundaries. This is not a native VideoFrame or encoder test.
  source=(ROOT/'.source-modified/third_party/blink/renderer/modules/mediastream/video_track_adapter.cc').read_text()
  calculation=source[source.index('bool VideoTrackAdapter::CalculateDesiredSize('):source.index('void VideoTrackAdapter::StartFrameMonitoringOnVideoTaskRunner(')]
  clamp=source[source.index('int ClampToValidDimension('):source.index('void ComputeFrameRate(')]
  code='''#include <algorithm>
#include <cassert>
#include <cmath>
#include <optional>
#define DCHECK_GE(a,b) assert((a)>=(b))
#define DCHECK_NE(a,b) assert((a)!=(b))
#define DCHECK(a) assert(a)
namespace media::limits {constexpr int kMaxDimension=16384;}
namespace gfx {struct Size {
 int w=0,h=0; Size()=default; Size(int a,int b):w(a),h(b){}
 int width()const{return w;} int height()const{return h;}
};}
struct VideoTrackAdapterSettings {
 std::optional<gfx::Size> size; double low=0,high=10000;
 const auto& target_size()const{return size;}
 double min_aspect_ratio()const{return low;}
 double max_aspect_ratio()const{return high;}
};
struct VideoTrackAdapter {
 static bool CalculateDesiredSize(bool,const gfx::Size&,const VideoTrackAdapterSettings&,gfx::Size*);
};
'''+clamp+calculation+'''
int main(){
 gfx::Size out;
 VideoTrackAdapterSettings landscape{gfx::Size(1280,720),16.0/9,16.0/9};
 assert(VideoTrackAdapter::CalculateDesiredSize(false,{1920,1440},landscape,&out));
 assert(out.width()==1280&&out.height()==720);
 VideoTrackAdapterSettings portrait{gfx::Size(720,1280),9.0/16,9.0/16};
 assert(VideoTrackAdapter::CalculateDesiredSize(false,{1920,1440},portrait,&out));
 assert(out.width()==720&&out.height()==1280);
 VideoTrackAdapterSettings square{gfx::Size(1280,720),1,1};
 assert(VideoTrackAdapter::CalculateDesiredSize(false,{1920,1080},square,&out));
 assert(out.width()==720&&out.height()==720);
 assert(VideoTrackAdapter::CalculateDesiredSize(false,{320,240},landscape,&out));
 assert(out.width()<=320&&out.height()<=240);
 VideoTrackAdapterSettings native;
 assert(!VideoTrackAdapter::CalculateDesiredSize(false,{20000,240},native,&out));
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'size.cc';p.write_text(code)
   subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(p),'-o',d+'/size'],check=True,capture_output=True)
   subprocess.run([d+'/size'],check=True)

 def test_real_policy_orientation_dimensions_and_isolation(self):
  header=ROOT/'chromium/third_party/blink/renderer/platform/mediastream/arc_camera_orientation_policy.h'
  self.assertTrue(header.is_file(),'Camera calibration policy must be implemented')
  code='''#include "'''+str(header)+'''"
#include <cassert>
using blink::ArcCameraOrientationPolicy;
int main(){
 ArcCameraOrientationPolicy a,b;
 assert(!a.Get().enabled);
 a.Set(-1);assert(a.Get().enabled&&a.Get().turns==0&&!a.Get().manual);
 assert(!b.Get().enabled);
 auto p=ArcCameraOrientationPolicy::Plan(a.Get(),640,480,0);
 assert(p.valid&&p.width==640&&p.height==480&&p.rotation==0);
 a.Set(1);p=ArcCameraOrientationPolicy::Plan(a.Get(),1280,720,90);
 assert(p.width==720&&p.height==1280&&p.rotation==90);
 a.Set(2);p=ArcCameraOrientationPolicy::Plan(a.Get(),1280,720,180);
 assert(p.width==1280&&p.height==720&&p.rotation==180);
 a.Set(3);p=ArcCameraOrientationPolicy::Plan(a.Get(),640,480,0);
 assert(p.rotation==0&&p.width==640&&p.height==480);
 a.Set(-1);p=ArcCameraOrientationPolicy::Plan(a.Get(),720,1280,0);
 assert(p.width==720&&p.height==1280); // explicit portrait survives.
 p=ArcCameraOrientationPolicy::Plan(a.Get(),1280,720,270);
 assert(p.width==720&&p.height==1280&&p.rotation==270);
 assert(!ArcCameraOrientationPolicy::Plan(a.Get(),0,720,0).valid);
 assert(!ArcCameraOrientationPolicy::Plan(a.Get(),1280,720,45).valid);
 a.Set(99);assert(!a.Get().enabled);
 a.Set(-2);assert(!a.Get().enabled);
 b.Set(0);assert(b.Get().enabled&&b.Get().manual&&!a.Get().enabled);
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'case.cc';p.write_text(code)
   subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(p),'-o',d+'/case'],check=True,capture_output=True)
   subprocess.run([d+'/case'],check=True)
if __name__=='__main__':unittest.main()
