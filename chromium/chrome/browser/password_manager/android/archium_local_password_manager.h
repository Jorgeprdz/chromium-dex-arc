// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#ifndef CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_LOCAL_PASSWORD_MANAGER_H_
#define CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_LOCAL_PASSWORD_MANAGER_H_

#include <cstdint>
#include <map>
#include <memory>
#include <vector>

#include "base/functional/callback.h"
#include "base/memory/weak_ptr.h"
#include "base/scoped_observation.h"
#include "components/device_reauth/device_authenticator.h"
#include "components/password_manager/core/browser/import/archium_password_import_preview.h"
#include "components/password_manager/core/browser/password_store/password_store_interface.h"
#include "components/password_manager/core/browser/ui/saved_passwords_presenter.h"

namespace password_manager {

// Native manager core. The profile/JNI owner must supply its real local profile
// store and platform DeviceAuthenticator (zero authentication validity period),
// and call Shutdown before that profile or its requesting UI is destroyed.
// No Java authentication-success input or account-store fallback exists here.
class ArchiumLocalPasswordManager : public SavedPasswordsPresenter::Observer {
 public:
  enum class Status {
    kSuccess = 0,
    kUnavailable = 1,
    kAuthenticationFailed = 2,
    kBusy = 3,
    kStale = 4,
    kInvalid = 5,
    kWriteFailed = 6,
  };
  struct Metadata {
    int64_t id;
    GURL url;
    std::u16string username;
  };
  using OperationReply = base::OnceCallback<void(Status)>;
  using SecretReply = base::OnceCallback<void(Status, PasswordString)>;
  using ExportReply = base::OnceCallback<void(Status, std::vector<StoredCredential>)>;
  using PreviewReply = base::OnceCallback<void(Status, std::vector<ArchiumPasswordImportPreview::Row>)>;

  ArchiumLocalPasswordManager(
      affiliations::AffiliationService* affiliations,
      scoped_refptr<PasswordStoreInterface> profile_store,
      std::unique_ptr<device_reauth::DeviceAuthenticator> authenticator,
      base::RepeatingClosure on_changed);
  ~ArchiumLocalPasswordManager() override;

  base::expected<std::vector<Metadata>, Status> GetMetadata();
  void Add(GURL url,
           std::u16string username,
           PasswordString password,
           OperationReply reply);
  void Update(int64_t id,
              std::u16string username,
              PasswordString password,
              OperationReply reply);
  void Delete(int64_t id, OperationReply reply);
  void Reveal(int64_t id, SecretReply reply);
  void Export(ExportReply reply);
  void PreviewImport(std::vector<CSVPassword> rows, PreviewReply reply);
  void ConfirmImport(std::vector<ArchiumPasswordImportPreview::Decision> decisions,
                     OperationReply reply);
  void CancelImport();
  void Shutdown();

 private:
  bool Ready() const;
  void Authenticate(OperationReply reply);
  void OnAuthenticated(OperationReply reply, bool success);
  void VerifyAddedCredential(const GURL& url,
                             const std::u16string& username,
                             const PasswordString& password,
                             OperationReply reply);
  void VerifyUpdatedCredential(const GURL& url,
                               const std::string& signon_realm,
                               const std::u16string& old_username,
                               const std::u16string& username,
                               const PasswordString& password,
                               OperationReply reply);
  void VerifyDeletedCredential(const std::string& signon_realm,
                               const std::u16string& username,
                               OperationReply reply);
  void OnSavedPasswordsChanged(const PasswordStoreChangeList& changes) override;

  scoped_refptr<PasswordStoreInterface> store_;
  std::unique_ptr<device_reauth::DeviceAuthenticator> authenticator_;
  SavedPasswordsPresenter presenter_;
  base::RepeatingClosure on_changed_;
  std::map<int64_t, CredentialUIEntry> entries_;
  int64_t next_id_ = 1;
  uint64_t import_generation_ = 0;
  bool live_ = true;
  bool authenticating_ = false;
  bool writing_ = false;
  std::unique_ptr<ArchiumPasswordImportPreview> preview_;
  base::ScopedObservation<SavedPasswordsPresenter, SavedPasswordsPresenter::Observer> observation_{this};
  base::WeakPtrFactory<ArchiumLocalPasswordManager> weak_ptr_factory_{this};
};

}  // namespace password_manager
#endif  // CHROME_BROWSER_PASSWORD_MANAGER_ANDROID_ARCHIUM_LOCAL_PASSWORD_MANAGER_H_
