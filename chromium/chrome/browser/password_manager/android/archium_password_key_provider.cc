// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "chrome/browser/password_manager/android/archium_password_key_provider.h"

#include <array>
#include <utility>

#include "base/android/jni_android.h"
#include "base/android/jni_array.h"
#include "base/functional/bind.h"
#include "base/task/thread_pool.h"
#include "components/os_crypt/async/common/algorithm.mojom.h"
#include "third_party/boringssl/src/include/openssl/mem.h"

// Must come after headers that specialize FromJniType/ToJniType.
#include "chrome/browser/password_manager/android/archium_key_jni_headers/ArchiumPasswordKeyBridge_jni.h"

namespace password_manager {
namespace {

std::vector<uint8_t> LoadAndroidKey() {
  JNIEnv* env = base::android::AttachCurrentThread();
  auto java_key = Java_ArchiumPasswordKeyBridge_getDataKey(env);
  std::vector<uint8_t> key;
  if (!java_key.is_null()) {
    base::android::JavaByteArrayToByteVector(env, java_key, &key);
    // Java owns a temporary copy; erase it as soon as the native key is copied.
    if (env->GetArrayLength(java_key.obj()) == 32) {
      const std::array<jbyte, 32> zeros = {};
      env->SetByteArrayRegion(java_key.obj(), 0, zeros.size(), zeros.data());
    }
  }
  return key;
}

base::expected<os_crypt_async::Encryptor::Key,
               os_crypt_async::KeyProvider::KeyError>
LoadEncryptionKey(ArchiumPasswordKeyProvider::KeyLoader loader) {
  auto bytes = loader.Run();
  if (bytes.size() != 32) {
    if (!bytes.empty()) OPENSSL_cleanse(bytes.data(), bytes.size());
    // Even corrupt or missing state must not authorize removal of saved rows.
    return base::unexpected(
        os_crypt_async::KeyProvider::KeyError::kTemporarilyUnavailable);
  }
  os_crypt_async::Encryptor::Key key(
      bytes, os_crypt_async::mojom::Algorithm::kAES256GCM);
  OPENSSL_cleanse(bytes.data(), bytes.size());
  return key;
}

}  // namespace

bool ArchiumLegacyKeyProvider::UseForEncryption() {
  return false;
}

ArchiumPasswordKeyProvider::ArchiumPasswordKeyProvider()
    : ArchiumPasswordKeyProvider(base::BindRepeating(&LoadAndroidKey)) {}

ArchiumPasswordKeyProvider::ArchiumPasswordKeyProvider(KeyLoader loader)
    : loader_(std::move(loader)) {}

ArchiumPasswordKeyProvider::~ArchiumPasswordKeyProvider() = default;

void ArchiumPasswordKeyProvider::GetKey(KeyCallback callback) {
  base::ThreadPool::PostTaskAndReplyWithResult(
      FROM_HERE, {base::MayBlock(), base::TaskPriority::USER_VISIBLE},
      base::BindOnce(&LoadEncryptionKey, loader_),
      base::BindOnce(
          [](KeyCallback callback,
             base::expected<os_crypt_async::Encryptor::Key, KeyError> key) {
            std::move(callback).Run("apw1", std::move(key));
          },
          std::move(callback)));
}

bool ArchiumPasswordKeyProvider::UseForEncryption() {
  return true;
}

}  // namespace password_manager

DEFINE_JNI(ArchiumPasswordKeyBridge)
