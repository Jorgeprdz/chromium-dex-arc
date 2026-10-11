"""Execute new runner's early gates; no Chromium or native build is simulated as PASS."""
import os, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RecoveryDispatchTests(unittest.TestCase):
 def invoke(self, **changes):
  with tempfile.TemporaryDirectory() as d:
   env={**os.environ,'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Jorgeprdz/chromium-dex-arc',
        'GITHUB_REF_NAME':'assistant/archium-r4-recovery','GITHUB_SHA':'a'*40,
        'ARCHIUM_EXPECTED_SHA':'a'*40,'RUNNER_TEMP':d,'GITHUB_WORKSPACE':str(ROOT),
        'ARCHIUM_SOURCE_TAG':'archium-checkpoint-38165289963-1',
        'ARCHIUM_SOURCE_COMMIT':'dcbd868ea42ffd0991c01c2872adce01316a9768'}
   env.update(changes)
   return subprocess.run(['bash',str(ROOT/'scripts/build-archium-recovery.sh'),'--prepare'],
                         env=env,capture_output=True,text=True)
 def test_protected_branch_rejected_before_restore(self):
  r=self.invoke(GITHUB_REF_NAME='feat/arc-desktop')
  self.assertEqual(r.returncode,2,r.stderr);self.assertIn('branch',r.stderr)
 def test_unpinned_dispatch_rejected_before_restore(self):
  r=self.invoke(ARCHIUM_EXPECTED_SHA='b'*40)
  self.assertEqual(r.returncode,2,r.stderr);self.assertIn('SHA',r.stderr)
 def test_missing_checkpoint_never_allows_clean_fallback(self):
  r=self.invoke(ARCHIUM_SOURCE_TAG='',ARCHIUM_SOURCE_COMMIT='')
  self.assertEqual(r.returncode,2,r.stderr);self.assertIn('checkpoint',r.stderr)
 def test_unbounded_native_slices_rejected_before_restore(self):
  r=self.invoke(ARCHIUM_MAX_SLICES='3')
  self.assertEqual(r.returncode,2,r.stderr);self.assertIn('budget',r.stderr)

class RecoveryArtifactBackendTests(unittest.TestCase):
 def test_native_stage_selects_actions_backend_for_restore_and_pack(self):
  stage=(ROOT/'.github/workflows/archium-recovery-stage.yml').read_text()
  self.assertIn("ARCHIUM_CHECKPOINT_STORAGE: artifact",stage)
  self.assertIn("ARCHIUM_SOURCE_RUN_ID: ${{ inputs.source_run_id }}",stage)


class RecoveryActionsCheckpointCliTests(unittest.TestCase):
 def test_workflow_env_drives_real_restore_then_pack_without_release_fallback(self):
  import importlib.util, json, re
  spec=importlib.util.spec_from_file_location('tiny_restore',ROOT/'tests/test_archium_checkpoint_restore_disk.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  stage=(ROOT/'.github/workflows/archium-recovery-stage.yml').read_text()
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);workspace,folder=module.CheckpointDiskRecoveryTests().make_artifact(base)
   bin=base/'bin';bin.mkdir();gh=bin/'gh';gh.write_text('#!/bin/sh\necho RELEASE_FALLBACK_REJECTED >&2\nexit 71\n');gh.chmod(0o755)
   env={**os.environ,'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Jorgeprdz/chromium-dex-arc',
    'GITHUB_SHA':'b'*40,'ARCHIUM_CHECKPOINT_DIR':str(folder),'PATH':str(bin)+':'+os.environ['PATH']}
   if 'ARCHIUM_CHECKPOINT_STORAGE: artifact' in stage:env['ARCHIUM_CHECKPOINT_STORAGE']='artifact'
   if 'ARCHIUM_SOURCE_RUN_ID: ${{ inputs.source_run_id }}' in stage:env['ARCHIUM_SOURCE_RUN_ID']='38018166249'
   command=['python3',str(ROOT/'scripts/archium-checkpoint.py'),'restore',str(workspace),module.TAG,'--source-commit',module.SOURCE_COMMIT]
   r=subprocess.run(command,env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertIn('ACTIONS_CHECKPOINT_RESTORE=PASS',r.stdout)
   self.assertEqual((workspace/'checkout/src/payload.txt').read_text(),'incremental-output-preserved')
   r=subprocess.run(['python3',str(ROOT/'scripts/archium-checkpoint.py'),'pack',str(workspace),'archium-checkpoint-456-1'],env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertIn('ACTIONS_CHECKPOINT_STAGED=PASS',r.stdout)
   manifest=json.loads((folder/'group-00/checkpoint.json').read_text())
   self.assertEqual(manifest['commit'],'b'*40)
