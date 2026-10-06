// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "chrome/browser/password_manager/android/archium_password_manager_bridge.h"

#include <algorithm>
#include <limits>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "base/android/jni_android.h"
#include "base/android/jni_string.h"
#include "base/functional/bind.h"
#include "chrome/browser/profiles/profile.h"

#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
#include "chrome/browser/affiliations/affiliation_service_factory.h"
#include "chrome/browser/device_reauth/chrome_device_authenticator_factory.h"
// GN cannot evaluate this buildflag conditional. The matching module dependency
// is present exactly when the flag is enabled.
#include "chrome/browser/password_manager/android/archium_local_password_manager.h"  // nogncheck
#include "chrome/browser/password_manager/factories/profile_password_store_factory.h"
#include "base/strings/utf_string_conversions.h"
#include "base/time/time.h"
#include "components/device_reauth/device_reauth_metrics_util.h"
#endif

// Must follow Profile and string conversion declarations used by @JniType.
#include "chrome/browser/password_manager/android/jni_headers/ArchiumPasswordManagerBridge_jni.h"

namespace {
constexpr int kUnavailable = 1;
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
using Manager = password_manager::ArchiumLocalPasswordManager;
constexpr int kInvalid = 5;

base::android::ScopedJavaLocalRef<jcharArray> SecretArray(
    JNIEnv* env, const password_manager::PasswordString& password) {
  auto secret = password.secure_value();
  if (secret.size() > static_cast<size_t>(std::numeric_limits<jsize>::max())) return {};
  auto result = base::android::ScopedJavaLocalRef<jcharArray>(
      env, env->NewCharArray(static_cast<jsize>(secret.size())));
  if (!result.is_null() && !secret.empty()) {
    env->SetCharArrayRegion(result.obj(), 0, static_cast<jsize>(secret.size()),
                           reinterpret_cast<const jchar*>(secret.data()));
  }
  return result;
}

std::optional<password_manager::PasswordString> PasswordFromJava(
    JNIEnv* env, const base::android::JavaRef<jcharArray>& password) {
  if (password.is_null()) return std::nullopt;
  const jsize length = env->GetArrayLength(password.obj());
  if (length < 0 || length > 1048576) return std::nullopt;
  std::u16string value(static_cast<size_t>(length), u'\0');
  if (length) {
    env->GetCharArrayRegion(password.obj(), 0, length,
                            reinterpret_cast<jchar*>(value.data()));
    if (env->ExceptionCheck()) {
      std::fill(value.begin(), value.end(), u'\0');
      return std::nullopt;
    }
  }
  return password_manager::PasswordString(std::move(value));
}
#endif
}  // namespace

static bool JNI_ArchiumPasswordManagerBridge_IsLocalEnabled(JNIEnv* env) {
  return BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS);
}

static int64_t JNI_ArchiumPasswordManagerBridge_Init(
    JNIEnv* env, const base::android::JavaRef<jobject>& peer, Profile* profile,
    const base::android::JavaRef<jobject>& activity) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  if (!profile || activity.is_null() || profile->ShutdownStarted()) return 0;
  return reinterpret_cast<intptr_t>(new ArchiumPasswordManagerBridge(
      peer, profile->GetOriginalProfile(), activity));
#else
  return 0;
#endif
}

ArchiumPasswordManagerBridge::ArchiumPasswordManagerBridge(
    const base::android::JavaRef<jobject>& peer, Profile* profile,
    const base::android::JavaRef<jobject>& activity)
    : peer_(peer), profile_(profile) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  profile_observation_.Observe(profile);
  auto authenticator = ChromeDeviceAuthenticatorFactory::GetForProfile(
      profile, activity, device_reauth::DeviceAuthParams(
          base::TimeDelta(), device_reauth::DeviceAuthSource::kPasswordManager));
  manager_ = std::make_unique<Manager>(
      AffiliationServiceFactory::GetForProfile(profile),
      ProfilePasswordStoreFactory::GetForProfile(profile, ServiceAccessType::EXPLICIT_ACCESS),
      std::move(authenticator), base::BindRepeating(
          [](base::WeakPtr<ArchiumPasswordManagerBridge> self) {
            if (self && self->manager_) self->Refresh(base::android::AttachCurrentThread());
          }, weak_ptr_factory_.GetWeakPtr()));
