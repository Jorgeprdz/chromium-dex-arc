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
