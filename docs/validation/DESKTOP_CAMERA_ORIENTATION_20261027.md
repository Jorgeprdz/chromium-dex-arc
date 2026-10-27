# Desktop camera orientation — candidate under validation

Baseline: `e1a86eba2b9d53b7e69618478c85aa0fbb30d62a`, branch `assistant/archium-r5-desktop-native-mobile`.

## Evidence and bounds

Physical neutral-page tests in DeX reproduced portrait decoded output: requested/settings 640×480 produced video/loopback 480×640; requested 1280×720 produced 720×1280. CSS transform was absent. Logical phone rotation 0/1/3 did not resolve it. A UA-only override did not resolve the neutral fixture; this was not a full website/Client Hints A/B. Samsung Camera landscape is user-reported. Exact sensor/display attribution remains unproven; no cache/profile deletion is justified.

Evidence: `/workspace/.local/state/archium-camera-orientation-20261027/results.json`. QA targets closed, original targets retained, camera released and phone configuration restored. User subsequently disconnected DeX; no network settings are changed.

## Candidate

- Browser-owned per-WebContents memory: Auto or manual 0/90/180/270. Existing ContentUtils owns its generated JNI header; a called-only bridge resolves actual Desktop mode independently of UA.
- Existing WebPreferences/Mojo transports one validated mode to a Page supplement. Atomic refcounted state crosses the existing video task runner and updates an active stream without restarting camera/microphone.
- Only hardware camera sources register the state. Native/Mobile disables adaptation; screen sharing never receives a camera policy.
- Existing VideoFrame wrapping and centered proportional crop target the requested display aspect. Native sensor transformation/mirroring is preserved and only explicit manual rotation is composed. No pixel-copy loop, new capture backend, CSS/JS injection, GPU change or sensor override.
- A native camera action beside extensions opens Auto/Manual/Rotate/Reset. Calibration belongs to the captured tab and remains memory-only. Footer width/height budgeting includes the action.

## Gates

| Check | Result |
|---|---|
| Pure delivered C++ policy: dimensions/quarter-turns/invalid inputs/context isolation | PASS locally |
| Full adapter preparation with actual Android SDK36 | PASS locally; Chrome/JNI boundaries are fixtures |
| Pinned WebContents preference callback and frame/transformation APIs inspected | PASS source/API inspection |
| Patch regeneration identical | PASS locally |
| Delivered patch transition from last APK and actual checkpoint source | PASS,208/207 untouched inputs retain mtimes; reconstructed pinned inputs and Git HEAD boundary explicitly mocked |
| Complete host regression suite | Initial run:501 tests, two failing subcases in one header-style gate; both corrected and affected gate rerun PASS. Final policy module:2 tests PASS. Fresh complete final suite remains mandatory in CI |
| Native Chromium compilation/link | PENDING CI |
| Candidate actual encoded camera orientation, front/rear/manual/reset | PENDING device |
| Camera + microphone + screen sharing, remote participant | PENDING real meeting |
| Desktop↔Mobile, no screen-capture changes, GPU-backed output/performance | PENDING candidate device |

A successful SDK/host check does not establish camera output or meeting acceptance. Cropping can reduce field of view to preserve the requested aspect. Candidate GPU-backed adaptation and receiver behavior require real native/device validation. No parity claim or guaranteed build success.

Local full-suite log: `full-host.log` (842.320s, preserved RED); `header-style-green.log`, `policy-green.log`, `googlebook-regression.log`, `preparation-final.log` in `/workspace/.local/state/archium-desktop-camera-fix-20261027/`. No assertion was removed or gate relaxed. The original `AllowsVideoThreadTypeOverride` body was moved unchanged to its existing `.cc` because the delivered-header gate now covers that newly patched header. Trace is out of line in its actual core GN owner.

Transition evidence: `actual-transition-proof.json` and `checkpoint-transition-proof.json`; upstream originals newly touched by this candidate were seeded by their certified pinned hashes into the reconstructed checkout. CI repeats the transition on the actual full restored source tree.
