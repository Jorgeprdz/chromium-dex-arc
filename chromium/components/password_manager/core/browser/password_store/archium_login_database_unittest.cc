// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "components/password_manager/core/browser/password_store/login_database.h"

#include <utility>

#include "base/files/scoped_temp_dir.h"
#include "base/functional/callback_helpers.h"
#include "base/functional/bind.h"
#include "base/test/task_environment.h"
#include "base/test/test_future.h"
#include "components/password_manager/core/browser/password_store/password_store.h"
#include "components/password_manager/core/browser/password_store/password_store_built_in_backend.h"
#include "components/password_manager/core/common/password_manager_pref_names.h"
#include "components/prefs/testing_pref_service.h"
#include "base/task/sequenced_task_runner.h"
#include "components/password_manager/core/browser/password_store/login_database_async_helper.h"
#include "components/os_crypt/async/browser/test_utils.h"
#include "components/password_manager/core/browser/password_store_factory_util.h"
#include "components/password_manager/core/browser/password_string.h"
#include "components/password_manager/core/browser/affiliation/affiliated_match_helper.h"
#include "components/sync/model/data_type_controller_delegate.h"
#include "sql/database.h"
#include "sql/statement.h"
#include "sql/test/test_helpers.h"
#include "testing/gtest/include/gtest/gtest.h"

namespace password_manager {
namespace {

StoredCredential Credential(std::string host, std::u16string password) {
  StoredCredential cred;
  cred.url = GURL("https://" + host + "/login");
  cred.signon_realm = "https://" + host + "/";
  cred.username_value = u"synthetic-user";
  cred.password_value = PasswordString(std::move(password));
  return cred;
}

class ArchiumLoginDatabaseTest : public testing::Test {
 protected:
  void SetUp() override {
    ASSERT_TRUE(directory_.CreateUniqueTempDir());
    encryptor_ = os_crypt_async::GetTestEncryptorForTesting();
    db_ = CreateLoginDatabase(kProfileStore, directory_.GetPath(), nullptr);
    path_ = db_->db_path();
    ASSERT_TRUE(db_->Init(base::NullCallback(), encryptor_));
  }

  void TearDown() override {
    if (store_) {
      store_->ShutdownOnUIThread();
      task_environment_.RunUntilIdle();
      store_.reset();
    }
  }

  void OpenStore(bool key_available = true) {
    db_.reset();
    prefs_.registry()->RegisterBooleanPref(prefs::kClearingUndecryptablePasswords,
                                          false);
    if (key_available) {
      crypt_ = os_crypt_async::GetTestOSCryptAsyncForTesting();
    } else {
      crypt_ = std::make_unique<os_crypt_async::OSCryptAsync>(
          std::vector<std::pair<os_crypt_async::OSCryptAsync::Precedence,
                               std::unique_ptr<os_crypt_async::KeyProvider>>>{});
    }
    store_ = base::MakeRefCounted<PasswordStore>(
        std::make_unique<PasswordStoreBuiltInBackend>(
            CreateLoginDatabase(kProfileStore, directory_.GetPath(), &prefs_),
            syncer::WipeModelUponSyncDisabledBehavior::kNever, &prefs_,
            crypt_.get(), nullptr));
    store_->Init();
  }

  void Reopen(scoped_refptr<os_crypt_async::Encryptor> encryptor) {
    db_.reset();
    db_ = CreateLoginDatabase(kProfileStore, directory_.GetPath(), nullptr);
    ASSERT_TRUE(db_->Init(base::NullCallback(), std::move(encryptor)));
  }

  int RowCount() {
    sql::Database inspect(sql::test::kTestTag);
    EXPECT_TRUE(inspect.Open(path_));
    sql::Statement count(inspect.GetUniqueStatement("SELECT COUNT(*) FROM logins"));
    EXPECT_TRUE(count.Step());
    return count.ColumnInt(0);
  }

