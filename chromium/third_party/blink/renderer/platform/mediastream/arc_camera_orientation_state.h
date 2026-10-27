// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef THIRD_PARTY_BLINK_RENDERER_PLATFORM_MEDIASTREAM_ARC_CAMERA_ORIENTATION_STATE_H_
#define THIRD_PARTY_BLINK_RENDERER_PLATFORM_MEDIASTREAM_ARC_CAMERA_ORIENTATION_STATE_H_
#include "base/memory/ref_counted.h"
#include "third_party/blink/renderer/platform/mediastream/arc_camera_orientation_policy.h"
namespace blink {
using ArcCameraOrientationState = base::RefCountedData<ArcCameraOrientationPolicy>;
}  // namespace blink
#endif