#endif
}

ArchiumPasswordManagerBridge::~ArchiumPasswordManagerBridge() {
  weak_ptr_factory_.InvalidateWeakPtrs();
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  if (manager_) manager_->Shutdown();
#endif
}

void ArchiumPasswordManagerBridge::Refresh(JNIEnv* env) {
  Java_ArchiumPasswordManagerBridge_onListStart(env, peer_);
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  auto result = manager_->GetMetadata();
  if (result) {
    for (const auto& entry : *result) {
      Java_ArchiumPasswordManagerBridge_onEntry(env, peer_, entry.id, entry.url.spec(), entry.username);
    }
  }
  Java_ArchiumPasswordManagerBridge_onListEnd(env, peer_, result ? 0 : static_cast<int>(result.error()));
#else
  Java_ArchiumPasswordManagerBridge_onListEnd(env, peer_, kUnavailable);
#endif
}

void ArchiumPasswordManagerBridge::Add(
    JNIEnv* env,
    int32_t request,
    const base::android::JavaRef<jstring>& url,
    const base::android::JavaRef<jstring>& username,
    const base::android::JavaRef<jcharArray>& password) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  auto secret = PasswordFromJava(env, password);
  if (url.is_null() || username.is_null() || !secret) {
    Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request, kInvalid);
    return;
  }
  manager_->Add(
      GURL(base::android::ConvertJavaStringToUTF8(env, url)),
      base::android::ConvertJavaStringToUTF16(env, username),
      std::move(*secret),
      base::BindOnce(
          [](base::WeakPtr<ArchiumPasswordManagerBridge> self,
             int32_t request, Manager::Status status) {
            if (self) {
              Java_ArchiumPasswordManagerBridge_onOperation(
                  base::android::AttachCurrentThread(), self->peer_, request,
                  static_cast<int>(status));
            }
          },
          weak_ptr_factory_.GetWeakPtr(), request));
#else
  Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request,
                                                kUnavailable);
#endif
}

void ArchiumPasswordManagerBridge::Update(
    JNIEnv* env,
    int32_t request,
    int64_t id,
    const base::android::JavaRef<jstring>& username,
    const base::android::JavaRef<jcharArray>& password) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  auto secret = PasswordFromJava(env, password);
  if (username.is_null() || !secret) {
    Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request, kInvalid);
    return;
  }
  manager_->Update(
      id, base::android::ConvertJavaStringToUTF16(env, username),
      std::move(*secret),
      base::BindOnce(
          [](base::WeakPtr<ArchiumPasswordManagerBridge> self,
             int32_t request, Manager::Status status) {
            if (self) {
              Java_ArchiumPasswordManagerBridge_onOperation(
                  base::android::AttachCurrentThread(), self->peer_, request,
                  static_cast<int>(status));
            }
          },
          weak_ptr_factory_.GetWeakPtr(), request));
#else
  Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request,
                                                kUnavailable);
#endif
}

void ArchiumPasswordManagerBridge::Delete(
    JNIEnv* env, int32_t request, int64_t id) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  manager_->Delete(
      id,
      base::BindOnce(
          [](base::WeakPtr<ArchiumPasswordManagerBridge> self,
             int32_t request, Manager::Status status) {
            if (self) {
              Java_ArchiumPasswordManagerBridge_onOperation(
                  base::android::AttachCurrentThread(), self->peer_, request,
                  static_cast<int>(status));
            }
          },
          weak_ptr_factory_.GetWeakPtr(), request));
#else
  Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request,
                                                kUnavailable);
#endif
}

