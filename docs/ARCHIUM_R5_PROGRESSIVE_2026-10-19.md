# R5 progressive repair audit — 2026-10-19

Status: **READY_FOR_SUPERVISED_INCREMENTAL_BUILD**. The user's QEMU and
Autonomous Supervisor annexes supersede the earlier physical-DeX gate. The
supervisor owns continuation, bounded technical repair and installation auditing;
Codex ends its active turn after the independent supervisor is verified.

The Surface crop lifecycle defect has a tested minimal fix. P0-01/P0-02 and
post-fix GPU/device acceptance remain pending; R5.2 is not claimed complete.
No new APK or runtime success is claimed by these host tests.

## Baseline and checkpoint

The fresh repository checkout is isolated at `/workspace/Archium-R5`, branch
`assistant/archium-r5-arc-experience`, starting at
`31ba1de` (full identity in git). No protected branch is edited.

Authorized ADB reports SM-S931B, Android 17, `arm64-v8a`, installed package
`app.archium.android`, version 157.0.8086.0 / 808600074. Installed APK SHA256:
`cca0e5eba76bab179c5ae132dcb3353bfeb9e2d32dcc652a65d6bef8c3b4064d`.
The downloaded run 38602932971 artifact passed SHA256SUMS and apksigner verification;
its report identifies source `90d3f9e5be9bccc047ebba5115aff3ae8a610e5f`, Chromium
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` and the source checkpoint below.
Its SHA256SUMS digest exactly matches the independently measured installed APK
digest. The verified signer SHA256 is
`32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`.

Latest candidate checkpoint: `archium-checkpoint-38511423805-1`, source run
38511423805, source commit `0abfc9f03e34c23762190365ccb0cf6f9e5c3260`.
The four unexpired groups are exactly:

| Group | Artifact ID | ZIP bytes |
| --- | --- | --- |
| 00 | 11871517881 | 8589940572 |
| 01 | 11871884143 | 8589935970 |
| 02 | 11871749444 | 8589935970 |
| 03 | 11872500508 | 738433380 |

Authenticated HTTP Range read obtained its manifest using only 5381 bytes;
[manifest](evidence/2026-10-19-r5-progressive/source-checkpoint.json) SHA256
`50d9ad33ed84646d15368c696ff74fd103a7a9ef5e5829c152c399b95ccea56f`.
It declares 25 parts totalling 26508236988 compressed bytes, Chromium pin as above,
source commit/tag as above, schema 1 and workspace
`/home/runner/work/_temp/chromium-archium`.

The source run failed genuine native theme tests; subsequent successful run
38602932971 demonstrably restored this checkpoint, passed genuine Robolectric/JNI
and published its APK. That historical successful restore is evidence of reusable
work, not a current restore or a reason to classify the earlier failure as a
recoverable BUILD_INCOMPLETE.

The candidate's source commit and current config have identical `archium-args.gn`
SHA256 `81ce4e68968921b23f0f494eebfa8d469528c8bd37217dbbf6d987a80abf7d24`.
Schema 1 does **not** bind GN/toolchain/output inventories separately. Therefore
approval still requires runner capacity, every part hash, restored Chromium and
depot_tools HEAD, actual restored GN args and working intermediate outputs. No
local full download/restore was attempted: local free disk was about 71 GiB and
fails the existing pre-download requirement of 75 GB plus archive bytes.

`baseline-build.yml` is the existing dispatchable caller for the reusable
`archium-r5-stage.yml`; no new workflow or clean fallback is necessary. Caller
permissions and the authenticated account permit Actions dispatch. A future run
must use the exact candidate source triple and its new reviewed expected SHA,
then use only its own verified complete successor checkpoint.

## Test-first repairs

### Surface crop lifecycle

`applyActiveSurfaceClip()` installed a fixed `clipBounds` but listened only for
holder layout and Surface attachment. The active Surface can initially have size
zero, or resize independently of the holder; its old empty/undersized clip then
persists. The Android view regression executes the delivered crop/restore methods
and delivered layout callback with real Robolectric `SurfaceView` objects. Only
Chromium's active-surface getter and frame entry point are construction adapters.

[RED](evidence/2026-10-19-r5-progressive/surface-red.log): both methods fail on both
SDK30/36 profiles. An initially empty Surface retains `Rect(0,0,0,0)` after growing;
a resized content-only Surface retains `Rect(0,0,348,600)` instead of
`Rect(52,0,400,600)`.

The fix registers the existing layout listener on the active Surface and removes
it before replacement/restoration. [GREEN](evidence/2026-10-19-r5-progressive/surface-green.log):
4 executions pass, including preservation of original crop and obsolete-listener
cleanup. [Negative mutation](evidence/2026-10-19-r5-progressive/surface-negative.log)
removing that registration reproduces all four failures with the final fixture.

Reproduce with JDK21 and a Robolectric 4.16.1 + JUnit 4.13.2 classpath (including
AndroidX monitor/idling classes and android-all API36):

```sh
python3 scripts/test-robolectric-r5-surface.py \
  --classpath-file /path/to/classpath.txt --java-home /path/to/jdk21 \
  --work .test-build/surface
