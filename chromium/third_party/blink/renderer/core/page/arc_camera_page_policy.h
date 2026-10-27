// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef THIRD_PARTY_BLINK_RENDERER_CORE_PAGE_ARC_CAMERA_PAGE_POLICY_H_
#define THIRD_PARTY_BLINK_RENDERER_CORE_PAGE_ARC_CAMERA_PAGE_POLICY_H_
#include "base/memory/scoped_refptr.h"
#include "third_party/blink/renderer/core/core_export.h"
#include "third_party/blink/renderer/core/page/page.h"
#include "third_party/blink/renderer/platform/heap/garbage_collected.h"
#include "third_party/blink/renderer/platform/mediastream/arc_camera_orientation_state.h"
#include "third_party/blink/renderer/platform/supplementable.h"
namespace blink {
class CORE_EXPORT ArcCameraPagePolicy final : public GarbageCollected<ArcCameraPagePolicy>,
                                 public Supplement<Page> {
 public:
  inline static const char kSupplementName[] = "ArcCameraPagePolicy";
  explicit ArcCameraPagePolicy(Page& page)
      : Supplement<Page>(page), state_(base::MakeRefCounted<ArcCameraOrientationState>()) {}
  static ArcCameraPagePolicy& From(Page& page) {
    auto* policy = Supplement<Page>::From<ArcCameraPagePolicy>(page);
    if (!policy) {
      policy = MakeGarbageCollected<ArcCameraPagePolicy>(page);
      Supplement<Page>::ProvideTo(page, policy);
    }
    return *policy;
  }
  scoped_refptr<ArcCameraOrientationState> State() const { return state_; }
  void Update(int mode) { state_->data.Set(mode); }
  void Trace(Visitor* visitor) const override;
 private:
  scoped_refptr<ArcCameraOrientationState> state_;
};
}  // namespace blink
#endif