void ArchiumPasswordManagerBridge::Reveal(JNIEnv* env, int32_t request, int64_t id) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  manager_->Reveal(id, base::BindOnce(
      [](base::WeakPtr<ArchiumPasswordManagerBridge> self, int32_t request,
         Manager::Status status, password_manager::PasswordString password) {
        if (!self) return;
        JNIEnv* env = base::android::AttachCurrentThread();
        auto array = SecretArray(env, password);
        if (array.is_null() && env->ExceptionCheck()) return;
        Java_ArchiumPasswordManagerBridge_onSecret(env, self->peer_, request,
            !array.is_null() ? static_cast<int>(status) : kUnavailable, array);
      }, weak_ptr_factory_.GetWeakPtr(), request));
#else
  Java_ArchiumPasswordManagerBridge_onSecret(env, peer_, request, kUnavailable, base::android::ScopedJavaLocalRef<jcharArray>());
#endif
}

void ArchiumPasswordManagerBridge::Export(JNIEnv* env, int32_t request) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  manager_->Export(base::BindOnce(
      [](base::WeakPtr<ArchiumPasswordManagerBridge> self, int32_t request,
         Manager::Status status, std::vector<password_manager::StoredCredential> entries) {
        if (!self) return;
        JNIEnv* env = base::android::AttachCurrentThread();
        Java_ArchiumPasswordManagerBridge_onExportStart(env, self->peer_, request);
        if (status == Manager::Status::kSuccess) {
          for (const auto& entry : entries) {
            auto array = SecretArray(env, entry.password_value);
            if (array.is_null()) {
              if (env->ExceptionCheck()) return;
              status = Manager::Status::kUnavailable;
              break;
            }
            Java_ArchiumPasswordManagerBridge_onExportRow(env, self->peer_, request,
                entry.url.spec(), entry.username_value, array);
          }
        }
        Java_ArchiumPasswordManagerBridge_onExportEnd(env, self->peer_, request, static_cast<int>(status));
      }, weak_ptr_factory_.GetWeakPtr(), request));
#else
  Java_ArchiumPasswordManagerBridge_onExportStart(env, peer_, request);
  Java_ArchiumPasswordManagerBridge_onExportEnd(env, peer_, request, kUnavailable);
#endif
}

void ArchiumPasswordManagerBridge::PreviewImport(
    JNIEnv* env, int32_t request, const base::android::JavaRef<jobjectArray>& urls,
    const base::android::JavaRef<jobjectArray>& users,
    const base::android::JavaRef<jobjectArray>& passwords) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  if (urls.is_null() || users.is_null() || passwords.is_null() || env->GetArrayLength(urls.obj()) > 100000 ||
      env->GetArrayLength(urls.obj()) != env->GetArrayLength(users.obj()) ||
      env->GetArrayLength(urls.obj()) != env->GetArrayLength(passwords.obj())) {
    Java_ArchiumPasswordManagerBridge_onPreviewStart(env, peer_, request);
    Java_ArchiumPasswordManagerBridge_onPreviewEnd(env, peer_, request, kInvalid);
    return;
  }
  std::vector<password_manager::CSVPassword> rows;
  const jsize count = env->GetArrayLength(urls.obj());
  size_t total_chars = 0;
  for (jsize i = 0; i < count; ++i) {
    auto url = base::android::ScopedJavaLocalRef<jstring>(env,
        static_cast<jstring>(env->GetObjectArrayElement(urls.obj(), i)));
    auto user = base::android::ScopedJavaLocalRef<jstring>(env,
        static_cast<jstring>(env->GetObjectArrayElement(users.obj(), i)));
    auto password = base::android::ScopedJavaLocalRef<jcharArray>(env,
        static_cast<jcharArray>(env->GetObjectArrayElement(passwords.obj(), i)));
    if (url.is_null() || user.is_null() || password.is_null()) {
      Java_ArchiumPasswordManagerBridge_onPreviewStart(env, peer_, request);
      Java_ArchiumPasswordManagerBridge_onPreviewEnd(env, peer_, request, kInvalid);
      return;
    }
    const jsize length = env->GetArrayLength(password.obj());
    total_chars += static_cast<size_t>(env->GetStringLength(url.obj()));
    total_chars += static_cast<size_t>(env->GetStringLength(user.obj()));
    total_chars += static_cast<size_t>(length);
    if (length > 1048576 || total_chars > 16777216) {
      Java_ArchiumPasswordManagerBridge_onPreviewStart(env, peer_, request);
      Java_ArchiumPasswordManagerBridge_onPreviewEnd(env, peer_, request, kInvalid);
      return;
    }
    crypto::SecureU16String secret;
    secret.resize(length);
    if (length) env->GetCharArrayRegion(password.obj(), 0, length, reinterpret_cast<jchar*>(secret.data()));
    rows.emplace_back(GURL(base::android::ConvertJavaStringToUTF8(env, url)),
        base::android::ConvertJavaStringToUTF8(env, user),
        base::UTF16ToUTF8(std::u16string_view(secret.data(), secret.size())), "",
        password_manager::CSVPassword::Status::kOK);
  }
  manager_->PreviewImport(std::move(rows), base::BindOnce(
      [](base::WeakPtr<ArchiumPasswordManagerBridge> self, int32_t request,
         Manager::Status status, std::vector<password_manager::ArchiumPasswordImportPreview::Row> rows) {
        if (!self) return;
        JNIEnv* env = base::android::AttachCurrentThread();
        Java_ArchiumPasswordManagerBridge_onPreviewStart(env, self->peer_, request);
        for (size_t i = 0; i < rows.size(); ++i) {
          Java_ArchiumPasswordManagerBridge_onPreviewRow(
              env, self->peer_, request, static_cast<int32_t>(i),
              static_cast<int32_t>(rows[i].kind), rows[i].url.spec(),
              rows[i].username, rows[i].identity,
              static_cast<int32_t>(rows[i].required_decision));
        }
        Java_ArchiumPasswordManagerBridge_onPreviewEnd(env, self->peer_, request, static_cast<int>(status));
      }, weak_ptr_factory_.GetWeakPtr(), request));
