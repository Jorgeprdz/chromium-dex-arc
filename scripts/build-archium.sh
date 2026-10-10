#!/usr/bin/env bash
set -euo pipefail

# This script may remove preinstalled SDKs ONLY on this project's disposable CI VM.
if [[ "${GITHUB_ACTIONS:-}" != true || "${GITHUB_REPOSITORY:-}" != Jorgeprdz/chromium-dex-arc ]]; then
    printf 'Refusing execution outside the dedicated GitHub Actions repository.\n' >&2
    exit 2
fi

readonly chromium_revision=cfd94726b7b5fb48aedcc32662f2f3fbdbadec35
readonly depot_revision=8a5434051036b32412a2ecb10c213a72e3f3ccb9
readonly build_workspace="$RUNNER_TEMP/chromium-archium"

build_phase="${1:---all}"
if (( $# > 1 )) || [[ ! "$build_phase" =~ ^--(all|prepare|work)$ ]]; then
    printf 'Usage: build-archium.sh [--prepare|--work]\n' >&2
    exit 2
fi
budget_value() {
    local value="$1" maximum="$2"
    if [[ ! "$value" =~ ^[1-9][0-9]*$ ]] \
        || (( ${#value} > ${#maximum} || value > maximum )); then
        printf 'Invalid stage budget: %s (maximum %s seconds).\n' "$value" "$maximum" >&2
        return 2
    fi
    printf '%s' "$value"
}
prepare_seconds=$(budget_value "${ARCHIUM_PREPARE_SECONDS:-3600}" 3600)
work_seconds=$(budget_value "${ARCHIUM_WORK_SECONDS:-14400}" 14400)
host_seconds=$(budget_value "${ARCHIUM_HOST_SECONDS:-1800}" 1800)
checkpoint_seconds=$(budget_value "${ARCHIUM_CHECKPOINT_SECONDS:-5400}" 5400)
slice_minutes=$(budget_value "${ARCHIUM_SLICE_MINUTES:-120}" 120)
script_started=$SECONDS
job_started=$(date +%s)
initial_elapsed=0
prepared_marker="$RUNNER_TEMP/archium-prepared-${GITHUB_RUN_ID:-local}"

job_elapsed() { printf '%s' "$((initial_elapsed + SECONDS - script_started))"; }

run_prepare() {
    local remaining=$((prepare_seconds - $(job_elapsed))) result=0
    if (( remaining <= 0 )); then
        printf 'Preparation budget exhausted; retaining the previous checkpoint.\n' >&2
        return 124
    fi
    timeout --signal=TERM --kill-after=30s "${remaining}s" "$@" || result=$?
    if (( result != 0 )); then
        printf 'Preparation stopped (exit %s); no new checkpoint identity published.\n' "$result" >&2
    fi
    return "$result"
}

save_checkpoint() {
    local final_status="${1:-0}" result=0
    printf 'CHECKPOINT: saving quiescent workspace; execution gates remain pending.\n'
    timeout --signal=TERM --kill-after=30s "${checkpoint_seconds}s" \
        python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" pack \
        "$build_workspace" "$ARCHIUM_CHECKPOINT_TAG" || result=$?
    if (( result != 0 )); then
        printf 'Checkpoint failed verification/upload (exit %s); continuation blocked.\n' "$result" >&2
        exit "$result"
    fi
    printf 'complete=false\n' >> "$GITHUB_OUTPUT"
    exit "$final_status"
}

run_work() {
    local signal="$1" limit="$2" timeout_status="$3"
    shift 3
    local checkpoint_on_failure=false
    if [[ "${1:-}" == --checkpoint-on-failure ]]; then
        checkpoint_on_failure=true
        shift
    fi
    local remaining=$((work_seconds - $(job_elapsed))) result=0
    if (( remaining <= 0 )); then save_checkpoint "$timeout_status"; fi
    if (( limit > remaining )); then limit=$remaining; fi
    timeout --signal="$signal" --kill-after=90s "${limit}s" "$@" || result=$?
    if (( result == 124 )); then
        save_checkpoint "$timeout_status"
    elif (( result != 0 )); then
        printf 'Work failed (exit %s); mandatory gates did not pass.\n' "$result" >&2
        # A compiler that returned normally has drained its backend. Preserve
        # its incremental outputs, while retaining FAILURE and blocking APK.
        # Signal/forced-kill exits cannot prove quiescence and never pack.
        if [[ "$checkpoint_on_failure" == true ]] && (( result < 128 )); then
            save_checkpoint "$result"
        fi
        exit "$result"
    fi
}

install_build_deps() {
    printf 'PREPARE: configuring bounded package downloads.\n'
    run_prepare sudo --preserve-env=GITHUB_ACTIONS,GITHUB_REPOSITORY \
        python3 "$GITHUB_WORKSPACE/scripts/configure-archium-apt.py"
    printf 'PREPARE: installing pinned Chromium dependencies (30 minute limit).\n'
    run_prepare sudo timeout --signal=TERM --kill-after=30s 30m \
        ./build/install-build-deps.sh --no-prompt --android
    printf 'PREPARE: dependencies installed.\n'
}

source_tag="${ARCHIUM_SOURCE_TAG:-}"
source_commit="${ARCHIUM_SOURCE_COMMIT:-}"
if [[ -n "$source_tag" || -n "$source_commit" ]]; then
    if [[ ! "$source_tag" =~ ^archium-checkpoint-[0-9]+-[0-9]+$ \
        || ! "$source_commit" =~ ^[0-9a-f]{40}$ \
        || -n "${ARCHIUM_PREVIOUS_TAG:-}" ]]; then
        printf 'Source checkpoint requires its exact tag/commit and no continuation tag.\n' >&2
        exit 2
    fi
fi

if [[ "$build_phase" != --work ]]; then
printf 'PREPARE: restoring/setting up this job (60 minute total limit).\n'
run_prepare sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/hostedtoolcache
available_bytes=$(df -B1 --output=avail "$RUNNER_TEMP" | tail -n 1 | tr -d ' ')
required_bytes=100000000000
# A verified Actions checkpoint has already consumed ~24 GiB as downloaded
# compressed input. During a resume, 75 GB free is sufficient for the proven
# ~56 GiB extraction peak plus reserve; the 100 GB rule is for clean checkout.
# Validate the archive hash before unpacking, then delete downloaded chunks
# only AFTER tar succeeds, reclaiming their disk for the incremental build.
if [[ "${ARCHIUM_CHECKPOINT_STORAGE:-}" == artifact \
      && ( -n "${ARCHIUM_PREVIOUS_TAG:-}" || -n "$source_tag" ) \
      && -f "${ARCHIUM_CHECKPOINT_DIR:-}/checkpoint.json" ]]; then
    required_bytes=75000000000
    printf 'CHECKPOINT_DISK_POLICY=RESUME verified-manifest-present (downloaded archive occupies disk)\n'
else
    printf 'CHECKPOINT_DISK_POLICY=CLEAN (100GB minimum)\n'
fi
printf 'DISK_PREFLIGHT available=%s required=%s\n' "$available_bytes" "$required_bytes"
if (( available_bytes < required_bytes )); then
    printf 'Insufficient disk space after cleanup: %s bytes; required %s\n' "$available_bytes" "$required_bytes" >&2
    exit 3
fi
df -h "$RUNNER_TEMP"
if [[ -n "$source_tag" || -n "${ARCHIUM_PREVIOUS_TAG:-}" ]]; then
    if [[ -n "$source_tag" ]]; then
        run_prepare python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" restore \
            "$build_workspace" "$source_tag" --source-commit "$source_commit"
    else
        run_prepare python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" restore \
            "$build_workspace" "$ARCHIUM_PREVIOUS_TAG"
    fi
    # Restoration deleted the downloaded archive only after checksum and tar
    # verification. Ensure the extracted checkout still has build headroom.
    available_bytes=$(df -B1 --output=avail "$RUNNER_TEMP" | tail -n 1 | tr -d ' ')
    printf 'DISK_POST_RESTORE available=%s bytes\n' "$available_bytes"
    if (( available_bytes < 30000000000 )); then
        printf 'Insufficient disk headroom after verified checkpoint restore: %s bytes\n' "$available_bytes" >&2
        exit 3
    fi
    df -h "$RUNNER_TEMP"
    export PATH="$build_workspace/depot_tools:$PATH"
    export DEPOT_TOOLS_UPDATE=0
    run_prepare bash "$build_workspace/depot_tools/ensure_bootstrap"
    cd "$build_workspace/checkout/src"
    install_build_deps
    if [[ -n "$source_tag" ]]; then
        run_prepare git -C "$GITHUB_WORKSPACE" fetch --depth 1 origin "$source_commit"
        run_prepare python3 "$GITHUB_WORKSPACE/scripts/transition-archium-patches.py" "$PWD" \
            --source-commit "$source_commit" --implementation-commit "$GITHUB_SHA"
        # Re-apply the audited binary launcher resource overlay on checkpoint transitions.
        run_prepare python3 "$GITHUB_WORKSPACE/scripts/integrate-archium-portal.py" "$PWD"
        cp "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn
        run_prepare gn gen out/Archium
    elif ! cmp -s "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn; then
        cp "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn
        run_prepare gn gen out/Archium
    fi
else
mkdir -p "$build_workspace"
cd "$build_workspace"
run_prepare git clone --depth 1 https://chromium.googlesource.com/chromium/tools/depot_tools.git
run_prepare git -C depot_tools fetch --depth 1 origin "$depot_revision"
run_prepare git -C depot_tools checkout --detach "$depot_revision"
export PATH="$build_workspace/depot_tools:$PATH"
export DEPOT_TOOLS_UPDATE=0
# Pinning disables gclient's automatic update/bootstrap. Initialize the pinned
# tools explicitly so GN's python-bin wrapper has its interpreter metadata.
run_prepare bash "$build_workspace/depot_tools/ensure_bootstrap"
run_prepare "$build_workspace/depot_tools/python-bin/python3" --version

mkdir checkout
cd checkout
cat > .gclient <<'GCLIENT'
solutions = [{
    "name": "src",
    "url": "https://chromium.googlesource.com/chromium/src.git",
    "managed": False,
    "custom_deps": {},
    "custom_vars": {},
}]
target_os = ["android"]
GCLIENT
run_prepare gclient sync --no-history --nohooks --revision "src@$chromium_revision"
cd src
test "$(git rev-parse HEAD)" = "$chromium_revision"
install_build_deps
run_prepare gclient runhooks

mkdir -p out/Archium
run_prepare python3 "$GITHUB_WORKSPACE/scripts/apply-arc-patches.py" "$PWD"
run_prepare python3 "$GITHUB_WORKSPACE/scripts/integrate-archium-portal.py" "$PWD"
cp "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn
run_prepare gn gen out/Archium
fi
# Applies to clean builds and resumed slices: resources must match approved Portal assets.
run_prepare python3 "$GITHUB_WORKSPACE/scripts/integrate-archium-portal.py" "$PWD" --verify
run_prepare python3 -m unittest discover -s "$GITHUB_WORKSPACE/tests" -p 'test_archium_portal_resources.py'
printf '%s\n%s\n' "$GITHUB_SHA" "$job_started" > "$prepared_marker"
if [[ "$build_phase" == --prepare ]]; then exit 0; fi
else
    if [[ ! -f "$prepared_marker" ]]; then
        printf 'This job has no completed preparation.\n' >&2
        exit 2
    fi
    mapfile -t prepared < "$prepared_marker"
    if (( ${#prepared[@]} != 2 )) || [[ "${prepared[0]}" != "$GITHUB_SHA" \
        || ! "${prepared[1]}" =~ ^[1-9][0-9]{0,10}$ ]] || (( prepared[1] > job_started )); then
        printf 'Preparation identity/clock mismatch.\n' >&2
        exit 2
    fi
    initial_elapsed=$((job_started - prepared[1]))
    export PATH="$build_workspace/depot_tools:$PATH"
    export DEPOT_TOOLS_UPDATE=0
    cd "$build_workspace/checkout/src"
fi

df -h .
# Inspect effective GN arguments after regeneration, including checkpoint resumes.
# This verifies compiled-in formats, not successful playback or hardware support.
python3 "$GITHUB_WORKSPACE/scripts/archium-media-preflight.py" \
    --out "$PWD/out/Archium" --report "$PWD/out/Archium/archium-media-config.json"
# SIGINT lets Ninja stop its children and flush .ninja_log/.ninja_deps before packing.
slice_started=$SECONDS
slice_seconds=$((slice_minutes * 60))
compile_slice() {
    local remaining=$((slice_seconds - (SECONDS - slice_started)))
    if (( remaining <= 0 )); then
        save_checkpoint
    fi
    # Use the interpreter from the pinned autoninja shell entrypoint. The thin
    # loader defers Python SIGINT so subprocess.call cannot SIGKILL its backend.
    run_work INT "$remaining" 0 --checkpoint-on-failure \
        "$build_workspace/depot_tools/python-bin/python3" \
        "$GITHUB_WORKSPACE/scripts/archium-autoninja.py" \
        "$build_workspace/depot_tools/autoninja.py" -C out/Archium "$@" -j 4
}
# Resolve real compiler actions for every Java delivery after GN generation. This
# includes modified upstream tests, unlike the isolated preparation contracts.
printf 'PHASE A1: compiling real Java/JNI owners before native work.\n'
java_targets_file="$PWD/out/Archium/archium-java-targets.txt"
run_work TERM "$work_seconds" 0 python3 "$GITHUB_WORKSPACE/scripts/archium-java-preflight.py" \
    --out "$PWD/out/Archium" --targets-file "$java_targets_file"
mapfile -t java_targets < "$java_targets_file"
if (( ${#java_targets[@]} == 0 )); then
    printf 'Java preflight did not resolve any compilation targets.\n' >&2
    exit 2
fi
compile_slice "${java_targets[@]}"
# Gate B/C: the original Robolectric regression and related tab-rail suites must
# pass before any expensive native password-manager linking or APK compilation.
# The generated Chrome junit runner is built from actual patched Chromium sources.
printf 'PHASE A1.5: proving Robolectric display-context repair before native work.\n'
compile_slice chrome_junit_tests
robolectric_runner="$PWD/out/Archium/bin/run_chrome_junit_tests"
test -x "$robolectric_runner" || {
    printf 'Chrome Robolectric runner missing after compilation.\n' >&2
    exit 2
}
# Unlike the previous run, save a quiescent checkpoint even on a JUnit failure.
run_work TERM "$host_seconds" 124 --checkpoint-on-failure "$robolectric_runner" -f \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinatorUnitTest.testIncognitoButtonVisibility_TabletUnder10Inches'
for suite in \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinatorUnitTest.*' \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.TabVerticalViewBinderUnitTest.*' \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayoutUnitTest.*'; do
    run_work TERM "$host_seconds" 124 --checkpoint-on-failure "$robolectric_runner" -f "$suite"
done
printf 'ARCHIUM_EARLY_ROBOLECTRIC_GATE=PASS\n'
# Check accessible native owners, including the bridge's generated JNI includes.
run_work TERM "$work_seconds" 0 gn check out/Archium //chrome/browser/password_manager/android:archium_password_manager_tests
# Verify the exact owner of WebPaymentsObserver / payment JNI is in the linker graph.
gn desc out/Archium //chrome/browser/password_manager/android:archium_password_manager_tests deps --all > "$RUNNER_TEMP/archium-password-link-deps.txt"
grep -Fq '//chrome/browser/payments:impl' "$RUNNER_TEMP/archium-password-link-deps.txt" || {
    printf 'Required payments implementation missing from native test link graph.\n' >&2
    exit 2
}
# Complete JNI-heavy link before compiling unrelated tests.
printf 'NATIVE_LINK_PROBE: archium_password_manager_tests first.\n'
compile_slice archium_password_manager_tests

compile_gate_targets="${ARCHIUM_COMPILE_GATE_TARGETS:-${ARCHIUM_VALIDATE_TARGETS:-}}"
if [[ -n "${ARCHIUM_VALIDATE_TARGETS:-}" && -z "${ARCHIUM_COMPILE_GATE_TARGETS:-}" ]]; then
    printf 'ARCHIUM_VALIDATE_TARGETS is deprecated; treating it as compile-only gate targets.\n' >&2
fi
if [[ -n "$compile_gate_targets" ]]; then
    read -r -a validation_targets <<< "$compile_gate_targets"
    for target in "${validation_targets[@]}"; do
        if [[ ! "$target" =~ ^[A-Za-z_][A-Za-z_0-9:/.-]*$ ]]; then
            printf 'Invalid compile-gate target.\n' >&2
            exit 2
        fi
    done
    # This source_set owns the edited upstream password client tests.
    validation_targets+=(chrome/browser/password_manager:unit_tests)
    printf 'PHASE A2: compiling Archium native/full test targets.\n'
    compile_slice "${validation_targets[@]}"
fi

# Verify every mandatory Android-native test produced Chromium's generated device
# launcher before the APK is permitted to compile. Missing launchers fail closed.
run_work TERM "$work_seconds" 0 python3 "$GITHUB_WORKSPACE/scripts/archium-test-gates.py" verify-device-runners \
    --out "$PWD/out/Archium"

if [[ -n "${ARCHIUM_RUN_HOST_GATES:-}" && "${ARCHIUM_RUN_HOST_GATES}" != true ]]; then
    printf 'ARCHIUM_RUN_HOST_GATES may not disable the mandatory host execution gate.\n' >&2
    exit 2
fi
printf 'PHASE B: executing mandatory Archium host gates.\n'
# Use the SDK pinned by this Chromium checkout. The GitHub-hosted ANDROID_HOME is
# deliberately removed earlier to reclaim disk, so relying on it here would be
# a stale-path gate. Parse the pinned public SDK version from Chromium itself.
android_sdk_version="$(sed -n 's/^[[:space:]]*public_android_sdk_platform_version = "\([0-9][0-9.]*\)"/\1/p' build/config/android/config.gni | head -n1)"
if [[ ! "$android_sdk_version" =~ ^[0-9]+([.][0-9]+)*$ ]]; then
    printf 'Unable to resolve Chromium public Android SDK platform version.\n' >&2
    exit 2
fi
android_jar="$PWD/third_party/android_sdk/public/platforms/android-${android_sdk_version}/android.jar"
if [[ ! -s "$android_jar" ]]; then
    printf 'Pinned Chromium Android platform jar is missing: %s\n' "$android_jar" >&2
    exit 2
fi
run_work TERM "$host_seconds" 124 python3 "$GITHUB_WORKSPACE/scripts/archium-test-gates.py" host \
    --android-jar "$android_jar" --out "$PWD/out/Archium"

printf 'PHASE C: host gates passed; APK target is now allowed.\n'
compile_slice chrome_public_apk
test -s out/Archium/apks/ChromePublic.apk
# Fail closed if packaged launcher aliases/resources are absent from the actual APK.
android_tools_version="$(sed -n 's/^[[:space:]]*public_android_sdk_build_tools_version = "\([^"]*\)"/\1/p' build/config/android/config.gni | head -n1)"
if [[ -z "$android_tools_version" ]]; then
    printf 'Unable to resolve pinned Android build tools for Portal resource gate.\n' >&2
    exit 2
fi
mkdir -p "$GITHUB_WORKSPACE/archium-output"
run_work TERM "$host_seconds" 0 python3 "$GITHUB_WORKSPACE/scripts/verify-archium-portal-apk.py" \
    --apk "$PWD/out/Archium/apks/ChromePublic.apk" \
    --aapt2 "$PWD/third_party/android_sdk/public/build-tools/$android_tools_version/aapt2" \
    --report "$GITHUB_WORKSPACE/archium-output/portal-branding-verified.json"
cp out/Archium/apks/ChromePublic.apk "$GITHUB_WORKSPACE/archium-output/Archium-for-Android-arm64.apk"
cp LICENSE "$GITHUB_WORKSPACE/archium-output/LICENSE.chromium"
sha256sum "$GITHUB_WORKSPACE/archium-output/Archium-for-Android-arm64.apk" > "$GITHUB_WORKSPACE/archium-output/SHA256SUMS"

printf 'complete=true\n' >> "$GITHUB_OUTPUT"
