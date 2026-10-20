# Split links and gestures implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline; one whole-change review at the end. Steps use checkbox tracking.

**Goal:** Complete the user-approved split batch and dispatch one checkpoint-based build after verification.
**Architecture:** Extend the existing divider/coordinator, preserving native Tab ownership. A window-scoped weak router connects the native link menu and existing NEW_SPLIT_VIEW disposition to the owning split coordinator. No DOM probing or synthetic mouse events.
**Tech Stack:** Chromium157 Android Java/C++, native navigation, existing Robolectric/host gates.
**Spec:** Approved in-chat design, plus `docs/superpowers/specs/2026-10-20-arc-split-view-design.md` for existing split invariants.

## Global constraints
- Preserve Chromium pin, package, GN args, toolchain, profiles, dialogs and checkpoints.
- Ctrl+click remains native; Ctrl+Alt+click uses upstream NEW_SPLIT_VIEW, normalized to ordinary foreground navigation outside eligible Arc windows.
- Context action only on valid HTTP(S) links in normal tabbed Arc windows, respecting enterprise/incognito restrictions and native navigation metadata.
- Existing pair: navigate neighbor with native LoadUrlParams; renderer-created WebContents retain original ownership/opener metadata and can replace the neighbor's displayed slot while keeping its previous Tab alive.
- No build before implementation/review/gates; then a single incremental dispatch and existing-monitor handoff. QEMU remains disabled by user.

## Review focus
- Link source may close, change window/profile, or stop being selected before menu selection; revalidate identity.
- Preserve referrer/additional navigation params, headers and POST data; normal navigation owns beforeunload/download/external handling.
- Deferred click/animation callbacks must not survive hide/destroy or act during a native modal.
- Maximizing must preserve pair/ratio across focus, background and window resize, and supply a visible restore action.
- Center snap must not trap resize or convert drag into click; respect motion settings/minimum width.

## Task1 — divider gestures and appearance
**Files:** ArcSplitDividerView.java; new ArcSplitResizePolicy.java; existing controls tests and runners/GN registration.
**Interfaces:** `setBalanceAction(Runnable)`, `setFocusAction(Runnable,String)`, `setFocusedMode(boolean,String)`; `ArcSplitResizePolicy.snap(float,boolean)`.
- [x] RED: double click balances once across compact/expanded grip; single click still opens; drag doesn't click; center capture/release hysteresis; hover and cleanup.
- [x] Implement shared grip gesture detector, snap+brief glow, stateful action backgrounds; test GREEN and existing controls.

## Task2 — coordinator temporary focus and link routing
**Files:** ArcSplitViewCoordinator.java; new ArcSplitLinkRouter.java; coordinator/route tests; SDK adapters.
**Interfaces:** `balance()`, `toggleFocusedPane()`, `canOpenLink(Tab)`, `openLink(Tab,LoadUrlParams)`, `presentCreatedLink(Tab,WebContents)`; router register/unregister/open/canOpen, scoped by Activity and source identity.
- [x] RED: balance preserves active Tab/ratio rules; focus/restore keeps pair/ratio and visible restore; ordinary and existing-pair link opens; stale source/profile/modal rejection; navigation params preserved; failure restores prior split.
- [x] Implement minimal native Tab actions, lifecycle cleanup and animation guards; GREEN.

## Task3 — native context/shortcut integration
**Files:** pinned ChromeContextMenuPopulator.java, TabWebContentsDelegateAndroidImpl.java, components/embedder_support/android/delegate/web_contents_delegate_android.cc; existing Arc resources and registration.
- [x] RED: execute delivered menu/Java forwarding with explicit adapters; native disposition fixture verifies Ctrl+Alt versus Ctrl/Alt/Shift and both forwarding branches.
- [x] Add menu entry without removing native options, preserve context metadata; accept existing NEW_SPLIT_VIEW at Android bridge; route Java requests and normalize unsupported cases. GREEN.

## Task4 — gates, PR and progressive handoff
- [ ] Regenerate patch/manifests; run relevant JVM/native/host/preparation gates, review whole diff and resolve Important findings with RED/GREEN.
- [ ] Update TODO/report/PR with implemented versus device-pending results; preserve checkpoints and inspect last compatible run/manifests before dispatch.
- [ ] Integrate authorized candidate to build branch, dispatch exactly once with matching SHA/source inputs, update existing watcher and verify independent Termux process/first poll, then end Codex turn.

## Ledger
- Baseline: draft PR2, HEAD23a493d, clean isolated branch assistant/archium-r5-split-polish-batch.
- Ruling: renderer-created child WebContents cannot be destroyed/transplanted speculatively; retain native creation and replace displayed neighbor slot, preserving prior Tab in sidebar. This preserves opener/navigation data and user forms, at cost of a new Tab on that route.
- Ruling: native WindowManager/GPU/device keyboard behavior remains pending APK acceptance; host adapters cannot certify it.
