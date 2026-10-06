# Local passwords — work in progress

This is preparation evidence, not accepted functionality or an APK delivery.

- Pinned source: Chromium 157, cfd94726b7b5fb48aedcc32662f2f3fbdbadec35.
- Actual Android Keystore tests: eight cases, a suppressed-commit failure regression and process reopen passed in the
  disposable app.archium.keytests on the physical Samsung Android 36 phone.
  The initial durability regression failed before implementation; file sync,
  committed-record verification and directory sync then passed on Android.
  ADB emulator-5554 is another alias for that same phone, not separate coverage.
- Local Python preparation/build routing: 28 tests passed.
- Sparse patch applies and all 59 source hashes match.
- JVM window classification and color/provider routing checks passed.
- Native provider/database/backend/JNI/GN compilation and execution: pending.
- Pure Java CSV reader/writer: 18 synthetic cases passed, including malformed
  quoting, errors without field contents, duplicates and bounded input.
- Save/fill readiness gating and regular-profile settings routing are written
  in the pinned patch; actual browser/native validation is pending.
- Password management screen and CSV/auth/SAF integration: pending.
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

CSV transport limits: 16,777,216 input characters, 100,000 records, 512 columns
and 1,048,576 characters per field. Exceeding a limit rejects the preview; no
PasswordStore mutation occurs in this parser. Conflicting passwords remain
separate rows for native duplicate review; only identical triples are skipped.

## Protección de vistas previas preparada (no validación nativa)

Se agregó un snapshot de credenciales sobre la secuencia real de DB, con token
único por inicialización de LoginDatabase, total_changes y data_version de SQLite.
La importación puede exigir la revisión del preview y la comprueba dentro de la
transacción, con snapshot de lectura adquirido antes de validar. Una escritura
posterior invalida el preview; no se deben reutilizar revisiones después de reabrir
el backend. El callback pendiente se cancela con el WeakPtr del PasswordStore.

Se añadieron seis regresiones C++: guardado web posterior, lecturas sucesivas,
reapertura, escritura por otra conexión, cola async y cierre durante snapshot.
No se han compilado ni ejecutado en Chromium todavía. Un experimento separado
con SQLite local verificó únicamente los contadores, no el código C++.
El gestor nativo visible, autenticación, SAF, review/confirmación CSV y exportación
siguen pendientes; esta API preparada no significa que ya se pueda importar.
