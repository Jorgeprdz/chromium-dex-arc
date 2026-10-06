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
