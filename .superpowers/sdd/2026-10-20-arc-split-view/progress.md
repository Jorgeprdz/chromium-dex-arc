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

Final review: fresh whole-branch reviewer /root/split_final_review at 4b69ca6, read-only; no Critical, five Important; no second review.
Final: fixed stale view/foreground presentation — unchangedGeometryStillRebindsInactiveContentAndForeground RED->GREEN.
Final: fixed focus divergence — selectionTransfersFocusButNeverStealsFromOmniboxOrModal API RED->GREEN, nativeFocusHelper real delivered body guards GREEN; native rail/initial focus call-site contracts checked.
Final: fixed inactive keyboard mode overwrite — inactiveInitializationCannotOverwriteActiveKeyboardPolicy actual delivered initializeTab body RED->GREEN.
Final: fixed transient restoration loss — savedPairSurvivesTransientStartupReadiness and sceneReadinessEventRetriesPendingRestoreWithoutLayoutChanges RED->GREEN.
Final: fixed unusable pane minima — asymmetricRatioKeepsTwoUsablePanesWithoutLosingIntendedRatio RED->GREEN, fractional densities and RTL GREEN.
Final: fixed failed-entry selection/peer visibility — failedFirstPresentationRestoresSelectionAndHidesUnattachedPeer / failedPresentationKeepsPreviousPairAndSelection RED4 -> GREEN.
Final: whole split/controller/native-body suite 68/68 PASS; preparation PASS after last source changes. Full corrected Python host suite running; original failed only stale filter inventory, focused inventory test now PASS2.
Final: Ruling: follow active-pane IME policy for the shared Android window, apply mode only from active Tab and initialize it before peer sizing — prevents inactive overwrite; mixed IME behavior requires APK validation.
Final: minor (deferred): UpdateVisibleIds called for two tabs per frame; preserve fallback correctness, measure cost later.
Final: minor (deferred): compact lifecycle formatting; no polish edits in the correction pass.
Final: Ruling: real GPU/Surface/IME/TalkBack/permissions/performance remain APK/device gates, GN/JNI are incremental-build gates — no host/adapter equivalence; cost if wrong: code cannot be accepted visually until actual validation.
Final: Ruling: no speculative NavigationController crash fix — same-pin implementation has pointer-zero getter/setter guards, additional source hash in report; no crash established.
Final: Ruling: Amazon remains outside this implementation and UNRESOLVED_GRAPHICS_BLOCKER — user excluded it from this batch; cost: Amazon still not repaired.

Task 6 source gates: complete at 044e148 — corrected full Python suite 340/340 PASS, 68/68 split after final rollback changes, preparation PASS, 44/44 helper and 18/18 address regressions PASS. Native scene and menu probes PASS; GN/JNI/runtime remain actual incremental-build/APK gates.
Final review correction pass complete. Source commit 044e1488dc3ab64547f6072d616283c888f9d3a3; no unaddressed Important/Critical. Do not rerun unrelated suites after documentation-only commits.
Ruling: integrate into the explicitly named assistant/archium-r5-arc-experience branch for the already authorized build — no main/feat changes, no separate permission menu; cost if wrong: preserve isolated branch and rollback source only, never touch checkpoints.
Ruling: retain the forensic worktree and versioned progress ledger for user-requested continuation; archive only generated review/brief artifacts privately — prevents losing continuation evidence, costs a small retained directory.
Budget: user asked optional renewal because current window ends 03:39 UTC; no reset applied while awaiting answer. Existing counters/stage/repair limits preserved.
