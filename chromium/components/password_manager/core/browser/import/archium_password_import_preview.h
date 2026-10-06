// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef COMPONENTS_PASSWORD_MANAGER_CORE_BROWSER_IMPORT_ARCHIUM_PASSWORD_IMPORT_PREVIEW_H_
#define COMPONENTS_PASSWORD_MANAGER_CORE_BROWSER_IMPORT_ARCHIUM_PASSWORD_IMPORT_PREVIEW_H_

#include <string>
#include <vector>

#include "base/containers/span.h"
#include "base/types/expected.h"
#include "components/password_manager/core/browser/import/csv_password.h"
#include "components/password_manager/core/browser/password_store/archium_password_import_snapshot.h"
#include "components/password_manager/core/browser/ui/credential_ui_entry.h"
#include "components/password_manager/core/browser/ui/saved_passwords_presenter.h"

namespace password_manager {

// A read-only, local-profile preview. Row metadata may be sent to the UI;
// passwords stay in the native entries and are never included in Row.
// The owner must authenticate confirmation and submit BuildBatch's output with
// revision() to ApplyImportedLogins. A changed DB revision rejects the entire
// transaction; BuildBatch itself never performs a write.
class ArchiumPasswordImportPreview {
 public:
  enum class Kind {
    kNew = 0,
    kExactMatch = 1,
    kConflict = 2,
    kInvalid = 3,
    kDuplicateInFile = 4,
    kConflictInFile = 5,
  };
  enum class Decision { kSkip = 0, kImport = 1, kReplace = 2 };
  enum class Error {
    kInvalidDecision,
    kMultipleChoicesForSite,
    kNonLocalSnapshot,
  };
  struct Row {
    GURL url;
    std::u16string username;
    // Canonical Chromium identity used by BuildBatch. The UI must never
    // reimplement realm canonicalization from the display URL.
    std::string identity;
    Kind kind;
    // The only non-skip decision that BuildBatch accepts for this row.
    Decision required_decision;
  };

  ArchiumPasswordImportPreview(base::span<const CSVPassword> input,
                              ArchiumPasswordImportSnapshot snapshot);
  ~ArchiumPasswordImportPreview();
  ArchiumPasswordImportPreview(const ArchiumPasswordImportPreview&) = delete;
  ArchiumPasswordImportPreview& operator=(const ArchiumPasswordImportPreview&) = delete;

  const std::vector<Row>& rows() const { return rows_; }
  const ArchiumPasswordImportRevision& revision() const {
    return snapshot_.revision;
  }
  base::expected<std::vector<StoredCredential>, Error> BuildBatch(
      const std::vector<Decision>& decisions) const;

 private:
  ArchiumPasswordImportSnapshot snapshot_;
  std::vector<Row> rows_;
  std::vector<CredentialUIEntry> entries_;
  std::vector<SavedPasswordsPresenter::AddResult> store_results_;
};

}  // namespace password_manager
#endif  // COMPONENTS_PASSWORD_MANAGER_CORE_BROWSER_IMPORT_ARCHIUM_PASSWORD_IMPORT_PREVIEW_H_
