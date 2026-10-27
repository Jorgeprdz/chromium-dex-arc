import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ChainTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('chain', ROOT/'scripts/r5-chain.py')
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

    def stage(self, n, outcome='BUILD_INCOMPLETE'):
        return dict(schema=1, outcome=outcome, expected_sha='a'*40, run_id='123',
            source_checkpoint='archium-checkpoint-100-1' if n==1 else f'archium-checkpoint-123-{n-1}',
            source_commit='b'*40 if n==1 else 'a'*40, source_run_id='100' if n==1 else '123',
            new_checkpoint=f'archium-checkpoint-123-{n}' if outcome=='BUILD_INCOMPLETE' else None,
            new_checkpoint_commit='a'*40 if outcome=='BUILD_INCOMPLETE' else None,
            exit_code=0, recoverable=outcome=='BUILD_INCOMPLETE', checkpoint_verified=outcome=='BUILD_INCOMPLETE',
            pack_verified=outcome=='BUILD_INCOMPLETE', progress=dict(fingerprint=f'{n:064x}',completed_outputs=n*100,completed_gates=10))

    def summarize(self, stages, maximum=12):
        return self.module().summarize(stages,'a'*40,'123','archium-checkpoint-100-1','b'*40,'100',maximum)

    def test_twelve_stages_preserve_latest_checkpoint_without_claiming_apk(self):
        r=self.summarize([self.stage(n) for n in range(1,13)])
        self.assertEqual(r['outcome'],'BUILD_INCOMPLETE')
        self.assertEqual(r['new_checkpoint'],'archium-checkpoint-123-12')
        self.assertEqual(r['source_run_id'],'100')
        self.assertEqual(r['chain']['stages_completed'],12)

    def test_success_stops_early_and_retains_exact_identity(self):
        r=self.summarize([self.stage(1),self.stage(2,'BUILD_SUCCESS')])
        self.assertEqual(r['outcome'],'BUILD_SUCCESS')
        self.assertEqual(r['chain']['stages_completed'],2)

    def test_failure_stall_wrong_source_and_missing_stage_rejected(self):
        for key,value in [('outcome','BUILD_FAILED'),('pack_verified',False),('source_run_id','999'),
                          ('source_commit','c'*40),('new_checkpoint','archium-checkpoint-123-9')]:
            second=self.stage(2);second[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.summarize([self.stage(1),second])
        second=self.stage(2);second['progress']=self.stage(1)['progress']
        with self.assertRaisesRegex(ValueError,'STALLED'):self.summarize([self.stage(1),second])
        with self.assertRaises(ValueError):self.summarize([self.stage(1),self.stage(3)])

    def test_premature_end_after_incomplete_cannot_become_success(self):
        with self.assertRaises(ValueError):self.summarize([self.stage(1)])
        with self.assertRaises(ValueError):self.summarize([self.stage(1,'BUILD_SUCCESS'),self.stage(2)])

    def test_caps_and_counter_regression(self):
        for cap in (0,13):
            with self.assertRaises(ValueError):self.summarize([self.stage(1)],cap)
        second=self.stage(2);second['progress']['completed_outputs']=1
        with self.assertRaises(ValueError):self.summarize([self.stage(1),second])

    def test_prune_only_complete_old_sets_from_this_chain_keeps_latest_two(self):
        m=self.module()
        items=[dict(id=n*10+i,name=f'archium-checkpoint-123-{n}-{i:02d}') for n in range(1,5) for i in range(2)]
        items += [dict(id=999,name='archium-checkpoint-100-1-00'),dict(id=998,name='Archium-for-Android-arm64')]
        selected=m.prunable(items,'123',5)
        self.assertEqual({a['id'] for a in selected},{10,11,20,21})
        with self.assertRaises(ValueError):m.prunable([dict(id=1,name='archium-checkpoint-123-1-01')],'123',4)

    def test_workflow_has_twelve_sequential_stages_and_no_dispatch_loop(self):
        workflow=(ROOT/'.github/workflows/baseline-build.yml').read_text()
        for n in range(2,13):
            job=workflow.split(f'  stage_{n}:\n',1)[1].split('\n  stage_',1)[0].split('\n  finish:',1)[0]
            previous='build' if n==2 else f'stage_{n-1}'
            self.assertIn(f'needs: {previous}',job)
            self.assertIn("outcome == 'BUILD_INCOMPLETE'",job)
            self.assertIn(f'stage_number: {n}',job)
            self.assertIn(f'needs.{previous}.outputs.new_checkpoint',job)
        self.assertNotIn('workflow run',(ROOT/'.github/workflows/archium-r5-stage.yml').read_text())

if __name__=='__main__':unittest.main()
