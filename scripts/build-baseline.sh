#!/usr/bin/env bash
set -euo pipefail

# This script may remove preinstalled SDKs ONLY on this project's disposable CI VM.
if [[ "${GITHUB_ACTIONS:-}" != true || "${GITHUB_REPOSITORY:-}" != Jorgeprdz/chromium-dex-arc ]]; then
    printf 'Refusing execution outside the dedicated GitHub Actions repository.\n' >&2
    exit 2
fi

readonly chromium_revision=cfd94726b7b5fb48aedcc32662f2f3fbdbadec35
readonly depot_revision=8a5434051036b32412a2ecb10c213a72e3f3ccb9
readonly build_workspace="$RUNNER_TEMP/chromium-arc-baseline"

sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/hostedtoolcache
available_bytes=$(df -B1 --output=avail "$RUNNER_TEMP" | tail -n 1 | tr -d ' ')
if (( available_bytes < 100000000000 )); then
    printf 'Insufficient disk space after cleanup: %s bytes\n' "$available_bytes" >&2
    exit 3
fi
df -h "$RUNNER_TEMP"
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

mkdir -p out/ArcBaseline
cat > out/ArcBaseline/args.gn <<'ARGS'
target_os = "android"
target_cpu = "arm64"
is_desktop_android = true
is_debug = false
is_official_build = true
is_component_build = false
symbol_level = 0
blink_symbol_level = 0
v8_symbol_level = 0
chrome_pgo_phase = 0
use_remoteexec = false
ARGS
gn gen out/ArcBaseline
df -h .
autoninja -C out/ArcBaseline chrome_public_apk -j 4
test -s out/ArcBaseline/apks/ChromePublic.apk
mkdir -p "$GITHUB_WORKSPACE/baseline-output"
cp out/ArcBaseline/apks/ChromePublic.apk "$GITHUB_WORKSPACE/baseline-output/ChromiumDesktop-baseline-1710899.apk"
cp LICENSE "$GITHUB_WORKSPACE/baseline-output/LICENSE.chromium"
sha256sum "$GITHUB_WORKSPACE/baseline-output/ChromiumDesktop-baseline-1710899.apk" > "$GITHUB_WORKSPACE/baseline-output/SHA256SUMS"
