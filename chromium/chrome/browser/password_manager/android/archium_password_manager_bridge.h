// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_MANAGER_BRIDGE_H_
#define CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_MANAGER_BRIDGE_H_

#include <jni.h>
#include <cstdint>
#include <memory>
#include <limits>
#include <map>
#include <utility>

#include "base/android/scoped_java_ref.h"
#include "base/memory/raw_ptr.h"
#include "base/memory/weak_ptr.h"
#include "base/scoped_observation.h"
#include "chrome/browser/profiles/profile_observer.h"
#include "components/password_manager/core/browser/password_manager_buildflags.h"

class Profile;
namespace password_manager { class ArchiumLocalPasswordManager; }

// Tested handle mapping used directly by JNI. Opaque IDs never contain a
// native address and are never reused during the registry's lifetime.
// Kept independent of Java so invalid/destroyed handle behavior is testable.
template <typename T>
class ArchiumNonReusingHandleMap {
 public:
  int64_t Insert(std::shared_ptr<T> object) {
    if (!object || next_handle_ == std::numeric_limits<int64_t>::max())
      return 0;
    const int64_t handle = next_handle_++;
    entries_.emplace(handle, std::move(object));
    return handle;
  }

  std::shared_ptr<T> Acquire(int64_t handle) const {
    if (handle <= 0) return {};
    auto it = entries_.find(handle);
    return it == entries_.end() ? std::shared_ptr<T>() : it->second;
  }

  void Remove(int64_t handle) { entries_.erase(handle); }

 private:
  int64_t next_handle_ = 1;
  std::map<int64_t, std::shared_ptr<T>> entries_;
};

class ArchiumPasswordManagerBridge : public ProfileObserver {
 public:
  // Shared by JNI entry and native tests. Never unwrap an OTR profile.
  static bool CanManageProfile(Profile* profile);
  ArchiumPasswordManagerBridge(const base::android::JavaRef<jobject>& peer,
                               Profile* profile,
                               const base::android::JavaRef<jobject>& activity);
  ~ArchiumPasswordManagerBridge() override;
  void Refresh(JNIEnv* env);
  void Add(JNIEnv* env,
           int32_t request,
           const base::android::JavaRef<jstring>& url,
           const base::android::JavaRef<jstring>& username,
           const base::android::JavaRef<jcharArray>& password);
  void Update(JNIEnv* env,
              int32_t request,
              int64_t id,
              const base::android::JavaRef<jstring>& username,
              const base::android::JavaRef<jcharArray>& password);
  void Delete(JNIEnv* env, int32_t request, int64_t id);
  void Reveal(JNIEnv* env, int32_t request, int64_t id);
  void Export(JNIEnv* env, int32_t request);
  void PreviewImport(JNIEnv* env, int32_t request,
                     const base::android::JavaRef<jobjectArray>& urls,
                     const base::android::JavaRef<jobjectArray>& users,
                     const base::android::JavaRef<jobjectArray>& passwords);
  void ConfirmImport(JNIEnv* env, int32_t request,
                     const base::android::JavaRef<jintArray>& decisions);
  void CancelImport(JNIEnv* env);
  // Called when the opaque Java handle is destroyed. Safe to call repeatedly.
  void Close();

 private:
  bool Operational() const;
  bool closed_ = false;
  void OnProfileWillBeDestroyed(Profile* profile) override;
  base::android::ScopedJavaGlobalRef<jobject> peer_;
  raw_ptr<Profile> profile_;
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  std::unique_ptr<password_manager::ArchiumLocalPasswordManager> manager_;
#endif
  base::ScopedObservation<Profile, ProfileObserver> profile_observation_{this};
  base::WeakPtrFactory<ArchiumPasswordManagerBridge> weak_ptr_factory_{this};
};
#endif  // CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_MANAGER_BRIDGE_H_
