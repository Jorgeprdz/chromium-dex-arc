# R5 UI review and corrections — 2026-10-14

The installed APK was independently identified as Actions run `38519244024`,
source `86bc71d54b017762a399a905e145e78465366198`. The installed base APK and
published SHA256SUMS both have digest
`2f5e7d98da97c44f65df80a2f4e73525353adac6f86615e1a988251b64d59561`.
The Actions build report records native Robolectric/JNI/APK gates as PASS for
that **baseline**, not for these new changes.

## Actual device observations

On the physical Samsung SM-S931B, Android 16, an external DeX display was
captured before and after force-stop/relaunch. The first launch rendered the
expanded rail with vertically stacked compact navigation and missing extension
controls. Collapsing changed the rail icons while the viewport retained its
previous left edge. The lower-left viewport wedge was visible. The top address
bar and MOBILE site-version issues were supplied by the user and investigated
in source; they were not independently accepted on a corrected APK.

Evidence is private in `/workspace/archium-r5-evidence/review-*.png`; screenshots
include the user's existing browsing/session and are not committed. A loading
page subsequently timed out its connection; this is not reported as proof of
an opaque compositor/input failure. No user profile was cleared. The user was
told the external display could be disconnected after these captures.

## Changes

- Queue the initial appearance pass even if rail bounds are unchanged. Changed
  rail/content bounds schedule work outside the Android layout pass. This
  prevents compact initialization from persisting until the next manual toggle.
- Discover an extension host inflated after the shell is constructed. Expanded
  visibility does not reuse the temporary startup GONE value. Use the native
  extension width consumers with a persistent sidebar budget, including their
  asynchronous visibility callbacks; clear that override on mobile restoration.
- The top native address bar uses a rectangular transparent surface and holder
  dimensions, with no Fusebox expansion margins, elevated pill, GLIF or rounded
  hover foreground. Command ownership and native autocomplete remain intact.
- Move the color selector beside About, remove its header tile and reduce its
  visual wheel from 24dp to 14dp while retaining a 44dp hit target.
- Follow a committed rail resize with native composited-layer and input origins,
  preserve hover as an overlay, refresh after native Side UI specs commit, and
  grow Blink once before collapse. Do not resize Blink for every animation frame.
- Use SurfaceView-compatible round-rect outline clipping with the lower corners
  outside a rectangular crop. The lower junction is square; the hit region uses
  the same geometry on every supported Android API.
- Before recreating UI for MOBILE, update existing regular/private tab UA state
  and switch/reload loaded desktop WebContents through Chromium's TabUtils.
  Frozen tabs receive mobile TabUserAgent state; destroyed tabs are skipped.
- Add **Tipografía de la interfaz** to Settings, with sans, medium sans, serif
  and monospace choices. Store it independently of page settings and preserve
  text style. Apply only to browser controls, sidebar and settings. The root
  lifecycle applies it to controls in mobile as well as Arc. Remove observers
  on destruction and update recycled sidebar controls during layout.

## Verification scope

Each focused Android probe compiles complete delivered helpers or explicitly
extracted production method bodies. Construction/JNI/tab/compositor adapters
are named in its output; these probes are not Chromium APK acceptance.

| Check | Result | Scope |
| --- | --- | --- |
| Cold/layout/native input runtime probe | PASS, 14 | Android SDK30/36; cold regression RED then GREEN |
| Top/sidebar/header probe | PASS, 18 | SDK29/36; top regression RED then GREEN; cosmetic adapters |
| Appearance/font suite | PASS, 17 | Actual Android shadows and complete appearance class; window metrics adapter |
| Mobile/rail transition probe | PASS, 12 | SDK30/36; renderer/input origin, hover isolation, frozen/private tabs, font/lifecycle |
| Extension callback allocation | PASS, 2 | SDK30/36; native allocation/callback bodies, width-consumer adapters; RED then GREEN |
| Frame/outline probe | PASS, 10 | SDK29/36; actual outline/crop and native frame method; compositor adapter |
| Geometry policy | PASS | Real JVM; bottom-right hit-region regression RED then GREEN |
| API36 preparation | PASS | Pinned patch application/hashes and Java API contracts; native Chromium adapters |
| Physical Android helper | PASS, suite and process restart | Real UI font/style and persisted font/mode; Chromium/JNI boundaries simulated |
| Complete host suite | PASS, 282 / 845.741 s | SDK/AAPT2 environment configured; first run lacked two environment variables |
| Full new Chromium GN/Java/JNI/Robolectric/APK | NOT_RUN | Needs a new native build of these changes |
| Corrected-APK DeX geometry/touch/hover/mobile acceptance | NOT_RUN | Needs new APK and reconnection of the external display |

The physical helper uses disposable `app.archium.windowtests.reviewr5`, retaining
existing test-package signatures and the actual Archium profile. Its first
attempt encountered an outdated Profile adapter; the adapter was corrected to
match the pinned interface. A separate package avoids replacing the historical
helper signed by a different disposable key. Those failed preparations are not
reported as successful runtime tests.

The genuine Chromium top-hover regression is included in the native test
source, but is outside the bounded focus/layout adapter and remains a native
CI gate. Patch/hash manifests are regenerated from pinned originals, including
the exact pinned CompositorViewHolder source. No new build was dispatched and
no corrected Archium APK has been installed by this review.
