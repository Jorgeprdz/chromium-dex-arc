// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "chrome/browser/password_manager/android/archium_password_key_provider.h"

#include "base/functional/bind.h"
#include "base/test/task_environment.h"
#include "base/test/test_future.h"
#include "base/threading/platform_thread.h"
#include "components/os_crypt/async/browser/os_crypt_async.h"
#include "testing/gtest/include/gtest/gtest.h"

namespace password_manager {
namespace {

class ArchiumPasswordKeyProviderTest : public testing::Test {
 protected:
  base::test::TaskEnvironment task_environment_;
};

TEST_F(ArchiumPasswordKeyProviderTest, WorkerLoadAndOriginSequenceReply) {
  const auto origin = base::PlatformThread::CurrentRef();
  ArchiumPasswordKeyProvider provider(base::BindRepeating([origin] {
    EXPECT_NE(origin, base::PlatformThread::CurrentRef());
    return std::vector<uint8_t>(32, 42);
  }));
  base::test::TestFuture<std::string,
                        base::expected<os_crypt_async::Encryptor::Key,
                                       os_crypt_async::KeyProvider::KeyError>> future;
  provider.GetKey(future.GetCallback());
  EXPECT_FALSE(future.IsReady());
  ASSERT_TRUE(future.Wait());
  EXPECT_EQ("apw1", future.Get<0>());
  EXPECT_TRUE(future.Get<1>().has_value());
  EXPECT_TRUE(provider.UseForEncryption());
}

TEST_F(ArchiumPasswordKeyProviderTest, RealEncryptorRoundTripAndTamperRejection) {
  std::vector<std::pair<size_t, std::unique_ptr<os_crypt_async::KeyProvider>>> providers;
  providers.emplace_back(20u, std::make_unique<ArchiumPasswordKeyProvider>(
      base::BindRepeating([] { return std::vector<uint8_t>(32, 42); })));
  os_crypt_async::OSCryptAsync crypt(std::move(providers));
  base::test::TestFuture<scoped_refptr<os_crypt_async::Encryptor>> future;
  crypt.GetInstance(future.GetCallback());
  auto encryptor = future.Get();
  ASSERT_TRUE(encryptor->IsEncryptionAvailable());
  auto ciphertext = encryptor->EncryptString("synthetic-password");
  ASSERT_TRUE(ciphertext.has_value());
  EXPECT_EQ("apw1", std::string(ciphertext->begin(), ciphertext->begin() + 4));
  EXPECT_EQ("synthetic-password", encryptor->DecryptData(*ciphertext));
  ciphertext->back() ^= 1;
  EXPECT_FALSE(encryptor->DecryptData(*ciphertext).has_value());
}

TEST_F(ArchiumPasswordKeyProviderTest, InvalidKeyFailsClosedAndPreservesData) {
  for (size_t size : {0u, 31u, 33u}) {
    std::vector<std::pair<size_t, std::unique_ptr<os_crypt_async::KeyProvider>>> providers;
    providers.emplace_back(20u, std::make_unique<ArchiumPasswordKeyProvider>(
        base::BindRepeating([size] { return std::vector<uint8_t>(size, 42); })));
    os_crypt_async::OSCryptAsync crypt(std::move(providers));
    base::test::TestFuture<scoped_refptr<os_crypt_async::Encryptor>> future;
    crypt.GetInstance(future.GetCallback());
    auto encryptor = future.Get();
    EXPECT_FALSE(encryptor->IsEncryptionAvailable());
    EXPECT_FALSE(encryptor->EncryptString("synthetic-password").has_value());
    os_crypt_async::Encryptor::DecryptFlags flags;
    const std::vector<uint8_t> unavailable_ciphertext = {'a', 'p', 'w', '1', 0};
    EXPECT_FALSE(encryptor->DecryptData(unavailable_ciphertext, &flags).has_value());
    EXPECT_TRUE(flags.temporarily_unavailable);
  }
}

}  // namespace
}  // namespace password_manager
