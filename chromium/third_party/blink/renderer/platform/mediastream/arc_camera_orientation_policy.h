// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef THIRD_PARTY_BLINK_RENDERER_PLATFORM_MEDIASTREAM_ARC_CAMERA_ORIENTATION_POLICY_H_
#define THIRD_PARTY_BLINK_RENDERER_PLATFORM_MEDIASTREAM_ARC_CAMERA_ORIENTATION_POLICY_H_

#include <atomic>

namespace blink {

// One instance per Page. No sensor override and no cross-page preference.
// -2: native/Mobile, -1: Desktop automatic, 0..3: Desktop manual quarter-turns.
class ArcCameraOrientationPolicy {
 public:
  struct Snapshot {
    bool enabled = false;
    bool manual = false;
    int turns = 0;
  };
  struct Geometry {
    bool valid = false;
    int width = 0;
    int height = 0;
    int rotation = 0;
  };

  void Set(int mode) {
    mode_.store(mode >= -2 && mode <= 3 ? mode : -2,
                std::memory_order_relaxed);
  }
  Snapshot Get() const {
    const int mode = mode_.load(std::memory_order_relaxed);
    return {mode >= -1, mode >= 0, mode >= 0 ? mode : 0};
  }

  // Dimensions describe the untransformed wrapped frame. Preserve upstream
  // orientation, composed with the user adjustment by VideoTransformation.
  // The display aspect respects explicit portrait requests as well.
  static Geometry Plan(Snapshot policy, int width, int height, int rotation) {
    if (!policy.enabled || width < 1 || height < 1 || width > 16384 ||
        height > 16384 || rotation < 0 || rotation >= 360 || rotation % 90) {
      return {};
    }
    if (rotation == 90 || rotation == 270) {
      const int old_width = width;
      width = height;
      height = old_width;
    }
    return {true, width, height, rotation};
  }

 private:
  std::atomic<int> mode_{-2};
};

}  // namespace blink
#endif  // THIRD_PARTY_BLINK_RENDERER_PLATFORM_MEDIASTREAM_ARC_CAMERA_ORIENTATION_POLICY_H_
