# Ambient mobile and desktop interaction follow-up — 29 October 2026

Installed baseline: `da97e5a50ee952973d0ce38c7e440ed6fd223489`, run
`40898064155`. This follow-up retains that linear desktop/mobile history.

## Changes

- Mobile navigation: all four existing buttons have a passive ambient aura;
  real Home/tab-switcher/menu state still controls stronger selection. New tab
  remains a momentary action. Passive aura does not mark a button selected.
- Color: reuse the resolved active-page appearance color already supplied to
  pull-to-reveal. Preserve hue for useful page colors; use Google blue
  `#4285F4` when the color is absent/neutral. No extra captures or page sampling.
- Omnibar: a subtle ambient tint inside its existing glass Backdrop, with
  220ms palette transitions; no additional overlay, blur, or viewport inset.
- Status: soften the existing status-height gradient, read existing reveal state
  to suppress its protection during pull-to-reveal, and restore it afterward.
  The approved `ArcPhonePullReveal.java` is byte unchanged, including colors,
  progressive corners, animation, translation and gestures. System visibility
  and insets remain owned by the existing native controls.
- Desktop favicons: resize the native fixed favicon **container** along with
  its artwork, rather than extending an ImageView past its clipping parent.
  Normal box 22dp, expanded pair 45×22dp, compact pair 32×22dp. Restore native
  sizes/margins/gravity when leaving desktop mode; preserve stale callback guards.
- Sidebar: titles gain another 1sp (native +2sp total), buttons 13→14sp,
  favorite tiles 48→50dp with 26dp optical icons and 56dp grid slots. Reserve
  whole rows after resize. Expanded native tab height gains another 2dp;
  minimum active-row radius becomes 11dp. Collapsed 52dp rail is unchanged.
- Command editor: remove a redundant detach/attach during opening so the real
  focused editor can receive and replace URL text. Complete the native tablet
  focus transition under the command overlay rather than playing a second
  focus-loss animation after closing. Preserve ordinary native tablet behavior.
  Closing uses the existing noneditable address proxy in the same transition;
  top omnibar/frame geometry remains unchanged.

Camera orientation, videoconference media/permissions, UA/Client Hints, compositor,
SurfaceView, native session, website zoom, WebContents and pull-to-reveal source
are outside the modification scope. F06 pixelation remains observed with pending
cause; this patch does not claim to fix it.

## Validation and delivery

Local verification on the final source:

- Integrated phone/command/glass/reveal/material/status suite: **244 passed**
  across SDK 30/36, including the real-editor key routing and close crossfade.
- Collections: **42 passed**; sidebar appearance: **30 passed**; delivered
  split favicon binding: **14 passed**.
- SDK preparation: **6 passed**; isolated real AAPT2 portal fixture: **18 resources
  compiled**. These do not establish a full Chromium native build.
- Verified installer/updater guard suite: **16 passed** (private harness).
- Generated patch/manifest reproduced identically twice; `git diff --check`,
  Python compilation, build-shell syntax and actionlint passed.
- Complete host suite: **517/517 passed** in 890.343s, with configured SDK/AAPT2; one final aggregate run.

Robolectric tests exercise real Android views, shaders and layout with explicit
native/graphics boundaries; they do not prove Samsung pixel rendering.

Physical acceptance remains **PENDING_DEVICE**: halo visibility/contrast across
pages, smooth close/real editing in both omnibox positions, favicon containment,
small/split windows, IME, theme changes, reveal corners, lifecycle and camera
calls require the resulting APK. No capture containing owner data is published.

Only one authorized incremental native chain will be dispatched after the host
gates pass. Reuse `archium-checkpoint-40819836489-1`; never fall back to a clean
build. The verified installer checks source/run identity, ARM64, APK hash,
package/signing identity and the installed bytes before reporting installation.

Old checkpoint cleanup is restricted to the eight artifact groups belonging to
`archium-checkpoint-40545718060-1` and `archium-checkpoint-40447986255-2`.
The four protected groups of `archium-checkpoint-40819836489-1` remain available;
actual restored bytes must still be verified by CI. APK and receipt artifacts
are retained. Private cleanup and installer receipts stay outside the repository.
