# R5.2B: absent-controls native-dialog regression

`NativeDialogGateProbe.java.in` is a harness, not a replacement presenter. The
runner extracts method definitions (matching the declared return type/name, not
call sites) from delivered source and pinned originals. The source catalog fixes
SHA-256 for every external input. Missing or mismatched inputs block execution.

Retrieve the catalog files from official Gitiles at the catalog revision using
`https://chromium.googlesource.com/chromium/src/+/REVISION/PATH?format=TEXT`, decode
base64, and preserve their relative paths in a private source directory. No
Chromium checkout, SDK image, Ninja action or architecture rebuild is needed.

```sh
python3 scripts/test-robolectric-native-dialog-gate.py \
  --pinned-source-dir /private/pinned \
  --classpath-file /private/robolectric-classpath.txt \
  --java-home /path/to/jdk-21 --work /tmp/r52b-dialog
```

Add `--baseline` for the negative control with the pinned unmodified presenter.
Robolectric/JUnit dependencies and Android SDK30/36 sandbox jars must be present.
The runner never changes those inputs, a checkout, outputs or the supervisor.

Real method bodies exercised: manager hidden ratios, BrowserControlsUtils gate,
ChromeTabModalPresenter show/readiness/offset/height/trace/remove methods,
TabModalPresenter enter/exit/remove, JavascriptModalDialog click/dismiss. The
native/JNI constraints, controls input state, property-model/resource inflation,
scrim and selection machinery are explicit adapters. The dialog is a real Android
FrameLayout child but its resources, animations' duration and custom view are
adapted. This does not execute the full Chromium class or its GN unit target.
It does not prove GPU presentation, WindowManager tokens, permissions or focus
restoration in the installed APK.

The delivered Chromium `ChromeTabModalPresenterUnitTest` also adds four cases
using its existing test subclass. Its full Chromium target remains pending CI;
no target was built during this no-build investigation.

## Directed device evidence after a separately authorized incremental build

Do not run a second twelve-case matrix merely to reproduce this known symptom.
Open the exact original content URI and select just one affected case. Capture
one opening and close/cancel with the correct logical and physical display IDs.
An observer reporting `shown` or JS returning does not prove visible pixels.

Opt-in metadata tag, disabled by default:

```sh
adb -s SERIAL shell setprop log.tag.ArchiumModal DEBUG
adb -s SERIAL logcat -v monotonic -s ArchiumModal:D '*:S'
# Perform one original-fixture dialog and preserve correlated screenshot/dumps.
adb -s SERIAL shell setprop log.tag.ArchiumModal INFO
```

These are future manual commands; they were not executed on the installed APK
in R5.2B. Never clear global logs or change graphics flags. Only transient
metadata is emitted: model/presenter/Activity/window handles, monotonic time,
thread/tab IDs, active controls position, heights/offsets/ratio, pending flag and
container dimensions/visibility/child count/focus. No title, origin, message or
prompt value. Correlate by process, model identity and request interval; model
identity hashes are process-local handles, not durable globally unique IDs.
Presenter events cap at 24 plus two close records; JavaScript bridge adds request
and close. No new view observers, retained models, windows or background process.

Expected root-cause signature in a failing APK with equivalent instrumentation:
`js_request(model=X)` → `show_request(model=X, active_h=0, hidden_ratio=1)` →
`show_deferred(pending=true, children=0)` without attachment before close.
Expected fixed signature: same absent-controls inputs followed by `attach_after`
with one child. Capture layout/draw separately: immediate post-attach dimensions
may still be zero before Android's next traversal. Real visual GREEN, focus,
window lifecycle and leak checks remain mandatory.
