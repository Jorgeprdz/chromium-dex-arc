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

sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/hostedtoolcache
available_bytes=$(df -B1 --output=avail "$RUNNER_TEMP" | tail -n 1 | tr -d ' ')
if (( available_bytes < 100000000000 )); then
    printf 'Insufficient disk space after cleanup: %s bytes\n' "$available_bytes" >&2
    exit 3
fi
df -h "$RUNNER_TEMP"
if [[ -n "$source_tag" || -n "${ARCHIUM_PREVIOUS_TAG:-}" ]]; then
    if [[ -n "$source_tag" ]]; then
        python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" restore \
            "$build_workspace" "$source_tag" --source-commit "$source_commit"
    else
        python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" restore \
            "$build_workspace" "$ARCHIUM_PREVIOUS_TAG"
    fi
    export PATH="$build_workspace/depot_tools:$PATH"
    export DEPOT_TOOLS_UPDATE=0
    bash "$build_workspace/depot_tools/ensure_bootstrap"
    cd "$build_workspace/checkout/src"
    sudo ./build/install-build-deps.sh --no-prompt --android
    if [[ -n "$source_tag" ]]; then
        git -C "$GITHUB_WORKSPACE" fetch --depth 1 origin "$source_commit"
        python3 "$GITHUB_WORKSPACE/scripts/transition-archium-patches.py" "$PWD" \
            --source-commit "$source_commit" --implementation-commit "$GITHUB_SHA"
        cp "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn
        gn gen out/Archium
    elif ! cmp -s "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn; then
        cp "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn
        gn gen out/Archium
    fi
else
mkdir -p "$build_workspace"
cd "$build_workspace"
git clone --depth 1 https://chromium.googlesource.com/chromium/tools/depot_tools.git
git -C depot_tools fetch --depth 1 origin "$depot_revision"
git -C depot_tools checkout --detach "$depot_revision"
export PATH="$build_workspace/depot_tools:$PATH"
export DEPOT_TOOLS_UPDATE=0
# Pinning disables gclient's automatic update/bootstrap. Initialize the pinned
# tools explicitly so GN's python-bin wrapper has its interpreter metadata.
bash "$build_workspace/depot_tools/ensure_bootstrap"
"$build_workspace/depot_tools/python-bin/python3" --version

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
gclient sync --no-history --nohooks --revision "src@$chromium_revision"
cd src
test "$(git rev-parse HEAD)" = "$chromium_revision"
sudo ./build/install-build-deps.sh --no-prompt --android
gclient runhooks

mkdir -p out/Archium
python3 "$GITHUB_WORKSPACE/scripts/apply-arc-patches.py" "$PWD"
cp "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn
gn gen out/Archium
fi

df -h .
# SIGINT lets Ninja stop its children and flush .ninja_log/.ninja_deps before packing.
slice_minutes="${ARCHIUM_SLICE_MINUTES:-120}"
if [[ ! "$slice_minutes" =~ ^[1-9][0-9]*$ ]]; then
    printf 'Invalid compilation slice duration.\n' >&2
    exit 2
fi
slice_started=$SECONDS
slice_seconds=$((slice_minutes * 60))
compile_slice() {
    local remaining=$((slice_seconds - (SECONDS - slice_started)))
    local result=0
    if (( remaining <= 0 )); then
        result=124
    else
        timeout --signal=INT --kill-after=90s "${remaining}s" \
            autoninja -C out/Archium "$@" -j 4 || result=$?
    fi
    if (( result == 124 )); then
        printf 'Compilation slice ended; saving complete workspace.\n'
        python3 "$GITHUB_WORKSPACE/scripts/archium-checkpoint.py" pack \
            "$build_workspace" "$ARCHIUM_CHECKPOINT_TAG"
        printf 'complete=false\n' >> "$GITHUB_OUTPUT"
        exit 0
    elif (( result != 0 )); then
        printf 'Compilation failed with exit %s; stopping the chain.\n' "$result" >&2
        exit "$result"
    fi
}
if [[ -n "${ARCHIUM_VALIDATE_TARGETS:-}" ]]; then
    read -r -a validation_targets <<< "$ARCHIUM_VALIDATE_TARGETS"
    for target in "${validation_targets[@]}"; do
        if [[ ! "$target" =~ ^[A-Za-z_][A-Za-z_0-9:/.-]*$ ]]; then
            printf 'Invalid validation target.\n' >&2
            exit 2
        fi
    done
    compile_slice "${validation_targets[@]}"
fi
compile_slice chrome_public_apk
test -s out/Archium/apks/ChromePublic.apk
mkdir -p "$GITHUB_WORKSPACE/archium-output"
cp out/Archium/apks/ChromePublic.apk "$GITHUB_WORKSPACE/archium-output/Archium-for-Android-arm64.apk"
cp LICENSE "$GITHUB_WORKSPACE/archium-output/LICENSE.chromium"
native_tests=(
    out/Archium/obj/chrome/browser/password_manager/android/archium_key_provider_tests/archium_key_provider_tests
    out/Archium/obj/components/password_manager/core/browser/password_store/archium_login_database_tests/archium_login_database_tests
    out/Archium/obj/components/password_manager/core/browser/import/archium_password_import_tests/archium_password_import_tests
)
for native_test in "${native_tests[@]}"; do
    if [[ -s "$native_test" ]]; then
        mkdir -p "$GITHUB_WORKSPACE/archium-output/native-tests"
        cp "$native_test" "$GITHUB_WORKSPACE/archium-output/native-tests/"
    fi
done
sha256sum "$GITHUB_WORKSPACE/archium-output/Archium-for-Android-arm64.apk" > "$GITHUB_WORKSPACE/archium-output/SHA256SUMS"

printf 'complete=true\n' >> "$GITHUB_OUTPUT"
