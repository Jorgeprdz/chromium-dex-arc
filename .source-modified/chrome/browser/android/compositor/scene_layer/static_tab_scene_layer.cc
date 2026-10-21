// Copyright 2015 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.h"

#include <vector>
#include <cmath>

#include "cc/input/android/offset_tag_android.h"
#include "cc/slim/filter.h"
#include "cc/slim/layer.h"
#include "chrome/browser/android/compositor/layer/content_layer.h"
#include "chrome/browser/android/compositor/layer_title_cache.h"
#include "chrome/browser/android/compositor/tab_content_manager.h"
#include "chrome/browser/android/tab_android.h"
#include "content/public/browser/web_contents.h"
#include "ui/android/view_android.h"

// Must come after all headers that specialize FromJniType() / ToJniType().
#include "chrome/android/chrome_jni_headers/StaticTabSceneLayer_jni.h"

using base::android::JavaRef;

namespace android {
namespace {

static bool LayerDraws(scoped_refptr<cc::slim::Layer> layer) {
  if (!layer.get() || layer->opacity() == 0.0f ||
      layer->hide_layer_and_subtree()) {
    return false;
  }

  if (layer->draws_content()) {
    return true;
  }

  for (const auto& child : layer->children()) {
    if (LayerDraws(child)) {
      return true;
    }
  }
  return false;
}

}  // namespace

StaticTabSceneLayer::StaticTabSceneLayer(JNIEnv* env,
                                         const JavaRef<jobject>& jobj)
    : SceneLayer(env, jobj),
      tab_content_manager_(nullptr),
      background_color_(SK_ColorWHITE) {}

StaticTabSceneLayer::~StaticTabSceneLayer() = default;

bool StaticTabSceneLayer::ShouldShowBackground() {
  scoped_refptr<cc::slim::Layer> root = layer_->RootLayer();
  return root && root->bounds() != layer_->bounds();
}

SkColor StaticTabSceneLayer::GetBackgroundColor() {
  return background_color_;
}

void StaticTabSceneLayer::UpdateTabLayer(JNIEnv* env,
                                         int32_t id,
                                         bool can_use_live_layer,
                                         int32_t default_background_color,
                                         float x,
                                         float y,
                                         const JavaRef<jobject>& joffset_tag) {
  DCHECK(tab_content_manager_)
      << "TabContentManager must be set before updating the layer";

  background_color_ = default_background_color;
  if (!content_layer_.get()) {
    content_layer_ = android::ContentLayer::Create(tab_content_manager_);
    layer_->AddChild(content_layer_->layer());
  }

  const bool split = can_use_live_layer && arc_left_id_ != -1 &&
                     arc_right_id_ != -1 && (id == arc_left_id_ || id == arc_right_id_);
  if (split) {
    if (!arc_secondary_layer_) {
      arc_secondary_layer_ = android::ContentLayer::Create(tab_content_manager_);
      layer_->AddChild(arc_secondary_layer_->layer());
    }
    tab_content_manager_->UpdateVisibleIds({arc_left_id_, arc_right_id_}, id);
    const auto draw = [&](ContentLayer* content, int tab_id, const gfx::RectF& bounds) {
      content->layer()->SetHideLayerAndSubtree(false);
      content->SetProperties(tab_id, /*can_use_live_layer=*/true, 0.f, false,
                             1.f, 1.f, /*should_clip=*/true,
                             gfx::Rect(0, 0, static_cast<int>(bounds.width()),
                                       static_cast<int>(bounds.height())));
      content->layer()->SetPosition(gfx::PointF(bounds.x(), bounds.y() + y));
      content->layer()->SetIsDrawable(true);
      content->layer()->SetOffsetTag(cc::android::FromJavaOffsetTag(env, joffset_tag));
      TabAndroid* tab = tab_content_manager_->GetTab(tab_id);
      if (tab && tab->web_contents() && tab->web_contents()->GetNativeView()) {
        // Each Android ContentView is placed at its own pane origin. Anchors are local.
        tab->web_contents()->GetNativeView()->set_content_offset_x(0.f);
      }
    };
    draw(content_layer_.get(), arc_left_id_, arc_left_bounds_);
    draw(arc_secondary_layer_.get(), arc_right_id_, arc_right_bounds_);
    return;
  }
  if (arc_secondary_layer_) arc_secondary_layer_->layer()->SetHideLayerAndSubtree(true);

  if (id != -1 && can_use_live_layer) {
    // StaticLayout may not know that the live layer cannot draw. Ensure it gets
    // a thumbnail if needed.
    bool update_visible_ids = true;
    if (auto live_layer = tab_content_manager_->GetLiveLayer(id)) {
      live_layer->SetHideLayerAndSubtree(!can_use_live_layer);
      update_visible_ids = !LayerDraws(live_layer);
    }
    if (update_visible_ids) {
      tab_content_manager_->UpdateVisibleIds({id}, id);
    }
    TabAndroid* tab = tab_content_manager_->GetTab(id);
    if (tab && tab->web_contents() && tab->web_contents()->GetNativeView()) {
      tab->web_contents()->GetNativeView()->set_content_offset_x(x);
    }
  }

  content_layer_->SetProperties(
      id, can_use_live_layer, /* static_to_view_blend= */ 0.f,
      /* should_override_content_alpha= */ false,
      /* content_alpha_override= */ 1.f, /* saturation= */ 1.f,
      /* should_clip= */ false, /* clip= */ gfx::Rect());

  content_layer_->layer()->SetPosition(gfx::PointF(x, y));
  content_layer_->layer()->SetIsDrawable(true);

  viz::OffsetTag tag = cc::android::FromJavaOffsetTag(env, joffset_tag);
  content_layer_->layer()->SetOffsetTag(tag);
}

void StaticTabSceneLayer::SetArcSplitTabs(
    JNIEnv* env, int32_t left_id, int32_t right_id,
    float left_x, float left_y, float left_width, float left_height,
    float right_x, float right_y, float right_width, float right_height) {
  const bool valid = left_id >= 0 && right_id >= 0 && left_id != right_id &&
      std::isfinite(left_x) && std::isfinite(left_y) && std::isfinite(left_width) &&
      std::isfinite(left_height) && std::isfinite(right_x) && std::isfinite(right_y) &&
      std::isfinite(right_width) && std::isfinite(right_height) &&
      left_width > 0 && right_width > 0 && left_height > 0 && right_height > 0;
  arc_left_id_ = valid ? left_id : -1;
  arc_right_id_ = valid ? right_id : -1;
  arc_left_bounds_ = valid ? gfx::RectF(left_x, left_y, left_width, left_height) : gfx::RectF();
  arc_right_bounds_ = valid ? gfx::RectF(right_x, right_y, right_width, right_height) : gfx::RectF();
}

void StaticTabSceneLayer::SetTabContentManager(
    JNIEnv* env,
    const base::android::JavaRef<jobject>& jtab_content_manager) {
  if (!tab_content_manager_) {
    tab_content_manager_ =
        TabContentManager::FromJavaObject(jtab_content_manager);
  }
}

static int64_t JNI_StaticTabSceneLayer_Init(JNIEnv* env,
                                            const JavaRef<jobject>& jobj) {
  // This will automatically bind to the Java object and pass ownership there.
  StaticTabSceneLayer* scene_layer = new StaticTabSceneLayer(env, jobj);
  return reinterpret_cast<intptr_t>(scene_layer);
}

}  // namespace android

DEFINE_JNI(StaticTabSceneLayer)
