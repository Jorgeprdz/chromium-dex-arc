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

 def test_native_resolution_adapter_is_preserved(self):
  name='third_party/blink/renderer/modules/mediastream/video_track_adapter.cc'
  actual=(ROOT/'.source-modified'/name).read_text()
  native=(ROOT/'.source-reference'/name).read_text()
  start='VideoTrackAdapter::VideoFrameResolutionAdapter::AdaptFrameResolution('
  stop='void VideoTrackAdapter::VideoFrameResolutionAdapter::DeliverFrame('
  self.assertEqual(actual[actual.index(start):actual.index(stop)],native[native.index(start):native.index(stop)],'Manual rotation must not replace the native size/aspect adapter')

 def test_camera_mode_isolation_and_manual_delta(self):
  header=ROOT/'chromium/third_party/blink/renderer/platform/mediastream/arc_camera_orientation_policy.h'
  code='#include \"'+str(header)+'\"\n'+'#include <cassert>\nusing blink::ArcCameraOrientationPolicy;\nint main(){\n ArcCameraOrientationPolicy a,b;\n assert(!a.Get().enabled);\n a.Set(-1);assert(!a.Get().enabled&&!a.Get().manual);\n assert(ArcCameraOrientationPolicy::RotationDegrees(a.Get())==0);\n a.Set(0);assert(a.Get().enabled&&a.Get().manual);\n assert(ArcCameraOrientationPolicy::RotationDegrees(a.Get())==0);\n for(int turns=1;turns<=3;turns++){\n  a.Set(turns);assert(ArcCameraOrientationPolicy::RotationDegrees(a.Get())==turns*90);\n  assert(!b.Get().enabled);\n }\n a.Set(-2);assert(ArcCameraOrientationPolicy::RotationDegrees(a.Get())==0);\n a.Set(99);assert(!a.Get().enabled);\n b.Set(1);assert(ArcCameraOrientationPolicy::RotationDegrees(b.Get())==90&&!a.Get().enabled);\n a.Set(-1);assert(!a.Get().enabled&&b.Get().enabled);\n}'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'case.cc';p.write_text(code)
   subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(p),'-o',d+'/case'],check=True,capture_output=True)
   subprocess.run([d+'/case'],check=True)
if __name__=='__main__':unittest.main()
