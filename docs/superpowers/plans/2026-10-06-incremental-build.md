# Archium Incremental Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile and verify the new password/Arc implementation while reusing verified objects from the previous build when possible.

**Architecture:** Preserve the old checkpoint identity and restore it strictly. A separately verified transition reapplies only touched source changes from old patch to new patch, copies new GN args, regenerates GN and lets Ninja rebuild invalidated targets. New stages keep their own checkpoints.

**Tech Stack:** Python, GitHub Actions, GN/Ninja, pinned Chromium checkout, APK signature tools and ADB.

**Spec:** `docs/superpowers/specs/2026-10-06-archium-local-arc-design.md`.

**Execution:** Inline. User requested documents in `/sdcard/Download/Archium-documentos`; copy this and both component plans there.

## Global Constraints

- Existing checkpoint `archium-checkpoint-37255997027-7`, source commit `c8ffd13ee7fe1c6baab4913da6a01e8009febe18`, Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
- Do not weaken checkpoint revision/commit/hash/path verification.
- Do not delete old checkpoints, installed apps, user profile or personal CSV.
- Preserve timestamps of untouched files and rebuild all changed GN/source inputs correctly.
- No guaranteed runtime estimate; measure the incremental rebuild.
- Do not launch final full build before the component implementations and targeted validations are ready.

## Review Focus

- Checkpoint from wrong commit/revision: reject before extraction or patch mutation.
- Divergent touched source/symlink: reject the entire transition before writing.
- Files removed from new patch: restore pinned originals, never leave old behavior behind.
- GN args/buildflags changed: regenerate and allow dependency-driven rebuild.
- Signature mismatch with installed APK: no uninstall/profile wipe as workaround.

### Task 1: Verified old-to-new patch transition

**Files:**
- Modify: `scripts/archium-checkpoint.py` to separate explicit source checkpoint identity from current implementation identity.
- Create: `scripts/transition-archium-patches.py`.
- Test: `tests/test_checkpoint.py`, `tests/test_patch_transition.py`.

**Interfaces:**
- Existing strict restore remains strict by default.
- `transition(checkout, old_manifest, new_manifest, old_patch, new_patch, original_sources)` verifies revision, both patch hashes and all touched inputs before changing files.
- Old patch/manifest are loaded from their explicit committed revision, not assumed to equal current files.
- Persist transition receipt with old/new identities only after all mutations succeed; new checkpoint records the new implementation commit.

- [ ] Write RED tests: old checkpoint accepted only with its declared commit; wrong revision/path/hash rejected; old-only file restored; removed new source removed only when exact old hash matches; divergent user file/symlink rejects all writes; interrupted mutation restores pre-transition bytes.
- [ ] Run RED, then implement validation/staging/rollback. Preserve unchanged file bytes and mtimes.
- [ ] Run tests; expected full transition and tamper/interruption cases pass.
- [ ] Commit transition and tests.

### Task 2: Incremental and targeted build workflow

**Files:**
- Modify: `scripts/build-archium.sh`, `.github/workflows/baseline-build.yml`, `.github/workflows/archium-stage.yml`.
- Modify: `docs/archium-staged-build.md`.

**Interfaces:**
- Workflow accepts an explicit source checkpoint/tag/commit for the first stage; later stages resume the new run's own checkpoints normally.
- After first transition run `gn gen out/Archium`; Ninja reads existing dependency state and invalidates changed sources/buildflags.
- Add selectable targeted validation steps for the native/Java tests introduced by component plans, naming targets after they are actually registered in the pinned GN graph.

- [ ] Write workflow/command-construction tests: first stage restores old identity then transitions/regenerates; later stages do not reapply transition; changed args cannot skip GN; nonzero compiler result stops the chain.
- [ ] Run RED, implement workflow and command routing, validate with actionlint and shell syntax checks.
- [ ] Run local simulated restore/transition/GN command tests. Expected strict source identity and continuation behavior pass.
- [ ] In CI, run changed-target compilation and selected password/Arc tests before final APK target; record actual targets and logs. These are real pinned Chromium checks, not stub-only verification.
- [ ] Commit workflow/tests/documentation. Launch when component plans meet their pre-build gates.

### Task 3: APK update and end-to-end verification

**Files:**
- Create: `docs/validation/archium-integrated-results.md`.
- Modify: install/delivery documentation or scripts only if signature inspection demonstrates a necessary change.

**Interfaces:**
- Consumes completed build artifact and component test results.
- Produces an update-compatible APK where the existing signing identity is available, SHA-256 and verified feature results.

- [ ] Inspect installed APK and candidate signing certificates. If update key is unavailable, stop before changing installation; present a concrete migration option preserving user data for approval.
- [ ] Download verified artifact, compare checksums, install as update and confirm version/package. No downgrade/uninstall/data-clear shortcuts.
- [ ] Execute both component acceptance suites on synthetic credentials/pages plus tablet/emulator where needed. Expected CSV CRUD/fill and Mac sidebar functionality actually work.
- [ ] Reopen existing user tabs and verify profile/extension continuity without reading their secrets.
- [ ] Save documents/results to the requested Download directory and report actual build duration, checks passed and remaining limitations.
- [ ] Commit validation. Do not claim complete if either component's acceptance is pending or failed.
