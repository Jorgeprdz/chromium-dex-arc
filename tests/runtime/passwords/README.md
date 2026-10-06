# Actual browser password acceptance — pending

These ordinary HTML forms exercise Chromium's form recognition/navigation. They
contain no password scraper, injected input events or substitute password store.
The server discards submitted bodies and does not log requests or secrets.
Use fictitious credentials only.

Run against an isolated test application/profile. Never execute a browser test
that calls `clearAllPasswords()` on the user's installed `app.archium.android`.
A separate test build can use `chrome_public_manifest_package` with a `.tests`
suffix; it needs its own data directory/Keystore namespace. Do not replace or
uninstall the user's APK for test setup. Native tests for temporary LoginDatabase
and key instrumentation have independent disposable storage.

After the final run/pause has been resumed and the isolated browser is available:

```
python3 tests/runtime/passwords/serve.py
adb -s DEVICE reverse tcp:8765 tcp:8765
adb -s DEVICE reverse tcp:8766 tcp:8766
```

ADB is test transport only; the delivered password feature requires no ADB.
For repeatable no-Google-backend browser assertions, use an instrumentation
variant with account sign-in and GMS password fakes omitted. The upstream
`PasswordSavingIntegrationTest` requires account/GMS and its save case is disabled;
that test alone does not validate this fork's local implementation.

| Case | Native acceptance requirement |
| --- | --- |
| Save | Submit synthetic credentials on `http://localhost:8765/login`, confirm Chromium's actual save prompt; one encrypted profile-store row remains after restart. |
| Update | Submit `/update`, confirm Chromium's actual update prompt; same stored credential has the new password, with no duplicate. |
| Cancel | Dismiss the actual save prompt; the fixture credential is absent from the store. |
| Blocklist | Choose Chromium's never-save action; repeat login produces no save prompt or new credential. |
| Fill | Revisit the same host/origin and accept Chromium's native fill UI; the fixture fills and submits successfully. |
| Lookalike | Visit `http://127.0.0.1:8765/login`; a credential for `localhost:8765` is not offered or filled for this different host. |
| Cross-origin iframe | Open `http://localhost:8765/frame`; the frame's `127.0.0.1:8766` realm never receives the parent's credential. |
| Incognito | Capture/update in incognito never writes the regular store; filling preserves Chromium's existing explicit-access/incognito policy. |
| Unavailable key | No capture/fill availability while backend initialization/encryption fails; previously encrypted rows remain intact. |
| Settings | Offer-to-save and auto-sign-in read regular profile preferences, without GMS settings fetches. |

No browser case above has passed yet. Full native build, browser instrumentation,
manager/CSV/authentication integration and runtime acceptance are still required.
