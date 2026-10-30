# Desktop follow-up ledger

Baseline: 0f5de40, existing linked worktree, clean at start.
Camera source processing is frozen; menu/default configuration only.
Version and footer proposal approved by owner. Earlier collected fixes remain
part of the follow-up, with physical Meet/Zoom observations in private local state.

Camera and capsule regression entrypoints are separate from portable host discovery.
`python3 -m unittest discover -s tests -p test_camera_angle_menu.py` compiles the
browser per-tab orientation default/storage executable with g++; it needs no JVM,
Android SDK, local Maven repository, or machine-specific classpath.

Run the Android checks explicitly with supplied dependencies:

```sh
python3 scripts/test-robolectric-camera-menu.py --classpath-file "$ROBOLECTRIC_CLASSPATH_FILE" --java-home "$JAVA_HOME" --work "$EVIDENCE/camera-menu"
python3 scripts/test-robolectric-omnibox-capsule.py --classpath-file "$ROBOLECTRIC_CLASSPATH_FILE" --java-home "$JAVA_HOME" --work "$EVIDENCE/omnibox-capsule"
```

Both runners use the supplied JDK and classpath and retain the original assertions.
Camera covers eight PopupMenu cases across Android 30/36 with explicit JNI and
WebContents boundaries. Capsule covers four cases across Android 30/36 using
verbatim delivered surface methods, real Android views/geometry/layer drawables,
and explicit Chrome native border/coordinator boundaries. Neither runner is
physical-device acceptance. They add no native-host CI Maven dependency.

Portability refactor rerun: browser default/storage 1/1, existing camera policy
3/3, explicit camera runner 8/8, explicit capsule runner 4/4. Logs:
`/tmp/camera-menu-portable-runner.log` and
`/tmp/omnibox-capsule-portable-runner.log`. Assertions were retained, and
`git diff --check` remained clean. Production files were not changed by this
runner refactor.

Owner subsequently authorized all implementation/build/install and requested Linux monitor; DeX disconnected. Owner then requested low quota operation (15% remaining) and explicitly allowed skipping unresolved Zoom. Zoom is deferred; no speculative factory, media eligibility or renderer-token change remains. Automatic Desktop/Mobile review passed identity10, appearance19, shell12 and external→phone roundtrip2; no behavioral source change warranted. Two Important independent review findings were fixed with RED/GREEN: compact favorites fallback budget (50 Android cases) and suppressed native extension click recovery. Camera frame processing freeze independently verified before release.

Final complete host suite: 528/528 PASS in 824.023s. Initial run528 had two integration failures (header inline virtual body and expanded glass test boundary), both corrected and affected tests rerun PASS before this fresh full run. SDK36 preparation6/6; footer24/24; collections50/50; camera menu8 and native policy3; phone244; tablet18; capsule4; About4; installer guards16. Patch regenerated identically twice. Native build and physical acceptance remain pending CI/device.

## Repair after run41013119275

The Java build succeeded (1138 actions); the early native Chromium Robolectric
About suite failed because its test expected the standalone fallback `desarrollo`
while the genuine compiled resource APK correctly contained Archium0.9.118.
The test now overlays a fixed, test-owned assets-only ZIP and asserts0.9.201 in
both environments. Local reproduction with that asset: two expected RED cases;
GREEN4/4 on SDK29/36. Production camera, PiP and UI sources are unchanged.
Checkpoint41013119275-1 has four groups/25parts, stage pack_verified and
checkpoint_verified true. Its exact immutable artifact IDs/digests and bounded
5381-byte manifest read are certified; restored full hashes remain mandatory CI
checks. Owner explicitly authorized the targeted repair and relaunch.
Checkpoint receipt tests8/8 and build-version tests5/5 passed. Remote complete
preflight is required again; no clean build, checkpoint deletion or gate bypass.
