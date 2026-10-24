# R5 — fixes from phone and DeX reviews

Date: 23 Oct 2026 CDMX. Branch: assistant/archium-r5-desktop-native-mobile.
Starting SHA: cd84ed4f5e60d2f7ebdd4cfbf85bbd143ec69f8a, installed run40028214072.
Scope approved: reliability/ergonomics of existing features; no AI/VPN/sync/extensions or visual redesign. User explicitly chose compact controls on scroll with a visible Archium control.

## Candidate changes

- Collections: pass the open folder to the controller when pinning. A new pin or conversion from favorite uses that folder; repeated pin keeps entry identity without duplication. Existing callers retain root pinning semantics.
- Persistence: serializer/store already round-trip empty folders. Native PrefServiceAndroid::SetString previously only changed the preference, leaving its disk write batched. For archium.sidebar.state only, request PrefService::CommitPendingWrite on its existing sequenced task runner. No second store or UI-thread disk wait. This reduces the quick-force-stop loss window; it does not promise durability if killed before asynchronous I/O finishes or if storage fails. Native preference branch remains unchanged for other keys. Candidate restart acceptance remains pending.
- DeX crash: physical stack u9f.z -> dhg.a/r -> dfh.i/E -> i22 is consistent with the pinned tab-strip layer's offset-tag restoration during synchronous TopControlsStacker removal. Targeted decompilation of the installed APK and pinned source retained in evidence. TabStripTopControlLayer now detaches the holder, transition and completion callback BEFORE removing itself from the stack; this prevents calling a compositor scene holder already destroyed during Activity recreation. Tokens still released.
- Desktop pins: expanded rail shows the native title with Space foreground contrast in one native column. Collapsed/native layout keeps icon-only grid behavior; close/pin/tab model remain native. Existing native compact-title test now explicitly selects native mode; separate Desktop title/contrast test added. Width, Space model and split geometry unchanged.
- Mobile: native GestureListenerManager drives compact/reveal on scroll direction. Native FormFieldFocusedSupplier compacts when a web field receives focus, retaining that state after IME closes. No polling, site-specific rules, DOM/JS injection or UA changes. Same bottom view becomes a 96dp Archium capsule; tap restores four controls, long press opens its real menu, horizontal drag moves it aside. Long press on the expanded Menu compacts for pages without a scroll range; accessible hints explain both actions. Compact control remains >=48dp tall. NTP/Hub retain existing behavior.
- Top capsule slides/fades in180ms without resizing the native editor. Reduced-animation setting skips animation. Toolbar remains focusable offscreen for hardware address editing. Tab/URL/focus/fullscreen/lifecycle release the compact state; gesture and form observers are detached on destruction.
- Retained toolbar texture: MiniOriginBarController writes the shared suppression supplier independently, including false on hide. TopToolbarOverlayMediator uses that supplier to hide/show the composited texture. The live Arc overlay previously relied on the same mutable signal. A derived read-only consumer combines native suppression with active Arc reasons so native releases cannot expose an old composited toolbar alongside the live one. Static owner race reproduced RED/GREEN; physical disappearance of the old arrow/URL still needs APK verification.
- Fullscreen return: legacy toolbar margin uses stable status-bar/cutout geometry while the visible inset is temporarily zero. Pill dimensions unchanged. Android WindowInsets test reproduces the transient-zero case.
- PageInfo/native menus: surface decorator lookup first uses the owning root View, then the previous Activity-context fallback. Native ContentViews with window/profile contexts can attach the same existing sampler. No extra capture mechanism; native actions, permissions and security text untouched. Whether this fixes the actual opaque PageInfo on-device remains pending.

## Evidence and gates

Evidence root: /workspace/archium-evidence/r5-review-fixes/.

