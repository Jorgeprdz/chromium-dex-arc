#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077
state_dir="${ARCHIUM_R5_STATE_DIR:-$HOME/.local/state/archium-r5-progressive}"
mkdir -p "$state_dir"
exec 8>"$state_dir/launcher.lock"
flock -n 8 || { printf 'MONITOR_LAUNCH_IN_PROGRESS\n' >&2; exit 17; }
# The long-lived native monitor holds this lock for its entire lifetime.
exec 9>"$state_dir/native-monitor.lock"
flock -n 9 || { printf 'MONITOR_ALREADY_ACTIVE\n' >&2; exit 17; }
flock -u 9
exec 9>&-
monitor_path="$HOME/.local/bin/archium-r5-monitor.sh"
if [[ "${1:-}" == --probe ]]; then monitor_path="$state_dir/session-probe.sh"; fi
exec am startservice --user 0 -n com.termux/.app.RunCommandService \
    -a com.termux.RUN_COMMAND \
    --es com.termux.RUN_COMMAND_PATH "$monitor_path" \
    --es com.termux.RUN_COMMAND_WORKDIR "$HOME" \
    --ez com.termux.RUN_COMMAND_BACKGROUND false \
    --es com.termux.RUN_COMMAND_SESSION_ACTION 0
