# Archium R5 audit and exact image 4 implementation plan

> Execute inline with superpowers:executing-plans. The user's specification authorizes execution without intermediate approvals, two commits in this tree, and exactly one final incremental native chain.

**Goal:** Fix the measurable F01–F09 defects, retain honest PENDING_REPRO for F06, then polish only the desktop shell toward the exact supplied image 4.
**Architecture:** Keep native TabModel/WebContents, bookmarks, editor, compositor and SurfaceView. Unify bookmark intent through native save callbacks and URL-idempotent Arc metadata. Use explicit window-to-container geometry for suggestions, input-transaction ownership and one frame contract. Style existing Views/resources; preserve all native actions.
**Tech stack:** Pinned Chromium cfd94726b7b5fb48aedcc32662f2f3fbdbadec35, Android Java, JVM/Robolectric, Python gates, R5 incremental Actions.
**Spec:** User's 2026-10-29 prompt and local docs/ARCHIUM_POLISH_AUDIT_2026-10-29.md. Exact image privately loaded from phone Download; current image available only as 480px thumbnail.

## Global constraints
- Same branch/tree; no resets or new worktree; preserve untracked private evidence.
- Two commits only: fix(r5), then style(r5); generate patch/manifest in each.
- No native build until both changes and all preflight gates pass. One final verified incremental chain; no clean fallback, no competing workflows.
- Camera/manual rotation, capture, permissions, UA/Client Hints, PiP/share untouched.
- No profile clearing, storage reset, global density/zoom, GPU flags or screenshot backdrops.
- No private captures committed/published. DeX disconnected: installed-final acceptance PENDING_DEVICE.

## Review focus
- Bookmark URL identity across close/reopen, edits, failed persistence and duplicate tabs.
- Double-click DOWN/UP and opening/closing interruption retaining one native editor.
- Container/window offsets after sidebar transitions, both omnibox positions, RTL.
- Short height/tab scrolling, compact 52dp, split and rounded-corner hit regions.
- Bitmap density/async callback identity and light/dark/incognito/custom palette preservation.

## Implementation 1 — audit corrections
- [x] Add failing behavior regressions to collection JVM tests for URL idempotence/title updates/reopen/persistence; route native bookmark completion/edit updates to Arc, native collection favorite command through the same bookmarker; no deletion of existing native items.
- [x] Trace pinned bookmark Activity theme/lifecycle; repair desktop dialog geometry/host continuity at source, preserving native controls. Regression for mode and bounds. Distinguish CODE CHANGED from PHYSICAL PASS.
- [x] Add Android View regressions for second click at origin, closing/reopening, focus and native editor preservation; implement bounded origin gesture ownership.
- [x] Add coordinate regressions with moved container/anchor and sidebar offsets; use actual destination coordinates. Restore top toolbar utilities without duplicate navigation or empty reservation during command panel.
- [x] Add real short-height/tab budget and four-corner hit tests; correct reservations and shared frame geometry.
- [x] Normalize favicon drawable optical bounds and density, neutral domain fallback; guard late callback identity. Test refresh and small bitmaps.
- [x] Extend existing bounded F06 capture protocol with surface/viewport/timestamp evidence; no speculative renderer fix; status PENDING_REPRO.
- [x] Run focused Java/Robolectric and full configured host gates; regenerate patch; commit fix(r5).

## Implementation 2 — image 4 polish
- [x] Regression tests for compact 48dp mosaic, >=44dp hit targets, responsive columns/menu fallback, active tab contrast, shared radii and custom palettes.
- [x] Remove large header tiles from presentation; preserve bookmark/Google access in a lightweight header/menu. Move existing new-tab row below scrolling tabs, above footer.
- [x] Harmonize lavender default/material continuity and active violet selection; retain selected custom colors/dark/incognito; never style web content.
- [x] Replace legacy save/star/camera/info/eye artwork with coherent desktop vector geometry and favicon initial fallback; preserve listener/accessibility/native extension owners.
- [ ] Run focused suites, full SDK-configured host suite, isolated API gate, generation twice, actionlint; review full change; commit style(r5).

## One final incremental build and handoff
- [ ] Verify remote final SHA, no competing workflows, checkpoint manifest/source/run/digests; dispatch existing R5 chain once. Persist run identity before polling. Recovery stages belong to same chain only.
- [ ] Verify real APK package/ABI/version/source SHA/signature/checksum and receipts. Install only verified final APK if device available and preserve data; actual physical acceptance otherwise PENDING_DEVICE.
- [ ] Deliver F01–F09 results table, image-4 matrix, both commit URLs/final SHA/single run/artifact digest; record every blocked gate honestly.

User steering: after dispatch, launch the SHA/run-bound Termux installer monitor with Termux:API notifications, verify it is active, then stop. Physical acceptance and APK results are monitor/device follow-up, not claimed in this turn.
