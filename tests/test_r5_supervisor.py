import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]

class SupervisorTests(unittest.TestCase):
 def module(self):
  s=importlib.util.spec_from_file_location('sup',ROOT/'scripts/archium-r5-supervisor.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_infrastructure_never_wakes_codex(self):
  m=self.module()
  for text in ['BLOCKED_CHECKPOINT_INCOMPATIBLE','No space left on device','QEMU_ABI_BLOCKED','HTTP 401 Bad credentials','quota exhausted']:
   self.assertEqual(m.classify(text)[0],'BLOCKED')
  self.assertEqual(m.classify('Foo.java:7: error: cannot find symbol')[0],'REPAIR')
  self.assertEqual(m.classify('undefined reference to JNI_App')[0],'REPAIR')
  self.assertEqual(m.classify('java.lang.NullPointerException in Robolectric suite')[0],'REPAIR')
  self.assertEqual(m.classify('FAILED (failures=1)')[0],'REPAIR')
  self.assertEqual(m.classify('unknown technical outcome')[0],'BLOCKED')
 def test_assertion_quoted_workflow_does_not_mask_technical_failure(self):
  m=self.module()
  failure="FAIL: test_workflow_exposes_source_identity_once_and_has_no_clean_continuation\nAssertionError: 'needs: preflight' not found in 'checkpoint source authorization signature expired'\nFAILED (failures=1)"
  self.assertEqual(m.classify(failure)[0],'REPAIR')
  self.assertEqual(m.classify(failure+'\nHTTP 403 Bad credentials')[0],'BLOCKED')
 def test_wrong_or_missing_thread_is_rejected(self):
  m=self.module()
  self.assertTrue(m.verify_thread_events([{'type':'thread.started','thread_id':'exact'},{'type':'turn.completed'}],'exact'))
  for events in [[],[{'type':'thread.started','thread_id':'other'}],[{'type':'thread.started','thread_id':'exact'},{'type':'turn.failed'}]]:
   with self.assertRaises(ValueError):m.verify_thread_events(events,'exact')
 def test_limits(self):
  m=self.module();s={'night_started_epoch':100,'stage':1,'repairs_by_cause':{}}
  self.assertIsNone(m.limit_reason(s,101,36000,6,'cause',2))
  self.assertEqual(m.limit_reason(s,36101,36000,6,'cause',2),'NIGHT_BUDGET')
  s['stage']=6;self.assertEqual(m.limit_reason(s,101,36000,6,'cause',2),'RUN_LIMIT')
  s['stage']=1;s['repairs_by_cause']['cause']=2
  self.assertEqual(m.limit_reason(s,101,36000,6,'cause',2),'REPAIR_LIMIT')
 def test_session_must_exist_exactly_and_idle_state_is_observed(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'rollout-id.jsonl';p.write_text(json.dumps({'type':'session_meta','payload':{'id':'id'}})+'\n'+json.dumps({'type':'event_msg','payload':{'type':'task_started'}})+'\n')
   self.assertEqual(m.find_session(Path(d),'id'),p);self.assertFalse(m.session_idle(p))
   with p.open('a') as f:f.write(json.dumps({'type':'event_msg','payload':{'type':'task_complete'}})+'\n')
   self.assertTrue(m.session_idle(p))
   with self.assertRaises(ValueError):m.find_session(Path(d),'wrong')

class InstallationReceiptTests(unittest.TestCase):
 def test_receipt_requires_system_evidence_and_exact_installed_identity(self):
  m=SupervisorTests().module()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);proof=p/'android-system.json';installed=p/'installed-base.apk';installed.write_bytes(b'installed fixture APK')
   proof.write_text(json.dumps(dict(schema=1,collector='android-package-inspection',authorization='AUTHORIZED',device_serial='fixture-device',package_path_output='package:/data/app/fixture/base.apk',package_dump='versionCode=808600074',installed_apk_file=str(installed))))
   import hashlib
   apk_digest=hashlib.sha256(installed.read_bytes()).hexdigest()
   r=dict(status='INSTALL_SUCCESS',source_sha='a'*40,run_id='42',apk_sha256=apk_digest,installed_apk_sha256=apk_digest,package='app.archium.android',version_code='808600074',certificate_sha256='c'*64,system_evidence_file=str(proof),system_evidence_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
   state=dict(expected_sha='a'*40,run_id='42',apk_sha256=apk_digest,apk_path='/expected.apk')
   badging="package: name='app.archium.android' versionCode='808600074' versionName='157.0.8086.0'"
   cert='Signer #1 certificate SHA-256 digest: '+'c'*64
   outputs=[badging,badging,cert,cert]
   with patch.object(m.subprocess,'check_output',side_effect=outputs):self.assertTrue(m.validate_installation(r,state,p,'aapt2','apksigner'))
   r['installed_apk_sha256']='d'*64
   with self.assertRaises(ValueError):m.validate_installation(r,state,p,'aapt2','apksigner')

class ResumeExecutionTests(unittest.TestCase):
 def setup_fixture(self,base,thread='exact'):
  import time
  from types import SimpleNamespace
  folder=base/'state';folder.mkdir()
  sessions=base/'sessions';sessions.mkdir()
  (sessions/'rollout-exact.jsonl').write_text(json.dumps({'type':'session_meta','payload':{'id':'exact'}})+'\n'+json.dumps({'type':'event_msg','payload':{'type':'task_complete'}})+'\n')
  fake=base/'codex';counter=base/'invocations'
  fake.write_text('#!/usr/bin/python3\nimport json,pathlib,sys\nsys.stdin.read()\np=pathlib.Path('+repr(str(counter))+');p.write_text(p.read_text()+"1" if p.exists() else "1")\nresult=pathlib.Path(sys.argv[sys.argv.index("--output-last-message")+1]).parent/"worker-result.json"\nresult.write_text(json.dumps({"status":"REPAIR_READY"}))\nprint(json.dumps({"type":"thread.started","thread_id":'+repr(thread)+'}),flush=True)\nprint(json.dumps({"type":"turn.completed"}),flush=True)\n')
  fake.chmod(0o755)
  args=SimpleNamespace(sessions=sessions,codex=str(fake),budget_hours=10)
  state=dict(codex_session_id='exact',night_started_epoch=time.time(),run_id='42',expected_sha='a'*40,last_valid_checkpoint=dict(source_checkpoint='archium-checkpoint-41-1',source_commit='b'*40,source_run_id='41'))
  report=folder/'event';report.mkdir();(report/'failure-report.md').write_text('fixture error: missing symbol')
  return args,state,folder,report,counter
 def test_real_subprocess_contract_checks_thread_and_replays_without_second_execution(self):
  m=SupervisorTests().module()
  with tempfile.TemporaryDirectory() as d:
   args,state,folder,report,counter=self.setup_fixture(Path(d))
   self.assertEqual(m.run_worker(args,state,folder,'repair',report)['status'],'REPAIR_READY')
   self.assertEqual(m.run_worker(args,state,folder,'repair',report)['status'],'REPAIR_READY')
   self.assertEqual(counter.read_text(),'1')
   self.assertTrue((report/'codex-repair/events.jsonl').is_file())
   self.assertTrue((report/'codex-repair/stderr.log').is_file())
 def test_wrong_thread_from_subprocess_is_rejected(self):
  m=SupervisorTests().module()
  with tempfile.TemporaryDirectory() as d:
   args,state,folder,report,counter=self.setup_fixture(Path(d),'accidental-new-thread')
   with self.assertRaisesRegex(ValueError,'CODEX_RESUME_BLOCKED'):m.run_worker(args,state,folder,'repair',report)

class SupervisorReviewRegressions(unittest.TestCase):
 def test_audit_result_can_replay_after_interruption(self):
  from types import SimpleNamespace
  m=SupervisorTests().module()
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d);(folder/'install-receipt.json').write_text('{}')
   state=dict(status='BUILD_SUCCESS QEMU_TESTS_PASS',expected_sha='a'*40,run_id='42',apk_sha256='b'*64,codex_session_id='exact')
   args=SimpleNamespace(sessions=folder,aapt2='aapt2',apksigner='apksigner')
   result=dict(status='AUDIT_PARTIAL',source_sha='a'*40,evidence_file=str(ROOT/'TODO.md'))
   with patch.object(m,'validate_installation',return_value=True),patch.object(m,'find_session',return_value=folder/'session'),patch.object(m,'session_idle',return_value=True),patch.object(m,'run_worker',side_effect=[RuntimeError('interrupted'),result]) as worker:
    with self.assertRaises(RuntimeError):m.finish_build(args,state,folder)
    m.finish_build(args,state,folder)
    self.assertEqual(state['status'],'COMPLETE_SCOPED');self.assertEqual(worker.call_count,2)
 def test_approved_repair_restarts_dispatch_without_polling_old_run(self):
  m=SupervisorTests().module()
  s=dict(status='REPAIR_APPROVED',expected_sha='a'*40,run_id='42',next_source_checkpoint='archium-checkpoint-41-1',next_source_commit='b'*40,next_source_run_id='41')
  with patch.object(m.monitor,'dispatch') as dispatch,patch.object(m.monitor,'poll') as poll,patch.object(m.monitor,'api',return_value={'object':{'sha':'a'*40}}),patch.object(m.monitor,'all_runs',return_value=[]):
   self.assertFalse(m.poll_owned_phase(s,Path('/fixture'),None))
   dispatch.assert_called_once();poll.assert_not_called()
 def test_unrelated_system_text_cannot_authorize_install_success(self):
  m=SupervisorTests().module()
  with tempfile.TemporaryDirectory() as d:
   import hashlib
   folder=Path(d);proof=folder/'unrelated.txt';proof.write_text('old unrelated capture')
   s=dict(expected_sha='a'*40,run_id='42',apk_sha256='b'*64,apk_path='/expected.apk')
   r=dict(status='INSTALL_SUCCESS',source_sha='a'*40,run_id='42',apk_sha256='b'*64,installed_apk_sha256='b'*64,package='app.archium.android',version_code='808600074',certificate_sha256='c'*64,system_evidence_file=str(proof),system_evidence_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
   with patch.object(m.subprocess,'check_output',side_effect=["package: name='app.archium.android' versionCode='808600074'",'certificate SHA-256 digest: '+'c'*64]):
    with self.assertRaises(ValueError):m.validate_installation(r,s,folder,'aapt2','apksigner')
