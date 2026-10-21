import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ContinuationTest(unittest.TestCase):
 def module(self):
  s=importlib.util.spec_from_file_location('continue_r5',ROOT/'scripts/check-r5-continuation.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_only_same_source_successfully_packed_controlled_incomplete_can_skip(self):
  m=self.module();r=dict(schema=1,outcome='BUILD_INCOMPLETE',expected_sha='a'*40,run_id='42',new_checkpoint='archium-checkpoint-42-1',new_checkpoint_commit='a'*40,exit_code=0,recoverable=True,checkpoint_verified=True,pack_verified=True)
  m.validate(r,'a'*40,'archium-checkpoint-42-1','42')
  for change in [dict(exit_code=7),dict(pack_verified=False),dict(expected_sha='b'*40),dict(outcome='BUILD_FAILED'),dict(new_checkpoint='archium-checkpoint-99-1')]:
   with self.subTest(change=change), self.assertRaises(ValueError):m.validate({**r,**change},'a'*40,'archium-checkpoint-42-1','42')
