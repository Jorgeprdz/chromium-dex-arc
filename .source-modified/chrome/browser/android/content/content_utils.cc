// Copyright 2017 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "base/android/jni_string.h"
#include "chrome/browser/android/content/arc_camera_orientation.h"
#include "build/build_config.h"
#include "components/embedder_support/user_agent_utils.h"
#include "components/version_info/version_info.h"
#include "content/public/browser/web_contents.h"
#include "third_party/blink/public/common/features.h"
#include "third_party/blink/public/common/user_agent/user_agent_metadata.h"
#include "url/android/gurl_android.h"

// Must come after all headers that specialize FromJniType() / ToJniType().
#include "chrome/browser/android/content/jni_headers/ContentUtils_jni.h"

static std::string JNI_ContentUtils_GetBrowserUserAgent(JNIEnv* env) {
  return embedder_support::GetUserAgent();
}

static void JNI_ContentUtils_SetUserAgentOverride(
    JNIEnv* env,
    const base::android::JavaRef<jobject>& jweb_contents,
    bool j_override_in_new_tabs) {
  // Google's reduced Googlebook UA intentionally retains the CrOS platform token,
  // while Client Hints identify Android and the real CPU. This is a WebContents
  // override only; the native Android profile remains completely untouched.
  const blink::UserAgentMetadata metadata =
      embedder_support::GetUserAgentMetadata();
  blink::UserAgentOverride spoofed_ua;
  spoofed_ua.ua_string_override =
      embedder_support::BuildUserAgentFromOSAndProduct(
          "X11; CrOS x86_64 14541.0.0",
          "Chrome/" + version_info::GetMajorVersionNumber() + ".0.0.0");
  spoofed_ua.ua_metadata_override = metadata;
  spoofed_ua.ua_metadata_override->platform = "Android";
  spoofed_ua.ua_metadata_override->model.clear();
  spoofed_ua.ua_metadata_override->mobile = false;
  spoofed_ua.ua_metadata_override->form_factors =
      embedder_support::GetFormFactorsClientHint(metadata, /*is_mobile=*/false);
#if defined(ARCH_CPU_ARM_FAMILY)
  spoofed_ua.ua_metadata_override->architecture = "arm";
#elif defined(ARCH_CPU_X86_FAMILY)
  spoofed_ua.ua_metadata_override->architecture = "x86";
#else
  spoofed_ua.ua_metadata_override->architecture = metadata.architecture;
#endif
  spoofed_ua.ua_metadata_override->bitness = sizeof(void*) == 8 ? "64" : "32";
  spoofed_ua.ua_metadata_override->wow64 = false;

  content::WebContents::FromJavaWebContents(jweb_contents)
      ->SetUserAgentOverride(spoofed_ua, j_override_in_new_tabs);
}

static int32_t JNI_ContentUtils_GetArcCameraOrientation(
    JNIEnv* env, const base::android::JavaRef<jobject>& contents) {
  return arc_camera::Get(content::WebContents::FromJavaWebContents(contents));
}
static void JNI_ContentUtils_SetArcCameraOrientation(
    JNIEnv* env, const base::android::JavaRef<jobject>& contents, int32_t turns) {
  arc_camera::Set(content::WebContents::FromJavaWebContents(contents), turns);
}
DEFINE_JNI(ContentUtils)
