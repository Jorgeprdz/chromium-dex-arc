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

## Physical follow-up after unlock

Evidence: `/workspace/.local/state/archium-r5-physical-followup-20261025/`. Galaxy RFCY203Q5TK verified; installed APK SHA256 a894776d24308f9d6e5d156b0ae6e2b7933ee5da9512fe55d4225d25329c11ea, still baseline fc910e0. These results do not validate the unbuilt candidate.

| Physical case | Actual result on installed baseline |
| --- | --- |
| Owned HTML5 video fullscreen | PASS: video enters landscape fullscreen without Archium pills; Back restores portrait page and both pills. Returning through Termux resumes the page. No claim for YouTube or repeated orientation cycles |
| Fixed bottom composer | PASS: in one uninterrupted case scroll compacts controls, exposed left input accepts QA_not_sent, input and local Send test control remain visible above IME. Nothing sent externally |
| Link preview | PASS: native context menu opens owned link in preview sheet without crash; Back dismisses it |
| Incognito context action | PARTIAL: native incognito tab opens without crash and closes back to normal model; local fixture stays blank on two captures. Content loading remains PENDING diagnosis, not PASS or a demonstrated root cause |
| Download | PASS: owned41-byte text file downloaded, native success banner visible; bytes match fixture, SHA25635640d8141930f895f2beecc2c7fafbf8a4ab9c292c416cddb2103728706018e. File retained as evidence in Download/Archium_QA_download.txt |
| Permission dialog | PASS for opening/dismissal only: native location prompt visible and cancelled with Back. No location granted or obtained |
| System theme transition | Dark editor/IME and restored auto/light editor captured on same QA tab. Clock remains legible in dark; poor/invisible clock over light editor reproduced. Overall contrast acceptance FAIL on baseline; candidate still pending APK |
| QA cleanup/configuration | Own normal QA tab and own incognito tab closed; normal tab counter5 and overview captured. No other tabs closed. Termux foreground after every case and at end; size904x1966, density420, rotation0, autorotation0, nightauto verified. Owned fixture server21392 stopped |

The earlier locked-screen captures remain inconclusive; the unlock blocker is resolved. The five-tab count is verified, but earlier historical tab titles are not asserted as a current inventory because user navigation may change them.

Pending: candidate physical Spaces/undo/NTP behavior, clock correction and favicon appearance; remaining real-DeX mouse/keyboard and populated-folder persistence; additional window/share cases; YouTube and repeated rotation/fullscreen; incognito fixture loading investigation. Credentials/passkeys/autofill remain NOT RUN without controlled accounts. No measured AA or performance claim. No density simulation or speculative renderer changes.

Source and local gates: READY FOR BUILD, with the above physical acceptance pending. Build still requires explicit authorization, exact final SHA, compatible checkpoint and normal preflight. No workflow, push, installation, checkpoint cleanup, main merge or production release performed.