# Add --omit-surface-layout-listener for the historical negative mutation.
```

This fixes a demonstrated crop lifecycle defect. It does not establish that the
reported scroll corruption, invisible native dialogs or all disappearing-content
cases share this cause. No GPU workaround, global scale, cache purge, tab recreation
or change to the Arc/Portal palette is introduced.

### Incremental compatibility guard

The build previously copied current GN args over incompatible restored args and
continued toward native compilation. The new regression first went
[RED](evidence/2026-10-19-r5-progressive/gn-args-red.log) because that simulated
routing reached complete=true instead of blocking. It now fails closed with
`BLOCKED_CHECKPOINT_INCOMPATIBLE` before installing dependencies or transitioning
patches, leaves args intact, and never starts Ninja/publication. Routing tests are
explicitly synthetic; they do not certify a Chromium build.

## Device probe and handoff gate

[Deterministic page](../tests/fixtures/rendering/r5-compositor.html) contains 80
local image/text tiles, canvas, sticky/fixed/transformed/paint-contained content,
scroll cycles, alert/confirm/prompt and HTML dialog, and viewport/DPR/scale metrics.
[Protocol](../tests/fixtures/rendering/README.md) covers phone/DeX, incognito,
resize, focus, mouse/touch and restoration. No external/private content is loaded.

Only the phone display was enumerated; no DeX external display was present.
An authorized VIEW intent was sent to a fresh local fixture tab, but a phone
capture showed another app, so no Archium screenshot or visual PASS was obtained.
Private captures and narrowly scoped package logs stay outside git. Existing
linker/GPU/vendor messages alone do not establish a compositor root cause.

The earlier optional physical-device question is superseded. No Galaxy/DeX is
required for Android testing. All future runtime execution goes through the
isolated QEMU job; hardware-specific results stay PENDING_DEVICE_VALIDATION.
The existing authorized native helper is used only to launch a separate Termux
session, not to test Archium on physical Android.

## Progressive supervisor

`baseline-build.yml` dispatches the first exact SHA and source tuple. It calls
host gates, the reusable native stage, then a separate QEMU validation job. Native
stages publish an exact machine receipt even on failure. Only exit-zero controlled
BUILD_INCOMPLETE with verified packed groups and the expected failed budget
sentinel can continue; compiler/test/JNI/resource errors cannot masquerade as it.

Host/Robolectric/resource gate receipts are preserved in `out/Archium` and keyed by
exact implementation SHA, GN args and pinned toolchain. The same-source successor
requires a verified controlled receipt to reuse preflight. A repaired SHA reruns
preflight and invalidates the source-dependent gate receipts. Ninja resumes its
preserved dependency graph and outputs; no clean fallback exists.

The Termux entrypoints are installed at `~/.local/bin/archium-r5-monitor.sh` and
`~/.local/bin/archium-r5-monitor-launch.sh`. The source versions live under
`scripts/termux/`. The native-session probe ran under Termux parent PID 4388,
SID 22290, `/dev/pts/1`, separate from the coding session `/dev/pts/0`.
This proves the launch mechanism, not that a production supervisor was active
before the dispatch/first-heartbeat verification recorded in runtime state.

`scripts/archium-r5-supervisor.py` wraps the tested progressive monitor. Its private
persistent state is `~/.local/state/archium-r5-progressive/state.json` in native
Termux (`/workspace/.local/state/archium-r5-progressive/state.json` in PRoot).
It records original Codex session ID, exact SHA/RUN_ID/source tuple, last verified
checkpoint, stage, attempts, per-cause repairs, gates, QEMU, installation, events,
heartbeats and evidence. Atomic writes, locks, durable dispatch nonces and phase
replay prevent duplicate runs/workers after restart.

Normal polls begin immediately and follow 600-second monotonic deadlines. Bounds
are six total new runs, two repairs per cause and ten hours. Known checkpoint,
quota, auth, disk, signature or QEMU infrastructure failures block without waking
Codex. Repeated unknown failures stop; no destructive fallback is used.

Codex CLI 0.163.0 was inspected locally and supports `exec resume SESSION_ID -
--json`. The exact original rollout exists. No real resume was launched while the
original turn was active. Resume execution is armed for technical events only;
its first streamed thread.started must match the saved ID or the subprocess is
terminated and CODEX_RESUME_BLOCKED is recorded. Capture includes prompt, JSONL,
stdout, stderr, exit status and result. A fixture subprocess verified mismatched
thread rejection and durable replay without a second execution; that is not a
claim that a real Codex repair event has occurred.

The repair worker may commit/push a minimal RED/GREEN correction but cannot dispatch
or start parallel agents. The supervisor checks clean branch/remote SHA, test
evidence hash and GN compatibility before authorizing its next incremental run.
A source change keeps the older checkpoint source commit/run identities separate.

## QEMU and installation scope

[QEMU report](validation/R5_QEMU_REPORT.md) records independently verified historical
APK bytes and the actual local QEMU_ABI_BLOCKED observation. The job regenerates
32 individual runtime case statuses for its exact same-run APK. A bare startup
cannot pass the full matrix. No available native ARM64/KVM/emulator/image means
BLOCKED, not simulated Android PASS or an x86 Chromium rebuild. Disposable QEMU
data/cache paths do not wipe an existing AVD's user data.

The supervisor stops new dispatches if the mandatory QEMU runtime gate is blocked.
It retains the verified APK and records INSTALL_PENDING_DEVICE, without triggering
code repair for absent ADB. No unattended installation backend is claimed here.
A future authorized installer must supply `install-receipt.json` plus structured
Android inspection evidence and a separate installed-base APK copied from the
system. The supervisor parses the package path/dump, independently checks installed
APK hash, package/version and certificate against the artifact, then permits one
bounded post-install audit for that installation. Unrelated evidence and asserted
receipt identity alone are rejected. No INSTALL_SUCCESS or VERIFIED COMPLETE is
claimed without those observations.

Official execution references: [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive),
[Termux RUN_COMMAND](https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent).

## Verification ledger

- Android crop lifecycle: GREEN, 4 SDK30/36 executions; historical mutation RED, 4 failures.
- Incremental routing: GREEN, 28 cases; later Chromium/depot incompatibility marker
  assertions separately RED then GREEN, 2 cases.
- Java/API preparation: PASS on the installed API36 jar, including patch application.
- Real AAPT2 isolated fixture: PASS, 18 resources; no Chromium-resource PASS claimed.
- Generated patch and hash manifest: reproducible twice, exact hashes equal.
- Bash syntax, Python compileall and git diff whitespace: PASS.
- Independent code review: no Important/Critical findings. Review confirms listener
  removal/restoration, dispatcher teardown guards and pre-transition GN preservation.
- Full host suite before orchestration additions: PASS, 283 tests / 704.540 seconds.
- Added orchestration checks: monitor 13 PASS, supervisor 10 PASS (including review
  regressions RED → GREEN), QEMU 9 PASS, stage receipt 2 PASS, continuation 1 PASS;
  28 updated routing cases PASS plus same-source gate-reuse regression PASS.
- actionlint 1.7.7: PASS for the complete workflow set.
  Host GN is distribution version 1000 (5e19d2f), not a claim of DEPS-pinned CI GN.
- Actual device is awake/unlocked but ChatGPT is resumed; Archium task is not visible.
  No user interaction or unrelated application controls are manipulated.
- New native build/checkpoint restore and QEMU execution are pending the exact
  dispatched run. Real device/DeX and installation remain unverified. Runtime
  dispatch/heartbeat records hold the live run identity without changing its SHA.
