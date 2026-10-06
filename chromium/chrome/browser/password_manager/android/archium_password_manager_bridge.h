// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_MANAGER_BRIDGE_H_
#define CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_MANAGER_BRIDGE_H_

#include <jni.h>
#include <cstdint>
#include <memory>

#include "base/android/scoped_java_ref.h"
#include "base/memory/raw_ptr.h"
#include "base/memory/weak_ptr.h"
#include "base/scoped_observation.h"
#include "chrome/browser/profiles/profile_observer.h"
#include "components/password_manager/core/browser/password_manager_buildflags.h"

class Profile;
namespace password_manager { class ArchiumLocalPasswordManager; }

class ArchiumPasswordManagerBridge : public ProfileObserver {
 public:
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
  void Destroy(JNIEnv* env);

 private:
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
