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
  void Set(int mode) {
    mode_.store(mode >= -2 && mode <= 3 ? mode : -2,
                std::memory_order_relaxed);
  }
  Snapshot Get() const {
    const int mode = mode_.load(std::memory_order_relaxed);
    return {mode >= 0, mode >= 0, mode >= 0 ? mode : 0};
  }

  // Auto uses the native pipeline unchanged. Only a user-selected manual
  // delta is composed with the existing frame transformation.
  static int RotationDegrees(Snapshot policy) {
    return policy.enabled && policy.manual ? policy.turns * 90 : 0;
  }

 private:
  std::atomic<int> mode_{-2};
};

}  // namespace blink
#endif  // THIRD_PARTY_BLINK_RENDERER_PLATFORM_MEDIASTREAM_ARC_CAMERA_ORIENTATION_POLICY_H_
