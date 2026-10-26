"""Known manifest reuse is bound to immutable API metadata, never a hash-gate bypass."""
import copy,hashlib,importlib.util,json,tempfile,unittest,os,sys,types
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checker',ROOT/'scripts/check-recovery-checkpoint.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
class CertifiedManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name);self.tag='archium-checkpoint-123-1';self.sha='a'*40
        self.groups=[dict(id=1,name=self.tag+'-00',size_in_bytes=100,digest='sha256:'+'b'*64)]
        self.payload=json.dumps(dict(tag=self.tag,commit=self.sha,parts=[])).encode()
        self.receipt=dict(schema=1,source_tag=self.tag,source_sha=self.sha,artifacts=copy.deepcopy(self.groups),manifest_json=self.payload.decode(),manifest_sha256=hashlib.sha256(self.payload).hexdigest())
    def load(self):
        (self.folder/(self.tag+'.json')).write_text(json.dumps(self.receipt))
        return checker.certified_manifest(self.groups,self.tag,self.sha,self.folder)
    def test_same_immutable_artifacts_return_exact_manifest(self):
        self.assertEqual(self.load(),self.payload)
    def test_changed_artifact_id_digest_or_size_rejected(self):
        for key,value in [('id',2),('digest','sha256:'+'c'*64),('size_in_bytes',99)]:
            with self.subTest(key=key):
                original=self.groups[0][key];self.groups[0][key]=value
                with self.assertRaisesRegex(ValueError,'identity differs'):self.load()
                self.groups[0][key]=original
    def test_tampered_manifest_is_rejected(self):
        self.receipt['manifest_json']+=' '
        with self.assertRaisesRegex(ValueError,'digest differs'):self.load()
    def test_wrong_source_is_rejected(self):
        self.receipt['source_sha']='c'*40
        with self.assertRaisesRegex(ValueError,'identity differs'):self.load()
    def test_unknown_checkpoint_uses_existing_remote_path(self):
        self.assertIsNone(checker.certified_manifest(self.groups,self.tag,self.sha,self.folder))
    def test_s0_uses_current_inventory_and_receipt_without_http_range(self):
        receipt=json.loads((ROOT/'config/checkpoint-receipts/archium-checkpoint-40283988917-1.json').read_text())
        artifacts=[dict(a,expires_at='2099-01-01T00:00:00Z',expired=False,
                        workflow_run={'head_sha':receipt['source_sha']}) for a in receipt['artifacts']]
        inventory=self.folder/'inventory.json';inventory.write_text(json.dumps({'artifacts':artifacts}))
        report=self.folder/'report.json'
        argv=['checker','--artifacts',str(inventory),'--source-tag',receipt['source_tag'],
              '--source-sha',receipt['source_sha'],'--report',str(report)]
        capacity=types.SimpleNamespace(f_frsize=1,f_bavail=200_000_000_000,f_favail=3_000_000)
        with patch.object(sys,'argv',argv),patch.dict(os.environ,{'RUNNER_TEMP':'/home/runner/work/_temp'},clear=True), \
             patch.object(checker.os,'statvfs',return_value=capacity), \
             patch.object(checker,'remote_manifest',side_effect=AssertionError('Range must not be called')):
            checker.main()
        result=json.loads(report.read_text())
        self.assertEqual(result['manifest_source'],'CERTIFIED_IMMUTABLE_ARTIFACT_RECEIPT')
        self.assertEqual(result['CHECKPOINT_ALL_BYTES'],'PENDING_POST_DOWNLOAD')
        self.assertEqual(result['bounded_bytes_read'],0)
    def test_checked_in_receipt_manifest_matches_pinned_identity(self):
        receipt=json.loads((ROOT/'config/checkpoint-receipts/archium-checkpoint-40283988917-1.json').read_text())
        payload=checker.certified_manifest(receipt['artifacts'],receipt['source_tag'],receipt['source_sha'])
        manifest=json.loads(payload)
        self.assertEqual(manifest['revision'],checker.REVISION)
        self.assertEqual(len(manifest['parts']),25)

if __name__=='__main__':unittest.main()
