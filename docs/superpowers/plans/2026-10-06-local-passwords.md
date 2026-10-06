# Local Passwords Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Guardar, rellenar, importar y exportar contraseñas locales en Archium Android sin cuenta ni Google Sync.

**Architecture:** PasswordManager y PasswordStore de Chromium conservan matching, captura y prompts. Un backend integrado basado en LoginDatabase usa una clave de datos aleatoria protegida por Android Keystore; una pantalla nativa administra el almacén y el CSV.

**Tech Stack:** Chromium 157, C++/JNI, Java Android, GN, SQLite, Android Keystore y Storage Access Framework.

**Spec:** `docs/superpowers/specs/2026-10-06-archium-local-arc-design.md`.

**Execution:** Inline, preservando el método de la sesión anterior. El usuario aprobó el diseño escrito con «go»; revisar este plan antes de implementar.

## Global Constraints

- Revisión `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`, paquete `app.archium.android`.
- No Google Sync, claves ajenas, root ni CSV personal en pruebas.
- No clave fija, proveedor POSIX como sustituto de Keystore ni CSV como base de datos.
- No anunciar disponibilidad antes de inicializar almacén y cifrado.
- No borrar registros ilegibles ni guardar texto claro ante errores de clave.
- Conservar políticas de incógnito, perfiles, navegación y extensiones.
- Los archivos upstream indicados se preparan en `.source-modified/`, conservando originales exactos en `.source-reference/`; los nuevos se escriben en `chromium/` con su ruta upstream. Generar `patches/archium-desktop.patch` y `patches/upstream-files.json` al integrar.

## Review Focus

- Keystore bloqueado o clave perdida: error recuperable sin borrado ni reemplazo silencioso.
- Orígenes parecidos/iframes: matching existente, sin filtración de contraseñas entre sitios.
- CSV con BOM, comillas, comas, Unicode y saltos de línea: roundtrip correcto.
- Cancelación, duplicados y fallos de escritura: resultado coherente, sin sobrescritura silenciosa.
- Incógnito, reinicio y cambio de perfil: aislamiento y persistencia correctos.

### Task 1: Clave de datos persistente protegida por Keystore

**Files:**
- Create: `chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordKey.java`.
- Create: `chrome/browser/password_manager/android/archium_password_key_provider.{h,cc}`.
- Modify: `chrome/browser/browser_process_impl.cc`.
- Modify: `chrome/browser/password_manager/android/BUILD.gn`.
- Modify: `chrome/browser/BUILD.gn`.
- Modify: `components/password_manager/core/browser/buildflags.gni`, `BUILD.gn`.
- Modify: `config/archium-args.gn` in this preparation repo.
- Test: Android instrumentation `ArchiumPasswordKeyTest.java`; C++ `archium_password_key_provider_unittest.cc`.

**Interfaces:**
- GN argument `enable_archium_local_passwords`, default false; generated `ENABLE_ARCHIUM_LOCAL_PASSWORDS`, enabled in this fork's args.
- Java `ArchiumPasswordKey.getOrCreateDataKey(Context context): byte[]`; throws on unavailable/invalid state, never returns a fallback key.
- C++ `ArchiumPasswordKeyProvider : os_crypt_async::KeyProvider` implements `GetKey(KeyCallback)` and `UseForEncryption()`.
- Produces a 32-byte random DEK with a stable provider tag, `apw1`. The DEK is wrapped with a nonexportable Keystore KEK and the wrapped bytes/nonce/version are persisted atomically. Plaintext DEK exists only in process memory during use.

- [ ] Write tests: two loads return the same DEK; wrapped state lacks plaintext DEK; corrupted nonce/ciphertext and missing KEK fail without creating replacement; locked Keystore is temporary unavailability; concurrent first loads create one persistent state.
- [ ] Run these tests before implementation; expected failure from missing provider/class. Record RED.
- [ ] Implement key lifecycle and JNI bridge, with disk/Keystore work off UI thread and callback returned on originating sequence.
- [ ] Register the provider in `BrowserProcessImpl` under the fork buildflag. The fork must fail closed when this provider is unavailable; prevent OS crypt legacy/plaintext fallback from writing password data.
- [ ] Run instrumentation against Android Keystore and provider unit tests; expected all above cases pass. Isolated javac/stubs do not prove this step.
- [ ] Commit provider, guarded build integration and tests.

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