#else
  Java_ArchiumPasswordManagerBridge_onPreviewStart(env, peer_, request);
  Java_ArchiumPasswordManagerBridge_onPreviewEnd(env, peer_, request, kUnavailable);
#endif
}

void ArchiumPasswordManagerBridge::ConfirmImport(
    JNIEnv* env, int32_t request, const base::android::JavaRef<jintArray>& decisions) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  if (decisions.is_null() || env->GetArrayLength(decisions.obj()) > 100000) {
    Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request, kInvalid);
    return;
  }
  std::vector<jint> raw(env->GetArrayLength(decisions.obj()));
  if (!raw.empty()) env->GetIntArrayRegion(decisions.obj(), 0, static_cast<jsize>(raw.size()), raw.data());
  std::vector<password_manager::ArchiumPasswordImportPreview::Decision> choices;
  for (jint value : raw) {
    if (value < 0 || value > 2) {
      Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request, kInvalid);
      return;
    }
    choices.push_back(static_cast<password_manager::ArchiumPasswordImportPreview::Decision>(value));
  }
  manager_->ConfirmImport(std::move(choices), base::BindOnce(
      [](base::WeakPtr<ArchiumPasswordManagerBridge> self, int32_t request, Manager::Status status) {
        if (self) Java_ArchiumPasswordManagerBridge_onOperation(
            base::android::AttachCurrentThread(), self->peer_, request, static_cast<int>(status));
      }, weak_ptr_factory_.GetWeakPtr(), request));
#else
  Java_ArchiumPasswordManagerBridge_onOperation(env, peer_, request, kUnavailable);
#endif
}

void ArchiumPasswordManagerBridge::CancelImport(JNIEnv* env) {
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  manager_->CancelImport();
#endif
}

void ArchiumPasswordManagerBridge::OnProfileWillBeDestroyed(Profile* profile) {
  weak_ptr_factory_.InvalidateWeakPtrs();
  profile_observation_.Reset();
  profile_ = nullptr;
#if BUILDFLAG(ENABLE_ARCHIUM_LOCAL_PASSWORDS)
  manager_->Shutdown();
#endif
  Refresh(base::android::AttachCurrentThread());
}

void ArchiumPasswordManagerBridge::Destroy(JNIEnv* env) { delete this; }

DEFINE_JNI(ArchiumPasswordManagerBridge)
