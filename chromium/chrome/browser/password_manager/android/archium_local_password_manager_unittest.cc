// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "chrome/browser/password_manager/android/archium_local_password_manager.h"

#include <algorithm>
#include <memory>
#include <utility>

#include "base/functional/bind.h"
#include "base/functional/callback_helpers.h"
#include "base/test/bind.h"
#include "base/test/task_environment.h"
#include "base/test/test_future.h"
#include "components/affiliations/core/browser/fake_affiliation_service.h"
#include "components/device_reauth/mock_device_authenticator.h"
#include "components/password_manager/core/browser/password_store/actionable_error.h"
#include "components/password_manager/core/browser/password_store/test_password_store.h"
#include "components/password_manager/core/browser/password_store/mock_password_store_interface.h"
#include "components/password_manager/core/browser/ui/saved_passwords_presenter.h"
#include "testing/gmock/include/gmock/gmock.h"
#include "testing/gtest/include/gtest/gtest.h"

namespace password_manager {
namespace {
using Status = ArchiumLocalPasswordManager::Status;
using ::testing::_;
using ::testing::Return;

class SnapshotFailingStore : public MockPasswordStoreInterface {
 public:
  void GetImportSnapshot(ArchiumImportSnapshotReply callback) override {
    std::move(callback).Run(base::unexpected(PasswordStoreBackendError(
        PasswordStoreBackendErrorType::kUncategorized)));
  }

