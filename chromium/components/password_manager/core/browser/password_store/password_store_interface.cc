// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "components/password_manager/core/browser/password_store/password_store_interface.h"

#include <utility>

namespace password_manager {

void PasswordStoreInterface::GetImportSnapshot(
    ArchiumImportSnapshotReply callback) {
  std::move(callback).Run(base::unexpected(PasswordStoreBackendError(
      PasswordStoreBackendErrorType::kUncategorized)));
}

void PasswordStoreInterface::ImportLoginsAtomically(
    std::vector<StoredCredential> credentials,
    ImportCompletion completion,
    std::optional<ArchiumPasswordImportRevision> expected_revision) {
  std::move(completion).Run(base::unexpected(PasswordStoreBackendError(
      PasswordStoreBackendErrorType::kUncategorized)));
}

}  // namespace password_manager
