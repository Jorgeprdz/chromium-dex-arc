# Archium R5 — specification and execution record

Base: `45865a0c3f3a2a0b360a15e13777f65208ec9582`, published R4 APK:
`39b1bcbfa6cd8f51e0b66a7eccdb9e586d8d78b3`, run 38322756782.
Chromium remains `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.

The user's R5 specification authorizes continuous implementation, testing,
branch publication, draft PR and Actions dispatch; it prohibits installation,
release, merge, signing changes and rewriting existing branches. It takes
precedence over additional skill design/plan approval handoffs.

## Design

1. Compact navigation uses the existing native Tab observer and buttons. Give
   collapse and Back separate 44dp rows; hide only Forward/Reload. Back stays
   visible, with native history controlling enabled state.
2. Persist Address Bar Position separately from UI mode. Sidebar retains the
   native holder. Top restores the same holder into Chromium's original toolbar
   and restores TopControlsStacker height reservation. Mobile always restores
   original parents/layout parameters. Do not add another omnibox/editor.
3. Command Bar uses the one native LocationBar holder and autocomplete session.
   A window-coordinate visual proxy animates to a wide rectangular surface;
   it has no input state. Native resolved navigation retains headers, POST,
   transition and callback while choosing a new tab only at confirmation.
   Tabs are enumerated only from the currently selected TabModel. Actions call
   existing settings/sidebar/Space operations. CLOSED/OPENING/OPEN/CLOSING
   govern interruption, cancellation, resize and destroy.
4. Preserve Chromium's status/security action and real extensions host. Do not
   advertise unsupported extensions or screenshot/zoom APIs.
5. R5 adapts the registered baseline workflow on the R5 branch only, referencing
   isolated R5 reusable workflows and build script. R4 branch/files remain
   untouched. Require exact R5 branch/SHA, global native concurrency, valid
   checkpoint manifest, pinned source, complete native/Java/resources/APK gates.

## Implementation plan

- Task 1: Android regression for compact buttons and native navigation, RED;
  implement layout/state, GREEN, diff check.
- Task 2: Preference and same-holder location switching regressions, RED;
  implement native toolbar reservation and restoration, GREEN.
- Task 3: Command state/input lifecycle/key/profile regressions, RED; implement
  complete panel, motion, native navigation integration; GREEN. Review upstream
  Fusebox SUGGESTIONS_POPOVER without enabling experimental flags globally.
- Task 4: CI branch/SHA/checkpoint/concurrency tests RED; isolate R5 workflows
  and script, GREEN; verify patch generation twice, host suite, actionlint.
- Task 5: Commit/push R5, draft PR, verify no heavy run, dispatch exact SHA once;
  monitor first errors, repair only with evidence; verify/download final APK.

## Review focus

Reparented LocationBarTablet direct parent and shared-window suggestions;
native navigation parameters; no tabs before Enter; private TabModel isolation;
focus restoration and listener cleanup; mid-animation resize/cancel;
mobile restoration; CI guards and checkpoint provenance; APK source/signature.

## Evidence policy

The four canonical images were downloaded privately and visually inspected.
They are not copied into this repository. Screenshot/transition acceptance
requires the R5 APK running on a device; host Android fixtures are not runtime.
Performance, Googlebook OS and Motorola remain NOT_RUN without measurements.

## Implementation ledger

- Compact navigation: missing setExpanded regression RED; complete production
  navigation helper GREEN, 8 SDK30/36 Robolectric executions with an explicit
  native Tab adapter. Current-tab callbacks and destruction remain observed.
- Placement/commands: absent helper RED; complete Android helper suite grew to
  28 executions. Index, unmatched Actions Enter, CLOSING confirmation and RTL
  mutations exercise the review findings; this is not full Chromium runtime.
- Native integration: LocationBarMediator receives already-resolved native
  params, preserves POST/headers/callback, and selects NEW_TAB only at commit.
  Actions cannot navigate; native input end closes/restores the surface. Three
  dedicated Chromium mediator regressions are blocking CI suites.
- Source pin, mobile paths, TabModel, browser security, renderer, GPU flags,
  signing and native password deprecation remain unchanged. No performance
  claim or comparison is accredited.
- Review: independent reviewer identified seven Important findings (initial
  palette, Sidebar order, Actions input, RTL, IME bounds, CLOSING confirmation,
  native session end). Corrections are in R5. CI intentionally fails closed
  if any other workflow is active, including host-only runs (minor limitation).
- CI routing: missing R5 script RED; six dispatch tests and 27 routing tests
  GREEN at explicitly synthetic native boundaries; real APK is still pending.
- Private canonical references A/B/C/D downloaded and inspected. Nothing from
  the copyrighted screenshots is redistributed.

## Scope and pending acceptance

Subsequent installed-APK failures and repair evidence are recorded in
[R5 runtime repair](ARCHIUM_R5_RUNTIME_FIXES_2026-10-14.md). The later user
instruction authorizing monitor installation supersedes the original
no-install restriction below. Successful build/installation is distinct from
runtime acceptance; DeX visual regressions were reproduced on the installed R5.

Site Control retains Chromium's real site identity/permissions control beside
its omnibox and installed-extension container. RDS/zoom remain native app menu
functions; screenshot action is not exposed. A custom combined Site Control
menu and the lower corner wedge are pending runtime diagnosis. Split View,
Boosts/Easels/Arc Max/Little Arc/advanced PiP are deferred to R6+.

ANDROID_RUNTIME, PERFORMANCE, Googlebook OS and Motorola are NOT_RUN for R5.
The user explicitly prohibits automatic installation. This session may verify
CI and download the APK but cannot call an R5 device test PASS from fixtures.

R4 signature reference (verified local published APK): certificate SHA256
`32a2fc74d731105859e5a85df16d95f102d85b22099b8064c5d8915c61dad1e0`.

## Local gate results before first CI dispatch

- HOST: PASS, 278 tests, 660.346 seconds, host-first.log.
- Android helper Robolectric: PASS, 28 SDK30/36 executions, final-green.log.
- Negative mutations: Sidebar index, Actions Enter, RTL and CLOSING each fail
  their new regression on both SDK profiles; production helper suite is GREEN.
- Java/API and patch application: PASS, check-arc-preparation on API36.
- AAPT2 fixture: PASS, 18 resources; full Chromium resources PENDING_CI.
- GN parsing: PASS for edited junit BUILD.gn and chrome_java_sources.gni;
  complete Chromium GN/JNI/native build PENDING_CI.
- actionlint/diff/compileall: PASS; generated patch/hash manifest idempotent.
- Source checkpoint metadata: four unexpired groups, source SHA and Chromium
  revision match bounded authenticated manifest. Full byte integrity and CI
  capacity remain blocking S0/S1 checks, not local PASS claims.

## Run 38483119466 — failed Java gate and correction, 2026-10-14

The run for f9ba7e6 FAILED; no APK was published or installed. First authentic
error at 2026-10-13 23:52:33 UTC: LocationBarLayout.java lines 237, 243 and
253 placed TYPE_USE-only Nullable before android.graphics.Rect. javac rejects
annotation of that qualifier. This was introduced by R5, not an SDK/network
failure. The earlier adapter preflight substituted a handwritten stub for
this API and therefore failed to detect the production declaration error.

Timeline from job 115592975541: metadata/capacity passed 23:25:39; checkpoint
download ended 23:33:45; restore/transition ended 23:44:37; complete restored
host suite passed 23:49:40; real Chromium resources passed 23:51:25; Java
failed 23:52:33. Quiescent checkpoint packing ended 00:11:12; four uploads
completed before run conclusion 00:15:11. No Robolectric/JNI/APK PASS applies.

Correction: import Rect and annotate that type directly. The new host
regression reproduces all three javac errors with the delivered declarations
and method bodies plus Chromium's exact TYPE_USE Nullable contract. It goes
RED before the fix and GREEN after it; reverting to qualified nullable types
remains a negative test. check-arc-preparation now compiles those real command
declarations/bodies rather than the old command stub, under TYPE_USE-only
Nullable. The superclass construction remains an explicit bounded adapter;
this is not claimed as a complete Chromium compile.

Fresh continuation checkpoint: archium-checkpoint-38483119466-1, source
f9ba7e64263bf715a0b908bfc20477b92f6a9d3b, four unexpired groups with 25
parts. Authenticated bounded manifest confirms the same Chromium revision
cfd94726b7b5fb48aedcc32662f2f3fbdbadec35. Byte integrity remains blocking
on restore. The next run uses this checkpoint and a new exact reviewed SHA.

Focused local checks after correction: two real javac annotation regressions
PASS, SDK/API preparation PASS, actionlint/diff/compileall/Bash PASS. The
previous full host suite 278/278 remains historical; CI must execute all 280
current host tests before downloading a checkpoint.

Later user instruction: "el monitor debe instalar el apk". This explicitly
authorizes automatic in-place installation by the Termux monitor after the
exact run succeeds and metadata/report/checksum/ABI/signature are validated.
It supersedes the initial no-automatic-install condition. The monitor compares
the actual installed certificate and never uninstalls or clears browser data.
Agent was paused while the first run continued; the failed-run report prompted
this focused correction and continuation.
