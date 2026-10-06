# Archium final build monitor

The FINAL Arc + local-password/CSV build has been dispatched.

- Run ID: `37438146116`
- Run URL: https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/37438146116
- Dispatch commit: `739efb61e79d7d606f5aa10694552b5edee42ef1`
- Source checkpoint: `archium-checkpoint-37255997027-7`
- Source checkpoint commit: `c8ffd13ee7fe1c6baab4913da6a01e8009febe18`
- Poll interval: **900 seconds / 15 minutes**

The monitor is read-only. It reports GitHub Actions state and never invents a build
percentage. A completed build is not the same as runtime acceptance: artifact,
signature, update installation and browser E2E checks remain separate steps.

One-shot verification:

```bash
python3 scripts/monitoring/monitor-archium-run.py \
  --run 37438146116 --interval 900 --once --no-window
```

Continuous foreground monitoring:

```bash
python3 scripts/monitoring/monitor-archium-run.py \
  --run 37438146116 --interval 900 --no-window
```

Background launcher:

```bash
sh scripts/monitoring/start-archium-monitor.sh
```

Termux watcher:

```bash
bash scripts/vigilar-compilacion-arc.sh
```

The repository launchers are now pinned to the current FINAL run. Do not switch them
to an older build ID or shorten the interval without an explicit reason.
