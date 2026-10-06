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
