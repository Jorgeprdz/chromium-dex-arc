// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "components/password_manager/core/browser/import/archium_password_import_preview.h"

#include <utility>
#include <vector>

#include "base/containers/span.h"
#include "base/time/time.h"
#include "components/password_manager/core/browser/password_store/password_form_converters.h"
#include "components/password_manager/core/browser/ui/saved_passwords_presenter.h"
#include "testing/gtest/include/gtest/gtest.h"

namespace password_manager {
namespace {
using AddResult = SavedPasswordsPresenter::AddResult;
using Kind = ArchiumPasswordImportPreview::Kind;
using Decision = ArchiumPasswordImportPreview::Decision;
using Error = ArchiumPasswordImportPreview::Error;

CSVPassword Csv(std::string password = "new", std::string url = "https://example.test/login") {
  return CSVPassword(GURL(url), "user", std::move(password), "", CSVPassword::Status::kOK);
}

StoredCredential Stored(std::string password = "old") {
  return SavedPasswordsPresenter::CreateImportedCredential(CredentialUIEntry(Csv(std::move(password))));
}

ArchiumPasswordImportSnapshot Snapshot() {
  ArchiumPasswordImportSnapshot snapshot;
  snapshot.revision.session = base::UnguessableToken::Create();
  snapshot.revision.total_changes = 7;
  return snapshot;
}

TEST(ArchiumPasswordImportPreviewTest, ReusesNativeAddValidationAcrossStores) {
  std::vector<StoredCredential> stored;
  const CredentialUIEntry incoming(Csv());
  auto evaluate = [&] {
    return SavedPasswordsPresenter::GetExpectedAddResultForStoredCredentials(incoming, stored);
  };
  EXPECT_EQ(evaluate(), AddResult::kSuccess);
  stored.push_back(Stored());
  EXPECT_EQ(evaluate(), AddResult::kConflictInProfileStore);
  stored.back().in_store = PasswordForm::Store::kAccountStore;
  EXPECT_EQ(evaluate(), AddResult::kConflictInAccountStore);
  stored.push_back(Stored());
  EXPECT_EQ(evaluate(), AddResult::kConflictInProfileAndAccountStore);
  stored.push_back(Stored("new"));
  EXPECT_EQ(evaluate(), AddResult::kExactMatch);
  EXPECT_EQ(SavedPasswordsPresenter::GetExpectedAddResultForStoredCredentials(
                CredentialUIEntry(Csv("", "https://example.test/")), stored),
            AddResult::kInvalid);
  EXPECT_EQ(SavedPasswordsPresenter::GetExpectedAddResultForStoredCredentials(
                CredentialUIEntry(Csv("secret", "javascript:alert(1)")), stored),
            AddResult::kInvalid);
  EXPECT_EQ(SavedPasswordsPresenter::GetExpectedAddResultForStoredCredentials(
                CredentialUIEntry(Csv("secret", "https://other.test/")), stored),
            AddResult::kSuccess);
}

TEST(ArchiumPasswordImportPreviewTest, PreviewIsReadOnlyAndCarriesExactRevision) {
  auto snapshot = Snapshot();
  const auto revision = snapshot.revision;
  snapshot.credentials.push_back(Stored());
  const std::vector<CSVPassword> input = {Csv()};
  ArchiumPasswordImportPreview preview(input, std::move(snapshot));
  ASSERT_EQ(preview.rows().size(), 1u);
  EXPECT_EQ(preview.rows()[0].kind, Kind::kConflict);
  EXPECT_EQ(preview.revision(), revision);
  auto skipped = preview.BuildBatch({Decision::kSkip});
  ASSERT_TRUE(skipped.has_value());
  EXPECT_TRUE(skipped->empty());
  auto unresolved = preview.BuildBatch({Decision::kImport});
  ASSERT_FALSE(unresolved.has_value());
  EXPECT_EQ(unresolved.error(), Error::kInvalidDecision);
}

TEST(ArchiumPasswordImportPreviewTest, ExactMatchesAndRepeatedFileRowsAreSkipped) {
  auto snapshot = Snapshot();
  snapshot.credentials.push_back(Stored("new"));
  const std::vector<CSVPassword> input = {Csv(), Csv()};
  ArchiumPasswordImportPreview preview(input, std::move(snapshot));
  EXPECT_EQ(preview.rows()[0].kind, Kind::kExactMatch);
  EXPECT_EQ(preview.rows()[1].kind, Kind::kDuplicateInFile);
  auto batch = preview.BuildBatch({Decision::kImport, Decision::kImport});
  ASSERT_TRUE(batch.has_value());
  EXPECT_TRUE(batch->empty());
}

TEST(ArchiumPasswordImportPreviewTest, DifferentPasswordsInFileNeedOneExplicitChoice) {
  const std::vector<CSVPassword> input = {Csv("first"), Csv("second")};
  ArchiumPasswordImportPreview preview(input, Snapshot());
  EXPECT_EQ(preview.rows()[0].kind, Kind::kConflictInFile);
  EXPECT_EQ(preview.rows()[1].kind, Kind::kConflictInFile);
  auto ambiguous = preview.BuildBatch({Decision::kImport, Decision::kImport});
  ASSERT_FALSE(ambiguous.has_value());
  EXPECT_EQ(ambiguous.error(), Error::kMultipleChoicesForSite);
  auto selected = preview.BuildBatch({Decision::kSkip, Decision::kImport});
  ASSERT_TRUE(selected.has_value());
  ASSERT_EQ(selected->size(), 1u);
  EXPECT_EQ(selected->front().password_value, u"second");
}

TEST(ArchiumPasswordImportPreviewTest,
     ExistingAccountWithMultipleCsvPasswordsRequiresReplaceForChosenRow) {
  auto snapshot = Snapshot();
  snapshot.credentials.push_back(Stored("old"));
  const std::vector<CSVPassword> input = {Csv("first"), Csv("second")};
  ArchiumPasswordImportPreview preview(input, std::move(snapshot));

  ASSERT_EQ(preview.rows().size(), 2u);
  for (const auto& row : preview.rows()) {
    EXPECT_EQ(row.kind, Kind::kConflictInFile);
    EXPECT_EQ(row.identity, "https://example.test/");
    EXPECT_EQ(row.required_decision, Decision::kReplace);
  }

  auto wrong = preview.BuildBatch({Decision::kImport, Decision::kSkip});
  ASSERT_FALSE(wrong.has_value());
  EXPECT_EQ(wrong.error(), Error::kInvalidDecision);

  auto selected = preview.BuildBatch({Decision::kReplace, Decision::kSkip});
  ASSERT_TRUE(selected.has_value());
  ASSERT_EQ(selected->size(), 1u);
  EXPECT_EQ(selected->front().password_value, u"first");
}

TEST(ArchiumPasswordImportPreviewTest,
     DifferentUrlPathsShareOneCanonicalRealmAndOneChoice) {
  const std::vector<CSVPassword> input = {
      Csv("first", "https://example.test/one"),
      Csv("second", "https://example.test/two")};
  ArchiumPasswordImportPreview preview(input, Snapshot());

  ASSERT_EQ(preview.rows().size(), 2u);
  EXPECT_EQ(preview.rows()[0].identity, "https://example.test/");
  EXPECT_EQ(preview.rows()[1].identity, "https://example.test/");
  EXPECT_EQ(preview.rows()[0].kind, Kind::kConflictInFile);
  EXPECT_EQ(preview.rows()[1].kind, Kind::kConflictInFile);

  auto ambiguous = preview.BuildBatch({Decision::kImport, Decision::kImport});
  ASSERT_FALSE(ambiguous.has_value());
  EXPECT_EQ(ambiguous.error(), Error::kMultipleChoicesForSite);
}

TEST(ArchiumPasswordImportPreviewTest, ReplacementPreservesEveryExistingFormAndMetadata) {
  auto snapshot = Snapshot();
  auto first = Stored();
  first.url = GURL("https://example.test/first");
  first.username_element = u"login";
  first.password_element = u"secret";
  first.date_created = base::Time::FromSecondsSinceUnixEpoch(10);
  first.times_used_in_html_form = 12;
  first.SetPasswordNote(u"keep my note");
  auto second = CloneStoredCredential(first);
  second.url = GURL("https://example.test/second");
  second.username_element = u"email";
  snapshot.credentials.push_back(std::move(first));
  snapshot.credentials.push_back(std::move(second));
  const std::vector<CSVPassword> input = {Csv()};
  ArchiumPasswordImportPreview preview(input, std::move(snapshot));
  auto batch = preview.BuildBatch({Decision::kReplace});
  ASSERT_TRUE(batch.has_value());
  ASSERT_EQ(batch->size(), 2u);
  EXPECT_EQ((*batch)[0].url, GURL("https://example.test/first"));
  EXPECT_EQ((*batch)[1].url, GURL("https://example.test/second"));
  EXPECT_EQ((*batch)[0].username_element, u"login");
  EXPECT_EQ((*batch)[1].username_element, u"email");
  for (const auto& entry : *batch) {
    EXPECT_EQ(entry.password_value, u"new");
    EXPECT_EQ(entry.date_created, base::Time::FromSecondsSinceUnixEpoch(10));
    EXPECT_EQ(entry.times_used_in_html_form, 12);
    EXPECT_EQ(entry.GetPasswordNote(), u"keep my note");
    EXPECT_TRUE(entry.password_issues.empty());
  }
}

TEST(ArchiumPasswordImportPreviewTest, RejectsWrongDecisionCountAndAccountSnapshot) {
  const std::vector<CSVPassword> input = {Csv()};
  ArchiumPasswordImportPreview preview(input, Snapshot());
  auto missing = preview.BuildBatch({});
  ASSERT_FALSE(missing.has_value());
  EXPECT_EQ(missing.error(), Error::kInvalidDecision);
  auto snapshot = Snapshot();
  auto account = Stored();
  account.in_store = PasswordForm::Store::kAccountStore;
  snapshot.credentials.push_back(std::move(account));
  ArchiumPasswordImportPreview account_preview(input, std::move(snapshot));
  auto batch = account_preview.BuildBatch({Decision::kReplace});
  ASSERT_FALSE(batch.has_value());
  EXPECT_EQ(batch.error(), Error::kNonLocalSnapshot);
}

TEST(ArchiumPasswordImportPreviewTest, InvalidRowsCannotBeForcedIntoBatch) {
  const std::vector<CSVPassword> input = {Csv(""), Csv("pw", "file:///private")};
  ArchiumPasswordImportPreview preview(input, Snapshot());
  EXPECT_EQ(preview.rows()[0].kind, Kind::kInvalid);
  EXPECT_EQ(preview.rows()[1].kind, Kind::kInvalid);
  auto batch = preview.BuildBatch({Decision::kImport, Decision::kImport});
  ASSERT_FALSE(batch.has_value());
  EXPECT_EQ(batch.error(), Error::kInvalidDecision);
}

TEST(ArchiumPasswordImportPreviewTest, InvalidParsedUrlDoesNotConstructNativeUiCredential) {
  const std::vector<CSVPassword> input = {
      CSVPassword(std::string("not a valid URL"), "user", "secret", "",
                  CSVPassword::Status::kOK),
      CSVPassword(GURL("https://example.test/"), "user", "secret", "",
                  CSVPassword::Status::kSyntaxError)};
  ArchiumPasswordImportPreview preview(input, Snapshot());
  ASSERT_EQ(preview.rows().size(), 2u);
  EXPECT_EQ(preview.rows()[0].kind, Kind::kInvalid);
  EXPECT_EQ(preview.rows()[1].kind, Kind::kInvalid);
  auto skipped = preview.BuildBatch({Decision::kSkip, Decision::kSkip});
  ASSERT_TRUE(skipped.has_value());
  EXPECT_TRUE(skipped->empty());
}

TEST(ArchiumPasswordImportPreviewTest, ChangingPreparedBatchDoesNotChangePreviewSecrets) {
  const std::vector<CSVPassword> input = {Csv()};
  ArchiumPasswordImportPreview preview(input, Snapshot());
  auto first = preview.BuildBatch({Decision::kImport});
  ASSERT_TRUE(first.has_value());
  ASSERT_EQ(first->size(), 1u);
  first->front().password_value = PasswordString(u"changed by caller");
  auto second = preview.BuildBatch({Decision::kImport});
  ASSERT_TRUE(second.has_value());
  ASSERT_EQ(second->size(), 1u);
  EXPECT_EQ(second->front().password_value, u"new");
  EXPECT_EQ(second->front().type, PasswordForm::Type::kImported);
  EXPECT_TRUE(second->front().IsUsingProfileStore());
}
}  // namespace
}  // namespace password_manager
