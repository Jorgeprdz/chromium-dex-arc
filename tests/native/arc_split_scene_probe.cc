// Host contract probe. Chromium layer/content/JNI boundaries are explicit adapters.
#include "chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.h"
#include <cassert>
int main() {
  android::TabContentManager manager;
  android::g_probe_manager = &manager;
  base::android::JavaRef<jobject> ref;
  android::StaticTabSceneLayer scene(nullptr, ref);
  scene.SetTabContentManager(nullptr, ref);
  scene.UpdateTabLayer(nullptr, 17, true, 0, 216, 0, ref);
  assert(scene.layer()->children().size() == 1);
  scene.SetArcSplitTabs(nullptr, 17, 42, 216, 0, 484, 800, 700, 0, 500, 800);
  scene.UpdateTabLayer(nullptr, 17, true, 0, 216, 0, ref);
  auto layers = scene.layer()->children();
  assert(layers.size() == 2);
  assert(layers[0]->tab_id == 17 && layers[1]->tab_id == 42);
  assert(layers[0]->position().x() == 216 && layers[1]->position().x() == 700);
  assert(layers[0]->clip_width == 484 && layers[1]->clip_width == 500);
  assert(layers[0]->live && layers[1]->live);
  assert(manager.primary == 17 && manager.visible == std::vector<int>({17,42}));
  scene.UpdateTabLayer(nullptr, 42, true, 0, 216, 0, ref);
  assert(layers[0]->tab_id == 17 && layers[1]->tab_id == 42 && manager.primary == 42);
  // Frame geometry can move independently while retaining the two identities.
  scene.SetArcSplitTabs(nullptr, 42, 17, 458, 0, 484, 800, 458, 0, 500, 800);
  scene.UpdateTabLayer(nullptr, 42, true, 0, 216, 0, ref);
  assert(layers[0]->tab_id == 42 && layers[1]->tab_id == 17);
  assert(layers[0]->position().x() == 458 && layers[1]->position().x() == 458);
  scene.SetArcSplitTabs(nullptr, -1, -1, 0,0,0,0,0,0,0,0);
  scene.UpdateTabLayer(nullptr, 42, true, 0, 216, 0, ref);
  assert(layers[0]->tab_id == 42 && layers[1]->hide_layer_and_subtree());
  assert(scene.layer()->children().size() == 2); // At most one reusable secondary layer.
  return 0;
}
