// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "components/password_manager/core/browser/password_store/password_store_backend.h"

#include <utility>

namespace password_manager {

void PasswordStoreBackend::GetImportSnapshotAsync(
    ArchiumImportSnapshotReply callback) {
  std::move(callback).Run(base::unexpected(PasswordStoreBackendError(
      PasswordStoreBackendErrorType::kUncategorized)));
}

void PasswordStoreBackend::ImportLoginsAtomicallyAsync(
    std::vector<StoredCredential> credentials,
    ArchiumImportChangesReply callback,
    std::optional<ArchiumPasswordImportRevision> expected_revision) {
  std::move(callback).Run(base::unexpected(ArchiumImportFailure::kUnavailable));
}

}  // namespace password_manager
