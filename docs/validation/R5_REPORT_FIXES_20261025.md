# Report findings — candidate based on fc910e0

Branch: `assistant/archium-r5-desktop-native-mobile`. Installed APK remains run40152874809 / fc910e0. No workflow, installation, checkpoint deletion, dependency/toolchain or Chromium pin change authorized or performed in this iteration.

## Confirmed baseline and candidate changes

- **Spaces:** on real DeX, closing the last tab of QADeX1025 displayed a Personal page while the selector/list remained in the empty Space. `ArcNativeTabSession` handled selection/restore/commit but not the native removal-for-closure event. It now coalesces `didRemoveTabForClosure` callbacks on the UI queue, after native successor selection; reuses an existing active-Space tab or its existing native-NTP creation path. Global close-all is left to Chromium. Pending closure metadata, undo, profile isolation and lifecycle guards remain intact. The exact pinned `TabModelObserver` and `ThreadUtils.postOnUiThread` declarations were checked from upstream; source copies are in evidence.
- **Focused status contrast:** baseline screenshots `status-light-edit-awake.png` / `status-fixture-edit.png` again show poor clock contrast over a light editor. The native window dump records legacy visibility `2010` and appearance `10`. Runtime Java color fields were not instrumented; the local production-expression probe proves the transparent-color contrast path fails to retain a light native-editor backing. The candidate uses `calculateDefaultStatusBarColor()` only for fully transparent, focused phone surfaces. The actual window color/fade stays unchanged; opaque indicators, Desktop, unfocused/native policies retain their owners. Device confirmation of the candidate remains pending.
- **Reveal favicon:** an orange favicon against the matching APKMirror header is difficult to distinguish. A small rounded neutral backing now contrasts with the cached icon without recoloring it. At most16 icon-pixel reads occur on bitmap replacement, not per frame; no page capture, bitmap copy, new resource or dependency. Hardware/recycled/transparent icons use a bounded fallback. Bar geometry, reveal thresholds64/120, input, identity first-line action and page color are unchanged.
- **Colored corners:** existing tests retain the mask for saturated blue/orange as well as light/dark. Matching header/gap colors can make the boundary disappear perceptually; no missing-mask defect was demonstrated. No new clipping, outline or corner mechanism was added.
- **DPI observation:** remains limited to the earlier simulated transition. Real DeX→Phone→DeX passed once, with five tabs retained and no process restart. A separate black capture was from an off display. No speculative rendering/lifecycle/GPU fix was made.

The Desktop frame is approved by the user and checked on DeX; it must remain unchanged. Split View passed both resize sequences on a known-breakpoint fixture (CSS/visual widths, constant DPR, preserved form and load counters); no Split/viewport source was modified.

## Local verification

Evidence: `/workspace/.local/state/archium-r5-report-fixes-20261025/`.

| Check | Actual result |
| --- | --- |
| Spaces regression | RED2 failures before production change; GREEN16 adapter scenarios at explicit synthetic native/JNI boundaries |
| Space cases | Normal/pinned last-tab close, existing peer, native NTP URL, pending undo, committed saved-entry reopen, subsequent Space switch, session reattach, global close-all, teardown; existing authority/profile cases retained |
| Favicon regression | RED2 expected SDK30/36 failures; GREEN204 Android/Robolectric executions across phone/Command Bar/material/status/reveal suites; Chromium shadow policy unchanged |
| Intermediate favicon run | Failed because the legacy Canvas shadow did not record the float-coordinate overload; cached RectF overload now records the real draw call. No shadow/gate relaxation |
| Focused contrast regression | RED1 production-expression failure; GREEN5 status-polish probes, including native light/dark backing and Desktop/unfocused/opaque preservation |
| Related host checks | Status modules6 PASS; reveal4 PASS; theme-owner1 PASS |
| SDK/preparation | SDK37.2 isolated adapter compilation, native-session scenarios and6 preparation checks PASS. Dependency contracts are explicit stubs; not a full Chromium build |
| Official patch generator |201 paths, identical regeneration PASS |
| Incremental transition | Hash-verified sparse fixture from sourcef4a1853736465f1f539722b65780dba33181d761:201 paths verified,183 unchanged timestamps retained. Not checkpoint-byte restoration/integrity verification |

No costly full host suite was duplicated. A successful local run is not acceptance of graphics, performance, native undo/snackbar interaction or an unbuilt APK.

## Physical validation remaining

The phone became locked during the additional keyboard/fullscreen checks. Black/lock-screen captures are inconclusive, not app failures or PASS. The user was asked to unlock and leave Termux foreground. No attempt to bypass device authentication was made.

Pending: candidate physical Spaces/undo/NTP behavior; clock in both themes with IME and suggestions; neutral favicon appearance; fixed bottom composer/IME; HTML5/YouTube fullscreen and rotation; additional context-menu/window/incognito/preview paths; mouse/keyboard focus and populated-folder persistence. The broader pending matrix in the HTML report is retained. Passwords/passkeys/autofill require controlled fixtures/accounts and remain NOT RUN. No performance or measured AA claim.

Temporary QA tabs may have been queued while the phone was locked; their exact count and cleanup must be checked after unlock. Only titles/URLs belonging to the owned QA origins127.0.0.1:8765/8766 may be closed. User tabs, profiles, favorites, history and settings must remain intact. Restore/verify density420, size904×1966, rotation0, autorotation0 and nightauto. Return to Termux after each completed case.

Candidate source/gates are ready for review; closing physical inspection remains blocked on device availability. A new build still requires explicit authorization, exact candidate SHA, compatible incremental source and normal preflight. No production release or main merge.
