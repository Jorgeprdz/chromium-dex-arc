#!/usr/bin/env bash
# R5 recovery: explicit checkpoint, isolated phases, one checkout and fatal gates.
set -euo pipefail
readonly chromium_revision=cfd94726b7b5fb48aedcc32662f2f3fbdbadec35
readonly depot_revision=8a5434051036b32412a2ecb10c213a72e3f3ccb9
readonly recovery_branch=assistant/archium-r5-desktop-native-mobile
die() { printf '%s\n' "$*" >&2; exit 2; }
[[ "${GITHUB_ACTIONS:-}" == true && "${GITHUB_REPOSITORY:-}" == Jorgeprdz/chromium-dex-arc ]] ||
    die 'Runner requires the dedicated CI repository.'
[[ "${GITHUB_REF_NAME:-}" == "$recovery_branch" ]] || die 'Recovery branch rejected.'
[[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ && "${ARCHIUM_EXPECTED_SHA:-}" == "$GITHUB_SHA" ]] ||
    die 'Dispatch SHA differs from the explicitly authorized SHA.'
[[ "${ARCHIUM_SOURCE_TAG:-}" =~ ^archium-checkpoint-[0-9]+-[0-9]+$ &&
   "${ARCHIUM_SOURCE_COMMIT:-}" =~ ^[0-9a-f]{40}$ ]] ||
    die 'Exact source checkpoint is required; clean fallback is disabled.'
