# SDD ledger — plan: docs/superpowers/plans/2026-10-20-arc-split-view.md
2026-10-20: plan approved explicitly; inline execution, isolated assistant/archium-r5-3-omnibox-split. BASE d31f37d.
Task 1: in progress — single mTabVisible/mContentView/OnscreenContentProvider verified; StaticTabSceneLayer owns one ContentLayer. ContextualSearchSceneLayer can embed another live layer; this alone does not establish correct lifecycle/input.
Preflight: state/controller signatures match; Task 3 JNI names must follow pinned headers. No build dispatch. Unrelated omnibox edits being finished independently.

Task 2: independent state implemented; RED class absent, GREEN 6/6 JUnit. GN and CI class registration prepared. Final gate: preparation PASS, complete helper runner 44/44 PASS, address touch runner 18/18 PASS.
Ruling: ratio clamped to .2–.8 and non-finite values rejected; pixel minimums belong to future layout controller. Physical ratio remains unchanged on swap.
Ruling: prepare independent state while native contract is investigated; do not wire menu before two live contents/input work. No renderer changes or inert button delivered.
User steering: capsule white, stacked dark opposite horizontal arrows; swap transition smooth/fast 180 ms, obey animations-disabled and settle on cancellation.
Task 1: exact remaining boundary documented in docs/validation/R5_3_SPLIT_VIEW.md; no claim that showing a second Tab preserves first, nor that View animations move native layers.
Tasks 3–6: pending native contract/integration; no new build. Omnibox/history independent changes are covered by targeted tests and preparation gate.

Verification: compact helper 28/28 PASS; native command/Fusebox bodies 14/14 PASS; native command API 4/4 PASS. No APK/device GREEN for new code. Source integration Task 1 remains pending; no split menu/capsule/animation shipped. Host source-adapter tests do not validate compositor.

Task 1 ruling: source viability established at explicit integration points: two independent ContentLayer live children; pair-aware StaticLayout.onShown; holder attaches two bounded ContentViews and routes focus before dispatch. Actual pixel/input acceptance remains mandatory after APK, not claimed by source audit. Source-only viability is distinct from Android GREEN.
User authorization: finish all designed features first, then one incremental build. Earlier dispatch preparation superseded; no run dispatched. Build budget/counters preserved.

Tasks 3–5: native pair presentation, controller and native menu/divider wired; source implementation ready for final review. RED native method absent / controller absent; controls and view attachment implemented test-first. Recovery regression RED NPE -> GREEN guarded reattachment.
Additional request: per-pane mobile behavior. Ruling: 600/640 dp hysteresis and temporary per-controller UA without reload — avoids destroying unsaved form state; server-only mobile layouts may require user navigation. Normal mobile preference remains mobile.
Verification 2026-10-20: 50 split tests PASS, 44 R5 helpers PASS; native actual C++ scene/AnchorInfo probes PASS at explicit adapters. Real Chromium compilation/JNI and APK graphical acceptance are pending, not PASS. Full host suite and final review running before dispatch.