  base::test::TaskEnvironment task_environment_;
  base::ScopedTempDir directory_;
  base::FilePath path_;
  scoped_refptr<os_crypt_async::Encryptor> encryptor_;
  std::unique_ptr<LoginDatabase> db_;
  TestingPrefServiceSimple prefs_;
  std::unique_ptr<os_crypt_async::OSCryptAsync> crypt_;
  scoped_refptr<PasswordStore> store_;
};

TEST_F(ArchiumLoginDatabaseTest, StaleImportPreviewCannotOverwriteLaterWebSave) {
  auto snapshot = db_->GetImportSnapshot();
  ASSERT_TRUE(snapshot.has_value());
  ASSERT_TRUE(snapshot->credentials.empty());
  auto web_save = db_->AddLogin(Credential("later.example", u"web-secret"));
  ASSERT_FALSE(web_save.empty());
  std::vector<StoredCredential> imported;
  imported.push_back(Credential("later.example", u"csv-secret"));
  auto result = db_->ApplyImportedLogins(imported, snapshot->revision);
  EXPECT_FALSE(result.has_value());
  std::vector<StoredCredential> actual;
  ASSERT_EQ(FormRetrievalResult::kSuccess, db_->GetAllLogins(&actual));
  ASSERT_EQ(1u, actual.size());
  EXPECT_EQ(u"web-secret", actual[0].password_value.value());
}

TEST_F(ArchiumLoginDatabaseTest, SnapshotReadDoesNotInvalidatePreviewAndCommitDoes) {
  auto first = db_->GetImportSnapshot();
  ASSERT_TRUE(first.has_value());
  auto second = db_->GetImportSnapshot();
  ASSERT_TRUE(second.has_value());
  EXPECT_EQ(first->revision, second->revision);
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("one.example", u"import-secret"));
  ASSERT_TRUE(db_->ApplyImportedLogins(rows, first->revision).has_value());
  std::vector<StoredCredential> later;
  later.push_back(Credential("two.example", u"second-secret"));
  EXPECT_FALSE(db_->ApplyImportedLogins(later, second->revision).has_value());
  EXPECT_EQ(1, RowCount());
}

TEST_F(ArchiumLoginDatabaseTest, ImportPreviewCannotBeReplayedOnReopenedDatabase) {
  auto snapshot = db_->GetImportSnapshot();
  ASSERT_TRUE(snapshot.has_value());
  Reopen(encryptor_);
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("one.example", u"synthetic-secret"));
  EXPECT_FALSE(db_->ApplyImportedLogins(rows, snapshot->revision).has_value());
  EXPECT_EQ(0, RowCount());
}

TEST_F(ArchiumLoginDatabaseTest, OtherConnectionWriteInvalidatesImportPreview) {
  ASSERT_FALSE(db_->AddLogin(Credential("one.example", u"original-secret")).empty());
  auto snapshot = db_->GetImportSnapshot();
  ASSERT_TRUE(snapshot.has_value());
  {
    sql::Database external(sql::test::kTestTag);
    ASSERT_TRUE(external.Open(path_));
    ASSERT_TRUE(external.Execute("UPDATE logins SET times_used = times_used + 1"));
  }
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("two.example", u"import-secret"));
  EXPECT_FALSE(db_->ApplyImportedLogins(rows, snapshot->revision).has_value());
  EXPECT_EQ(1, RowCount());
}

TEST_F(ArchiumLoginDatabaseTest, AtomicImportPersistsEncryptedPasswordsAfterReopen) {
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("one.example", u"synthetic-secret-1"));
  rows.push_back(Credential("two.example", u"synthetic-secret-2"));
  auto result = db_->ApplyImportedLogins(rows);
  ASSERT_TRUE(result.has_value());
  EXPECT_EQ(2u, result->size());
  db_.reset();
  {
    sql::Database inspect(sql::test::kTestTag);
    ASSERT_TRUE(inspect.Open(path_));
    sql::Statement query(inspect.GetUniqueStatement(
        "SELECT password_value FROM logins ORDER BY signon_realm"));
    ASSERT_TRUE(query.Step());
    std::string blob = query.ColumnString(0);
    EXPECT_NE(std::string::npos, blob.find(os_crypt_async::kDefaultTestKeyPrefix));
    EXPECT_EQ(std::string::npos, blob.find("synthetic-secret-1"));
    std::u16string decrypted;
    ASSERT_TRUE(encryptor_->DecryptString16(blob, &decrypted));
    EXPECT_EQ(u"synthetic-secret-1", decrypted);
  }
  Reopen(encryptor_);
  std::vector<StoredCredential> found;
  ASSERT_EQ(FormRetrievalResult::kSuccess, db_->GetAllLogins(&found));
  ASSERT_EQ(2u, found.size());
  EXPECT_EQ(u"synthetic-secret-1", found[0].password_value.value());
  EXPECT_EQ(u"synthetic-secret-2", found[1].password_value.value());
}