 protected:
  ~SnapshotFailingStore() override = default;
};

class ArchiumLocalPasswordManagerTest : public testing::Test {
 protected:
  void SetUp() override {
    store_->Init();
    CSVPassword csv(GURL("https://example.test/"), "user", "secret", "", CSVPassword::Status::kOK);
    store_->AddLogin(SavedPasswordsPresenter::CreateImportedCredential(CredentialUIEntry(csv)));
    auto auth = std::make_unique<testing::NiceMock<device_reauth::MockDeviceAuthenticator>>();
    auth_ = auth.get();
    ON_CALL(*auth_, CanAuthenticateWithBiometricOrScreenLock()).WillByDefault(Return(true));
    ON_CALL(*auth_, AuthenticateWithMessage(_, _)).WillByDefault(
        [this](const std::u16string&, device_reauth::DeviceAuthenticator::AuthenticateCallback reply) {
          pending_auth_ = std::move(reply);
        });
    manager_ = std::make_unique<ArchiumLocalPasswordManager>(
        &affiliations_, store_, std::move(auth), base::DoNothing());
    tasks_.RunUntilIdle();
  }
  void TearDown() override {
    manager_.reset();
    store_->ShutdownOnUIThread();
    tasks_.RunUntilIdle();
  }
  int64_t FirstId() {
    auto metadata = manager_->GetMetadata();
    EXPECT_TRUE(metadata.has_value());
    if (!metadata || metadata->empty()) return -1;
    return metadata->front().id;
  }
  base::test::SingleThreadTaskEnvironment tasks_;
  scoped_refptr<TestPasswordStore> store_ = base::MakeRefCounted<TestPasswordStore>();
  affiliations::FakeAffiliationService affiliations_;
  device_reauth::MockDeviceAuthenticator* auth_ = nullptr;
  device_reauth::DeviceAuthenticator::AuthenticateCallback pending_auth_;
  std::unique_ptr<ArchiumLocalPasswordManager> manager_;
};

TEST_F(ArchiumLocalPasswordManagerTest, MetadataDoesNotRequestAuthenticationOrRevealSecrets) {
  EXPECT_CALL(*auth_, AuthenticateWithMessage(_, _)).Times(0);
  auto metadata = manager_->GetMetadata();
  ASSERT_TRUE(metadata.has_value());
  ASSERT_EQ(metadata->size(), 1u);
  EXPECT_GT(metadata->front().id, 0);
  EXPECT_EQ(metadata->front().url, GURL("https://example.test/"));
  EXPECT_EQ(metadata->front().username, u"user");
}

TEST_F(ArchiumLocalPasswordManagerTest, AddAuthenticatesAndVerifiesPersistedCredential) {
  base::test::TestFuture<Status> result;
  manager_->Add(GURL("https://added.test/"), u"new-user",
                PasswordString(std::u16string(u"new-secret")),
                result.GetCallback());
  EXPECT_FALSE(result.IsReady());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  tasks_.RunUntilIdle();
  ASSERT_TRUE(result.IsReady());
  EXPECT_EQ(result.Get(), Status::kSuccess);

  auto metadata = manager_->GetMetadata();
  ASSERT_TRUE(metadata.has_value());
  EXPECT_EQ(metadata->size(), 2u);
  EXPECT_TRUE(std::ranges::any_of(*metadata, [](const auto& entry) {
    return entry.url == GURL("https://added.test/") &&
           entry.username == u"new-user";
  }));
}

TEST_F(ArchiumLocalPasswordManagerTest, UpdateRevalidatesIdAndVerifiesPersistedCredential) {
  const int64_t id = FirstId();
  base::test::TestFuture<Status> result;
  manager_->Update(id, u"renamed",
                   PasswordString(std::u16string(u"new-secret")),
                   result.GetCallback());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  tasks_.RunUntilIdle();
  ASSERT_TRUE(result.IsReady());
  EXPECT_EQ(result.Get(), Status::kSuccess);

  auto metadata = manager_->GetMetadata();
  ASSERT_TRUE(metadata.has_value());
  ASSERT_EQ(metadata->size(), 1u);
  EXPECT_EQ(metadata->front().username, u"renamed");

  base::test::TestFuture<Status, PasswordString> reveal;
  manager_->Reveal(metadata->front().id, reveal.GetCallback());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  EXPECT_EQ(reveal.Get<0>(), Status::kSuccess);
  EXPECT_EQ(reveal.Get<1>(), u"new-secret");
}

TEST_F(ArchiumLocalPasswordManagerTest, DeleteRevalidatesIdAndVerifiesRemoval) {
  const int64_t id = FirstId();
  base::test::TestFuture<Status> result;
  manager_->Delete(id, result.GetCallback());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  tasks_.RunUntilIdle();
  ASSERT_TRUE(result.IsReady());
  EXPECT_EQ(result.Get(), Status::kSuccess);

  auto metadata = manager_->GetMetadata();
  ASSERT_TRUE(metadata.has_value());
  EXPECT_TRUE(metadata->empty());
}

TEST_F(ArchiumLocalPasswordManagerTest, StoreChangeDuringUpdateAuthenticationMakesIdStale) {
  const int64_t id = FirstId();
  base::test::TestFuture<Status> result;
  manager_->Update(id, u"renamed",
                   PasswordString(std::u16string(u"new-secret")),
                   result.GetCallback());
  CSVPassword csv(GURL("https://other.test/"), "another", "different", "",
                  CSVPassword::Status::kOK);
  store_->AddLogin(
      SavedPasswordsPresenter::CreateImportedCredential(CredentialUIEntry(csv)));
  tasks_.RunUntilIdle();
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  EXPECT_EQ(result.Get(), Status::kStale);
}

TEST_F(ArchiumLocalPasswordManagerTest, InvalidAddDoesNotReportWriteSuccess) {
  base::test::TestFuture<Status> result;
  manager_->Add(GURL("https://invalid.test/"), u"user", PasswordString(),
                result.GetCallback());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  EXPECT_EQ(result.Get(), Status::kInvalid);
}

TEST_F(ArchiumLocalPasswordManagerTest,
       StoreChangeAfterPreviewMakesConfirmationStale) {
  std::vector<CSVPassword> rows;
  rows.emplace_back(GURL("https://import.test/"), "import-user",
                    "import-secret", "", CSVPassword::Status::kOK);
  base::test::TestFuture<
      Status, std::vector<ArchiumPasswordImportPreview::Row>>
      preview;
  manager_->PreviewImport(std::move(rows), preview.GetCallback());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  tasks_.RunUntilIdle();
  ASSERT_EQ(preview.Get<0>(), Status::kSuccess);

  CSVPassword changed(GURL("https://changed.test/"), "other", "changed", "",
                      CSVPassword::Status::kOK);
  store_->AddLogin(
      SavedPasswordsPresenter::CreateImportedCredential(
          CredentialUIEntry(changed)));
  tasks_.RunUntilIdle();

  EXPECT_CALL(*auth_, AuthenticateWithMessage(_, _)).Times(0);
  base::test::TestFuture<Status> confirm;
  manager_->ConfirmImport(
      {ArchiumPasswordImportPreview::Decision::kImport},
      confirm.GetCallback());
  EXPECT_EQ(confirm.Get(), Status::kStale);
}

TEST(ArchiumLocalPasswordManagerWriteFailureTest,
     AcceptedAddDoesNotReportSuccessWhenSnapshotVerificationFails) {
  base::test::SingleThreadTaskEnvironment tasks;
  affiliations::FakeAffiliationService affiliations;
  auto store = base::MakeRefCounted<SnapshotFailingStore>();
  ON_CALL(*store, GetError()).WillByDefault(Return(ActionableError::kNoError));
  EXPECT_CALL(*store, GetAllLoginsWithAffiliationAndBrandingInformation(_))
      .WillOnce([&](base::WeakPtr<PasswordStoreConsumer> consumer) {
        consumer->OnGetPasswordStoreResultsFrom(store.get(), {});
      });
  ON_CALL(*store, AddLogin(_, _))
      .WillByDefault([](StoredCredential, base::OnceClosure completion) {
        if (completion) std::move(completion).Run();
      });

  auto auth =
      std::make_unique<
          testing::NiceMock<device_reauth::MockDeviceAuthenticator>>();
  auto* auth_ptr = auth.get();
  ON_CALL(*auth_ptr, CanAuthenticateWithBiometricOrScreenLock())
      .WillByDefault(Return(true));
  device_reauth::DeviceAuthenticator::AuthenticateCallback pending;
  ON_CALL(*auth_ptr, AuthenticateWithMessage(_, _))
      .WillByDefault(
          [&](const std::u16string&,
              device_reauth::DeviceAuthenticator::AuthenticateCallback reply) {
            pending = std::move(reply);
          });

  ArchiumLocalPasswordManager manager(
      &affiliations, store, std::move(auth), base::DoNothing());
  tasks.RunUntilIdle();

  base::test::TestFuture<Status> result;
  manager.Add(GURL("https://write-fails.test/"), u"user",
              PasswordString(std::u16string(u"secret")),
              result.GetCallback());
  ASSERT_TRUE(pending);
  std::move(pending).Run(true);
  tasks.RunUntilIdle();
  EXPECT_EQ(result.Get(), Status::kWriteFailed);
  manager.Shutdown();
}

TEST_F(ArchiumLocalPasswordManagerTest, RevealWaitsForRealAuthenticatorResult) {
  base::test::TestFuture<Status, PasswordString> result;
  manager_->Reveal(FirstId(), result.GetCallback());
  EXPECT_FALSE(result.IsReady());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  ASSERT_TRUE(result.IsReady());
  EXPECT_EQ(result.Get<0>(), Status::kSuccess);
  EXPECT_EQ(result.Get<1>(), u"secret");
}

TEST_F(ArchiumLocalPasswordManagerTest, DeniedAuthenticationRevealsNothing) {
  base::test::TestFuture<Status, PasswordString> result;
  manager_->Reveal(FirstId(), result.GetCallback());
  std::move(pending_auth_).Run(false);
  EXPECT_EQ(result.Get<0>(), Status::kAuthenticationFailed);
  EXPECT_TRUE(result.Get<1>().empty());
}

TEST_F(ArchiumLocalPasswordManagerTest, UnavailableScreenLockDoesNotFallBackToUnprotectedReveal) {
  EXPECT_CALL(*auth_, CanAuthenticateWithBiometricOrScreenLock()).WillOnce(Return(false));
  EXPECT_CALL(*auth_, AuthenticateWithMessage(_, _)).Times(0);
  base::test::TestFuture<Status, PasswordString> result;
  manager_->Reveal(FirstId(), result.GetCallback());
  EXPECT_EQ(result.Get<0>(), Status::kAuthenticationFailed);
  EXPECT_TRUE(result.Get<1>().empty());
}

TEST_F(ArchiumLocalPasswordManagerTest, StoreChangeDuringAuthenticationInvalidatesOpaqueId) {
  base::test::TestFuture<Status, PasswordString> result;
  manager_->Reveal(FirstId(), result.GetCallback());
  CSVPassword csv(GURL("https://other.test/"), "another", "different", "", CSVPassword::Status::kOK);
  store_->AddLogin(SavedPasswordsPresenter::CreateImportedCredential(CredentialUIEntry(csv)));
  tasks_.RunUntilIdle();
  std::move(pending_auth_).Run(true);
  EXPECT_EQ(result.Get<0>(), Status::kStale);
  EXPECT_TRUE(result.Get<1>().empty());
}

TEST_F(ArchiumLocalPasswordManagerTest, ConcurrentSensitiveRequestCannotReusePendingAuthentication) {
  const int64_t id = FirstId();
  base::test::TestFuture<Status, PasswordString> first, second;
  manager_->Reveal(id, first.GetCallback());
  manager_->Reveal(id, second.GetCallback());
  EXPECT_EQ(second.Get<0>(), Status::kBusy);
  EXPECT_TRUE(second.Get<1>().empty());
  std::move(pending_auth_).Run(true);
  EXPECT_EQ(first.Get<0>(), Status::kSuccess);
}

TEST_F(ArchiumLocalPasswordManagerTest, ShutdownDropsLateSensitiveCallbackAndClearsReadiness) {
  bool delivered = false;
  manager_->Reveal(FirstId(), base::BindLambdaForTesting(
      [&](Status, PasswordString) { delivered = true; }));
  EXPECT_CALL(*auth_, Cancel()).Times(1);
  manager_->Shutdown();
  std::move(pending_auth_).Run(true);
  EXPECT_FALSE(delivered);
  auto metadata = manager_->GetMetadata();
  ASSERT_FALSE(metadata.has_value());
  EXPECT_EQ(metadata.error(), Status::kUnavailable);
}

TEST_F(ArchiumLocalPasswordManagerTest, DeniedExportNeverReturnsStoreCredentials) {
  base::test::TestFuture<Status, std::vector<StoredCredential>> result;
  manager_->Export(result.GetCallback());
  std::move(pending_auth_).Run(false);
  EXPECT_EQ(result.Get<0>(), Status::kAuthenticationFailed);
  EXPECT_TRUE(result.Get<1>().empty());
}

TEST_F(ArchiumLocalPasswordManagerTest,
       BusyPreviewRequestDoesNotInvalidateAcceptedImportFlow) {
  std::vector<CSVPassword> first_rows;
  first_rows.emplace_back(GURL("https://import.test/"), "import-user",
                          "import-secret", "", CSVPassword::Status::kOK);
  base::test::TestFuture<
      Status, std::vector<ArchiumPasswordImportPreview::Row>>
      first_preview;
  manager_->PreviewImport(std::move(first_rows), first_preview.GetCallback());
  ASSERT_TRUE(pending_auth_);

  std::vector<CSVPassword> second_rows;
  second_rows.emplace_back(GURL("https://rejected.test/"), "other",
                           "other-secret", "", CSVPassword::Status::kOK);
  base::test::TestFuture<
      Status, std::vector<ArchiumPasswordImportPreview::Row>>
      rejected_preview;
  manager_->PreviewImport(std::move(second_rows),
                          rejected_preview.GetCallback());
  EXPECT_EQ(rejected_preview.Get<0>(), Status::kBusy);

  std::move(pending_auth_).Run(true);
  tasks_.RunUntilIdle();
  ASSERT_EQ(first_preview.Get<0>(), Status::kSuccess);
  ASSERT_EQ(first_preview.Get<1>().size(), 1u);

  base::test::TestFuture<Status> confirmed;
  manager_->ConfirmImport({ArchiumPasswordImportPreview::Decision::kImport},
                          confirmed.GetCallback());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(true);
  tasks_.RunUntilIdle();
  EXPECT_EQ(confirmed.Get(), Status::kSuccess);
}

TEST_F(ArchiumLocalPasswordManagerTest,
       DeniedImportAuthenticationDoesNotCreateConfirmablePreview) {
  std::vector<CSVPassword> rows;
  rows.emplace_back(GURL("https://import.test/"), "import-user",
                    "import-secret", "", CSVPassword::Status::kOK);
  base::test::TestFuture<
      Status, std::vector<ArchiumPasswordImportPreview::Row>>
      preview;
  manager_->PreviewImport(std::move(rows), preview.GetCallback());
  ASSERT_TRUE(pending_auth_);
  std::move(pending_auth_).Run(false);
  EXPECT_EQ(preview.Get<0>(), Status::kAuthenticationFailed);

  EXPECT_CALL(*auth_, AuthenticateWithMessage(_, _)).Times(0);
  base::test::TestFuture<Status> confirm;
  manager_->ConfirmImport({}, confirm.GetCallback());
  EXPECT_EQ(confirm.Get(), Status::kStale);
}

TEST_F(ArchiumLocalPasswordManagerTest, CancelledImportCannotConfirmAnything) {
  manager_->CancelImport();
  EXPECT_CALL(*auth_, AuthenticateWithMessage(_, _)).Times(0);
  base::test::TestFuture<Status> result;
  manager_->ConfirmImport({}, result.GetCallback());
  EXPECT_EQ(result.Get(), Status::kStale);
}

TEST(ArchiumLocalPasswordManagerReadErrorTest, FailedStoreReadCannotLookLikeAnEmptyVault) {
  base::test::SingleThreadTaskEnvironment tasks;
  affiliations::FakeAffiliationService affiliations;
  auto store = base::MakeRefCounted<testing::NiceMock<MockPasswordStoreInterface>>();
  ON_CALL(*store, GetError()).WillByDefault(Return(ActionableError::kNoError));
  EXPECT_CALL(*store, GetAllLoginsWithAffiliationAndBrandingInformation(_)).WillOnce(
      [&](base::WeakPtr<PasswordStoreConsumer> consumer) {
        consumer->OnGetPasswordStoreResultsOrErrorFrom(store.get(), base::unexpected(
            PasswordStoreBackendError(PasswordStoreBackendErrorType::kUncategorized)));
      });
  auto auth = std::make_unique<testing::NiceMock<device_reauth::MockDeviceAuthenticator>>();
  EXPECT_CALL(*auth, AuthenticateWithMessage(_, _)).Times(0);
  ArchiumLocalPasswordManager manager(&affiliations, store, std::move(auth), base::DoNothing());
  auto metadata = manager.GetMetadata();
  ASSERT_FALSE(metadata.has_value());
  EXPECT_EQ(metadata.error(), Status::kUnavailable);
  base::test::TestFuture<Status, PasswordString> reveal;
  manager.Reveal(1, reveal.GetCallback());
  EXPECT_EQ(reveal.Get<0>(), Status::kUnavailable);
  EXPECT_TRUE(reveal.Get<1>().empty());
}
}  // namespace
}  // namespace password_manager
