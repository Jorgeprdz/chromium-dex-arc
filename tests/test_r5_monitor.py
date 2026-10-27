import importlib.util
import json
from pathlib import Path
import tempfile
import hashlib
import zipfile
import unittest
from unittest.mock import Mock, patch

PATH = Path(__file__).resolve().parents[1] / 'scripts/archium-r5-monitor.py'
spec = importlib.util.spec_from_file_location('r5_monitor', PATH)
m = importlib.util.module_from_spec(spec)
if PATH.exists(): spec.loader.exec_module(m)


class MonitorTests(unittest.TestCase):
    def state(self):
        return dict(expected_sha='a'*40, run_id='123', stage=1,
                    source_checkpoint='archium-checkpoint-100-1', source_commit='b'*40,
                    source_run_id='100')

    def receipt(self):
        return dict(schema=1, outcome='BUILD_INCOMPLETE', expected_sha='a'*40, run_id='123',
                    source_checkpoint='archium-checkpoint-100-1', source_commit='b'*40,
                    source_run_id='100', new_checkpoint='archium-checkpoint-123-1',
                    new_checkpoint_commit='a'*40, exit_code=0, recoverable=True,
                    checkpoint_verified=True, pack_verified=True, progress={'fingerprint':'new'})

    def test_failure_is_never_recoverable(self):
        r=self.receipt(); r['outcome']='BUILD_FAILED'
        with self.assertRaises(ValueError): m.validate_receipt(r,self.state())

    def test_incomplete_requires_exit_zero_and_exact_identity(self):
        m.validate_receipt(self.receipt(),self.state())
        for key,value in [('exit_code',1),('run_id','124'),('pack_verified',False),('expected_sha','c'*40)]:
            r=self.receipt(); r[key]=value
            with self.assertRaises(ValueError): m.validate_receipt(r,self.state())

    def test_bounds_and_stall(self):
        s=self.state();s['stage']=12;m.validate_state(s,12)
        for value in [0,13]:
            with self.assertRaises(ValueError): m.validate_state(self.state(),value)
        r=self.receipt(); s=self.state(); s['progress_fingerprint']='new'
        with self.assertRaisesRegex(ValueError,'STALLED'): m.validate_receipt(r,s)

    def test_duplicate_lock_refused_and_state_atomic(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); first=m.acquire_lock(p)
            try:
                with self.assertRaises(RuntimeError): m.acquire_lock(p)
                m.save_state(p,self.state())
                self.assertEqual(json.loads((p/'state.json').read_text()),self.state())
            finally: first.close()

    def test_dispatch_intent_persisted_before_network_and_not_repeated(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); s=self.state(); s['new_checkpoint']='archium-checkpoint-123-1'; calls=[]
            def gh(args):
                calls.append(args)
                if args[:2]==['workflow','run']:
                    self.assertIn('dispatch_intent',json.loads((p/'state.json').read_text()))
                    raise RuntimeError('connection lost')
                return {'workflow_runs':[]}
            m.dispatch(s,p,gh)
            m.dispatch(s,p,gh)
            self.assertEqual(sum(c[:2]==['workflow','run'] for c in calls),1)
            self.assertEqual(s['status'],'DISPATCH_AMBIGUOUS')

    def test_nonce_recovers_only_exact_run(self):
        s=self.state(); s['dispatch_intent']={'nonce':'abc','stage':2}
        gh=Mock(return_value={'workflow_runs':[
            dict(id=456,display_title='Archium R5 abc',head_sha='a'*40,
                 head_branch=m.BRANCH,event='workflow_dispatch',path='.github/workflows/baseline-build.yml')]})
        self.assertEqual(m.find_dispatched(s,gh),'456')

    def test_manifest_count_is_exact(self):
        groups=[dict(id=1,name='archium-checkpoint-123-1-00',expires_at='2099-01-01T00:00:00Z',expired=False,
                     size_in_bytes=1,digest='sha256:'+'c'*64,workflow_run={'head_sha':'a'*40})]
        manifest=dict(schema=1,revision=m.PIN,commit='a'*40,tag='archium-checkpoint-123-1',
                      workspace='/mnt/archium/chromium-archium',parts=[
                          dict(name=f'checkpoint-{i:04d}.tar.gz.part',bytes=1,sha256='d'*64) for i in range(9)])
        with self.assertRaises(ValueError): m.validate_checkpoint(groups,manifest,'archium-checkpoint-123-1','a'*40)

    def test_qemu_identity_and_failure(self):
        r=dict(status='QEMU_ABI_BLOCKED',source_sha='a'*40,run_id='123',apk_sha256='e'*64,
               device_validation='PENDING_DEVICE_VALIDATION')
        self.assertEqual(m.validate_qemu(r,self.state(),'e'*64),'QEMU_ABI_BLOCKED')
        r['status']='FAIL'
        with self.assertRaises(ValueError): m.validate_qemu(r,self.state(),'e'*64)

    def incomplete_jobs(self):
        names=['S0 source, capacity and bounded checkpoint manifest',
               'S1 download exactly the verified checkpoint groups',
               'S1 restore once and transition patches', 'S2-S4 blocking gates and incremental build',
               'Preserve checkpoint group 00']
        steps=[dict(name=n,status='completed',conclusion='success') for n in names]
        steps.append(dict(name='Reject incomplete budget as a successful build',status='completed',conclusion='failure'))
        return [dict(name='authorize',status='completed',conclusion='success',steps=[]),
                dict(name='preflight / host',status='completed',conclusion='success',steps=[]),
                dict(name='build / native',status='completed',conclusion='failure',steps=steps),
                dict(name='qemu / qemu',status='completed',conclusion='skipped',steps=[])]

    def test_controlled_incomplete_failure_requires_successful_compiler_and_uploads(self):
        jobs=self.incomplete_jobs()
        m.validate_incomplete_jobs(jobs,1,self.state())
        for index in [3,4]:
            jobs=self.incomplete_jobs(); jobs[2]['steps'][index]['conclusion']='failure'
            with self.assertRaises(ValueError): m.validate_incomplete_jobs(jobs,1,self.state())
        jobs=self.incomplete_jobs(); jobs[1]['conclusion']='skipped'
        with self.assertRaises(ValueError): m.validate_incomplete_jobs(jobs,1,self.state())

    def test_deadline_uses_poll_start_not_finish(self):
        self.assertEqual(m.next_deadline(100,150),700)
        self.assertEqual(m.next_deadline(100,750),1300)


    def test_apk_requires_hash_report_signature_package_and_exclusive_abi(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d); apk=folder/'Archium-for-Android-arm64.apk'
            with zipfile.ZipFile(apk,'w') as archive: archive.writestr('lib/arm64-v8a/libchrome.so',b'fixture')
            digest=hashlib.sha256(apk.read_bytes()).hexdigest()
            (folder/'SHA256SUMS').write_text(digest+'  '+apk.name+'\n')
            report=dict(source_sha='a'*40,run_id='123',branch=m.BRANCH,chromium_pin=m.PIN,
                        APK_VERIFIED='PASS',ROBOLECTRIC_PASS='PASS',JNI_LINK_PASS='PASS',mandatory_gates='PASS')
            (folder/'BUILD_REPORT.json').write_text(json.dumps(report))
            with patch.object(m.subprocess,'run') as signer, patch.object(m.subprocess,'check_output',
                return_value="package: name='app.archium.android'\nnative-code: 'arm64-v8a'\n"):
                self.assertEqual(m.verify_apk(folder,self.state(),'apksigner','aapt2'),(apk,digest))
                self.assertEqual(signer.call_args.args[0][:2],['apksigner','verify'])
            with patch.object(m.subprocess,'run',side_effect=m.subprocess.CalledProcessError(1,['apksigner'])):
                with self.assertRaises(ValueError): m.verify_apk(folder,self.state(),'apksigner','aapt2')
            report['mandatory_gates']='FAIL'; (folder/'BUILD_REPORT.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError): m.verify_apk(folder,self.state(),'apksigner','aapt2')
            report['mandatory_gates']='PASS'; (folder/'BUILD_REPORT.json').write_text(json.dumps(report))
            with patch.object(m.subprocess,'run'),patch.object(m.subprocess,'check_output',
                    return_value="package: name='app.archium.android'\nnative-code: 'arm64-v8a' 'x86_64'"):
                with self.assertRaises(ValueError): m.verify_apk(folder,self.state(),'apksigner','aapt2')

    def test_repair_dispatch_preserves_older_checkpoint_tuple_and_reruns_preflight(self):
        s=self.state();s.update(next_source_checkpoint='archium-checkpoint-99-1',next_source_commit='b'*40,next_source_run_id='99')
        calls=[]
        def call(args):
            if args[0]=='workflow':
                calls.append(args);return None
            return {'workflow_runs':[]}
        with tempfile.TemporaryDirectory() as d:
            m.dispatch(s,Path(d),call)
            fields=' '.join(calls[0])
            self.assertIn('source_checkpoint=archium-checkpoint-99-1',fields)
            self.assertIn('source_commit='+'b'*40,fields)
            self.assertIn('source_run_id=99',fields)
            self.assertIn('skip_preflight=false',fields)
            self.assertEqual(s['dispatch_intent']['source_run_id'],'99')

    def test_failed_github_run_never_downloads_or_installs(self):
        s=self.state()
        run=dict(head_sha=s['expected_sha'],head_branch=m.BRANCH,path='.github/workflows/'+m.WORKFLOW,
                 status='completed',conclusion='failure')
        with patch.object(m,'api',side_effect=[run,{'jobs':[]}]),patch.object(m,'download') as dl, patch.object(m,'unique_json',return_value=dict(self.receipt(),outcome='BUILD_FAILED')):
            with self.assertRaises(ValueError): m.poll(s,Path('/unused'),Mock())
            self.assertEqual(dl.call_count,1)

if __name__=='__main__': unittest.main()
