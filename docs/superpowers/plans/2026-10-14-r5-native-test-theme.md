# R5 native omnibox test theme repair

> **For agentic workers:** Use superpowers:executing-plans inline. The user already authorized continuous repair, verification, compilation and the Termux installer.

**Goal:** Unblock the native R5 gate without weakening its command geometry checks.

**Architecture:** Give the real LocationBarLayout in the two new command-coordinate tests a browser-themed ContextThemeWrapper. Keep the generic Activity and all other tests unchanged. Regenerate the pinned patch and resume the exact R5 branch from the newly retained checkpoint.

**Tech Stack:** Chromium Android, Java, Robolectric SDK29/37, Python host gates, GitHub Actions.

**Spec:** docs/ARCHIUM_R5_RUNTIME_FIXES_2026-10-14.md; failed Actions 38511423805.

## Global constraints
- Preserve Chromium pin cfd94726b7b5fb48aedcc32662f2f3fbdbadec35, product logic and signing.
- Work only in assistant/archium-r5-arc-experience; no merge/release.
- Keep all geometry and action-mode assertions, SDKs and native gate filters.
- Dispatch only after branch/SHA/checkpoint/concurrency verification.

## Review focus
- LTR physical left and width/height: keep existing exact assertions.
- RTL anchor origin: keep existing exact assertions and qualifiers.
- Actions hide native suggestions: keep width=height=0 assertions.
- Generic Activity must not affect other tests: theme only this helper's views.
- Resource inflation must use the real browser theme: native CI is decisive; local adapters do not prove it.

## Task 1: Correct the real native fixture and resume CI

**Files:** Modify .source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/OmniboxSuggestionsDropdownEmbedderImplUnitTest.java; regenerate patches/archium-desktop.patch and patches/upstream-files.json.

- [x] RED: read the genuine native gate; both command alignment methods fail at LocationBarLayout construction on SDK29/37, 4 failures/51 executions, with an unresolved layout dimension under Theme.AppCompat.Light.
- [x] Add android.view.ContextThemeWrapper and create the helper's holder/bar with R.style.Theme_BrowserUI_DayNight, matching existing LocationBarMediatorUnitTest.
- [x] Regenerate patch; run host suite, preparation, idempotence, diff/workflow syntax checks. Preserve the unexecuted native scope explicitly.
- [ ] Review the diff; commit and push R5 only.
- [ ] Verify checkpoint groups/manifest and exact remote SHA; dispatch a single baseline build and pin the Termux monitor/installer to it.
- [ ] GREEN requires the complete real native suite on SDK29/37 passing; final APK is only success after verification/installation.


## Execution ledger

- Existing linked worktree confirmed; original R5 HEAD and native RED retained.
- Helper-only theme fix implemented; generated hashes reviewed.
- Reviewer found no Critical/Important/Minor issues; genuine native GREEN remains pending CI.
- Checkpoint remote manifest verified with bounded 5381-byte transfer; 4 groups/25 parts and source 0abfc9f agree. Capacity is deliberately left to CI.
- Preparation, 18-resource AAPT2 fixture, patch idempotence, diff and actionlint passed.
- Local host run lacked ARCHIUM_TEST_AAPT2/ARCHIUM_TEST_ANDROID_JAR and reported resource test environment assertions. Ruling: restore the explicit SDK/AAPT2 environment used by CI, keep all test/product code unchanged, rerun verification. This session reset those environment variables.
- The two SDK/AAPT2-dependent resource tests passed on focused rerun with explicit CI variables (2 tests, 301.409 seconds). No test or product code changed for this environment correction. Avoid another full resource-fixture run: the full-suite remainder is still being read and genuine CI executes its own complete suite with those variables.
- Full local suite finished: 280/282 passed; the only two failures were missing SDK/AAPT2 environment and both passed the focused rerun. Preparation, patch idempotence, AAPT2 fixture and actionlint passed. Native GREEN and APK remain pending.
