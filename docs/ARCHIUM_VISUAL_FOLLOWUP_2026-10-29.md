# Archium visual/functional follow-up, 29 October 2026

Reference: the original `/storage/emulated/0/Download/ARCHIUM_META_IMAGEN_4_EXACTA.png`,
807 × 408 px, SHA-256
`612106d26f3934f770160a014f567e4101da90f1388175cf1b717cef9bd82e1a`.
The downloaded copy was compared by SHA-256 with the phone file. No regenerated
render was substituted. Owner screenshots remain local and private.

Installed baseline: run `40865729895`, source
`dba6ff7575970339db6fe855df4b709e4312056a`. Pending mobile aura fix
`d8f5e687f3e6da47038806373b399aa67403a771` is an ancestor of this follow-up.
All previous desktop FIX/polish, mobile premium/dynamic-color changes and the
supplier-API/preflight fixes remain in the same linear history.

## Findings and implementation

| Area | Evidence before change | Delivered source change | Validation scope |
|---|---|---|---|
| Address entry | Physical single click opened and selected the URL; consecutive origin clicks closed the panel, leaving typed input without visible editor. | Keep origin-hit focus while the address panel is alive; remove the double-tap-timeout cutoff. Consume the complete origin gesture; real outside clicks still close normally. | Regression failed on API 30/36, then passed with 12 delayed origin gestures per case. Physical acceptance of the new APK pending. |
| Top omnibox left curve | Native glass refresh could reinstall the sidebar capsule in integrated top/command mode. | Integrated editors retain transparent backgrounds. Exiting command mode explicitly rebuilds sidebar glass. | Delivered native method bodies tested through synthetic parent/drawable boundaries, including actual command-exit transition. Not full native drawing. |
| Toolbar/sidebar continuity and lower white line | Top toolbar used a different solid fill, native fixed background/hairline and a separate glass edge. | A single frame-aligned gradient feeds the existing toolbar. Its fixed background and hairline become transparent while the Arc frame is supplied; native mobile restoration remains explicit. No new toolbar or editor. | Native toolbar hooks exercised at synthetic widget boundaries and SDK preparation gate. DeX drawing pending. |
| Exterior contour | Owner clarified that the desired rounding is the outer Archium contour, not just the web viewport. | Existing DecorView receives one 24dp outline, restored on exit/destroy. Keep original inner viewport radius 16dp and 8dp inset: the radii are concentric. No window-translucency flag, background replacement, new overlay, GPU flag or surface transaction. | Real Android decor outline, resize and restoration tests; pure geometry. Samsung caption/leash/shadow remains system-owned. Actual visible transparency/crop at all four exterior corners requires the next APK on DeX. |
| Favorite mosaic | Second row visibly sliced. Regression measured 76px viewport for two 54px rows at mdpi. | Allocate full grid rows (108px for two rows), recompute on width/count changes, count root padding in shared height budget and retain menu/scroll fallback. | Real collection views, short-window menu, focus, refresh and resize regressions. New APK pending. |
| Pair favicons | Two icons were compressed into a native single-icon box. Physical report and code path confirmed; no completed isolated physical acceptance. | Separate 41×20dp expanded / 32×20dp compact pair box, minimum 20dp normal box and native-size restoration. Preserve artwork, tint-free callbacks and stale-generation rejection. | Actual sizing helper and delivered binder callbacks tested on Android views; layout/model/fetch boundaries are fixtures. DeX pixel sharpness pending. |
| Sidebar readability | Owner requested slightly larger type and active row. | Sidebar buttons 12→13sp; native titles +1sp once, restored on mobile; expanded rows +4dp; native rounded row shape minimum 10dp, restoring original radius. Collapsed rail width and height contracts unchanged. | Typography idempotence/mobile restore, outline tests and existing native binding gates. Physical final legibility pending. |
| Color action | Sweep-gradient rainbow icon did not match camera/info family. | Shared 24-unit palette vector, same stroke/cap/join and theme tint, 44dp target, existing tooltip/listeners. | Shared glyph optical-box and collection/action tests. No camera action code changed. |
| Mobile aura | Installed aura was hard to see outside its icon. | Includes `d8f5e68`: broader visible shoulder, page-derived color, max 14.1% alpha, transparent edge, existing contextual states. | 226 cases passed in its commit; expanded phone suite includes it. Still needs new APK. |

