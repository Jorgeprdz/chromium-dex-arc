# Desktop camera orientation and manual fallback

User authorization: fix, scope/plan, implementation, incremental build and verified install.
Branch: assistant/archium-r5-desktop-native-mobile. Baseline e1a86eba2b9d53b7e69618478c85aa0fbb30d62a.

## Scope and acceptance

- Neutral-page physical tests reproduce portrait output in DeX for front/rear cameras. Settings640x480 render/decode480x640; requested1280x720 renders720x1280. CSS transform none. Local WebRTC loopback is not a remote meeting.
- User confirms native Camera can show landscape. Forced logical phone rotations0/1/3 did not change Desktop output; physical-pose correlation and exact native mechanism remain unproven. UA-only Chrome/Linux override did not fix the neutral fixture; no claim of a full real-site Client Hints A/B.
- Preserve native sensor orientation. Calibrate camera output to requested aspect without stretching, arbitrary fixed90 rotation, website JavaScript injection or CSS-only correction.
- Native camera button beside extensions in the existing Desktop footer. Auto, Manual quarter-turns and Reset. Per-WebContents memory; no persistent cross-site/profile calibration, no fake extension.
- Process only real camera sources. Screen capture, microphone and Mobile remain untouched. Keep stream/track identity and permissions while changing manual calibration.
- Reuse VideoFrame wrapping/cropping and metadata; prioritize shared buffers. GPU-backed compatibility and actual receiver orientation require native/device gates, not stubs.

## Integration under validation

1. Existing ContentUtils JNI owner stores per-WebContents manual mode; pure ArcDesktopPolicyBridge resolves actual window mode. No duplicate JNI registration.
2. Propagate small camera policy through existing per-WebContents WebPreferences updates. Per-Page thread-safe state enables live changes without restarting capture.
3. Configure policy only for DEVICE_VIDEO_CAPTURE sources. Calibrate frames in the existing video-track adaptation path before local/encoder sinks, preserving ownership and upstream metadata.
4. New Desktop control reuses existing icon/menu/material and footer geometry. Reserve its measured width; do not widen sidebar or add a toolbar.

## Execution and evidence

- [x] Physical reproduction and cleanup: /workspace/.local/state/archium-camera-orientation-20261027/results.json. Phone config restored, original targets retained, camera released; no profile/cache erased.
- [x] Verify pinned preferences/frame adapters/GN owners and finalize exact frame math; actual native compile remains CI.
- [x] RED/GREEN delivered C++ policy tests: quarter-turn geometry, invalid inputs and independent state; actual size algorithm covers explicit portrait/landscape/square constraints and no upscaling. Pixel crop/encoder and Mobile/screen behavior require candidate device validation.
- [ ] Implement narrow native path plus live per-page policy; compile affected real entrypoints/API boundaries locally.
- [x] Implement Desktop camera menu and mode/lifecycle synchronization using existing material. Preparation/SDK compile passed; UI/device theme acceptance remains pending.
- [x] Final preparation/affected host gates and identical patch regeneration; delivered transitions from prior APK/source checkpoint preserve208/207 unchanged mtimes. Full host run501 preserved RED for two header assertions, corrected and rerun GREEN. Fresh final full suite/native/device gates remain CI/PENDING; no device acceptance inferred.
- [ ] Commit/push exact SHA; inventory newest compatible complete checkpoint. One baseline-build dispatch, skip_preflight=false, run_qemu=false, max_stages=12, no clean or automatic failure repair.
- [ ] Native Termux monitor/notifications and verified ARM64 APK update, preserving backup and data.
- [ ] Candidate physical matrix and real meeting confirmation; report PASS/FAIL/PENDING honestly. Stop if encoding, shared-image ownership, or output orientation cannot be proven safe.
