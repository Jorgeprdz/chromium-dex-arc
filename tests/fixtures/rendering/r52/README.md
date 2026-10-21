# R5.2 bounded diagnostics

The original popup HTML is immutable and has SHA-256
`ea568bda931099858fc8d24336507d194bb60a6a0ef0e07ef7843fec87427dac`.
Open that original through its actual Android content URI. Do not silently serve
it from another origin: storage, activation and popup permissions may differ.
`original-observer.js` is optional metadata instrumentation, not a replacement
page; it does not replace click handlers. `window.__archiumR52.stop()` disconnects
it. Neither this observer nor ArcViewProbe was injected into the tested APK.

`r52-repaint.html` is a separate synthetic GPU repaint fixture, with no dialogs,
network or personal session. Use identical viewport, DPR, sidebar geometry and
phase before comparing screenshots. Wait for images to decode and two animation
frames; this is a sampling convention, not proof that pixels reached the display.
Capture reference/candidate PNGs externally. Supply explicit fixture-only ROI
rectangles in physical image pixels, excluding toolbar, taskbar and private UI.

```sh
python3 scripts/r52_forensics.py collect --serial SERIAL --event SYNTHETIC_LABEL --samples 3 --output /private/fresh-metadata
python3 scripts/r52_forensics.py compare --reference reference.png --candidate candidate.png --regions regions.json
python3 scripts/r52_capture_trace.py --serial SERIAL --output /private/fresh-plan
```

The trace command is plan-only. After placing only a synthetic fixture in front,
add `--execute --fixture-confirmed` for an independent eight-second Perfetto
session. Start a separately timed reproduction while it records. Add
`--raw-logcat-private` only for private evidence. The tool never stops another
trace, launches Archium, clears logs or changes GPU flags. Availability of each
Perfetto data source must be checked in the trace; an empty trace is not PASS.
Raw artifacts may contain system/window metadata: preserve privately and redact
before sharing. Metadata capture is bounded and non-atomic; synchronize UTC and
device local time with opening events. A container GONE when closed is normal.

For Java instrumentation, ArcViewProbe must run on the UI thread with an explicit
node budget; close its session to detach only its own SurfaceHolder callbacks.
It has not been wired into Chromium. To prove the proposed native-dialog gate,
an additional adapter must record BrowserControlsStateProvider hidden ratio,
heights/offsets, pending-enter flag, observer callbacks and add/remove events.
Do not alter flags or skip the gate simply to make a host test green.

## R5.2D layer boundary probe

`r52d-layer-reuse.html` is an additional synthetic page, not a replacement for
the original popup diagnostics. It has 96 cards, sixteen shared 768² PNG sources,
sticky/fixed elements, fractional transforms, multiply blending and paint
containment. `window.r52d.cycle()` performs twelve scroll/recycle steps and returns
to the original phase and scroll position. Await `window.r52d.ready` first.
Manually resize the window and restore its original geometry before comparing
explicit card ROIs. Different phases, viewports, DPRs or image placement are not
a valid pixel oracle. This new fixture has not been executed on Android yet.

After serving that exact filename on localhost and placing it visibly in front,
an operator can allocate a temporary CDP forward and run:

```sh
adb -s SERIAL forward tcp:0 localabstract:chrome_devtools_remote
node scripts/r52d-layer-probe.cjs RETURNED_PORT /private/new-probe
adb -s SERIAL forward --remove tcp:RETURNED_PORT
```

Use Node 22 or later. The probe performs no navigation, scroll, reload, Android
input or ADB commands. It selects only the synthetic localhost pathname. The
explicit `--amazon-homepage` argument instead permits only the exact Amazon MX
HTTPS homepage, without query or fragment; this mode requires an available
device and authorized homepage reproduction. Never run it on account/form pages.
It records at most 512 layers, three visible-image layer replays, bounded metadata
and private screenshots. It does not save text, titles, source URLs or inputs.
All output is private: screenshots can contain personalized images. Do not commit
or upload them. A metadata-stable pair is not a GPU resource identity guarantee.

`makeSnapshot` runs inspector lifecycle work and `replaySnapshot` uses a fresh
software bitmap in the pinned implementation. It is not a live tile/texture
readback. Treat clean replay plus corrupt composition as a narrower hypothesis,
not proof of the first failing GPU stage. Re-check after-snapshot presentation
because the act of inspecting may alter state.

`r52d-frame-timeline.pbtxt` prepares a separate eight-second gfx-only Perfetto
capture with process-name metadata. It has not been executed on Android. Raw
process/window information stays private. Use a unique output under
`/data/misc/perfetto-traces`, never stop another session, coordinate the action
within the capture, and inspect loss/import statistics before interpreting it.
This config does not by itself collect Chromium tile/resource IDs. Query
`Tracing.getCategories` and arrange an independently bounded Chromium trace for
that boundary; neither trace availability nor capture success is a visual PASS.
