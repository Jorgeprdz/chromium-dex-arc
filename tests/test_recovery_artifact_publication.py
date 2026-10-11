import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('artifact',Path(__file__).resolve().parents[1]/'scripts/verify-archium-artifact.py');artifact=importlib.util.module_from_spec(spec);spec.loader.exec_module(artifact)
class ArtifactPublicationTests(unittest.TestCase):
 def metadata(self):return {'id':7,'name':'Archium-for-Android-arm64','expired':False,'size_in_bytes':123,'workflow_run':{'head_sha':'a'*40},'digest':'sha256:'+'b'*64}
 def test_expected_remote_identity_and_digest(self):self.assertEqual(artifact.validate(self.metadata(),'a'*40,'7','b'*64),123)
 def test_wrong_source_sha_rejected(self):
  with self.assertRaises(ValueError):artifact.validate(self.metadata(),'c'*40,'7','b'*64)
 def test_wrong_uploaded_digest_rejected(self):
  with self.assertRaises(ValueError):artifact.validate(self.metadata(),'a'*40,'7','c'*64)
 def test_empty_or_expired_artifact_rejected(self):
  for key,value in [('size_in_bytes',0),('expired',True),('id',8),('name','historical')]:
   with self.subTest(key=key):
    data=self.metadata();data[key]=value
    with self.assertRaises(ValueError):artifact.validate(data,'a'*40,'7','b'*64)
