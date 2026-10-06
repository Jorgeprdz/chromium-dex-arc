#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$base/archium-monitor"
export DISPLAY="${DISPLAY:-:2}"
nohup /usr/bin/python3 "$base/monitor-archium-run.py" \
  </dev/null >"$base/archium-monitor/monitor-output.log" 2>&1 &
printf 'Monitor solicitado. Registro: %s/archium-monitor/actividad.log\n' "$base"
