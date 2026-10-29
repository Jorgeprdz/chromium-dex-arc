# Archium Mobile premium floating polish

Base: `677c73fcebd14d37b52ec68e2dffba627282c0bf`.
Branch: `assistant/archium-r5-mobile-polish-pending`, isolated worktree.
The mandatory dynamic-color annex supersedes the earlier fixed-blue design.

## Implemented

- Existing floating omnibar uses one refined `ArcPhoneGlass.Backdrop`, thin edge and subtle sheen. White/dark translucent roles retain native foreground contrast. Native rectangle, height, margins, editor and shadow owner are unchanged. Radius follows the native capsule (approximately 26dp at 52dp height).
- Existing lower bar retains **Inicio | Nueva | Pestañas | Menú**, order, labels, handlers, 48dp touch minimum, compact drag and native host ownership. Existing pills now paint a subtle elliptical aura with 14% peak alpha, transparent edge and 220ms property-only transitions.
- Aura uses page metadata from the **unchanged** `ToolbarThemeColorProvider.getArcPhonePageColor`, the same resolver used by reveal. Saturation/value are constrained per theme; blue is only the fallback when no chromatic source exists. Icons/text keep native contrast.
- Home selection means native Archium NTP, not an external configured homepage. Tabs follows the native HUB host; Menu follows the existing sheet lifetime; New gives a brief pulse and is never selected. Animations cancel on destruction/mode disable and honor disabled animations.
- `ArcPhoneStatusFade` receives the same metadata source. It derives a very light/dark tinted, translucent gradient, with protection adjusted conservatively for contrast. Hue/opacity changes animate over 220ms; a native light/dark indicator-role change is applied immediately to avoid temporarily opposing icon and backing luminance. Native `StatusVisibility`, system indicators, fade bounds and insets remain unchanged.
- An optional metadata observer survives the toolbar's intentional neutral-color clamp, deduplicates unchanged color/fallback events, and unregisters on destruction. No capture target, sampling loop, interval or compositor change was added.
- Existing sheet retains 28dp upper corners, native dismissal/back/scroll and existing handlers. Favicon uses FIT_CENTER; the domain is legible with end ellipsis/tooltip and secondary subtitle; quick actions use equal optical icons and subtle rounded tiles. Zoom is now minus / centered percentage / plus, with unchanged zoom logic and symmetric 48dp controls. More uses a dedicated three-dot vector. Favorite selection is read from the native bookmark model and remains distinct from pin state.
- A URL snapshot prevents a sheet left over from a previous URL in the same native tab from executing stale actions.

## Preserved

`ArcPhonePullReveal.java`, `SwipeRefreshHandler.java`, `ToolbarPhone.java` and `ArcCameraControls.java` remain byte-identical to base. Tests also compare the reveal binding, identity, gesture bridge, top-inset method, color resolver, status visibility owner and capture scheduling against base.

No changes to SurfaceView/compositor/raster/GPU flags, native bottom controls coordinator, viewport, IME/insets/fullscreen ownership, web padding/scale/zoom behavior, UA/Client Hints, permissions, camera capture or manual orientation. Existing pull's progressive two upper corners, 16dp cap, gap fill, transforms, touch mapping and refresh threshold remain intact.

## Local verification

- Baseline relevant Android suite: **206 PASS**.
- Added behavior regressions before production changes: **16 expected failures** across API30/36.
- Expanded Android suite: **224 PASS**, including palette/contrast sweep, state/lifecycle, menu/zoom, glass, status and all existing reveal tests. Native controller/actions/compositor boundaries remain explicit test fixtures.
- Phone ownership/geometry/input/focus/status contracts: **41 PASS**.
- Mobile rollback/ownership and premium immutable-source contracts: **15 PASS**.
- Native status theme-owner probe: **1 PASS**.
- Isolated SDK API compilation and pinned patch application: **PASS**; six existing native-session boundary tests also pass. This is local Java validation, not native APK compilation.
- `git diff --check`, syntax checks and deterministic patch/manifest generation are required before commit. Fresh source review found no substantive product blocker.

No native product build, APK or installation was performed during implementation. No workflow was changed and no direct Actions dispatch was made for this work during implementation.

## Deferred build/install authorization

The user subsequently explicitly requested a watchdog to build **and install** this candidate after the existing run `40819836489`. That supersedes the original NO BUILD / NO INSTALLATION handoff restrictions only for the deferred candidate.

Private watchdog code and receipts are separate from this visual commit. It must:

1. Wait for the exact existing run at base SHA to complete successfully with its product receipt, and for its older installer to settle. The current run/installer is never modified or cancelled.
2. Verify the pending SHA and a complete, unexpired checkpoint identity. Prefer a checkpoint from the completed run; otherwise use the existing certified incremental checkpoint. Runner capacity and restored bytes remain CI gates; no clean fallback.
3. Advance the remote build branch only from the exact base to this one reviewed descendant commit. A compare-and-swap lease prevents a moved ref from being overwritten. There is no merge commit or history rewrite.
4. Refuse a competing workflow; persist a unique dispatch intent and launch **one** incremental chain. Ambiguous submission is recovery-only, never a blind redispatch.
5. Verify source/run receipt, package, ABI, checksum, signing certificate and physical device identity before update. Keep the verified APK while the phone is unavailable or Archium capture is active; wait instead of interrupting media. Copy the verified candidate to Download and use the existing single-attempt verified updater, preserving app data.
6. Notify through Termux:API. A failed/blocked build or update requires review; no automated source repair, cache reset or uninstall.

## Pending physical acceptance

`DEVICE VALIDATION PENDING`: no claim of matching approved renders without installed screenshots. Required Samsung checks: both bars over white/dark/images, indicator readability, scrolling/autohide/touch reveal, IME, native hub/menu, sheet scroll/dismissal/zoom, all reveal animation frames and two corners, rotation/fullscreen and Desktop→Mobile return. Manual camera/Meet/Zoom must be checked on the final APK. Drawing/geometry tests do not establish compositor or device acceptance.

If integrating manually later, first stop the private watchdog to prevent a duplicate dispatch, then cherry-pick this single commit onto the next authorized build source and rerun relevant preflight. No PR is opened automatically.

Additional installer hardening is private to the watchdog: transient transport loss before any durable install attempt remains pending, while an ambiguous attempted install is terminal. Capture is checked again after verification/backup, immediately before writing the install intent, so a call starting during transfer does not get interrupted. Offline watchdog/installer suites: **33 PASS** (policy, single dispatch/recovery, reconnect/media guards, existing verified-update checks). These are simulated command boundaries, not actual installation results.
