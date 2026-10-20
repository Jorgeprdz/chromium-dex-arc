#!/data/data/com.termux/files/usr/bin/bash
# Native independent Termux session. The Python watcher keeps the screen open.
set -euo pipefail
umask 077
state_dir="${ARCHIUM_R5_STATE_DIR:-$HOME/.local/state/archium-r5-progressive}"
mkdir -p "$state_dir"
exec 9>"$state_dir/native-monitor.lock"
flock -n 9 || { printf 'MONITOR_ALREADY_ACTIVE\n' >&2; exit 17; }
monitor_tty=$(tty)
python3 - "$state_dir" "$$" "$PPID" "$monitor_tty" <<'PY'
import datetime,json,os,sys
from pathlib import Path
(Path(sys.argv[1])/'native-session.json').write_text(json.dumps(dict(
    pid=int(sys.argv[2]),ppid=int(sys.argv[3]),tty=sys.argv[4],sid=os.getsid(0),
    native_termux=True,mode='WATCH_ONLY',started=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
PY
command -v termux-wake-lock >/dev/null && termux-wake-lock || true
trap 'command -v termux-wake-unlock >/dev/null && termux-wake-unlock || true' EXIT
printf '\033]0;ARCHIUM R5 | BUILD MONITOR\007'
# Direct TTY output enables color and clear-before-redraw; durable logs are JSONL.
watch_exit=0
proot-distro login codexbox --bind "$HOME:/workspace" -- /bin/bash -lc '
    cd /workspace/Archium-R5
    exec /usr/bin/python3 scripts/archium-r5-watch.py \
      --state-dir /workspace/.local/state/archium-r5-progressive
' || watch_exit=$?
if (( watch_exit != 0 )); then
    printf '\033[31mMonitor detenido con codigo %s. Evidencia preservada.\033[0m\n' "$watch_exit"
    read -r -p 'Pulsa Enter para cerrar esta ventana...' || true
fi
