# R5 polish implementation evidence

Base: `71da56fd2530d9a48813c9f9165c8fd98f501b36`. Same working tree and branch.
The original audit and owner screenshots remain local; private screenshots are not published.
Exact target `ARCHIUM_META_IMAGEN_4_EXACTA.png` was read from phone Download. The current
`122079.jpg` available in storage is only a 480px thumbnail; no high-resolution comparison is claimed.

## FIX checkpoint

`CODE CHANGED` is distinct from `HOST TEST PASS`, `NATIVE BUILT` and `PHYSICAL PASS`.

| Finding | Before | Change | Evidence / current acceptance |
|---|---|---|---|
| F01 | Native Ctrl+D did not project into the mosaic | Optional native bookmark completion callback; star uses same bookmarker; native ID observer projects edits; URL identity and write-before-native ordering | `tests/test_polish_favorite_identity.py`, collection JVM tests; `PARTIAL`, final device persistence pending |
| F02 | Native edit/picker could expose desktop | Public API30 `Activity.setTranslucent` scoped to runtime desktop mode, reevaluated on resume/configuration; native theme retained; adjustResize | `tests/test_polish_dialog_visibility.py`; `PENDING_DEVICE`. Intermittently absent buttons remain unverified |
| F03 | Second origin click dismissed moved editor | Bound double-click transaction consumes origin DOWN/UP, retains unique editor/focus; normal later outside click closes | `ArcCommandBarTest.secondOriginClickKeepsEditorAndLaterOutsideClickCloses`; `PARTIAL`, physical 12+6 matrix pending |
| F04 | Suggestions displaced by rail coordinates | Container converts window bounds against its actual layout origin once; re-evaluates after layout | `scripts/test-robolectric-r5.py` extracted production method on Android Views across parent offsets and RTL; `PARTIAL` |
| F05 | Independent mosaic/collections budgets starved tabs | Shared total collection budget including fixed chrome | `ArcCollectionsFocusTest`, `tests/test_recovery_geometry.py`; `PARTIAL`, 903×779 native tabs pending |
| F06 | Intermittent pixelation reported, not conclusively reproduced | No renderer/GPU fix asserted; bounded read-only capture tool | `scripts/capture-arc-renderer.py`; `PENDING_REPRO` |
| F07 | Top omnibox duplicate nav and empty reparented toolbar | Sidebar nav hidden in top mode; native toolbar stack suppressed during command transaction and restored afterwards | Existing toolbar contracts + helper probes; `PENDING_DEVICE` |
| F08 | Frame/corner discontinuity reported | Surface/holder outline and touch predicate share four rounded corners; no second OS window clip | `tests/test_recovery_geometry.py`; `PARTIAL`, four physical corners and top junction pending |
| F09 | Bitmap density changed favicon optical size | FIT_CENTER in a fixed optical box; neutral domain initial fallback; brand colors preserved | `ArcCollectionsFocusTest.faviconOpticalBoxIsStableAcrossBitmapDensitiesAndRefresh`; `PARTIAL`, final device refresh/restart pending |

Focused FIX checks: isolated SDK API/patch gate PASS; JVM favorite/dialog/geometry regressions PASS;
Robolectric helpers/coordinate probe **56 tests PASS**, collections **34 tests PASS** on API30/36.
These use explicit synthetic native/resource boundaries and do not validate an installed APK.
A source review caught and resolved same-tab/different-URL favorite overwriting and incorrect
sw600-only dialog scoping. Full SDK-configured host suite is recorded separately at final preflight.

## Renderer reproduction protocol

Use a synthetic page and synthetic account on the final APK; keep raw evidence private:

```sh
python3 scripts/capture-arc-renderer.py --serial DEVICE --output PRIVATE_DIR/before --samples 3 --screenshot
# Reproduce click/double-click, sidebar collapse, resize and split, noting device uptime.
python3 scripts/capture-arc-renderer.py --serial DEVICE --output PRIVATE_DIR/after --samples 8 --screenshot
```

Correlate UTC/uptime, SurfaceFlinger active layers and dimensions, display density/scale,
window bounds, gfx framestats and compositor log messages. Compare actual SurfaceView crop,
size, transform and renderer frame timestamp to the visible pixelation. Capture video separately
only on synthetic pages. A screenshot or successful resize alone is not proof of reproduction
or a causal fix. Do not clear caches/profile, change GPU flags, density or page zoom.

Camera capture, manual orientation, UA/Client Hints and permission paths are outside this diff.
Manual camera, Meet/Zoom, PiP/share, split, mobile and final DeX acceptance remain `PENDING_DEVICE`.
No native compilation has been dispatched at this checkpoint.

