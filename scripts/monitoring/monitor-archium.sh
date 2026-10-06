#!/data/data/com.termux/files/usr/bin/bash
# Termux: bash ~/monitor-archium.sh
set -u
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
monitor="$script_dir/macdesk-maintenance/monitor-archium-run.py"
run_id="${1:-37438146116}"
state_dir="$script_dir/.archium-monitor-termux"
python_bin=$(command -v python3 || command -v python || true)
if [ -z "$python_bin" ]; then
  printf 'Instala Python primero: pkg install python\n' >&2
  exit 1
fi
if [ ! -f "$monitor" ]; then
  printf 'Falta el monitor: %s\n' "$monitor" >&2
  exit 1
fi
mkdir -p "$state_dir"
trap 'printf "\nMonitor detenido. La compilacion sigue en GitHub.\n"; exit 0' INT TERM
while :; do
  if [ -t 1 ]; then printf '\033[2J\033[H'; fi
  "$python_bin" "$monitor" --run "$run_id" --once --no-window --ascii --state-dir "$state_dir"
  if [ "${ARCHIUM_MONITOR_ONCE:-0}" = 1 ]; then exit 0; fi
  printf '\nLog guardado en: %s/actividad.log\n' "$state_dir"
  if read -r -t 900 -n 1 key; then
    case "$key" in q|Q) exit 0 ;; esac
  fi
  printf '\n'
done
