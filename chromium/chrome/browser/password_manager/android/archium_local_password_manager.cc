// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "chrome/browser/password_manager/android/archium_local_password_manager.h"

#include <algorithm>
#include <utility>

#include "base/functional/bind.h"
#include "base/location.h"
#include "base/task/thread_pool.h"
#include "components/password_manager/core/browser/password_store/actionable_error.h"

namespace password_manager {

ArchiumLocalPasswordManager::ArchiumLocalPasswordManager(
    affiliations::AffiliationService* affiliations,
    scoped_refptr<PasswordStoreInterface> profile_store,
    std::unique_ptr<device_reauth::DeviceAuthenticator> authenticator,
    base::RepeatingClosure on_changed)
    : store_(std::move(profile_store)),
      authenticator_(std::move(authenticator)),
      presenter_(affiliations, store_, /*account_store=*/nullptr),
      on_changed_(std::move(on_changed)) {
  observation_.Observe(&presenter_);
  presenter_.Init();
}

ArchiumLocalPasswordManager::~ArchiumLocalPasswordManager() { Shutdown(); }

bool ArchiumLocalPasswordManager::Ready() const {
  return live_ && store_ && store_->GetError() == ActionableError::kNoError &&
         !presenter_.IsWaitingForPasswordStore() && !presenter_.HasPasswordStoreReadError();
}

base::expected<std::vector<ArchiumLocalPasswordManager::Metadata>, ArchiumLocalPasswordManager::Status>
ArchiumLocalPasswordManager::GetMetadata() {
  if (!Ready()) return base::unexpected(Status::kUnavailable);
  entries_.clear();
  std::vector<Metadata> metadata;
  for (auto& entry : presenter_.GetSavedPasswords()) {
    const int64_t id = next_id_++;
    metadata.push_back({id, entry.GetURL(), entry.username});
    entries_.emplace(id, std::move(entry));
  }
  return metadata;
}

void ArchiumLocalPasswordManager::Authenticate(OperationReply reply) {
  if (!Ready()) { std::move(reply).Run(Status::kUnavailable); return; }
  if (authenticating_ || writing_) { std::move(reply).Run(Status::kBusy); return; }
  if (!authenticator_ || !authenticator_->CanAuthenticateWithBiometricOrScreenLock()) {
    std::move(reply).Run(Status::kAuthenticationFailed);
    return;
  }
  authenticating_ = true;
  authenticator_->AuthenticateWithMessage(
      std::u16string(), base::BindOnce(&ArchiumLocalPasswordManager::OnAuthenticated,
                                     weak_ptr_factory_.GetWeakPtr(), std::move(reply)));
}

void ArchiumLocalPasswordManager::OnAuthenticated(OperationReply reply, bool success) {
  authenticating_ = false;
  std::move(reply).Run(!success ? Status::kAuthenticationFailed
                              : Ready() ? Status::kSuccess : Status::kUnavailable);
}

void ArchiumLocalPasswordManager::Reveal(int64_t id, SecretReply reply) {
  Authenticate(base::BindOnce(
      [](base::WeakPtr<ArchiumLocalPasswordManager> self, int64_t id, SecretReply reply, Status status) {
        if (!self) return;
        if (status != Status::kSuccess) { std::move(reply).Run(status, PasswordString()); return; }
        auto found = self->entries_.find(id);
        if (found == self->entries_.end()) {
          std::move(reply).Run(Status::kStale, PasswordString());
          return;
        }
        std::move(reply).Run(Status::kSuccess, found->second.password);
      }, weak_ptr_factory_.GetWeakPtr(), id, std::move(reply)));
}

void ArchiumLocalPasswordManager::Export(ExportReply reply) {
  Authenticate(base::BindOnce(
      [](base::WeakPtr<ArchiumLocalPasswordManager> self, ExportReply reply, Status status) {
        if (!self) return;
        if (status != Status::kSuccess) { std::move(reply).Run(status, {}); return; }
        self->store_->GetImportSnapshot(base::BindOnce(
            [](base::WeakPtr<ArchiumLocalPasswordManager> self, ExportReply reply,
               ArchiumImportSnapshotResult snapshot) {
              if (!self) return;
              if (!snapshot || !self->Ready()) { std::move(reply).Run(Status::kUnavailable, {}); return; }
              std::erase_if(snapshot->credentials, [](const StoredCredential& entry) {
                return entry.blocked_by_user || entry.federation_origin.IsValid() || entry.password_value.empty();
              });
              std::move(reply).Run(Status::kSuccess, std::move(snapshot->credentials));
            }, self, std::move(reply)));
      }, weak_ptr_factory_.GetWeakPtr(), std::move(reply)));
}

void ArchiumLocalPasswordManager::PreviewImport(std::vector<CSVPassword> rows, PreviewReply reply) {
  CancelImport();
  const uint64_t generation = import_generation_;
  Authenticate(base::BindOnce(
      [](base::WeakPtr<ArchiumLocalPasswordManager> self, uint64_t generation,
         std::vector<CSVPassword> rows, PreviewReply reply, Status status) {
        if (!self) return;
        if (status != Status::kSuccess) { std::move(reply).Run(status, {}); return; }
        if (generation != self->import_generation_) { std::move(reply).Run(Status::kStale, {}); return; }
        self->store_->GetImportSnapshot(base::BindOnce(
            [](base::WeakPtr<ArchiumLocalPasswordManager> self, uint64_t generation,
               std::vector<CSVPassword> rows, PreviewReply reply, ArchiumImportSnapshotResult snapshot) {
              if (!self) return;
              if (!snapshot || !self->Ready()) { std::move(reply).Run(Status::kUnavailable, {}); return; }
              if (generation != self->import_generation_) { std::move(reply).Run(Status::kStale, {}); return; }
              base::ThreadPool::PostTaskAndReplyWithResult(
                  FROM_HERE, {base::TaskPriority::USER_VISIBLE},
                  base::BindOnce([](std::vector<CSVPassword> rows, ArchiumPasswordImportSnapshot snapshot) {
                    return std::make_unique<ArchiumPasswordImportPreview>(rows, std::move(snapshot));
                  }, std::move(rows), std::move(*snapshot)),
                  base::BindOnce([](base::WeakPtr<ArchiumLocalPasswordManager> self,
                                    uint64_t generation, PreviewReply reply,
                                    std::unique_ptr<ArchiumPasswordImportPreview> preview) {
                    if (!self) return;
                    if (!self->Ready() || generation != self->import_generation_) {
                      std::move(reply).Run(Status::kStale, {});
                      return;
                    }
                    self->preview_ = std::move(preview);
                    std::move(reply).Run(Status::kSuccess, self->preview_->rows());
                  }, self, generation, std::move(reply)));
            }, self, generation, std::move(rows), std::move(reply)));
      }, weak_ptr_factory_.GetWeakPtr(), generation, std::move(rows), std::move(reply)));
}

void ArchiumLocalPasswordManager::ConfirmImport(
    std::vector<ArchiumPasswordImportPreview::Decision> decisions, OperationReply reply) {
  if (!preview_) { std::move(reply).Run(Status::kStale); return; }
  const uint64_t generation = import_generation_;
  Authenticate(base::BindOnce(
      [](base::WeakPtr<ArchiumLocalPasswordManager> self, uint64_t generation,
         std::vector<ArchiumPasswordImportPreview::Decision> decisions, OperationReply reply, Status status) {
        if (!self) return;
        if (status != Status::kSuccess) { std::move(reply).Run(status); return; }
        if (generation != self->import_generation_ || !self->preview_) {
          std::move(reply).Run(Status::kStale);
          return;
        }
        auto batch = self->preview_->BuildBatch(decisions);
        if (!batch) { std::move(reply).Run(Status::kInvalid); return; }
        const auto revision = self->preview_->revision();
        self->preview_.reset();
        if (batch->empty()) { std::move(reply).Run(Status::kSuccess); return; }
        self->writing_ = true;
        self->store_->ImportLoginsAtomically(std::move(*batch), base::BindOnce(
            [](base::WeakPtr<ArchiumLocalPasswordManager> self, OperationReply reply,
               base::expected<void, PasswordStoreBackendError> result) {
              if (!self) return;
              self->writing_ = false;
              std::move(reply).Run(result ? Status::kSuccess : Status::kWriteFailed);
            }, self, std::move(reply)), revision);
      }, weak_ptr_factory_.GetWeakPtr(), generation, std::move(decisions), std::move(reply)));
}

void ArchiumLocalPasswordManager::CancelImport() {
  ++import_generation_;
  preview_.reset();
}

void ArchiumLocalPasswordManager::OnSavedPasswordsChanged(const PasswordStoreChangeList& changes) {
  if (!live_) return;
  entries_.clear();
  CancelImport();
  if (on_changed_) on_changed_.Run();
}

void ArchiumLocalPasswordManager::Shutdown() {
  if (!live_) return;
  live_ = false;
  weak_ptr_factory_.InvalidateWeakPtrs();
  observation_.Reset();
  entries_.clear();
  CancelImport();
  on_changed_.Reset();
  if (authenticating_ && authenticator_) authenticator_->Cancel();
  authenticating_ = false;
}

}  // namespace password_manager
