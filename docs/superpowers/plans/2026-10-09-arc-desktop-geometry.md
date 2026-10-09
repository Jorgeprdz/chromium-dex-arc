# Arc Desktop Geometry Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline with TDD; final independent review. User restrictions override commit/staging/worktree creation and artifact deletion steps.

**Goal:** Reproduce the supplied Arc composition while preserving Chromium browser behavior and Android window decorations.

**Architecture:** Centralize responsive measurements in ArcDesktopPolicy; integrate rail sizing at the native Side UI allocator, internal chrome at ArcDesktopCoordinator, and existing R2 caption/omnibox fixes. Reuse native tabs/compositor/outline and event-based listeners.

**Tech Stack:** Java17, Android37 API, Python3.12, Chromium pinned patch overlay.

**Spec:** docs/superpowers/specs/2026-10-09-arc-desktop-geometry.md

## Global Constraints
- Existing feat/arc-media-only at1255da5745e3cd1453ff17f3b237cd3f97a24b58; preserve all prior modifications with backup.
- ARCHIUM_BUILD_SCOPE=arc-media, local passwords disabled.
- No commit, staging, push, merge, Actions, APK installation, ADB, deletion or new worktree.
- No false traffic lights/titlebar, duplicate LocationBar/tab system, arbitrary bookmark margin, or permanent polling.
- Python3.12/JDK17; pinned Chromium cfd94726b7b5fb48aedcc32662f2f3fbdbadec35.

## Review Focus
- Extremely short/high-density windows must retain usable tab area and native navigation access.
- Caption transition/fullscreen must not double-reserve header or recursively update stacker.
- Same-size surface swaps must reapply clipping and release old listeners/outlines.
- RTL bounds must follow Side UI physical anchor and hit testing, including padding.
- Preference changes/destroy before posted callbacks must restore MOBILE geometry without resurrecting Arc.

### Task 1: Preserve and integrate R2 baseline
**Files:** existing R2 payload, coordinator/policy/TabbedRoot; .sync-audit/arc-geometry-20261009/before.
**Interfaces:** Produces known integrated R2 policy/dropdown/caption and preserved previous byte hashes.
- [x] Back up uncommitted files and index hash; upgrade only recognized R1 payload.
- [x] Regenerate patch; run full preparation and repository checks. Expected137/137 Python and preparation PASS.
- [x] Record evidence and index/HEAD preservation; no commit.

### Task 2: Geometry policy and native sidebar sizing
**Files:** ArcDesktopPolicy.java; tests/java/ArcDesktopGeometryTest.java; tests/test_arc_geometry.py; VerticalTabsSideUiCoordinator.java pinned overlay; check-arc-preparation.py.
**Interfaces:** Produces expandedSidebarWidth(windowPx,availablePx,density), geometry(windowPx,heightPx,sidebarPx,density,rtl,captionPx) immutable bounds and internal sidebar measurements; consumes R2 captionReserveHeight.
- [x] Write failing fixtures:1382×863, sidebar334, viewport1037×840,12/11/11 insets;48dp touch bounds,52dp collapsed, monotonic resize, RTL, invalid density.
- [x] Run Java geometry regression and observe missing policy behavior.
- [x] Implement ratio sizing with native92..500dp rail bounds and usable navigation minimum; use allocated available width. Preserve manual resize, hover and MOBILE upstream paths.
- [x] Extend preparation to run geometry tests and verify patch; expected new geometry cases PASS.

### Task 3: Sidebar/chrome and clipping integration
**Files:** ArcDesktopCoordinator.java; ArcCollectionsView.java; VerticalTabRailLayout.java; tests/test_arc_geometry_runtime.py; existing R2 TabbedRootUiCoordinator.java as necessary.
**Interfaces:** Consumes policy geometry/native allocation and R2 caption; produces frame margins/outline/hit rect and responsive chrome, cleanup.
- [x] Add executable regressions using real production method bodies: no content-edge gap, correct margins, footer/tab budgeting, collapsed/narrow navigation, MOBILE restore, same-size surface swap, destroyed callbacks, caption updates.
- [x] Verify RED, implement minimal layout deltas without rewriting coordinator. No arbitrary BookmarkBar offsets.
- [x] Use global layout/surface events to update clipping, no polling; map holder rect into active surface coordinates and restore originals.
- [x] Repeat policy/dropdown/coordinator host tests and isolated Android API compilation; record limits.

### Task 4: Full verification and reviewable delivery
**Files:** patches/archium-desktop.patch; patches/upstream-files.json; docs/arc-desktop-geometry-review-20261009.md; .sync-audit/arc-geometry-20261009/full.diff.
**Interfaces:** Consumes all preceding changes; produces full diff/hash/test/status matrix.
- [x] Regenerate patch and hash manifest, run full preparation and repository checks with Python3.12/JDK17.
- [x] Review complete uncommitted diff including untracked files; independent reviewer reads spec and evidence.
- [x] Address real findings with failing regressions; repeat complete suite after final changes.
- [x] Verify HEAD/index and passwords/scope; deliver PASS/PARTIAL/BLOCKED matrix and honest commit readiness. Keep artifacts and all changes uncommitted.

Publication update: the user explicitly authorized commit, push of this branch and workflow_dispatch after implementation and reauditingR2. This supersedes the initial no-staging/no-commit/no-CI restriction; no installation, ADB, merge, deletion or new worktree is authorized. Fresh final checks154/154 and95 pinned patch files PASS; integrated APK acceptance remains pending.
