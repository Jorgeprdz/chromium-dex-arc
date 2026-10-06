// Copyright 2023 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/password_manager/android/password_manager_android_util.h"

#include <string>
#include <utility>

#include "components/password_manager/core/browser/password_manager_buildflags.h"

#include "base/android/device_info.h"
#include "base/strings/string_number_conversions.h"
#include "chrome/browser/password_manager/android/password_manager_util_bridge_interface.h"
#include "components/password_manager/core/browser/split_stores_and_local_upm.h"

namespace password_manager_android_util {

namespace {

bool HasMinGmsVersionForFullUpmSupport() {
  std::string gms_version_str = base::android::device_info::gms_version_code();
  int gms_version = 0;
  // gms_version_code() must be converted to int for comparison, because it can
  // have legacy values "3(...)" and those evaluate > "2023(...)".
  return base::StringToInt(gms_version_str, &gms_version) &&
         gms_version >= password_manager::GetSplitStoresUpmMinVersion();
}

}  // namespace

bool IsPasswordManagerAvailable(
    std::unique_ptr<PasswordManagerUtilBridgeInterface> util_bridge) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  return true;  // Capability only; store GetError() gates readiness/save/fill.
#else
  return IsGooglePasswordManagerAvailable(std::move(util_bridge));
#endif
}

bool IsGooglePasswordManagerAvailable(
    std::unique_ptr<PasswordManagerUtilBridgeInterface> util_bridge) {
  return util_bridge->IsInternalBackendPresent() &&
         HasMinGmsVersionForFullUpmSupport();
}

bool IsPasswordManagerAvailable(bool is_internal_backend_present) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  return true;  // Never reports the Google internal backend as present.
#else
  if (!is_internal_backend_present) {
    return false;
  }

  if (!HasMinGmsVersionForFullUpmSupport()) {
    return false;
  }

  return true;
#endif
}

}  // namespace password_manager_android_util
