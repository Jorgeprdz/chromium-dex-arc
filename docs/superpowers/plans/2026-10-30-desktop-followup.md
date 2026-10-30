# Desktop follow-up implementation plan

> Use superpowers:executing-plans. Implement in the existing isolated worktree.

**Goal:** Apply the approved version/About change and the collected desktop fixes,
preserving the working camera pipeline.

**Architecture:** Keep Chromium's capture and native menu owners. Package build
identity separately from the Chromium package version. Use existing Android views
and test the delivered behavior with the existing host and Robolectric tools.

**Tech Stack:** Chromium 157 pinned sources, Java/Android, Python, GN, Robolectric.

**Spec:** docs/superpowers/specs/2026-10-30-desktop-followup-design.md

## Constraints and review focus

- Camera frame pipeline and native resolution adapter remain byte-identical.
- Mobile and screen sharing must not inherit Desktop rotation defaults.
- Repeated build stages retain one release number; independent builds increment.
- Favorites reflow after both resize and refresh, without smaller targets.
- New Folder retains its full native target and sufficient bottom spacing.
- Extensions retain native ownership; no replacement extension UI.
- PiP requires eligibility and site cooperation; never inject conferencing code.
- No automatic build/install/merge or profile/checkpoint cleanup.

## Tasks

- [ ] Camera: add menu/default regressions, observe RED, reduce menu to three
  angles and set unset Desktop choice to 90°, then verify the policy tests and
  source hashes for unchanged frame files.
- [ ] Version/About: add allocation/resume and About display regressions; package
  immutable Archium 0.9.N build metadata with the APK; move info last; verify
  SDK compilation, real About dialog and build integration.
- [ ] Collections: reproduce refresh/reflow and clipped folder action, keep
  mosaic geometry, add 8dp collection separation and bottom clearance; verify
  full Android collections cohort at both SDK levels.
- [ ] Extensions: trace the native popup anchor through sidebar reparenting;
  add a regression for the actual failing path and repair native anchoring.
- [ ] PiP: trace tab-switch versus Activity background eligibility at the exact
  pin; preserve camera/call state. Implement only a native path justified by
  the evidence and report any site dependency not safely resolved.
- [ ] Regenerate patch/manifest twice, run preparation/full host suite and affected
  Robolectric cohorts. Review the complete diff before reporting completion.
