"""Watch-only UI: identity gates, no QEMU dependency, deadlines and nonclosing finish."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r53_watch',ROOT/'scripts/archium-r5-watch.py')
w=importlib.util.module_from_spec(spec)
if Path(spec.origin).exists():spec.loader.exec_module(w)

class WatchTests(unittest.TestCase):
    def state(self):return dict(run_id='123',expected_sha='a'*40,source_checkpoint='archium-checkpoint-100-1',source_commit='b'*40,source_run_id='100',stage=6)
    def github_run(self,conclusion=None):
        return dict(id=123,head_sha='a'*40,head_branch='assistant/archium-r5-arc-experience',path='.github/workflows/baseline-build.yml',status='completed' if conclusion else 'in_progress',conclusion=conclusion,html_url='https://github.com/example/run/123')
    def test_clear_before_ascii_frame_and_color_status(self):
        output=io.StringIO();s=self.state();s.update(status='BUILD_SUCCESS',github_status='completed/success',terminal=True)
        w.render(s,output=output,color=True,clear=True,width=80)
        text=output.getvalue();self.assertTrue(text.startswith('\x1b[2J\x1b[H'));self.assertIn('+',text);self.assertIn('ARCHIUM R5',text);self.assertIn('\x1b[32m',text);self.assertIn('Ctrl+C',text)
        self.assertNotIn('QEMU_ABI_BLOCKED',text)
    def test_no_qemu_download_install_or_dispatch_for_success(self):
        s=self.state();call=Mock(side_effect=[self.github_run('success'),{'jobs':[{'name':'build / build','status':'completed','conclusion':'success','steps':[]}]},{'artifacts':[{'name':'Archium-for-Android-arm64','expired':False,'size_in_bytes':100}]}])
        w.refresh(s,call=call);self.assertTrue(s['terminal']);self.assertEqual(s['status'],'BUILD_SUCCESS');self.assertEqual(s['apk_status'],'ARTIFACT_AVAILABLE_NOT_DOWNLOADED')
        self.assertEqual(call.call_count,3);self.assertTrue(all('qemu' not in c.args[0].lower() for c in call.call_args_list))
    def test_failure_retains_run_diagnostic_without_retry(self):
        s=self.state();call=Mock(side_effect=[self.github_run('failure'),{'jobs':[{'name':'build / build','status':'completed','conclusion':'failure','steps':[{'name':'Compile Java','conclusion':'failure','status':'completed'}]}]},{'artifacts':[]}])
        w.refresh(s,call=call);self.assertTrue(s['terminal']);self.assertEqual(s['status'],'BUILD_FAILED');self.assertIn('Compile Java',s['job_step']);self.assertEqual(s['apk_status'],'NO_APK')
    def test_wrong_identity_is_rejected(self):
        s=self.state();run=self.github_run();run['head_sha']='c'*40
        with self.assertRaisesRegex(ValueError,'identity'):w.refresh(s,call=Mock(return_value=run))
    def test_finished_monitor_stays_open_without_more_github_queries(self):
        s=self.state();clock=[0.];sleeps=[];frames=[]
        def sleep(n):
            sleeps.append(n);clock[0]+=n
            if len(sleeps)==3:raise KeyboardInterrupt
        def query(state):state.update(terminal=True,status='BUILD_SUCCESS')
        query=Mock(side_effect=query)
        with tempfile.TemporaryDirectory() as d:
            w.run_loop(s,Path(d),query=query,draw=lambda v:frames.append(v['status']),sleep=sleep,monotonic=lambda:clock[0],wall=lambda:1000+clock[0])
        self.assertEqual(query.call_count,1);self.assertEqual(frames,['BUILD_SUCCESS','BUILD_SUCCESS']);self.assertEqual(sleeps,[0.,600.,600.])
    def test_first_query_immediate_then_exact_600_seconds_despite_query_duration(self):
        s=self.state();clock=[0.];calls=[];sleeps=[]
        def sleep(n):
            sleeps.append(n);clock[0]+=n
            if len(sleeps)==3:raise KeyboardInterrupt
        def query(state):calls.append(clock[0]);clock[0]+=17
        with tempfile.TemporaryDirectory() as d:
            w.run_loop(s,Path(d),query=query,draw=lambda s:None,sleep=sleep,monotonic=lambda:clock[0],wall=lambda:1000+clock[0])
        self.assertEqual(calls,[0.,600.]);self.assertEqual(sleeps,[0.,583.,583.])
    def test_controlled_incomplete_is_not_reported_as_compiler_failure(self):
        s=self.state();receipt=dict(schema=1,outcome='BUILD_INCOMPLETE',expected_sha='a'*40,run_id='123',source_checkpoint=s['source_checkpoint'],source_commit=s['source_commit'],source_run_id=s['source_run_id'],exit_code=0,recoverable=True,checkpoint_verified=True,pack_verified=True,new_checkpoint='archium-checkpoint-123-1',new_checkpoint_commit='a'*40,progress={'fingerprint':'advanced'})
        call=Mock(side_effect=[self.github_run('failure'),{'jobs':[]},{'artifacts':[{'name':'Archium-R5-stage-receipt','expired':False,'size_in_bytes':495}]}])
        w.refresh(s,call=call,read_receipt=Mock(return_value=receipt))
        self.assertEqual(s['status'],'BUILD_INCOMPLETE_CHECKPOINT_SAVED');self.assertTrue(s['terminal']);self.assertEqual(s['new_checkpoint'],'archium-checkpoint-123-1')
    def test_temporary_receipt_network_error_does_not_freeze_terminal_state(self):
        s=self.state();call=Mock(side_effect=[self.github_run('success'),{'jobs':[]},{'artifacts':[{'name':'Archium-R5-stage-receipt','expired':False,'size_in_bytes':495}]}])
        with self.assertRaises(RuntimeError):w.refresh(s,call=call,read_receipt=Mock(side_effect=RuntimeError('temporary network failure')))
        self.assertFalse(s.get('terminal',False))
    def test_receipt_from_other_run_is_blocked(self):
        s=self.state();receipt=dict(schema=1,outcome='BUILD_FAILED',run_id='999')
        call=Mock(side_effect=[self.github_run('failure'),{'jobs':[]},{'artifacts':[{'name':'Archium-R5-stage-receipt','expired':False,'size_in_bytes':495}]}])
        with self.assertRaisesRegex(ValueError,'identity'):w.refresh(s,call=call,read_receipt=Mock(return_value=receipt))
    def test_terminal_reopen_preserves_screen_without_network(self):
        s=self.state();s.update(terminal=True,status='BUILD_FAILED');query=Mock();calls=[0]
        def sleep(n):
            calls[0]+=1
            if calls[0]>1:raise KeyboardInterrupt
        with tempfile.TemporaryDirectory() as d:
            w.run_loop(s,Path(d),query=query,draw=lambda s:None,sleep=sleep,monotonic=lambda:0.,wall=lambda:1000.)
        query.assert_not_called()
