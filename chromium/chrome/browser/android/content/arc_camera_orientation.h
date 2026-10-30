// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef CHROME_BROWSER_ANDROID_CONTENT_ARC_CAMERA_ORIENTATION_H_
#define CHROME_BROWSER_ANDROID_CONTENT_ARC_CAMERA_ORIENTATION_H_
#include <memory>
#include "base/supports_user_data.h"
#include "content/public/browser/web_contents.h"
namespace arc_camera {
inline constexpr char kOrientationKey[] = "archium-camera-orientation";
struct OrientationData final : base::SupportsUserData::Data {
  explicit OrientationData(int value) : turns(value) {}
  int turns;
};
inline int Get(content::WebContents* contents) {
  if (!contents) return -1;
  auto* data = static_cast<OrientationData*>(contents->GetUserData(kOrientationKey));
  // Only the Desktop policy consumes this value; Mobile keeps native orientation.
  // Existing explicit angles, including zero, belong to their WebContents.
  return data && data->turns >= 0 ? data->turns : 1;
}
inline void Set(content::WebContents* contents, int turns) {
  if (!contents) return;
  if (turns < -1 || turns > 3) turns = -1;
  contents->SetUserData(kOrientationKey, std::make_unique<OrientationData>(turns));
  contents->OnWebPreferencesChanged();
}
}  // namespace arc_camera
#endif
