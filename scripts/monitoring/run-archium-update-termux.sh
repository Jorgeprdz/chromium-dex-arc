#!/data/data/com.termux/files/usr/bin/bash
# Independent native Termux worker; survives the coding agent being paused or closed.
set -euo pipefail
run_id="${1:?Pass the authorized run ID}"
commit="${2:?Pass the exact build commit}"
[[ "$run_id" =~ ^[0-9]+$ && "$commit" =~ ^[a-f0-9]{40}$ ]] || exit 2
mkdir -p "/data/data/com.termux/files/home/.archium-install/$run_id"
export PATH="/data/data/com.termux/files/usr/bin:/system/bin:$PATH"
exec /data/data/com.termux/files/usr/bin/proot-distro login codexbox \
    --bind /data/data/com.termux/files/home:/workspace -- /bin/bash -lc '
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
    exec /usr/bin/python3 /workspace/macdesk-maintenance/update-archium-run.py \
        --wait --interval 600 --run "$1" --commit "$2" --serial emulator-5554 \
        --state-dir "/workspace/.archium-install/$1" \
        >"/workspace/.archium-install/$1/update.log" 2>&1
    ' archium-update "$run_id" "$commit"