### Task 3: Save/update and fill on actual login forms

**Files:**
- Modify: `chrome/browser/password_manager/chrome_password_manager_client.cc` only for local availability/UI routing actually needed.
- Modify: Java password-manager Android helpers that gate save/fill on Google backend availability; fetch and audit every touched file against the pinned revision before editing.
- Create: runtime test pages under `tests/runtime/passwords/` with fictitious credentials.
- Test: browser/instrumentation save/update/fill tests against actual PasswordManager paths.

**Interfaces:**
- Consumes the functional profile PasswordStore from Task 2.
- Uses existing `PromptUserToSaveOrUpdatePassword(std::unique_ptr<PasswordFormManagerForUI>, bool)` and native form matching. Do not add a JavaScript password scraper.

- [ ] Write integration tests for a successful login, password update, canceled prompt, blocklisted site, same-origin fill, hostile lookalike origin, cross-origin iframe and incognito policy.
- [ ] Run against the unmodified gating; expected local save/fill fails. Record RED.
- [ ] Route local-capability checks to Task 2 and keep Chromium prompts and matching; remove only Google-specific requirements that block this local implementation.
- [ ] Run tests; expected save/update persist, user cancellation does not write, and no credential is filled into an unrelated origin.
- [ ] Commit integration and tests.

### Task 4: Native management and CSV workflow

**Files:**
- Create: `chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordSettingsFragment.java`.
- Create: `chrome/browser/password_manager/android/java/src/org/chromium/chrome/browser/password_manager/ArchiumPasswordCsv.java`.
- Create: `chrome/browser/password_manager/android/archium_password_manager_bridge.{h,cc}`.
- Modify: corresponding `BUILD.gn`, Android strings/settings entry points, and `ArcDesktopCoordinator` password-settings callback.
- Test: `tests/java/ArchiumPasswordCsvTest.java`; Android UI tests and native import bridge tests.

**Interfaces:**
- `ArchiumPasswordCsv.parse(Reader input): ParseResult`; `write(Writer output, List<Row> rows): void`.
- Row fields `url`, `username`, `password`; ParseResult reports valid rows, line errors and duplicates without logging values.
- Native bridge owns SavedPasswordsPresenter/profile lifecycle; opaque record IDs returned to Java, secrets revealed only after device authentication. List/search does not expose plaintext secrets.
- `previewImport` is read-only; `confirmImport` passes accepted credentials/duplicate decisions to Task 2's atomic import on the original profile.
- Export uses an explicitly chosen SAF URI, authenticated user action and streaming CSV writer; no shared-path/temp-file default.

- [ ] Write Java parser tests: BOM, missing headers, additional columns, empty username, quoted comma, escaped quote, embedded newline, Unicode, malformed quoting and parse/write/parse equivalence.
- [ ] Run RED before implementing parser.
- [ ] Implement CSV parser/writer and preview. Validate URL/realm through Chromium native types before committing credentials; do not invent matching in Java.
- [ ] Write bridge/UI tests: cancellation leaves store unchanged; identical duplicates skip; differing password requires choice; stale preview is rejected/recomputed; write failure rolls back; destroyed profile callback cannot update UI; export cancellation leaves no copy.
- [ ] Implement native settings CRUD, authentication, SAF import/export, atomic commit and summary; explicitly label the store local.
- [ ] Run parser, bridge and UI tests; expected all cases pass.
- [ ] Commit management/import/export and settings routing.

### Task 5: Patch verification and device acceptance

**Files:**
- Modify: `scripts/check-arc-preparation.py`, patch manifests and `docs/arc-preparation.md`.
- Create: `docs/validation/local-passwords-results.md`.

**Interfaces:**
- Produces a pinned, reviewable patch consumable by the integration-build plan.
- Device validation records test fixture identity and observed result, never real secrets.

- [ ] Generate patch and run preparation/application tests. Expected patch hashes, original revision and source compilation checks pass.
- [ ] Run full GN/C++/Java build checks for changed targets through the integration workflow. Expected compilation/link succeeds; no claim based only on stubs.
- [ ] On test APK: import synthetic CSV, login/fill, save/update, CRUD, export/reimport, restart, incognito and key-failure checks. Expected no missing functionality or credential loss.
- [ ] Record limitations and errors honestly. Only then permit personal CSV import by the user and mark local-password functionality accepted.
- [ ] Commit validation report and final patch.
