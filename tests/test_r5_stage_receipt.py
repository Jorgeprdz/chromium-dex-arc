import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class StageReceiptTest(unittest.TestCase):
    def module(self):
        spec=importlib.util.spec_from_file_location('r5receipt',ROOT/'scripts/r5-stage-receipt.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def test_ninja_progress_ignores_timing_and_order_but_tracks_outputs(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);log=out/'.ninja_log'
            log.write_text('# ninja log v5\n1\t2\t77\ta.o\tdead\n2\t3\t88\tb.o\tbeef\n')
            first=m.progress(out)
            log.write_text('# ninja log v5\n7\t9\t88\tb.o\tbeef\n1\t8\t77\ta.o\tdead\n')
            self.assertEqual(first,m.progress(out))
            with log.open('a') as f:f.write('3\t4\t99\tc.o\tfeed\n')
            self.assertNotEqual(first['fingerprint'],m.progress(out)['fingerprint'])
    def test_genuine_failure_never_becomes_recoverable_when_pack_exists(self):
        m=self.module()
        env=dict(GITHUB_SHA='a'*40,GITHUB_RUN_ID='42',ARCHIUM_SOURCE_TAG='archium-checkpoint-41-1',ARCHIUM_SOURCE_COMMIT='b'*40,ARCHIUM_SOURCE_RUN_ID='41',ARCHIUM_CHECKPOINT_TAG='archium-checkpoint-42-1')
        r=m.receipt(env,exit_code=7,packed=True,complete=False,progress={'fingerprint':'x'})
        self.assertEqual(r['outcome'],'BUILD_FAILED');self.assertFalse(r['recoverable'])
        r=m.receipt(env,exit_code=0,packed=True,complete=False,progress={'fingerprint':'x'})
        self.assertEqual(r['outcome'],'BUILD_INCOMPLETE');self.assertTrue(r['recoverable'])
        r=m.receipt(env,exit_code=0,packed=False,complete=False,progress={'fingerprint':'x'})
        self.assertEqual(r['outcome'],'BUILD_FAILED');self.assertFalse(r['recoverable'])
