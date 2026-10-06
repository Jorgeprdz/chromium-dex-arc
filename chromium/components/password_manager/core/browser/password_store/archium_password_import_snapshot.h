// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef COMPONENTS_PASSWORD_MANAGER_CORE_BROWSER_PASSWORD_STORE_ARCHIUM_PASSWORD_IMPORT_SNAPSHOT_H_
#define COMPONENTS_PASSWORD_MANAGER_CORE_BROWSER_PASSWORD_STORE_ARCHIUM_PASSWORD_IMPORT_SNAPSHOT_H_

#include <cstdint>
#include <vector>

#include "base/functional/callback.h"
#include "base/types/expected.h"
#include "base/unguessable_token.h"
#include "components/password_manager/core/browser/password_store/password_store_backend_error.h"
#include "components/password_manager/core/browser/password_store/stored_credential.h"

namespace password_manager {

// Valid only for a preview owned by this live backend/connection, never persisted.
// total_changes includes this connection's writes, even before observers arrive;
// data_version also detects writes made by other SQLite connections.
struct ArchiumPasswordImportRevision {
  base::UnguessableToken session;
  int64_t total_changes = 0;
  int64_t data_version = 0;
  friend bool operator==(const ArchiumPasswordImportRevision&,
                         const ArchiumPasswordImportRevision&) = default;
};

struct ArchiumPasswordImportSnapshot {
  ArchiumPasswordImportRevision revision;
  std::vector<StoredCredential> credentials;
};

using ArchiumImportSnapshotResult =
    base::expected<ArchiumPasswordImportSnapshot, PasswordStoreBackendError>;
using ArchiumImportSnapshotReply =
    base::OnceCallback<void(ArchiumImportSnapshotResult)>;

}  // namespace password_manager
#endif  // COMPONENTS_PASSWORD_MANAGER_CORE_BROWSER_PASSWORD_STORE_ARCHIUM_PASSWORD_IMPORT_SNAPSHOT_H_
