"""Explicit user opt-out skips Android emulation without weakening native gates."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('monitor',ROOT/'scripts/archium-r5-monitor.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class QemuOptOutTests(unittest.TestCase):
    def test_workflow_qemu_is_conditional_on_explicit_input(self):
        text=(ROOT/'.github/workflows/baseline-build.yml').read_text()
        self.assertIn('run_qemu:',text);self.assertIn('inputs.run_qemu',text.split('  qemu:')[1])
        self.assertIn('default: false',text.split('      run_qemu:')[1].split('      skip_preflight:')[0])
        self.assertIn('uses: ./.github/workflows/archium-r5-stage.yml',text)
    def test_optout_is_bound_to_exact_dispatch(self):
        s=dict(run_id='123',stage=5,expected_sha='a'*40,source_checkpoint='archium-checkpoint-100-1',source_commit='b'*40,source_run_id='100',next_source_checkpoint='archium-checkpoint-123-1',qemu_enabled=False)
        calls=[]
        def gh(args):
            calls.append(args)
            return {'workflow_runs':[]} if args[0]=='api' else None
        with tempfile.TemporaryDirectory() as d:m.dispatch(s,Path(d),call=gh)
        submitted=next(a for a in calls if a[0]=='workflow');self.assertIn('run_qemu=false',submitted);self.assertIn('expected_sha='+'a'*40,submitted)
