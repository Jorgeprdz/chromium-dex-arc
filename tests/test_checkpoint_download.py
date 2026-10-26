"""Exercise sequential download completion with local artifact fixtures, never CI bytes."""
import hashlib, importlib.util, json, subprocess, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class DownloadTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('download', ROOT/'scripts/download-r5-checkpoint.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)/'checkpoint'
        self.tag = 'archium-checkpoint-123-1'; self.sha = 'a'*40
        self.manifest = {'tag':self.tag,'commit':self.sha,'parts':[
            {'name':f'checkpoint-{i:04d}.tar.gz.part','bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}
            for i in range(9)]}
        self.payload = json.dumps(self.manifest).encode()
        self.report = dict(source_tag=self.tag,source_sha=self.sha,
            manifest_sha256=hashlib.sha256(self.payload).hexdigest(),
            available_bytes=100_000_000_000,free_inodes=3_000_000)
        self.items = [dict(name=f'{self.tag}-{i:02d}',id=i+1,size_in_bytes=100,
            expires_at='2099-01-01T00:00:00Z',expired=False,digest='sha256:'+'b'*64,
            workflow_run={'head_sha':self.sha}) for i in range(2)]
        self.calls=[]; self.failure=None
    def runner(self,command,**kwargs):
        self.calls.append(command)
        group=int(command[command.index('--name')+1][-2:])
        folder=Path(command[command.index('--dir')+1]); folder.mkdir(parents=True,exist_ok=True)
        if group==0:(folder/'checkpoint.json').write_bytes(self.payload)
        for part in self.manifest['parts'][group*8:(group+1)*8]:
            (folder/part['name']).write_bytes(b'x')
        if group==1:
            if self.failure=='missing':(folder/self.manifest['parts'][8]['name']).unlink()
            if self.failure=='extra':(folder/'unexpected').write_bytes(b'x')
            if self.failure=='truncated':(folder/self.manifest['parts'][8]['name']).write_bytes(b'')
            if self.failure=='exit':raise subprocess.CalledProcessError(1,command)
        return subprocess.CompletedProcess(command,0)
    def run_download(self):
        self.module.download_groups(self.items,self.report,self.folder,'owner/repo','123',runner=self.runner)
    def test_workflow_uses_checked_sequential_downloader(self):
        stage=(ROOT/'.github/workflows/archium-r5-stage.yml').read_text()
        step=stage.split('      - name: S1 download exactly the verified checkpoint groups',1)[1].split('      - name: S1 restore once',1)[0]
        self.assertIn('scripts/download-r5-checkpoint.py',step)
        self.assertNotIn('merge-multiple',step)
        self.assertIn('--preflight "$RUNNER_TEMP/checkpoint-preflight.json"',step)
    def test_sequential_complete_inventory(self):
        self.run_download()
        self.assertEqual(len(self.calls),2)
        self.assertEqual({p.name for p in self.folder.iterdir()}, {'checkpoint.json'}|{p['name'] for p in self.manifest['parts']})
    def test_success_exit_with_missing_group_files_is_rejected(self):
        self.failure='missing'
        with self.assertRaisesRegex(ValueError,'missing=.*checkpoint-0008'):self.run_download()
    def test_extra_or_truncated_file_is_rejected(self):
        for failure,pattern in [('extra','unexpected'),('truncated','truncated')]:
            with self.subTest(failure=failure):
                self.folder=Path(self.temp.name)/failure;self.failure=failure
                with self.assertRaisesRegex(ValueError,pattern):self.run_download()
    def test_transfer_failure_is_not_retried(self):
        self.failure='exit'
        with self.assertRaises(subprocess.CalledProcessError):self.run_download()
        self.assertEqual(len(self.calls),2)
    def test_changed_manifest_is_rejected(self):
        self.report['manifest_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'manifest digest'):self.run_download()
        self.assertEqual(len(self.calls),1)
    def test_wrong_source_run_rejected_before_download(self):
        with self.assertRaisesRegex(ValueError,'Source run'):
            self.module.download_groups(self.items,self.report,self.folder,'owner/repo','999',runner=self.runner)
        self.assertEqual(self.calls,[])

if __name__=='__main__':unittest.main()
