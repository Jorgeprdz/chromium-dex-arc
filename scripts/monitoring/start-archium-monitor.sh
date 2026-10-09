#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$base/archium-monitor"
export DISPLAY="${DISPLAY:-:2}"
nohup /usr/bin/python3 "$base/monitor-archium-run.py" \
  --run "${1:-37871846597}" --interval 600 --no-window --ascii \
  </dev/null >"$base/archium-monitor/monitor-output.log" 2>&1 &
printf '%s\n' "$!" >"$base/archium-monitor/launcher.pid"
printf 'Monitor solicitado. Registro: %s/archium-monitor/actividad.log\n' "$base"