phase="${1:---all}"
if (( $# > 1 )) || [[ ! "$phase" =~ ^--(all|prepare|work)$ ]]; then die 'Unknown phase.'; fi
budget() {
    local value="$1" maximum="$2"
    if [[ ! "$value" =~ ^[1-9][0-9]*$ ]] || (( ${#value} > ${#maximum} || value > maximum )); then
        die 'Invalid recovery budget.'
    fi
    printf '%s' "$value"
}
slice_minutes=$(budget "${ARCHIUM_SLICE_MINUTES:-75}" 75)
max_slices=$(budget "${ARCHIUM_MAX_SLICES:-2}" 2)
prepare_seconds=$(budget "${ARCHIUM_PREPARE_SECONDS:-3600}" 3600)
work_seconds=$(budget "${ARCHIUM_WORK_SECONDS:-9000}" 9000)
host_seconds=$(budget "${ARCHIUM_HOST_SECONDS:-1800}" 1800)
checkpoint_seconds=$(budget "${ARCHIUM_CHECKPOINT_SECONDS:-3600}" 3600)
upload_seconds=$(budget "${ARCHIUM_UPLOAD_RESERVE_SECONDS:-1200}" 1200)
readonly build_workspace="$RUNNER_TEMP/chromium-archium"
readonly prepared_marker="$RUNNER_TEMP/archium-recovery-prepared"
readonly host_python="${ARCHIUM_HOST_PYTHON:-/usr/bin/python3}"
job_started=$(date +%s)
script_started=$SECONDS
deadline="${ARCHIUM_JOB_DEADLINE_EPOCH:-$((job_started + 10800))}"
[[ "$deadline" =~ ^[1-9][0-9]{0,10}$ ]] || die 'Invalid job deadline.'
initial_elapsed=0
job_elapsed() { printf '%s' "$((initial_elapsed + SECONDS - script_started))"; }
wall_remaining() { printf '%s' "$((deadline - $(date +%s) - checkpoint_seconds - upload_seconds))"; }
stage() { printf 'FASE=%s SHA=%s RUN=%s\n' "$1" "$GITHUB_SHA" "${GITHUB_RUN_ID:-local}"; }
save_checkpoint() {
    local status="$1" pack_status=0
    printf 'BUILD_INCOMPLETE: saving quiescent output; original exit=%s\n' "$status"
    timeout --signal=TERM --kill-after=30s "${checkpoint_seconds}s" \
        python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" pack \
        "$build_workspace" "$ARCHIUM_CHECKPOINT_TAG" || pack_status=$?
    if (( pack_status != 0 )); then
        printf 'CHECKPOINT_SAVE=FAIL exit=%s source=%s remains remote\n' "$pack_status" "$ARCHIUM_SOURCE_TAG" >&2
        (( status == 0 )) && status=$pack_status
    else
        for group in "$ARCHIUM_CHECKPOINT_DIR"/group-*; do
            [[ -d "$group" ]] || continue
            printf 'saved_%s=true\n' "${group##*/}" | tr '-' '_' >> "$GITHUB_OUTPUT"
        done
    fi
    local receipt_args=()
    (( pack_status == 0 )) && receipt_args+=(--packed)
    "$host_python" "$GITHUB_WORKSPACE/scripts/r5-stage-receipt.py" \
        --out "$build_workspace/checkout/src/out/Archium" \
        --receipt "$RUNNER_TEMP/stage-receipt.json" --exit-code "$status" "${receipt_args[@]}"
    printf 'complete=false\n' >> "$GITHUB_OUTPUT"
    exit "$status"
}
run_prepare() {
    local remaining=$((prepare_seconds - $(job_elapsed))) wall
    wall=$(wall_remaining)
    (( remaining > wall )) && remaining=$wall
    (( remaining > 0 )) || { printf 'Restore deadline reached; remote checkpoint retained.\n' >&2; return 124; }
    timeout --signal=TERM --kill-after=30s "${remaining}s" "$@"
}
run_work() {
    local signal="$1" limit="$2" checkpoint_failure="$3" result=0 remaining wall
    shift 3
    remaining=$((work_seconds - $(job_elapsed)))
    wall=$(wall_remaining)
    (( remaining > wall )) && remaining=$wall
    (( remaining > 0 )) || save_checkpoint 0
    (( limit > remaining )) && limit=$remaining
    timeout --signal="$signal" --kill-after=90s "${limit}s" "$@" || result=$?
    if (( result == 124 )); then
        # Forced timeout cannot prove quiescence. Only the autoninja wrapper's
        # graceful exit 124 is safe for packing; signal exit 137 is never packed.
        return 124
    fi
    if (( result != 0 )); then
        printf 'GATE=FAIL exit=%s; all later phases blocked.\n' "$result" >&2
        [[ "$checkpoint_failure" == true ]] && (( result < 128 )) && save_checkpoint "$result"
        exit "$result"
    fi
}
install_deps() {
    run_prepare sudo --preserve-env=GITHUB_ACTIONS,GITHUB_REPOSITORY \
        python3 "$GITHUB_WORKSPACE/scripts/configure-archium-apt.py"
    run_prepare sudo timeout --signal=TERM --kill-after=30s 30m \
        ./build/install-build-deps.sh --no-prompt --android
}
if [[ "$phase" != --work ]]; then
    stage S1
    [[ -n "${ARCHIUM_CHECKPOINT_DIR:-}" ]] || die 'Downloaded checkpoint directory is required.'
    # S0 measured disk/metadata BEFORE this download. Restore hashes every part.
    run_prepare python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" restore \
        "$build_workspace" "$ARCHIUM_SOURCE_TAG" --source-commit "$ARCHIUM_SOURCE_COMMIT"
    export PATH="$build_workspace/depot_tools:$PATH"
    export DEPOT_TOOLS_UPDATE=0
    run_prepare bash "$build_workspace/depot_tools/ensure_bootstrap"
    cd "$build_workspace/checkout/src"
    [[ "$(git rev-parse HEAD)" == "$chromium_revision" ]] ||
        die 'BLOCKED_CHECKPOINT_INCOMPATIBLE: restored Chromium pin mismatch.'
    [[ "$(git -C "$build_workspace/depot_tools" rev-parse HEAD)" == "$depot_revision" ]] ||
        die 'BLOCKED_CHECKPOINT_INCOMPATIBLE: restored depot_tools pin mismatch.'
    # A changed configuration needs an explicitly compatible checkpoint. Never
    # overwrite restored args: that would silently invalidate its native outputs.
    cmp -s "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn ||
        die 'BLOCKED_CHECKPOINT_INCOMPATIBLE: restored GN args differ; outputs preserved.'
    install_deps
    run_prepare git -C "$GITHUB_WORKSPACE" fetch --depth 1 origin "$ARCHIUM_SOURCE_COMMIT"
    run_prepare python3 "$GITHUB_WORKSPACE/scripts/transition-archium-patches.py" "$PWD" \
        --source-commit "$ARCHIUM_SOURCE_COMMIT" --implementation-commit "$GITHUB_SHA"
    run_prepare "$host_python" "$GITHUB_WORKSPACE/scripts/integrate-archium-portal.py" "$PWD"
    run_prepare gn gen out/Archium
    printf '%s\n%s\n%s\n' "$GITHUB_SHA" "$job_started" "$deadline" > "$prepared_marker"
    df -B1 .
    df -i .
    [[ "$phase" == --prepare ]] && exit 0
else
    [[ -f "$prepared_marker" ]] || die 'Restore has not completed in this job.'
    mapfile -t prepared < "$prepared_marker"
    if (( ${#prepared[@]} != 3 )) || [[ "${prepared[0]}" != "$GITHUB_SHA" ||
        ! "${prepared[1]}" =~ ^[1-9][0-9]{0,10}$ ||
        ! "${prepared[2]}" =~ ^[1-9][0-9]{0,10}$ ]]; then die 'Restore receipt identity rejected.'; fi
    initial_elapsed=$((job_started - prepared[1]))
    (( initial_elapsed >= 0 )) || die 'Restore receipt clock rejected.'
    deadline="${prepared[2]}"
    export PATH="$build_workspace/depot_tools:$PATH"
    export DEPOT_TOOLS_UPDATE=0
    cd "$build_workspace/checkout/src"
fi
slice_count=1
slice_started=$SECONDS
compile_slice() {
    local remaining result
    while true; do
        remaining=$((slice_minutes * 60 - (SECONDS - slice_started)))
        if (( remaining <= 0 )); then
            (( slice_count < max_slices )) || save_checkpoint 0
            slice_count=$((slice_count + 1)); slice_started=$SECONDS
            continue
        fi
        result=0
        run_work INT "$remaining" true \
            "$build_workspace/depot_tools/python-bin/python3" \
            "$GITHUB_WORKSPACE/scripts/archium-autoninja.py" \
            "$build_workspace/depot_tools/autoninja.py" -C out/Archium "$@" -j 4 || result=$?
        (( result == 124 )) || return "$result"
        (( slice_count < max_slices )) || save_checkpoint 0
        slice_count=$((slice_count + 1)); slice_started=$SECONDS
    done
}
gate() {
    local result=0
    run_work TERM "$host_seconds" true "$@" || result=$?
    if (( result == 124 )); then
        printf "Host timeout: quiescence unverified; source checkpoint retained remotely.\n" >&2
        exit 124
    fi
    return "$result"
}
# These receipts are part of the checkpoint. Reuse only for the exact source,
# args and pinned toolchain; a source/configuration change gets a fresh namespace.
gate_key=$(printf '%s\n' "$GITHUB_SHA" "$chromium_revision" "$depot_revision" \
    "$(sha256sum out/Archium/args.gn)" | sha256sum | cut -d' ' -f1)
gate_dir="$PWD/out/Archium/.archium-r5-gates/$gate_key"
mkdir -p "$gate_dir"
gate_once() {
    local name="$1"; shift
    if [[ -f "$gate_dir/$name" ]]; then
        printf 'GATE_REUSED=PASS name=%s source=%s\n' "$name" "$GITHUB_SHA"
        return
    fi
    gate "$@"
    printf '%s\n' "$GITHUB_SHA" > "$gate_dir/$name"
}
stage S2
ninja_query="$PWD/third_party/ninja/ninja"
[[ -x "$ninja_query" ]] || die 'Pinned Ninja query tool absent.'
gate "$ninja_query" --version
# Validate the generated graph before spending a slice on compilation/tests.
# Query copied manifests only: depot_tools rejects Siso here, and raw Ninja
# can repair logs even for `-t query`. The restored output must stay untouched.
gate "$host_python" "$GITHUB_WORKSPACE/scripts/archium-ninja-query.py" \
    --out "$PWD/out/Archium" --ninja "$ninja_query" \
    --target libchrome --report "$RUNNER_TEMP/archium-native-query.txt"
gate python3 "$GITHUB_WORKSPACE/scripts/archium-media-preflight.py" \
    --out "$PWD/out/Archium" --report "$PWD/out/Archium/archium-media-config.json"
gate gn check out/Archium //chrome/android:chrome_public_apk
gate gn desc out/Archium //chrome/android:chrome_public_apk deps --all \
    > "$RUNNER_TEMP/archium-apk-link-deps.txt"
gate "$host_python" "$GITHUB_WORKSPACE/scripts/check-archium-password-deprecation.py" \
    --out out/Archium --deps "$RUNNER_TEMP/archium-apk-link-deps.txt"
grep -Fq '//chrome/browser/payments:impl' "$RUNNER_TEMP/archium-apk-link-deps.txt" ||
    die 'Payments owner absent from the real GN graph.'
android_config=build/config/android/config.gni
tools_version=$(sed -n 's/^[[:space:]]*public_android_sdk_build_tools_version = "\([^"]*\)"/\1/p' "$android_config" | head -n1)
platform_version=$(sed -n 's/^[[:space:]]*public_android_sdk_platform_version = "\([^"]*\)"/\1/p' "$android_config" | head -n1)
[[ -n "$tools_version" && -n "$platform_version" ]] || die 'Pinned SDK version absent.'
sdk_tools="$PWD/third_party/android_sdk/public/build-tools/$tools_version"
android_jar="$PWD/third_party/android_sdk/public/platforms/android-$platform_version/android.jar"
# Validate the complete host suite under the restored PATH/toolchain before native work.
# A failure here has no new native outputs to save: retain the remote source.
host_preflight_status=0
if [[ -f "$gate_dir/host_preflight" ]]; then
    printf 'GATE_REUSED=PASS name=host_preflight source=%s\n' "$GITHUB_SHA"
else
    run_work TERM "$host_seconds" false \
        "$host_python" "$GITHUB_WORKSPACE/scripts/archium-test-gates.py" host-preflight \
        --out "$PWD/out/Archium" --android-jar "$android_jar" || host_preflight_status=$?
    (( host_preflight_status == 0 )) || exit "$host_preflight_status"
    printf '%s\n' "$GITHUB_SHA" > "$gate_dir/host_preflight"
fi
compile_slice chrome_public_apk__compile_resources
gate_once portal_resources "$host_python" "$GITHUB_WORKSPACE/scripts/check-portal-chromium-resources.py" \
    --out "$PWD/out/Archium" --aapt2 "$sdk_tools/aapt2" --report "$PWD/out/Archium/archium-real-resources.json"
targets="$PWD/out/Archium/archium-java-targets.txt"
gate python3 "$GITHUB_WORKSPACE/scripts/archium-java-preflight.py" --out "$PWD/out/Archium" --targets-file "$targets"
mapfile -t java_targets < "$targets"
(( ${#java_targets[@]} > 0 )) || die 'No real Java owners resolved.'
compile_slice "${java_targets[@]}"
compile_slice chrome_junit_tests
runner="$PWD/out/Archium/bin/run_chrome_junit_tests"
[[ -x "$runner" ]] || die 'Real Robolectric runner absent.'
for suite in \
    'org.chromium.chrome.browser.arc.ArcAboutDialogTest.*' \
    'org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearanceTest.*' \
    'org.chromium.chrome.browser.arc.ArcColorPickerTest.*' \
    'org.chromium.chrome.browser.arc.ArcCompactOmniboxTest.*' \
    'org.chromium.chrome.browser.arc.ArcFrameDispatchTest.*' \
    'org.chromium.chrome.browser.arc.ArcNavigationControlsTest.*' \
    'org.chromium.chrome.browser.arc.ArcCommandBarTest.*' \
    'org.chromium.chrome.browser.arc.ArcDesktopMaterialTest.*' \
    'org.chromium.chrome.browser.arc.ArcPhoneStatusFadeTest.*' \
    'org.chromium.chrome.browser.arc.ArcOmniboxPlacementTest.*' \
    'org.chromium.chrome.browser.omnibox.LocationBarMediatorUnitTest.testArcCommand*' \
    'org.chromium.chrome.browser.arc.ArcCollectionsFocusTest.*' \
    'org.chromium.chrome.browser.toolbar.top.ArcToolbarReparentingTest.*' \
    'org.chromium.chrome.browser.omnibox.OmniboxSuggestionsDropdownEmbedderImplUnitTest.*' \
    'org.chromium.chrome.browser.omnibox.LocationBarTabletUnitTest.*' \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.ArcTabSelectionTest.*' \
    'org.chromium.chrome.browser.tabbed_mode.TabbedRootUiCoordinatorUnitTest.*' \
    'org.chromium.chrome.browser.tasks.tab_management.TabListMediatorUnitTest.testSetThumbnailSpinnerVisibility_NotFlatLayout_Asserts*' \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinatorUnitTest.*' \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.TabVerticalViewBinderUnitTest.*' \
    'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayoutUnitTest.*'; do
    # Assertions belong to this subprocess only. Later compilers inherit no -ea.
    suite_key=$(printf '%s' "$suite" | sha256sum | cut -d' ' -f1)
    gate_once "robolectric_$suite_key" env JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -ea" "$runner" -f "$suite"
done
printf 'ROBOLECTRIC_PASS=PASS scope=early_Chromium_suites\n'
compile_slice libchrome
nm="$PWD/third_party/llvm-build/Release+Asserts/bin/llvm-nm"
[[ -x "$nm" && -s out/Archium/lib.unstripped/libchrome.so ]] ||
    die 'Real native library or symbol tool absent.'
"$nm" -C out/Archium/lib.unstripped/libchrome.so > "$RUNNER_TEMP/archium-native-symbols.txt"
if grep -E '(^|[[:space:]])U[[:space:]].*(WebPaymentsObserver|ServiceWorkerPaymentAppBridge)' "$RUNNER_TEMP/archium-native-symbols.txt"; then
    die 'Unresolved payment JNI symbols.'
fi
printf 'JNI_LINK_PASS=PASS scope=real_APK_libchrome_link_and_symbols\n'
stage S3
printf 'PASSWORD_TESTS=DEPRECATED OUT_OF_SCOPE; no native test PASS claimed\n'
gate_once final_robolectric "$host_python" "$GITHUB_WORKSPACE/scripts/archium-test-gates.py" robolectric --out "$PWD/out/Archium" --android-jar "$android_jar"
stage S4
compile_slice chrome_public_apk
apk="$PWD/out/Archium/apks/ChromePublic.apk"
[[ -s "$apk" ]] || die 'APK absent or empty.'
gate "$host_python" "$GITHUB_WORKSPACE/scripts/verify-archium-portal-apk.py" \
    --apk "$apk" --aapt2 "$sdk_tools/aapt2" --report "$PWD/out/Archium/archium-apk-verification.json"
gate "$sdk_tools/apksigner" verify --verbose "$apk"
"$sdk_tools/aapt2" dump badging "$apk" > "$RUNNER_TEMP/archium-apk-badging.txt"
grep -Fq "package: name='app.archium.android'" "$RUNNER_TEMP/archium-apk-badging.txt" ||
    die 'APK package differs from configured Archium application ID.'
grep -Eq "^native-code: 'arm64-v8a'$" "$RUNNER_TEMP/archium-apk-badging.txt" || die 'APK ABI is not exclusively ARM64.'
zipinfo -1 "$apk" > "$RUNNER_TEMP/archium-apk-entries.txt"
grep -Eq '^lib/arm64-v8a/.+\.so$' "$RUNNER_TEMP/archium-apk-entries.txt" || die 'No real ARM64 native library in APK.'
stage S5
output="$GITHUB_WORKSPACE/archium-output"
mkdir -p "$output"
cp "$apk" "$output/Archium-for-Android-arm64.apk"
cp LICENSE "$output/LICENSE.chromium"
"$sdk_tools/apksigner" verify --verbose --print-certs "$apk" > "$output/SIGNATURE.txt"
cp "$RUNNER_TEMP/archium-apk-badging.txt" "$output/APK_BADGING.txt"
(cd "$output"; sha256sum Archium-for-Android-arm64.apk > SHA256SUMS)
"$host_python" - "$output/BUILD_REPORT.json" <<'PY'
import json, os, sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({
    'source_sha': os.environ['GITHUB_SHA'],
    'branch': os.environ['GITHUB_REF_NAME'], 'run_id': os.environ['GITHUB_RUN_ID'],
    'source_checkpoint': os.environ['ARCHIUM_SOURCE_TAG'],
    'checkpoint_commit': os.environ['ARCHIUM_SOURCE_COMMIT'],
    'PERFORMANCE': 'NOT_RUN',
    'chromium_pin': 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35',
    'APK_VERIFIED': 'PASS', 'ROBOLECTRIC_PASS': 'PASS', 'JNI_LINK_PASS': 'PASS',
    'mandatory_gates': 'PASS',
    'ARCHIUM_PASSWORD_FEATURE': 'DEPRECATED', 'ARCHIUM_PASSWORD_TESTS': 'OUT_OF_SCOPE',
    'ANDROID_RUNTIME': 'NOT_EXECUTED'}, indent=2) + '\n')
PY
printf 'APK_VERIFIED=PASS\ncomplete=true\n' >> "$GITHUB_OUTPUT"
"$host_python" "$GITHUB_WORKSPACE/scripts/r5-stage-receipt.py" \
    --out "$PWD/out/Archium" --receipt "$RUNNER_TEMP/stage-receipt.json" \
    --exit-code 0 --complete
