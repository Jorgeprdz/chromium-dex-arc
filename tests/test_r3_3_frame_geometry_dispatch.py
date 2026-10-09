"""R3.3 R-03 source contract: stale geometry callback suppression, NOT device runtime."""
from pathlib import Path
import re
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java").read_text()


class FrameGeometryDispatchContract(unittest.TestCase):
    def test_surface_callbacks_use_guarded_dispatch(self):
        self.assertIn('postCurrentFrameGeometry(view);', SOURCE)
        self.assertIn('postCurrentFrameGeometry(mCompositorViewHolder);', SOURCE)
        self.assertNotIn('view.post(ArcDesktopCoordinator.this::applyFrameGeometry);', SOURCE)

    def test_pending_queue_is_cancelled_with_generation(self):
        self.assertIn('mPendingFrameGeometryHost.removeCallbacks(mPendingFrameGeometry);', SOURCE)
        self.assertIn('mFrameGeometryGeneration++;', SOURCE)
        self.assertIn('generation != mFrameGeometryGeneration', SOURCE)

    def test_mode_and_lifecycle_guards_precede_apply(self):
        self.assertRegex(SOURCE, r'private void applyFrameGeometry\(\) \{\s*if \(mDestroyed \|\| !ArcDesktopAppearance.isDesktopWindow\(mActivity\)\) return;')
        self.assertRegex(SOURCE, r'private void clearFrameGeometry\(\) \{\s*//[^\n]*\n\s*invalidatePendingFrameGeometry\(\);')


if __name__ == "__main__":
    unittest.main()
