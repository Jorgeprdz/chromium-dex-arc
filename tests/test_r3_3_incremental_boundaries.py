#!/usr/bin/env python3
"""Static guardrails: only marker dispatches native builds and reuse is pinned."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class IncrementalR3Test(unittest.TestCase):
    def test_only_explicit_incremental_marker_can_trigger_its_push(self):
        workflow=(ROOT/'.github/workflows/baseline-build.yml').read_text()
        self.assertIn('.archium-r3-3-incremental-dispatch', workflow)
        self.assertNotIn('on: [push]', workflow)
        self.assertIn('archium-checkpoint-38018166249-1', workflow)
        self.assertIn('507f28e1265fb98551d3bc1a66f4739fb48d2625', workflow)
        self.assertIn('Confirm R3.3 Actions checkpoint is complete before large download', workflow)
        self.assertIn('source_run_id:', workflow)
        self.assertIn("github.ref_name != 'assistant/archium-r3-visual-fixes' && needs.stage2.outputs.complete != 'true'",workflow)
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