## F06: pixelation observed; cause and fix still pending

During this session the owner reported the episode live. Captures at
`2026-10-29T14:20:42Z` and a later sample show both split web panes pixelated while
sidebar/native controls and the other window remained sharp. SurfaceFlinger,
window state and logcat were saved before altering focus. The Chromium buffer
remained 1979×1152; the compositor dump reported no cached GPU-blurred images for
the observed child surface. A subsequent bring-to-front sample was sharp without
reload, cache clear, GPU changes or zoom adjustments.

This establishes the observed symptom and a focus correlation, not proof of
thumbnail fallback, renderer raster scale or a specific lifecycle cause. No F06
behavioral correction is claimed. Status: `OBSERVED / PENDING_CAUSE`, not `PASS`.
Private receipt: `.local/state/archium-visual-followup-20261029/F06-receipt-private.json`.
Do not upload raw screenshots/logs; they contain owner data.

The existing read-only `scripts/capture-arc-renderer.py` remains the diagnostic
collector. For DeX, also capture the physical display explicitly (discover its ID
with `adb shell dumpsys SurfaceFlinger --display-id`) before any focus, resize or
reload. Correlate its PNG with the collector's UTC/uptime, SurfaceFlinger, window,
framestats and renderer logs. Capture a second sample after a controlled focus
change. Capture itself is not functional acceptance.

## Physical-session limits and cleanup

The short authorized untouched session covered single/consecutive address clicks,
visible typing/suggestions, collapse/expand and a reduced-height window sample;
bounds were restored to `[166,53][2161,1221]`. It did not complete the original
12+6 physical acceptance matrix or Ctrl+D, native bookmark moving, camera calls,
PiP/share, themes and mobile/DeX acceptance for this candidate. The owner later
used split and reported F06. Subsequent captures document that episode separately.

The local CDP attempt to open an isolated fixture returned HTTP 500; no successful
fixture tab or bookmark action is claimed. Its temporary HTTP server was stopped
and the forwarding removed. No owner tabs, bookmarks, profiles, caches or settings
were deleted/reset. Camera controls/UA/Client Hints/permissions and the approved
pull-to-reveal implementation are unchanged.

## Build/install handoff

One native incremental chain only, after host gates. Successful run `40865729895`
has no new compiled-workspace checkpoint artifact. Reuse verified
`archium-checkpoint-40819836489-1` (source `677c73f...`), whose immutable receipt is
already versioned. Validate current artifact IDs/digests/expiry again, and require
capacity/full part hashes/restoration in CI. No clean fallback or parallel native
workflow. The candidate includes the pending mobile commit and this follow-up.

Reuse the verified background installer with Termux API notifications. Require
exact source SHA, native receipt, package, ARM64, checksum, certificate and device
identity; defer active media capture and device disconnection. Installation and
Samsung visual/functional acceptance remain pending until actual receipts exist.

## Local verification receipt

- SDK preparation/production adapter gate: PASS; six session boundary cases PASS.
- Full host suite with Android 36 jar and AAPT2 37: **516/516 PASS** in 629.563s
  on the Termux/proot host. Negative-fixture messages are not product failures.
- Expanded real-view Robolectric suite: **230 PASS**, APIs 30/36.
- Collection real-view suite: **42 PASS**, including full-row budget and compact menu.
- Sidebar appearance/title/sizing suite: **26 PASS**, APIs 30/36.
- Delivered pair binder/callback suite: **12 PASS**, APIs 30/36.
- Native topbar and toolbar method probes: PASS at explicitly synthetic boundaries.
- Independent read-only review found a command-exit glass restoration gap; an actual
  command-exit regression reproduced it, the source was corrected, and review
  confirmed the blocker addressed. No additional API/module blocker was reported.

These are host results. No native build or physical pass is inferred from them.
Logs and raw captures stay in the private local state directory; only this
sanitized receipt is versioned.
