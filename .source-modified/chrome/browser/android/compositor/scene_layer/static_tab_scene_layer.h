// Copyright 2015 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_ANDROID_COMPOSITOR_SCENE_LAYER_STATIC_TAB_SCENE_LAYER_H_
#define CHROME_BROWSER_ANDROID_COMPOSITOR_SCENE_LAYER_STATIC_TAB_SCENE_LAYER_H_

#include <jni.h>

#include "base/android/jni_weak_ref.h"
#include "base/android/scoped_java_ref.h"
#include "base/memory/raw_ptr.h"
#include "base/memory/scoped_refptr.h"
#include "chrome/browser/ui/android/layouts/scene_layer.h"
#include "ui/gfx/geometry/rect_f.h"

namespace android {

class ContentLayer;
class TabContentManager;

// A SceneLayer to render a static tab.
class StaticTabSceneLayer : public SceneLayer {
 public:
  StaticTabSceneLayer(JNIEnv* env, const base::android::JavaRef<jobject>& jobj);

  StaticTabSceneLayer(const StaticTabSceneLayer&) = delete;
  StaticTabSceneLayer& operator=(const StaticTabSceneLayer&) = delete;

  ~StaticTabSceneLayer() override;

  bool ShouldShowBackground() override;
  SkColor GetBackgroundColor() override;

  // Update StaticTabSceneLayer with the new parameters.
  void UpdateTabLayer(JNIEnv* env,
                      int32_t id,
                      bool can_use_live_layer,
                      int32_t default_background_color,
                      float x,
                      float y,
                      const base::android::JavaRef<jobject>& joffset_tag);

  void SetArcSplitTabs(JNIEnv* env, int32_t left_id, int32_t right_id,
                       float left_x, float left_y, float left_width, float left_height,
                       float right_x, float right_y, float right_width, float right_height);

  void SetTabContentManager(
      JNIEnv* env,
      const base::android::JavaRef<jobject>& jtab_content_manager);

 private:
  scoped_refptr<android::ContentLayer> content_layer_;
  scoped_refptr<android::ContentLayer> arc_secondary_layer_;
  int32_t arc_left_id_ = -1;
  int32_t arc_right_id_ = -1;
  gfx::RectF arc_left_bounds_;
  gfx::RectF arc_right_bounds_;


  raw_ptr<TabContentManager> tab_content_manager_;
  int background_color_;
};

}  // namespace android

#endif  // CHROME_BROWSER_ANDROID_COMPOSITOR_SCENE_LAYER_STATIC_TAB_SCENE_LAYER_H_
