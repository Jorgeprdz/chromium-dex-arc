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

mkdir -p out/Archium
python3 "$GITHUB_WORKSPACE/scripts/apply-arc-patches.py" "$PWD"
cp "$GITHUB_WORKSPACE/config/archium-args.gn" out/Archium/args.gn
gn gen out/Archium
df -h .
autoninja -C out/Archium chrome_public_apk -j 4
test -s out/Archium/apks/ChromePublic.apk
mkdir -p "$GITHUB_WORKSPACE/archium-output"
cp out/Archium/apks/ChromePublic.apk "$GITHUB_WORKSPACE/archium-output/Archium-for-Android-arm64.apk"
cp LICENSE "$GITHUB_WORKSPACE/archium-output/LICENSE.chromium"
sha256sum "$GITHUB_WORKSPACE/archium-output/Archium-for-Android-arm64.apk" > "$GITHUB_WORKSPACE/archium-output/SHA256SUMS"
