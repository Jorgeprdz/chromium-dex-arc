### Task 2: Functional profile password backend

**Files:**
- Modify: `components/password_manager/core/browser/password_store/BUILD.gn`.
- Modify: `components/password_manager/core/browser/password_store_factory_util.{h,cc}`.
- Modify: `components/password_manager/core/browser/password_store/login_database.{h,cc}` and `login_database_async_helper.{h,cc}` only where the fork needs Android support or atomic import.
- Modify: `chrome/browser/password_manager/factories/password_store_backend_factory.cc`.
- Modify: `chrome/browser/password_manager/factories/profile_password_store_factory.cc`.
- Modify: `chrome/browser/password_manager/android/password_manager_android_util.{h,cc}`.
- Modify: `chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/PasswordManagerUtilBridge.java`.
- Test: C++ backend/factory tests with real temporary LoginDatabase and test encryptor, plus Android runtime integration.

**Interfaces:**
- Consumes `ENABLE_ARCHIUM_LOCAL_PASSWORDS` and the verified `apw1` encryptor from Task 1.
- Produces a functional profile `PasswordStoreInterface` through existing `ProfilePasswordStoreFactory::GetForProfile`.
- Preserve existing account backend behavior, but do not select/use it for local save/import. Local availability must not pretend `isInternalBackendPresent()` is true.
- `LoginDatabase::ApplyImportedLogins(const std::vector<StoredCredential>& credentials): base::expected<PasswordStoreChangeList, PasswordStoreBackendError>` commits one transaction or returns failure with no changes. Wire through async helper/backend on the existing DB sequence; notify PasswordStore observers only after commit.

- [ ] Write tests: profile factory with fork flag gets persistent backend; flag off preserves upstream choice; database contains encrypted password bytes; reopened store decrypts; failed encryptor prevents writes; missing/corrupt key does not clear entries; account/Syncless state cannot clear local credentials.
- [ ] Run and observe RED. Also exercise atomic import with injected failure after the first row; expected zero committed rows.
- [ ] Enable built-in backend sources under the fork buildflag, including required affiliation and async helper dependencies. Adapt `CreateLoginDatabase` with undecryptable-record deletion disabled for the fork.
- [ ] Instantiate built-in profile backend with the affiliation service and Task 1's verified encryption. Integrate capability/error checks without changing Google backend reporting.
- [ ] Implement transactional batch insertion/update and async observer propagation.
- [ ] Run tests; expected persistence, fail-closed behavior, unchanged upstream flag-off behavior and atomicity pass. Inspect GN dependencies in a full pinned checkout before completion.
- [ ] Commit backend and tests.
