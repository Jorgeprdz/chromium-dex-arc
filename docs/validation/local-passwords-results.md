# Local passwords — work in progress

This is preparation evidence, not accepted functionality or an APK delivery.

- Pinned source: Chromium 157, cfd94726b7b5fb48aedcc32662f2f3fbdbadec35.
- Actual Android Keystore tests: eight cases and process reopen passed in the
  disposable app.archium.keytests on the physical Samsung Android 36 phone.
  ADB emulator-5554 is another alias for that same phone, not separate coverage.
- Local Python preparation/build routing: 28 tests passed.
- Sparse patch applies and all 54 source hashes match.
- JVM window classification and color/provider routing checks passed.
- Native provider/database/backend/JNI/GN compilation and execution: pending.
- Password save/fill, management screen and CSV integration: pending.
- Locked-device key behavior: pending; no lock/PIN changes performed.

Native database tests written before implementation cover persistence with
ciphertext, reopen, failed second-row insertion and replacement rollback,
missing/wrong key preservation, empty-password failure without encryption,
local helper without Sync, and real asynchronous store notification after commit.
These tests are registered for compilation and artifact preservation; they have
not yet run. No synthetic parser or compiler stub result substitutes for them.

Required runtime startup checks after build/resume:

1. Launch a regular profile and load a login fixture without a Google backend.
2. Verify the local store initializes and its errors gate saving/filling.
3. Verify PASSWORDS and password-sharing Sync controllers are not registered
   for the local-vault fork; other browser controllers remain upstream.
4. Change account/Sync state with synthetic credentials only; no local row loss
   or upload. Preserve the account backend's genuine Google capability reporting.
5. Import a fixture, restart, save/update/fill, manage/export/reimport, verify
   incognito and key-failure behavior. Do not use the personal CSV for testing.

The final run has not been dispatched. After dispatch, update the monitors with
its actual ID and pause as requested; installation/runtime checks wait for resume.
