#!/usr/bin/env python3
"""Check terminal diagnostics against a real failed job log; no CI execution claim."""
import argparse
import importlib.util
from pathlib import Path
import tempfile
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--monitor', type=Path, required=True)
    parser.add_argument('--job-log', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('monitor', args.monitor)
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)

    class DiagnosticsTest(unittest.TestCase):
        def logs(self, jobs, contents):
            with tempfile.TemporaryDirectory() as temporary:
                state = Path(temporary)
                for job, body in zip(jobs, contents):
                    (state / f"job-{job['id']}.log").write_text(body)
                    (state / f"job-{job['id']}.final").write_text('complete')
                return monitor.log_tail(jobs, state)

        def test_failed_job_precedes_tied_successful_cleanup(self):
            jobs = [{'id': 1, 'name': 'authorize', 'status': 'completed', 'conclusion': 'success',
                     'completed_at': '2026-10-12T17:01:42Z'},
                    {'id': 2, 'name': 'build / build', 'status': 'completed', 'conclusion': 'failure',
                     'completed_at': '2026-10-12T17:01:42Z'}]
            label, lines = self.logs(jobs, ['Cleaning up orphan processes\n', args.job_log.read_text()])
            self.assertEqual(label, 'PRIMER ERROR REAL', lines)
            self.assertIn('AssertionError', '\n'.join(lines))

        def test_sharded_assertion_keeps_the_affected_test(self):
            job = {'id': 3, 'name': 'build / build', 'status': 'completed', 'conclusion': 'failure'}
            label, lines = self.logs([job], [args.job_log.read_text()])
            self.assertEqual(label, 'PRIMER ERROR REAL', lines)
            self.assertIn('ArcToolbarReparentingTest', '\n'.join(lines))

        def test_existing_ninja_diagnostic_remains_visible(self):
            job = {'id': 4, 'name': 'build / build', 'status': 'completed', 'conclusion': 'failure'}
            label, lines = self.logs([job], ['2026-10-12T16:39:00Z NINJA_QUERY=FAIL: invalid bytes\n'])
            self.assertEqual(label, 'PRIMER ERROR REAL')
            self.assertIn('NINJA_QUERY=FAIL', '\n'.join(lines))

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DiagnosticsTest))
    raise SystemExit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
