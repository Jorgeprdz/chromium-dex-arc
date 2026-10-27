"""Execute the delivered budget calculations; no Chromium build or remote dispatch."""
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class R5TimeBudgetTests(unittest.TestCase):
    def budget(self, **overrides):
        source = (ROOT/'scripts/build-archium-r5.sh').read_text()
        prefix = source[source.index('budget() {'):source.index('save_checkpoint() {')]
        shell = '''set -euo pipefail
die() { exit 2; }
date() { printf 100000; }
''' + prefix + '''
printf '[%s,%s,%s,%s,%s,%s,%s]' "$slice_minutes" "$max_slices" "$work_seconds" "$deadline" "$checkpoint_seconds" "$upload_seconds" "$(wall_remaining)"
'''
        env = {k:v for k,v in os.environ.items() if not k.startswith('ARCHIUM_')}
        env.update(RUNNER_TEMP='/tmp', **overrides)
        return subprocess.run(['bash', '-c', shell], env=env, capture_output=True, text=True)

    def test_extended_work_window_keeps_full_checkpoint_and_upload_reserves(self):
        result = self.budget()
        self.assertEqual(result.returncode, 0, result.stderr)
        slices, count, work, deadline, checkpoint, upload, available = json.loads(result.stdout)
        self.assertEqual((slices, count, work), (120, 2, 18000))
        self.assertEqual(deadline-100000, 21600)
        self.assertEqual((checkpoint, upload), (3600, 1200))
        self.assertEqual(available, 21600-checkpoint-upload)

    def test_workflow_deadline_and_slices_match_script_and_hosted_limit(self):
        workflow = (ROOT/'.github/workflows/archium-r5-stage.yml').read_text()
        minutes = int(re.search(r'timeout-minutes: (\d+)', workflow)[1])
        deadline = int(re.search(r'\$\(date \+%s\) \+ (\d+)', workflow)[1])
        self.assertEqual(minutes, 360)
        self.assertEqual(deadline, minutes*60-300)
        self.assertIn("ARCHIUM_SLICE_MINUTES: '120'", workflow)
        result = self.budget(ARCHIUM_JOB_DEADLINE_EPOCH=str(100000+deadline))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[-1], deadline-4800)
        self.assertGreater(json.loads(result.stdout)[-1], 4*3600)

    def test_chain_work_budget_excludes_restore_time(self):
        source=(ROOT/'scripts/build-archium-r5.sh').read_text()
        function=source[source.index('run_work() {'):source.index('install_deps() {')]
        shell="""set -euo pipefail
work_seconds=18000
ARCHIUM_STAGE_WORK_SECONDS=7200
stage_work_seconds=7200
work_started=$((SECONDS-30))
job_elapsed() { printf 1500; }
wall_remaining() { printf 16000; }
timeout() { printf '%s\\n' "$@"; }
"""+function+'\nrun_work TERM 10000 false true\n'
        r=subprocess.run(['bash','-c',shell],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('7170s',r.stdout)

    def test_budget_caps_still_reject_unbounded_or_invalid_overrides(self):
        for override in [dict(ARCHIUM_SLICE_MINUTES='121'),
                         dict(ARCHIUM_MAX_SLICES='3'),
                         dict(ARCHIUM_WORK_SECONDS='18001'),
                         dict(ARCHIUM_CHECKPOINT_SECONDS='0')]:
            with self.subTest(override=override):
                self.assertEqual(self.budget(**override).returncode, 2)