TEST_F(ArchiumLoginDatabaseTest, FailedSecondRowRollsBackFirstInsert) {
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("one.example", u"synthetic-secret"));
  rows.push_back(Credential("two.example", u"other-secret"));
  rows.back().signon_realm.clear();
  EXPECT_FALSE(db_->ApplyImportedLogins(rows).has_value());
  EXPECT_EQ(0, RowCount());
}

TEST_F(ArchiumLoginDatabaseTest, FailedSecondRowRollsBackReplacement) {
  auto existing = Credential("one.example", u"original-secret");
  ASSERT_FALSE(db_->AddLogin(CloneStoredCredential(existing)).empty());
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("one.example", u"replacement-secret"));
  rows.push_back(Credential("invalid.example", u"other-secret"));
  rows.back().signon_realm.clear();
  EXPECT_FALSE(db_->ApplyImportedLogins(rows).has_value());
  Reopen(encryptor_);
  std::vector<StoredCredential> found;
  ASSERT_EQ(FormRetrievalResult::kSuccess, db_->GetAllLogins(&found));
  ASSERT_EQ(1u, found.size());
  EXPECT_EQ(u"original-secret", found[0].password_value.value());
}

TEST_F(ArchiumLoginDatabaseTest, MissingKeyDoesNotDeleteAndRecoveryDecryptsAgain) {
  ASSERT_FALSE(db_->AddLogin(Credential("one.example", u"synthetic-secret")).empty());
  Reopen(os_crypt_async::GetTestEncryptorWithoutKeysForTesting());
  std::vector<StoredCredential> found;
  EXPECT_NE(FormRetrievalResult::kSuccess, db_->GetAllLogins(&found));
  EXPECT_EQ(1, RowCount());
  EXPECT_TRUE(db_->AddLogin(Credential("two.example", u"secret")).empty());
  EXPECT_TRUE(db_->AddLogin(Credential("empty.example", u"")).empty());
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("three.example", u"secret"));
  EXPECT_FALSE(db_->ApplyImportedLogins(rows).has_value());
  EXPECT_EQ(1, RowCount());
  Reopen(encryptor_);
  ASSERT_EQ(FormRetrievalResult::kSuccess, db_->GetAllLogins(&found));
  ASSERT_EQ(1u, found.size());
  EXPECT_EQ(u"synthetic-secret", found[0].password_value.value());
}

TEST_F(ArchiumLoginDatabaseTest, WrongKeyDoesNotDeleteUnreadableCredentials) {
  ASSERT_FALSE(db_->AddLogin(Credential("one.example", u"synthetic-secret")).empty());
  Reopen(os_crypt_async::GetTestEncryptorForTesting());
  std::vector<StoredCredential> found;
  EXPECT_NE(FormRetrievalResult::kSuccess, db_->GetAllLogins(&found));
  EXPECT_EQ(1, RowCount());
  Reopen(encryptor_);
  ASSERT_EQ(FormRetrievalResult::kSuccess, db_->GetAllLogins(&found));
  ASSERT_EQ(1u, found.size());
}

TEST_F(ArchiumLoginDatabaseTest, EmptyBatchChangesNothing) {
  auto result = db_->ApplyImportedLogins({});
  ASSERT_TRUE(result.has_value());
  EXPECT_TRUE(result->empty());
  EXPECT_EQ(0, RowCount());
}

TEST_F(ArchiumLoginDatabaseTest, LocalHelperDoesNotCreateSyncDelegate) {
  db_.reset();
  LoginDatabaseAsyncHelper helper(
      CreateLoginDatabase(kProfileStore, directory_.GetPath(), nullptr),
      base::SequencedTaskRunner::GetCurrentDefault(),
      syncer::WipeModelUponSyncDisabledBehavior::kNever);
  helper.CreateSyncBackend();
  EXPECT_FALSE(helper.GetSyncControllerDelegate());
  ASSERT_TRUE(helper.Initialize(base::NullCallback(), base::NullCallback(),
                                base::NullCallback(), encryptor_));
  std::vector<StoredCredential> rows;
  rows.push_back(Credential("one.example", u"synthetic-secret"));
  auto result = helper.ImportLoginsAtomically(std::move(rows));
  ASSERT_TRUE(result.has_value());
  ASSERT_TRUE(result->has_value());
  EXPECT_EQ(1u, result->value().size());
  EXPECT_EQ(1, RowCount());
}

