#!/data/data/com.termux/files/usr/bin/bash
# Independent native Termux session; no physical-device Android tests or ADB.
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
p=Path(sys.argv[1])/'native-session.json'
p.write_text(json.dumps(dict(pid=int(sys.argv[2]),ppid=int(sys.argv[3]),tty=sys.argv[4],
    sid=os.getsid(0),native_termux=True,started=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
PY
command -v termux-wake-lock >/dev/null && termux-wake-lock || true
trap 'command -v termux-wake-unlock >/dev/null && termux-wake-unlock || true' EXIT
printf '\033]0;ARCHIUM R5 — PROGRESSIVE BUILD\007'
# Separate PRoot lifecycle: TermuxService is the parent, not the coding agent.
proot-distro login codexbox --bind "$HOME:/workspace" -- /bin/bash -lc '
    cd /workspace/Archium-R5
    exec /usr/bin/python3 scripts/archium-r5-supervisor.py \
      --state-dir /workspace/.local/state/archium-r5-progressive \
      --max-stages 6 --max-repairs 2 --budget-hours 10 \
      --apksigner /workspace/.local/state/archium-r5-progressive/apksigner-host.sh \
      --aapt2 /opt/android-sdk/build-tools/37.0.0/aapt2
' 2>&1 | tee -a "$state_dir/monitor.log"
# The supervisor owns installation gates. A missing authorized installer/system
# receipt remains INSTALL_PENDING_DEVICE; never open an installer after BLOCKED.
python3 - "$state_dir" <<'PYRECEIPT'
import json,sys
from pathlib import Path
state=json.loads((Path(sys.argv[1])/'state.json').read_text())
print('SUPERVISOR_FINAL='+str(state.get('status','UNKNOWN')),flush=True)
print('INSTALL_STATUS='+str(state.get('installation',{}).get('status','INSTALL_PENDING_DEVICE')),flush=True)
PYRECEIPT
