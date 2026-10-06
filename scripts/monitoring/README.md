# Existing monitor scripts preserved for continuation

These are snapshots of the workspace monitor scripts, not a newly started monitor.
Their old default IDs and intervals have intentionally been preserved. After the
FINAL build dispatch, use its actual ID and 900 seconds (15 minutes), verify
`--once`, leave one monitor running, then pause the agent.

Portable direct invocation from a clone (replace ID_REAL with the actual ID):

```bash
python3 scripts/monitoring/monitor-archium-run.py --run ID_REAL --interval 900 --once --no-window
python3 scripts/monitoring/monitor-archium-run.py --run ID_REAL --interval 900 --no-window
```

The second command runs continuously in the foreground; use a persistent process
launcher appropriate to the execution environment for background monitoring.
The legacy launchers have workspace-specific paths and need integration before
use from this directory. Legacy text still says ten minutes and includes an old
duration estimate: update those labels at final dispatch, with no duration promise.
No personal credentials are included; the Python monitor uses the public GitHub API.
