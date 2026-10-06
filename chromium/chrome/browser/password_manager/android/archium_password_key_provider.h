// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_KEY_PROVIDER_H_
#define CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_KEY_PROVIDER_H_

#include <cstdint>
#include <vector>

#include "base/functional/callback.h"
#include "components/os_crypt/async/browser/key_provider.h"

namespace password_manager {

// Android Keystore-backed wrapping of the password database's stable data key.
class ArchiumPasswordKeyProvider final : public os_crypt_async::KeyProvider {
 public:
  using KeyLoader = base::RepeatingCallback<std::vector<uint8_t>()>;
  ArchiumPasswordKeyProvider();
  explicit ArchiumPasswordKeyProvider(KeyLoader loader);
  ~ArchiumPasswordKeyProvider() override;

  void GetKey(KeyCallback callback) override;
  bool UseForEncryption() override;

 private:
  KeyLoader loader_;
};

}  // namespace password_manager
#endif  // CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_PASSWORD_KEY_PROVIDER_H_
