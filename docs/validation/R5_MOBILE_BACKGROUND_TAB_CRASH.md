# Mobile link-opening crash — 24 Oct 2026

## Evidence and cause

Physical Galaxy RFCY203Q5TK, installed package app.archium.android, APK SHA2560823eb6645c87193fe2281a362711bc732793557f2c24db246dba9f5e8082b5c, matches verified run40116057788 /0f6c610. Read existing device crash records without clearing logs, navigating, creating tabs or changing user data.

Latest recorded main-thread crash at16:26:18.998 (device time): NullPointerException invoking View.findViewById on null, a6a.o line313. The preceding crash at16:25:38 has the same failing instruction. Disassembly of this exact APK shows an inlined native NewBackgroundTabAnimationData lookup: root.findViewById(0x7f0101f7), then that result.findViewById(0x7f010ce0). APK resources identify these as bottom_bar_container and tab_switcher_button. The pinned Chromium source at cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 confirms updateBottomBarTabSwitcherButtonCalculations requires precisely those views. ArcPhoneNavigation replaced that native component but assigned neither ID. Production assertions were not a null guard, so opening a background tab crashed when the native animation tried to snapshot its target.

Evidence: `/workspace/.local/state/archium-r5-mobile-open-crash/` contains crash.txt, a6a.txt, i5a.txt, APK resources and the pinned animation source. These are existing crash observations plus exact-APK/source analysis; this session did not intentionally crash the user's running app.

## Local correction

Assign the existing native bottom_bar_container ID to the single floating navigation bar and tab_switcher_button ID to its real Tabs action. Reuse the existing native background-tab animation; do not catch/swallow the exception, disable menu actions, fabricate an animation target or add another bar. No visual/geometry/material changes, Desktop code, engine or dependencies changed in this fix. The preceding thin Desktop frame fix remains in the candidate.

## Verification

- RED: the added real-view regression failed on SDK30 and36 because the native bar lookup returned null.194 executions,2 expected failures, retained in red.log.
- GREEN:194 Android/Robolectric executions PASS, including native ID lookup, actual Tabs action, Hub borrowing/reattachment, compact/expanded identity and existing phone/glass/Command Bar/material/status/reveal tests. Pinned Chromium shadow policy PASS,88 methods. Native resource IDs are explicit test boundaries; native animation/controller/tab creation are not run end to end by this JVM suite.
- The runner now stores resource boundary classes by package path so two distinct R.java classes are not overwritten. Isolated SDK definitions include the existing native tab ID. No application shadows or relaxed gates.
-10 related host tests PASS: floating native contracts6, shadow policy2, host gate coverage2.
- SDK37.2 preparation and pinned sparse application PASS, including6 related checks.201-file source-checkpoint delta verified;184 unchanged timestamps preserved; patch regeneration identical. Sparse fixture is not an actual checkpoint restoration.

Pending: integrated Chromium compile, candidate APK, physical long-press→open new tab/group/window/incognito, tab count and group membership, return/back/undo, compact mode, NTP and Phone↔DeX transition. The observed failures share the animation path, but every menu variant is NOT declared fixed on device without a candidate APK test. No new workflow dispatched and no installation performed for this fix.
