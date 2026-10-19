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
