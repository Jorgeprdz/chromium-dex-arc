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
