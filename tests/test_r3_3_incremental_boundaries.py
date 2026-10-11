#!/usr/bin/env python3
"""Static guardrails: explicit SHA-pinned dispatch; no push or clean fallback."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class IncrementalR3Test(unittest.TestCase):
    def test_only_explicit_sha_pinned_workflow_dispatch_can_trigger_build(self):
        workflow=(ROOT/'.github/workflows/baseline-build.yml').read_text()
        self.assertNotIn('  push:', workflow)
        self.assertNotIn('.archium-', workflow)
        self.assertIn('expected_sha:', workflow)
        self.assertIn('EXPECTED_SHA: ${{ inputs.expected_sha }}', workflow)
        self.assertIn('test "$GITHUB_SHA" = "$EXPECTED_SHA"', workflow)
        self.assertNotIn('on: [push]', workflow)
        self.assertIn('archium-checkpoint-38018166249-1', workflow)
        self.assertIn('507f28e1265fb98551d3bc1a66f4739fb48d2625', workflow)
        self.assertIn('Confirm R3.3 Actions checkpoint is complete before large download', workflow)
        self.assertIn('source_run_id:', workflow)
        self.assertIn("needs.stage1.result == 'success'",workflow)
        self.assertIn('r3-incomplete-budget:',workflow)
    def test_stages_are_bounded_and_artifact_transfer_is_explicit(self):
        stage=(ROOT/'.github/workflows/archium-stage.yml').read_text()
        self.assertIn("ARCHIUM_CHECKPOINT_STORAGE: artifact",stage)
        self.assertIn("ARCHIUM_SLICE_MINUTES: '75'",stage)
        self.assertIn("ARCHIUM_WORK_SECONDS: '7200'",stage)
        self.assertIn('actions/upload-artifact@v4',stage)
        self.assertIn('actions/download-artifact@v4',stage)
if __name__ == '__main__':
    unittest.main()