class CommittedRowsObserver : public PasswordStoreInterface::Observer {
 public:
  explicit CommittedRowsObserver(base::FilePath path) : path_(std::move(path)) {}
  void OnLoginsChanged(PasswordStoreInterface*,
                       const PasswordStoreChangeList&) override {
    sql::Database inspect(sql::test::kTestTag);
    ASSERT_TRUE(inspect.Open(path_));
    sql::Statement count(inspect.GetUniqueStatement("SELECT COUNT(*) FROM logins"));
    ASSERT_TRUE(count.Step());
    committed_counts.push_back(count.ColumnInt(0));
  }
  void OnLoginsRetained(PasswordStoreInterface*,
                       const std::vector<StoredCredential>&) override {
    ADD_FAILURE() << "Atomic import must provide committed changes";
  }
  std::vector<int> committed_counts;

 private:
  base::FilePath path_;
};

TEST_F(ArchiumLoginDatabaseTest, InitializedDatabaseWithoutKeyIsNotAvailable) {
  OpenStore(/* key_available= */ false);
  // The snapshot callback runs after backend initialization, so this checks the
  // ready-state result rather than just the initial "not initialized" state.
  base::test::TestFuture<ArchiumImportSnapshotResult> initialized;
  store_->GetImportSnapshot(initialized.GetCallback());
  EXPECT_FALSE(initialized.Take().has_value());
  EXPECT_NE(ActionableError::kNoError, store_->GetError());
  EXPECT_EQ(0, RowCount());
}

TEST_F(ArchiumLoginDatabaseTest, AsyncSnapshotQueuesAndRejectsSubsequentWebSave) {
  OpenStore();
  base::test::TestFuture<ArchiumImportSnapshotResult> preview;
  store_->GetImportSnapshot(preview.GetCallback());
  auto snapshot = preview.Take();
  ASSERT_TRUE(snapshot.has_value());
  EXPECT_TRUE(snapshot->credentials.empty());
  store_->AddLogin(Credential("one.example", u"web-secret"));
  std::vector<StoredCredential> imported;
  imported.push_back(Credential("one.example", u"csv-secret"));
  base::test::TestFuture<base::expected<void, PasswordStoreBackendError>> result;
  store_->ImportLoginsAtomically(std::move(imported), result.GetCallback(),
                                 snapshot->revision);
  EXPECT_FALSE(result.Take().has_value());
  base::test::TestFuture<ArchiumImportSnapshotResult> current;
  store_->GetImportSnapshot(current.GetCallback());
  auto actual = current.Take();
  ASSERT_TRUE(actual.has_value());
  ASSERT_EQ(1u, actual->credentials.size());
  EXPECT_EQ(u"web-secret", actual->credentials[0].password_value.value());
}

TEST_F(ArchiumLoginDatabaseTest, ShutdownDropsPendingSnapshotReply) {
  OpenStore();
  bool replied = false;
  store_->GetImportSnapshot(base::BindOnce(
      [](bool* replied, ArchiumImportSnapshotResult) { *replied = true; },
      &replied));
  store_->ShutdownOnUIThread();
  task_environment_.RunUntilIdle();
  EXPECT_FALSE(replied);
  store_.reset();
}

TEST_F(ArchiumLoginDatabaseTest, AsyncStoreNotifiesOnlyAfterCompleteCommit) {
  OpenStore();
  CommittedRowsObserver observer(path_);
  store_->AddObserver(&observer);
  std::vector<StoredCredential> invalid;
  invalid.push_back(Credential("one.example", u"synthetic-secret"));
  invalid.push_back(Credential("invalid.example", u"other-secret"));
  invalid.back().signon_realm.clear();
  base::test::TestFuture<base::expected<void, PasswordStoreBackendError>> failed;
  // Request before initialization finishes: it must queue and return an error.
  store_->ImportLoginsAtomically(std::move(invalid), failed.GetCallback());
  EXPECT_FALSE(failed.Take().has_value());
  EXPECT_TRUE(observer.committed_counts.empty());
  EXPECT_EQ(0, RowCount());
  EXPECT_FALSE(store_->CreateSyncControllerDelegate());

  std::vector<StoredCredential> valid;
  valid.push_back(Credential("one.example", u"synthetic-secret"));
  valid.push_back(Credential("two.example", u"other-secret"));
  base::test::TestFuture<base::expected<void, PasswordStoreBackendError>> committed;
  store_->ImportLoginsAtomically(std::move(valid), committed.GetCallback());
  EXPECT_TRUE(committed.Take().has_value());
  ASSERT_EQ(1u, observer.committed_counts.size());
  EXPECT_EQ(2, observer.committed_counts.front());
  EXPECT_EQ(2, RowCount());
  store_->RemoveObserver(&observer);
}

}  // namespace
}  // namespace password_manager