- collections-red.log: folder pin expected folder ID but got null, both SDK30/36. convert-red.log: favorite conversion also lost open folder. collections-final.log:32 Android executions PASS, native command boundary mocked.
- teardown-red.log, prefs-red.log, pinned-title-red.log, pin-contrast-red.log: delivered methods fail before their changes. lifecycle-final.log:4 cases PASS; native/JNI/dependency boundaries explicitly simulated. C++ probe compiles the delivered SetString body against a recording PrefService boundary. Full Chromium C++ compilation NOT RUN locally.
- phone-red.log/inset-red.log/drag-red.log: missing compact escape, unstable inset and stuck pressed state respectively. phone-final-candidate.log:159 Android executions PASS, original Chromium shadow policy79 methods; source capture/native actions remain explicit boundaries. Not device acceptance.
- scene-owner-red.log -> scene-owner-green.log: native release could expose cached toolbar while phone overlay active; candidate guard and Desktop/native reset PASS. adaptive-final.log:2 delivered-policy cases PASS, OS/JNI/animation delivery simulated.
- menu-root-red.log -> menu-root-green.log: ContentView with non-Activity context but valid owning root now attaches the decorator; unknown/unowned contexts remain native.
- host-phone-final.log:29 tests PASS before final drag/tint cleanup; host-phone-final-candidate.log records the final affected rerun.
- full-host.log:432 tests,430 PASS and2 FAIL because resource test SDK env was omitted. resource-repeat.log used Debian AAPT2, which cannot read the SDK37 resource table:2 ERROR. resource-sdk-repeat.log repeats unchanged tests with /opt/android-sdk/build-tools/37.0.0/aapt2 and SDK37.0:2 PASS, real18-resource fixture. The first full invocation is NOT reported as green.
- preparation-verified.log: isolated SDK37.2 compilation and pure/native-session probes PASS before final native test additions; preparation-final-candidate.log records final preparation. Does not compile all modified Chromium consumers.
- coverage-final.log:2 PASS, gates expanded to include VerticalPinnedTabListRecyclerViewUnitTest and TabStripTopControlLayerUnitTest. These native suites are delivered/selected but NOT RUN locally through Chromium runner.
- Patch/manifest generated from pinned originals. source-transition-result.json verifies sparse transition from198fe8a, preserving unchanged source timestamps. Fixture substitutes a synthetic sparse HEAD; full checkpoint bytes NOT restored or verified here.

## Acceptance and build

Candidate implementation is locally tested; installed Galaxy still runs cd84ed4. No Actions dispatch, monitor or APK installation in this change. No checkpoint deletion or clean build.

NOT RUN on candidate APK: scroll/reveal/manual compact/drag on varied sites, fixed headers/composers, no-scroll pages, IME open/closed with retained field focus, gestures, hardware Ctrl+L, TalkBack, all menus/PageInfo, both themes, automatic theme change, fullscreen/rotation/resume, DeX cold restart and empty nested folders. Status-clock contrast and text behind system indicators require physical confirmation; no universal overlap or graphical PASS claimed.

Native actual compilation/JUnit and physical acceptance remain required before calling the fixes complete. Amazon, external-window backdrop blur and pending NTP redesign remain outside this scope. Other-browser comparisons are product goals, not claims of equal security, speed or measured performance.

## Final local checkpoint

Final phone runner:159 PASS; collections:32 PASS; delivered lifecycle/persistence/title probes:4 PASS; adaptive/scene ownership:2 PASS; host phone:29 PASS; patch:25 PASS; gate coverage:2 PASS; SDK37.2 preparation PASS. Original shadow policy79 methods PASS. Native Chromium suites NOT RUN here, now explicitly selected for CI. Final patch197 files, regeneration identical; sparse source transition PASS,146 unchanged timestamps preserved. Receipts: patch-reproducibility.json, source-transition-result.json; full checkpoint byte verification belongs to CI.

Additional regressions caught during implementation: compact drag could leave pressed state active; narrowing after a drag could place the compact control outside the window; teardown during a reveal animation could leave an animator writing to released views. drag-red.log, compact-resize-red.log and animation-destroy-red.log preserve failures. Final candidate passes the corresponding local tests. Focus uses the existing native supplier and keeps compaction while editing even if scroll direction changes. Mobile/DeX physical acceptance remains NOT RUN for this candidate.

Status: READY FOR BUILD against available local gates; native integrated compilation/tests and candidate APK/device acceptance remain pending. No new run was dispatched.

## Follow-up: preflight run 40046612155

The single authorized incremental dispatch built SHA f6a998ab568f215747ebb7581ca9df5ddd097d27. Authorization passed; preflight failed before checkpoint restore/native compilation. CI ran434 host tests and reported one failure: test_r4_composited_toolbar extracted updateToolbarSceneLayerSuppression into a Java fixture without the newly called updateArcToolbarSceneGuard. This is a missing dependency in the host probe; native Chromium compilation was not reached.

The probe now includes the actual extracted guard method and its supplier, checks all16 combinations, and asserts that another owner releasing its supplier cannot release Arc's independent guard. No production code, generated patch, preflight policy or gate was weakened. Local RED reproduces the missing-symbol error; GREEN passes. Related adaptive/ownership suite:2 PASS. Evidence: run-40046612155-preflight.log, preflight-probe-red.log, preflight-probe-green.log, host-after-preflight-fix.log under /workspace/archium-evidence/r5-review-fixes/.

User explicitly authorized one new incremental attempt after this fix. Full local host rerun, final SHA and new run receipt are recorded separately when available. No native compilation or physical acceptance inferred from host tests.

Dispatch readiness: causal probe1 PASS and related adaptive/scene tests2 PASS; git diff --check PASS. Full434-test local rerun is still in progress, not reported as PASS. User reiterated immediate Archium dispatch; mandatory remote preflight remains enabled and independently reruns all gates before any checkpoint restore or native compilation. This follow-up changes only the host probe and documentation; production patch/manifest are unchanged from f6a998a.
