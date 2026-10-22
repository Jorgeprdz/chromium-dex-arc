// Copyright 2015 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.h"

#include <cmath>
#include <memory>
#include <set>
#include <vector>

#include "base/supports_user_data.h"
#include "cc/input/android/offset_tag_android.h"
#include "cc/slim/filter.h"
#include "cc/slim/layer.h"
#include "chrome/browser/android/compositor/layer/content_layer.h"
#include "chrome/browser/android/compositor/layer_title_cache.h"
#include "chrome/browser/android/compositor/tab_content_manager.h"
#include "chrome/browser/android/tab_android.h"
#include "content/public/browser/web_contents.h"
#include "third_party/blink/public/common/web_preferences/web_preferences.h"
#include "ui/android/view_android.h"

// Must come after all headers that specialize FromJniType() / ToJniType().
#include "chrome/android/chrome_jni_headers/StaticTabSceneLayer_jni.h"

using base::android::JavaRef;

namespace android {
namespace {

const char kArcSplitViewportOwnersKey = 0;

struct ArcSplitViewportOwners : public base::SupportsUserData::Data {
  std::set<const void*> owners;
};

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

void SetArcSplitViewportOwner(content::WebContents* contents,
                             const void* owner,
                             bool enabled) {
  if (!contents || !owner) {
    return;
  }
  auto* data = static_cast<ArcSplitViewportOwners*>(
      contents->GetUserData(&kArcSplitViewportOwnersKey));
  if (!data) {
    if (!enabled) {
      return;
    }
    auto fresh = std::make_unique<ArcSplitViewportOwners>();
    data = fresh.get();
    contents->SetUserData(&kArcSplitViewportOwnersKey, std::move(fresh));
  }
  const bool was_split = !data->owners.empty();
  if (enabled) {
    data->owners.insert(owner);
  } else {
    data->owners.erase(owner);
  }
  const bool is_split = !data->owners.empty();
  if (!is_split) {
    contents->RemoveUserData(&kArcSplitViewportOwnersKey);
  }
  if (was_split != is_split) {
    // Recompute native preferences, including any current user/site overrides.
    // Do not restore a stale snapshot or send preference IPC on every frame.
    contents->OnWebPreferencesChanged();
  }
}

void ApplyArcSplitViewportPreferences(
    content::WebContents* contents,
    blink::web_pref::WebPreferences* prefs) {
  if (contents->GetUserData(&kArcSplitViewportOwnersKey) &&
      !prefs->viewport_meta_enabled) {
    // Request Desktop Site ignores viewport meta. Leaving the Android viewport
    // mechanism enabled then supplies a wide fallback layout (980px), even when
    // the widget/visual viewport is narrower. Desktop layout must follow the
    // actual widget width, as in desktop Chromium, so CSS breakpoints can run.
    // Explicit mobile mode retains Chromium's meta-viewport handling.
    prefs->viewport_enabled = false;
  }
}

StaticTabSceneLayer::StaticTabSceneLayer(JNIEnv* env,
                                         const JavaRef<jobject>& jobj)
    : SceneLayer(env, jobj),
      tab_content_manager_(nullptr),
      background_color_(SK_ColorWHITE) {}

StaticTabSceneLayer::~StaticTabSceneLayer() {
  for (const auto& contents : arc_viewport_contents_) {
    if (contents) {
      SetArcSplitViewportOwner(contents.get(), this, false);
    }
  }
}

void StaticTabSceneLayer::UpdateArcSplitViewportPolicy() {
  auto previous = arc_viewport_contents_;
  const int32_t ids[] = {arc_left_id_, arc_right_id_};
  for (size_t i = 0; i < arc_viewport_contents_.size(); ++i) {
    TabAndroid* tab = tab_content_manager_ && ids[i] >= 0
                          ? tab_content_manager_->GetTab(ids[i])
                          : nullptr;
    arc_viewport_contents_[i] = tab && tab->web_contents()
                                   ? tab->web_contents()->GetWeakPtr()
                                   : base::WeakPtr<content::WebContents>();
  }
  // Compare membership rather than position so swapping panes doesn't remove
  // and reapply preferences. Weak references don't keep destroyed tabs alive.
  for (const auto& contents : previous) {
    if (contents && contents.get() != arc_viewport_contents_[0].get() &&
        contents.get() != arc_viewport_contents_[1].get()) {
      SetArcSplitViewportOwner(contents.get(), this, false);
    }
  }
  for (const auto& contents : arc_viewport_contents_) {
    if (contents && contents.get() != previous[0].get() &&
        contents.get() != previous[1].get()) {
      SetArcSplitViewportOwner(contents.get(), this, true);
    }
  }
}

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
    UpdateArcSplitViewportPolicy();
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
  UpdateArcSplitViewportPolicy();
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
