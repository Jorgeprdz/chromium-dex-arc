// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "components/password_manager/core/browser/import/archium_password_import_preview.h"

#include <algorithm>
#include <map>
#include <set>
#include <unordered_set>
#include <utility>

#include "base/time/time.h"
#include "base/strings/utf_string_conversions.h"
#include "components/password_manager/core/browser/password_store/password_form_converters.h"

namespace password_manager {
namespace {
using AddResult = SavedPasswordsPresenter::AddResult;
using Decision = ArchiumPasswordImportPreview::Decision;
using Kind = ArchiumPasswordImportPreview::Kind;
using Identity = std::pair<std::string, std::u16string>;

Identity GetIdentity(const CredentialUIEntry& entry) {
  return {entry.GetFirstSignonRealm(), entry.username};
}

Kind GetKind(AddResult result) {
  switch (result) {
    case AddResult::kSuccess:
      return Kind::kNew;
    case AddResult::kExactMatch:
      return Kind::kExactMatch;
    case AddResult::kInvalid:
      return Kind::kInvalid;
    case AddResult::kConflictInProfileStore:
    case AddResult::kConflictInAccountStore:
    case AddResult::kConflictInProfileAndAccountStore:
      return Kind::kConflict;
  }
  return Kind::kInvalid;
}

ArchiumPasswordImportPreview::Decision GetRequiredDecision(AddResult result) {
  switch (result) {
    case AddResult::kSuccess:
    case AddResult::kExactMatch:
      return Decision::kImport;
    case AddResult::kConflictInProfileStore:
      return Decision::kReplace;
    case AddResult::kInvalid:
    case AddResult::kConflictInAccountStore:
    case AddResult::kConflictInProfileAndAccountStore:
      return Decision::kSkip;
  }
  return Decision::kSkip;
}
}  // namespace

ArchiumPasswordImportPreview::ArchiumPasswordImportPreview(
    base::span<const CSVPassword> input,
    ArchiumPasswordImportSnapshot snapshot)
    : snapshot_(std::move(snapshot)) {
  std::map<Identity, std::vector<size_t>> groups;
  entries_.reserve(input.size());
  rows_.reserve(input.size());
  store_results_.reserve(input.size());
  for (const auto& csv : input) {
    // CredentialUIEntry's CSV constructor requires a parsed URL and kOK.
    // Preserve a non-secret invalid row without invoking that constructor.
    if (csv.GetParseStatus() != CSVPassword::Status::kOK || !csv.GetURL()) {
      rows_.push_back({GURL(), base::UTF8ToUTF16(csv.GetUsername()), "",
                       Kind::kInvalid, Decision::kSkip});
      entries_.emplace_back();
      store_results_.push_back(AddResult::kInvalid);
      continue;
    }
    CredentialUIEntry entry(csv);
    AddResult result = SavedPasswordsPresenter::GetExpectedAddResultForStoredCredentials(
        entry, snapshot_.credentials);
    const size_t index = entries_.size();
    rows_.push_back({entry.GetURL(), entry.username,
                     entry.GetFirstSignonRealm(), GetKind(result),
                     GetRequiredDecision(result)});
    store_results_.push_back(result);
    entries_.push_back(std::move(entry));
    if (result != AddResult::kInvalid) {
      groups[GetIdentity(entries_.back())].push_back(index);
    }
  }
  // Resolve canonical site/user identity in native Chromium types, including
  // URLs that differ textually but normalize to the same sign-on realm.
  for (const auto& [identity, indices] : groups) {
    std::vector<size_t> unique;
    std::unordered_set<PasswordString, PasswordString::TransparentHash,
                       PasswordString::TransparentEqual> seen;
    for (size_t index : indices) {
      if (!seen.insert(entries_[index].password).second) {
        rows_[index].kind = Kind::kDuplicateInFile;
      } else {
        unique.push_back(index);
      }
    }
    if (unique.size() > 1) {
      for (size_t index : unique) {
        rows_[index].kind = Kind::kConflictInFile;
      }
    }
  }
}

ArchiumPasswordImportPreview::~ArchiumPasswordImportPreview() = default;

base::expected<std::vector<StoredCredential>, ArchiumPasswordImportPreview::Error>
ArchiumPasswordImportPreview::BuildBatch(
    const std::vector<Decision>& decisions) const {
  if (decisions.size() != rows_.size()) {
    return base::unexpected(Error::kInvalidDecision);
  }
  if (std::ranges::any_of(snapshot_.credentials, [](const auto& entry) {
        return !entry.IsUsingProfileStore() || entry.IsUsingAccountStore();
      })) {
    return base::unexpected(Error::kNonLocalSnapshot);
  }
  std::set<Identity> selected;
  std::vector<StoredCredential> batch;
  for (size_t index = 0; index < rows_.size(); ++index) {
    Decision decision = decisions[index];
    if (decision == Decision::kSkip) {
      continue;
    }
    if (decision != Decision::kImport && decision != Decision::kReplace) {
      return base::unexpected(Error::kInvalidDecision);
    }
    if (rows_[index].kind == Kind::kDuplicateInFile) {
      if (decision != Decision::kImport) {
        return base::unexpected(Error::kInvalidDecision);
      }
      continue;
    }
    const auto& entry = entries_[index];
    AddResult result = store_results_[index];
    if (result == AddResult::kInvalid ||
        (result == AddResult::kSuccess && decision != Decision::kImport) ||
        (result == AddResult::kExactMatch && decision != Decision::kImport) ||
        (result == AddResult::kConflictInProfileStore && decision != Decision::kReplace) ||
        result == AddResult::kConflictInAccountStore ||
        result == AddResult::kConflictInProfileAndAccountStore) {
      return base::unexpected(Error::kInvalidDecision);
    }
    if (!selected.insert(GetIdentity(entry)).second) {
      return base::unexpected(Error::kMultipleChoicesForSite);
    }
    if (result == AddResult::kExactMatch) {
      continue;
    }
    if (result == AddResult::kSuccess) {
      batch.push_back(SavedPasswordsPresenter::CreateImportedCredential(entry));
      continue;
    }
    // Match Chromium's edit behavior: change all actual saved form keys for
    // this site/user, preserving form fields, dates, notes and usage metadata.
    // Never replace them with a CSV-created form with empty element names.
    const size_t previous_size = batch.size();
    for (const auto& existing : snapshot_.credentials) {
      if (existing.signon_realm != entry.GetFirstSignonRealm() ||
          existing.username_value != entry.username || existing.blocked_by_user ||
          existing.federation_origin.IsValid()) {
        continue;
      }
      auto updated = CloneStoredCredential(existing);
      updated.password_value = entry.password;
      updated.date_password_modified = base::Time::Now();
      updated.password_issues.clear();
      batch.push_back(std::move(updated));
    }
    if (batch.size() == previous_size) {
      return base::unexpected(Error::kInvalidDecision);
    }
  }
  return batch;
}

}  // namespace password_manager
