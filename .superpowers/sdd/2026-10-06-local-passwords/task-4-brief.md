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
