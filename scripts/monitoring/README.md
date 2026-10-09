# Archium final build monitor

The Arc desktop geometry + media build has been dispatched, with local passwords disabled.

- Run ID: `37871846597`
- Run URL: https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/37871846597
- Dispatch commit: `0a403f4cf72c74906aaf3a17eb7a8026f6d1dd38`
- Source checkpoint: `archium-checkpoint-37807259506-1`
- Source checkpoint commit: `33db26aa6fad2e8a9ac9ccf26774605edb9db771`
- Poll interval: **600 seconds / 10 minutes**
- Planning ETA: **80–110 minutes from run creation**, based on the recent successful builds of88min21s and93min54s; conditional on passing the gates. Run IDs above are historical examples; pass the newly dispatched run explicitly.

The monitor is read-only. It reports GitHub Actions state and never invents a build
percentage. A completed build is not the same as runtime acceptance: artifact,
signature, update installation and browser E2E checks remain separate steps.

One-shot verification:

```bash
python3 scripts/monitoring/monitor-archium-run.py \
  --run 37871846597 --interval 600 --once --no-window
```

Continuous foreground monitoring:

```bash
python3 scripts/monitoring/monitor-archium-run.py \
  --run 37871846597 --interval 600 --no-window --ascii
```

Background launcher:

```bash
sh scripts/monitoring/start-archium-monitor.sh
```

Termux watcher:

```bash
bash scripts/vigilar-compilacion-arc.sh
```

The launchers point to the current geometry run. The local Termux entry point is
`/workspace/monitor-archium.sh`; it uses `/workspace/macdesk-maintenance/monitor-archium-run.py`.
The repository Termux entry point is `scripts/monitoring/monitor-archium.sh`.
An optional first argument overrides the run ID in the monitoring launchers.

The terminal panel uses continuous box borders and shows only status, current phase,
elapsed time, planning ETA, update time and controls. Detailed events remain in the log.

The user subsequently authorized downloading and installing the update after this run.
`update-archium-run.py` is an independent worker: it requires a successful run at the
expected commit, checks the artifact checksum, package and APK signature, targets the
explicit authorized Samsung device, and installs with `adb install -r` to preserve data.
It records the installed version and compares the installed `base.apk` SHA-256 with
the downloaded artifact. A matching version code alone never confirms installation.
It never uninstalls or clears application data.

The terminal wrapper displays the independent updater state from
`.archium-install/<run>/status.json`, including **Instalación: CONFIRMADA** only after
the installed hash matches. Its refresh interval remains ten minutes. The updater
continues when the visible monitor is closed.
Closing the read-only monitor does not stop the independently launched update worker.

```bash
python3 scripts/monitoring/update-archium-run.py --wait \
  --serial emulator-5554 --device-ip 192.168.101.105 \
  --state-dir .sync-audit/arc-geometry-20261009/automatic-update
```

In this environment `emulator-5554` is the verified ADB bridge to the Samsung SM-S931B
at the authorized IP. Installation rechecks the device manufacturer and IP.