## VISUAL checkpoint: actual → exact image 4

| Area in current thumbnail | Implemented target | Verification boundary |
|---|---|---|
| Two large bookmark/Google cards | One lightweight bookmark heading with retained native bookmark action and compact Google menu | Existing listeners retained; final visual capture pending |
| 64dp tiles, density-dependent favicons | 48dp targets, 24dp optical artwork, 54dp responsive slots; narrow/short view uses explicit complete favorites menu | Robolectric size, colors, bitmap-density and reflow checks |
| Tabs start below a tall collections stack | Shared collection height; native scrolling list uses remaining height; existing New-tab row follows list above footer | Android View budget/menu checks; native DeX focus/resize pending |
| Neutral default/material and pale active tab | Lavender default, default active violet `#7365D8` with calculated contrasting text; custom/dark/incognito branches retained | Default/custom/contrast probes; physical theme matrix pending |
| Save/star/camera/info legacy artwork | Shared 24-unit vector path family, explicit dp bounds/scaling, pin and camera-orientation semantics | Optical path bounds, source/API compilation; native camera listener unchanged |
| Command panel and content corners | 16dp command/content radii; content outline and touch predicate agree at all four corners; existing gap/OS window ownership retained | Real Android outline probe at API36 plus pure hit tests; actual SurfaceFlinger/DeX corners pending |

Direct target sampling (807×408 original) found common sidebar RGB values `(217,205,244)`,
`(218,207,244)`, `(217,206,244)` in an interior crop. Chosen default `#DCCDF7` is a nearby
starting point, not a colorimetric calibration; material intensity and custom color choices remain.
The white vertical ChatGPT rail and the webpage are untouched. No OS window contour is clipped twice.

Additional focused results: collections/icon/menu tests **40 PASS** at API30/36; sidebar appearance
**22 PASS** at API30/36; material/contrast/draft tests **12 PASS** at API30/36; frame/palette/outline
**5 PASS at API36 only** (explicit compositor boundary); command/helpers/coordinates **56 PASS**.
A 48dp regression failed against the old 64dp implementation before the visual change.
Source review also caught density-dependent footer glyph sizing; explicit FIT_CENTER resolved it.

Same-size before/after installed-APK captures and physical four-corner acceptance are **PENDING_DEVICE**.
No synthetic render is presented as an installed build. F06 remains **PENDING_REPRO**.

## Final handoff contract

The user requested stopping once the sole incremental run is dispatched and the Termux installer
monitor is launched. The monitor must be bound to the final SHA and run ID, observe only that chain,
verify receipt/package/ABI/hash/signature, copy the verified APK to phone Download, and perform one
verified update without clearing data. It must defer installation while foreground media capture is
active. Termux:API notifications cover stage changes, failure/blocking, APK verification and install.
No independent native relaunches, repairs, GPU changes or storage resets are authorized by the monitor.
Build/install receipts and final SHA are recorded in the private dispatch directory, not invented here.

Final configured host suite: **506/506 PASS in 695.183s**, with
`ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2` and
`ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-36/android.jar`.
Earlier implementation checkpoint suite: **505/505 PASS in 819.080s**; the added dialog
policy test accounts for the later count. This is separate from the original audit's
502/504 plus configured 2/2 rerun. Isolated SDK/patch/native-session adapter gate PASS;
`git diff --check`, Python compileall, shell syntax and deterministic patch generation PASS.
Local actionlint is unavailable; the unchanged existing CI preflight retains its actionlint gate.

Checkpoint identity: unexpired four-group `archium-checkpoint-40545718060-1`, source
`8f312c0519ec143ae414723bf356d5212339827d`. Its artifact IDs/digests and downloaded manifest
match the repository's certified receipt. This verifies identity only; runner capacity and
all restored bytes are checked by CI before native work. No clean-build fallback is added.

The strengthened second-origin-click regression was counterchecked against audited HEAD
`71da56f`: **2 expected failures** (API30/36) with the original command bar, then **56/56 PASS**
with the delivered command bar. The fixture waits for posted Android click callbacks before
asserting, so a queued dismissal cannot masquerade as a pass.

Known limit: existing native bookmark records are never merged or deleted. If a native edit changes
one favorite's URL to another already-favorited URL, conflicting preexisting Arc identities are not
coalesced automatically in this revision. Normal repeated Ctrl+D/star saves for one URL converge;
this URL-edit collision case still needs a non-destructive conflict policy and device validation.
