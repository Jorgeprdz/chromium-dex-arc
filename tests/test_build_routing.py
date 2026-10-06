"""Run the build orchestrator against disposable command fakes, inspecting actual routing."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = 'a' * 40
CURRENT_COMMIT = 'b' * 40
SOURCE_TAG = 'archium-checkpoint-123-7'
CURRENT_TAG = 'archium-checkpoint-456-1'


class BuildRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / 'bin'; self.bin.mkdir()
        self.repo = self.root / 'repo'; self.repo.mkdir()
        shutil.copytree(ROOT / 'config', self.repo / 'config')
        self.trace = self.root / 'trace.jsonl'
        self.output = self.root / 'output'
        self.output.touch()
        driver = self.bin / 'driver'
        driver.write_text('''#!/usr/bin/python3
import json,os,pathlib,sys
name=pathlib.Path(sys.argv[0]).name
args=sys.argv[1:]
with open(os.environ['MOCK_TRACE'],'a') as f:f.write(json.dumps([name]+args)+'\\n')
if name=='df':print('Available\\n150000000000')
elif name=='python3' and args[0].endswith('archium-checkpoint.py') and args[1]=='restore':
 w=pathlib.Path(args[2]);s=w/'checkout/src';s.mkdir(parents=True)
 (s/'out/Archium/apks').mkdir(parents=True)
 (s/'out/Archium/args.gn').write_text(os.environ.get('MOCK_RESTORED_ARGS','restored old args\\n'))
 (s/'out/Archium/apks/ChromePublic.apk').write_bytes(b'synthetic APK fixture')
 for relative in os.environ.get('MOCK_NATIVE_TEST_PATHS','').split(':'):
  if relative:
   binary=s/relative;binary.parent.mkdir(parents=True,exist_ok=True);binary.write_bytes(b'synthetic native test artifact')
 (s/'LICENSE').write_text('fixture license')
 (s/'build').mkdir();(s/'build/install-build-deps.sh').write_text('exit 0\\n')
 (w/'depot_tools').mkdir();(w/'depot_tools/ensure_bootstrap').write_text('exit 0\\n')
elif name=='timeout':
 i=0
 while args[i].startswith('--'):i+=1
 os.execvp(args[i+1],args[i+1:])
elif name=='autoninja':sys.exit(int(os.environ.get('MOCK_NINJA_RESULT','0')))
''')
        driver.chmod(0o755)
        for name in ['sudo', 'df', 'git', 'python3', 'gn', 'timeout', 'autoninja']:
            (self.bin / name).symlink_to(driver)
        self.env = {**os.environ, 'PATH': str(self.bin) + ':' + os.environ['PATH'],
                    'MOCK_TRACE': str(self.trace), 'GITHUB_ACTIONS': 'true',
                    'GITHUB_REPOSITORY': 'Jorgeprdz/chromium-dex-arc',
                    'GITHUB_SHA': CURRENT_COMMIT, 'RUNNER_TEMP': str(self.root / 'runner'),
                    'GITHUB_WORKSPACE': str(self.repo), 'GITHUB_OUTPUT': str(self.output),
                    'ARCHIUM_CHECKPOINT_TAG': 'archium-checkpoint-456-2'}
        for name in ['ARCHIUM_SOURCE_TAG', 'ARCHIUM_SOURCE_COMMIT', 'ARCHIUM_PREVIOUS_TAG',
                     'ARCHIUM_VALIDATE_TARGETS']:
            self.env.pop(name, None)

    def run_build(self, **env):
        return subprocess.run(['bash', str(ROOT / 'scripts/build-archium.sh')],
                              env={**self.env, **env}, capture_output=True, text=True)

    def calls(self):
        return [json.loads(line) for line in self.trace.read_text().splitlines()] if self.trace.exists() else []

    def test_first_stage_restores_declared_old_commit_transitions_and_regenerates_gn(self):
        result = self.run_build(ARCHIUM_SOURCE_TAG=SOURCE_TAG, ARCHIUM_SOURCE_COMMIT=SOURCE_COMMIT)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        restore = next(c for c in calls if c[0]=='python3' and c[1].endswith('archium-checkpoint.py'))
        self.assertIn('--source-commit', restore)
        self.assertEqual(restore[restore.index('--source-commit')+1], SOURCE_COMMIT)
        change = next(c for c in calls if c[0]=='python3' and c[1].endswith('transition-archium-patches.py'))
        self.assertIn(SOURCE_COMMIT, change); self.assertIn(CURRENT_COMMIT, change)
        gn = next(c for c in calls if c[:2]==['gn','gen'])
        ninja = next(c for c in calls if c[0]=='autoninja')
        self.assertLess(calls.index(change),calls.index(gn))
        self.assertLess(calls.index(gn),calls.index(ninja))
        self.assertEqual(self.output.read_text(),'complete=true\n')

    def test_continuation_preserves_strict_current_identity_and_does_not_transition(self):
        args = (self.repo / 'config/archium-args.gn').read_text()
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG, MOCK_RESTORED_ARGS=args)
        self.assertEqual(result.returncode,0,result.stderr)
        calls=self.calls()
        self.assertFalse(any('transition-archium-patches.py' in c[1] for c in calls if c[0]=='python3'))
        restore=next(c for c in calls if c[0]=='python3')
        self.assertNotIn('--source-commit',restore)
        self.assertFalse(any(c[0]=='gn' for c in calls))

    def test_changed_args_force_gn_even_for_current_checkpoint(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(any(c[:2]==['gn','gen'] for c in self.calls()))

    def test_incomplete_or_ambiguous_source_identity_rejected_before_any_commands(self):
        cases=[{'ARCHIUM_SOURCE_TAG':SOURCE_TAG}, {'ARCHIUM_SOURCE_COMMIT':SOURCE_COMMIT},
               {'ARCHIUM_SOURCE_TAG':SOURCE_TAG,'ARCHIUM_SOURCE_COMMIT':'wrong'},
               {'ARCHIUM_SOURCE_TAG':SOURCE_TAG,'ARCHIUM_SOURCE_COMMIT':SOURCE_COMMIT,
                'ARCHIUM_PREVIOUS_TAG':CURRENT_TAG}]
        for env in cases:
            with self.subTest(env=env):
                if self.trace.exists():self.trace.unlink()
                result=self.run_build(**env)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(self.calls(),[])
                self.assertEqual(self.output.read_text(),'')

    def test_validation_compiles_before_apk_and_compiler_failure_stops_chain(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_VALIDATE_TARGETS='archium_key_provider_tests archium_key_java',
                              MOCK_NINJA_RESULT='1')
        self.assertEqual(result.returncode,1,result.stderr)
        ninja=[c for c in self.calls() if c[0]=='autoninja']
        self.assertEqual(len(ninja),1)
        self.assertIn('archium_key_provider_tests',ninja[0]);self.assertIn('archium_key_java',ninja[0])
        self.assertNotIn('chrome_public_apk',ninja[0])
        self.assertEqual(self.output.read_text(),'')
        self.assertFalse(any('pack' in c for c in self.calls()))

    def test_slice_timeout_publishes_current_checkpoint_without_completion_claim(self):
        result=self.run_build(ARCHIUM_SOURCE_TAG=SOURCE_TAG, ARCHIUM_SOURCE_COMMIT=SOURCE_COMMIT,
                              MOCK_NINJA_RESULT='124')
        self.assertEqual(result.returncode,0,result.stderr)
        pack=next(c for c in self.calls() if c[0]=='python3' and 'pack' in c)
        self.assertNotIn('--source-commit',pack)
        self.assertEqual(self.output.read_text(),'complete=false\n')

    def test_all_native_test_executables_are_kept_in_artifact(self):
        binaries = [
            'out/Archium/obj/chrome/browser/password_manager/android/archium_key_provider_tests/archium_key_provider_tests',
            'out/Archium/obj/components/password_manager/core/browser/password_store/archium_login_database_tests/archium_login_database_tests',
            'out/Archium/obj/components/password_manager/core/browser/import/archium_password_import_tests/archium_password_import_tests',
        ]
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                                MOCK_NATIVE_TEST_PATHS=':'.join(binaries))
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in binaries:
            kept = self.repo / 'archium-output/native-tests' / Path(path).name
            self.assertTrue(kept.is_file(), str(kept))
            self.assertEqual(kept.read_bytes(), b'synthetic native test artifact')

    def test_workflow_exposes_source_identity_only_to_first_stage(self):
        workflow=(ROOT / '.github/workflows/baseline-build.yml').read_text()
        first=workflow[workflow.index('  stage1:'):workflow.index('  stage2:')]
        self.assertIn('inputs.source_checkpoint',first)
        self.assertIn('inputs.source_commit',first)
        continuation=workflow[workflow.index('  stage2:'):]
        self.assertNotIn('inputs.source_commit',continuation)
        stage=(ROOT / '.github/workflows/archium-stage.yml').read_text()
        self.assertIn('ARCHIUM_SOURCE_COMMIT:',stage)
        self.assertIn('ARCHIUM_VALIDATE_TARGETS:',stage)


if __name__=='__main__':unittest.main()
