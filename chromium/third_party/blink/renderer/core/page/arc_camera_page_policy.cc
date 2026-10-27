// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "third_party/blink/renderer/core/page/arc_camera_page_policy.h"

namespace blink {
void ArcCameraPagePolicy::Trace(Visitor* visitor) const {
  Supplement<Page>::Trace(visitor);
}
}  // namespace blink
