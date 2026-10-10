"""Run the build orchestrator against disposable command fakes, inspecting actual routing."""
import json
import importlib.util
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
import json,os,pathlib,sys,time,signal
name=pathlib.Path(sys.argv[0]).name
args=sys.argv[1:]
with open(os.environ['MOCK_TRACE'],'a') as f:f.write(json.dumps([name]+args)+'\\n')
if name=='df':print('Available\\n150000000000')
elif name=='python3' and args[0].endswith('archium-checkpoint.py') and args[1]=='restore':
 time.sleep(float(os.environ.get('MOCK_RESTORE_SLEEP','0')))
 w=pathlib.Path(args[2]);s=w/'checkout/src';s.mkdir(parents=True,exist_ok=True)
 (s/'out/Archium/apks').mkdir(parents=True,exist_ok=True)
 (s/'out/Archium/args.gn').write_text(os.environ.get('MOCK_RESTORED_ARGS','restored old args\\n'))
 (s/'out/Archium/apks/ChromePublic.apk').write_bytes(b'synthetic APK fixture')
 for relative in os.environ.get('MOCK_NATIVE_TEST_PATHS','').split(':'):
  if relative:
   binary=s/relative;binary.parent.mkdir(parents=True,exist_ok=True);binary.write_bytes(b'synthetic native test artifact')
 (s/'LICENSE').write_text('fixture license')
 (s/'build').mkdir(exist_ok=True);(s/'build/install-build-deps.sh').write_text('exit 0\\n')
 (s/'build/config/android').mkdir(parents=True,exist_ok=True)
 (s/'build/config/android/config.gni').write_text('  public_android_sdk_platform_version = \"37.0\"\\n  public_android_sdk_build_tools_version = \"37.0.0\"\\n')
 android_jar=s/'third_party/android_sdk/public/platforms/android-37.0/android.jar'
 android_jar.parent.mkdir(parents=True,exist_ok=True);android_jar.write_bytes(b'synthetic android jar fixture')
 (w/'depot_tools').mkdir(exist_ok=True);(w/'depot_tools/ensure_bootstrap').write_text('exit 0\\n')
 (w/'depot_tools/python-bin').mkdir(exist_ok=True)
 python_link=w/'depot_tools/python-bin/python3'
 if not python_link.exists():python_link.symlink_to(pathlib.Path(sys.argv[0]).resolve())
elif name=='python3' and args and args[0].endswith('archium-autoninja.py'):
 os.execvp('autoninja',['autoninja']+args[2:])
elif name=='python3' and args and args[0].endswith('archium-media-preflight.py'):
 sys.exit(int(os.environ.get('MOCK_MEDIA_GATE_RESULT','0')))
elif name=='python3' and args and args[0].endswith('archium-java-preflight.py'):
 time.sleep(float(os.environ.get('MOCK_PREFLIGHT_SLEEP','0')))
 if os.environ.get('MOCK_JAVA_PREFLIGHT_RESULT','0')!='0':sys.exit(int(os.environ['MOCK_JAVA_PREFLIGHT_RESULT']))
 pathlib.Path(args[args.index('--targets-file')+1]).write_text('obj/archium-fixture.javac.jar\\n')
elif name=='python3' and args and args[0].endswith('archium-test-gates.py') and len(args)>1 and args[1]=='host':
 time.sleep(float(os.environ.get('MOCK_HOST_SLEEP','0')))
 sys.exit(int(os.environ.get('MOCK_HOST_GATE_RESULT','0')))
elif name=='python3' and args and args[0].endswith('archium-checkpoint.py') and args[1]=='pack':
 if os.environ.get('MOCK_REQUIRE_FLUSH')=='true':
  log=pathlib.Path(args[2])/'checkout/src/out/Archium/.ninja_log'
  if not log.exists() or log.read_text()!='flushed after SIGINT':sys.exit(9)
 sys.exit(int(os.environ.get('MOCK_PACK_RESULT','0')))
elif name=='python3' and args and args[0].endswith('archium-test-gates.py') and len(args)>1 and args[1]=='verify-device-runners':
 sys.exit(int(os.environ.get('MOCK_DEVICE_RUNNER_VERIFY_RESULT','0')))
elif name=='timeout':
 if './build/install-build-deps.sh' in args:
  sys.exit(int(os.environ.get('MOCK_DEPS_RESULT','0')))
 if os.environ.get('MOCK_REAL_TIMEOUT')=='true':
  os.execv('/usr/bin/timeout',['timeout']+args)
 i=0
 while args[i].startswith('--'):i+=1
 os.execvp(args[i+1],args[i+1:])
elif name=='autoninja':
 if os.environ.get('MOCK_NINJA_WAIT')=='true':
  def stopped(signum,frame):
   (pathlib.Path.cwd()/'out/Archium/.ninja_log').write_text('flushed after SIGINT')
   sys.exit(130)
  signal.signal(signal.SIGINT,stopped)
  time.sleep(10)
 is_java='obj/archium-fixture.javac.jar' in args
 sys.exit(int(os.environ.get('MOCK_JAVA_NINJA_RESULT' if is_java else 'MOCK_NINJA_RESULT','0')))
elif name=='gn' and args and args[0]=='desc' and args[-2:]==['deps','--all']:
 if os.environ.get('MOCK_MISSING_NATIVE_LINK_OWNER')=='true':sys.exit(0)
 print('//chrome/browser/payments:impl')
elif name=='sudo' and args and args[0]=='timeout':
 os.execvp('timeout',args[1:])
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
                     'ARCHIUM_VALIDATE_TARGETS', 'ARCHIUM_COMPILE_GATE_TARGETS',
                     'ARCHIUM_RUN_HOST_GATES']:
            self.env.pop(name, None)

    def run_build(self, phase=None, **env):
        return subprocess.run(['bash', str(ROOT / 'scripts/build-archium.sh')]
                              + ([phase] if phase else []),
                              env={**self.env, **env}, capture_output=True, text=True)

    def calls(self):
        return [json.loads(line) for line in self.trace.read_text().splitlines()] if self.trace.exists() else []

    def test_real_java_preflight_precedes_native_and_apk_compilation(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_password_manager_tests')
        self.assertEqual(result.returncode,0,result.stderr)
        calls=self.calls()
        resolution=next(i for i,c in enumerate(calls)
                        if c[0]=='python3' and c[1].endswith('archium-java-preflight.py'))
        ninjas=[(i,c) for i,c in enumerate(calls) if c[0]=='autoninja']
        self.assertIn('obj/archium-fixture.javac.jar',ninjas[0][1])
        self.assertLess(resolution,ninjas[0][0])
        self.assertIn('archium_password_manager_tests',ninjas[1][1])
        self.assertIn('archium_password_manager_tests',ninjas[2][1])
        self.assertIn('chrome/browser/password_manager:unit_tests',ninjas[2][1])
        self.assertIn('chrome_public_apk',ninjas[3][1])

    def test_missing_payments_owner_blocks_broad_native_link(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              MOCK_MISSING_NATIVE_LINK_OWNER='true')
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertIn('Required payments implementation missing',result.stderr)
        ninjas=[c for c in self.calls() if c[0]=='autoninja']
        self.assertEqual(len(ninjas),1)
        self.assertIn('obj/archium-fixture.javac.jar',ninjas[0])
        self.assertNotIn('complete=true',self.output.read_text())

    def test_dependency_timeout_stops_before_gn_or_compilation(self):
        result = self.run_build(ARCHIUM_SOURCE_TAG=SOURCE_TAG,
                                ARCHIUM_SOURCE_COMMIT=SOURCE_COMMIT,
                                MOCK_DEPS_RESULT='124')
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertFalse(any(c[0] in ('gn', 'autoninja') for c in self.calls()))
        self.assertEqual(self.output.read_text(), '')

    def test_global_work_deadline_saves_before_any_later_compilation(self):
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                                ARCHIUM_WORK_SECONDS='3', MOCK_REAL_TIMEOUT='true',
                                MOCK_PREFLIGHT_SLEEP='10')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), 'complete=false\n')
        self.assertTrue(any('pack' in c for c in self.calls()))
        self.assertFalse(any(c[0]=='autoninja' for c in self.calls()))

    def test_preparation_deadline_never_packs_incomplete_workspace(self):
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                                ARCHIUM_PREPARE_SECONDS='1', MOCK_REAL_TIMEOUT='true',
                                MOCK_RESTORE_SLEEP='10')
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertFalse(any('pack' in c for c in self.calls()))
        self.assertEqual(self.output.read_text(), '')

    def test_host_timeout_preserves_checkpoint_but_does_not_pass_gate(self):
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                                ARCHIUM_HOST_SECONDS='1', MOCK_REAL_TIMEOUT='true',
                                MOCK_HOST_SLEEP='10')
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertTrue(any('pack' in c for c in self.calls()))
        self.assertFalse(any(c[0]=='autoninja' and 'chrome_public_apk' in c
                             for c in self.calls()))
        self.assertEqual(self.output.read_text(), 'complete=false\n')

    def test_failed_checkpoint_upload_cannot_claim_resumable_completion(self):
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                                MOCK_NINJA_RESULT='124', MOCK_PACK_RESULT='8')
        self.assertEqual(result.returncode, 8, result.stderr)
        self.assertEqual(self.output.read_text(), '')

    def test_work_requires_this_jobs_completed_preparation(self):
        result = self.run_build('--work', ARCHIUM_PREVIOUS_TAG=CURRENT_TAG)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(self.calls(), [])

    def test_split_steps_restore_only_once_and_preserve_job_deadline(self):
        result = self.run_build('--prepare', ARCHIUM_PREVIOUS_TAG=CURRENT_TAG)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(c[0]=='autoninja' for c in self.calls()))
        result = self.run_build('--work', ARCHIUM_PREVIOUS_TAG=CURRENT_TAG)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(c[0]=='python3' and 'restore' in c for c in self.calls()), 1)
        self.assertEqual(self.output.read_text(), 'complete=true\n')

    def test_global_cut_waits_for_ninja_sigint_flush_before_packing(self):
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                                ARCHIUM_WORK_SECONDS='4', MOCK_REAL_TIMEOUT='true',
                                MOCK_NINJA_WAIT='true', MOCK_REQUIRE_FLUSH='true')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), 'complete=false\n')
        self.assertEqual((self.root/'runner/chromium-archium/checkout/src/out/Archium/.ninja_log').read_text(),
                         'flushed after SIGINT')

    def test_forced_kill_never_claims_a_quiescent_checkpoint(self):
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG, MOCK_NINJA_RESULT='137')
        self.assertEqual(result.returncode, 137, result.stderr)
        self.assertFalse(any(c[0]=='python3' and 'pack' in c for c in self.calls()))
        self.assertEqual(self.output.read_text(), '')

    def test_work_step_counts_time_spent_in_preparation(self):
        result = self.run_build('--prepare', ARCHIUM_PREVIOUS_TAG=CURRENT_TAG)
        self.assertEqual(result.returncode, 0, result.stderr)
        marker = self.root/'runner'/('archium-prepared-'+self.env.get('GITHUB_RUN_ID','local'))
        prepared = marker.read_text().splitlines()
        prepared[1] = str(int(prepared[1])-14401)
        marker.write_text('\n'.join(prepared)+'\n')
        result = self.run_build('--work', ARCHIUM_PREVIOUS_TAG=CURRENT_TAG)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), 'complete=false\n')
        self.assertFalse(any(c[0]=='autoninja' for c in self.calls()))

    def test_stage_budgets_cannot_disable_reserve_or_overflow(self):
        cases = [('ARCHIUM_WORK_SECONDS', value) for value in
                 ('0', '-1', '14401', '99999999999999999999999999999999')]
        cases.append(('ARCHIUM_SLICE_MINUTES', '121'))
        for name, value in cases:
            with self.subTest(name=name, value=value):
                result=self.run_build(**{name:value})
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.calls(), [])

    def test_media_configuration_failure_prevents_all_compilation(self):
        result = self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                                MOCK_MEDIA_GATE_RESULT='2')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(any(c[0] == 'autoninja' for c in self.calls()))
        self.assertEqual(self.output.read_text(), '')

    def test_java_compiler_failure_prevents_native_and_apk(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_password_manager_tests',
                              MOCK_JAVA_NINJA_RESULT='1')
        self.assertEqual(result.returncode,1,result.stderr)
        ninjas=[c for c in self.calls() if c[0]=='autoninja']
        self.assertEqual(len(ninjas),1)
        self.assertIn('obj/archium-fixture.javac.jar',ninjas[0])
        self.assertFalse(any('archium_password_manager_tests' in c or 'chrome_public_apk' in c for c in ninjas))
        self.assertEqual(self.output.read_text(),'complete=false\n')
        self.assertTrue(any(c[0]=='python3' and 'pack' in c for c in self.calls()))

    def test_missing_java_owner_stops_before_any_compilation(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              MOCK_JAVA_PREFLIGHT_RESULT='5')
        self.assertEqual(result.returncode,5,result.stderr)
        self.assertFalse(any(c[0]=='autoninja' for c in self.calls()))
        self.assertEqual(self.output.read_text(),'')

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
        self.assertFalse(any(c[:2]==['gn','gen'] for c in calls))

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
        ninja=[c for c in self.calls() if c[0]=='autoninja' and 'obj/archium-fixture.javac.jar' not in c]
        self.assertEqual(len(ninja),1)
        self.assertIn('archium_password_manager_tests',ninja[0])
        self.assertNotIn('chrome_public_apk',ninja[0])
        self.assertEqual(self.output.read_text(),'complete=false\n')
        calls=self.calls()
        pack_index=next(i for i,c in enumerate(calls) if c[0]=='python3' and 'pack' in c)
        compiler_index=max(i for i,c in enumerate(calls) if c[0]=='autoninja')
        self.assertGreater(pack_index,compiler_index)
        self.assertIn('mandatory gates did not pass',result.stderr)

    def test_compiler_failure_with_failed_upload_never_claims_saved_checkpoint(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_key_provider_tests',
                              MOCK_NINJA_RESULT='1', MOCK_PACK_RESULT='8')
        self.assertEqual(result.returncode,8,result.stderr)
        self.assertEqual(self.output.read_text(),'')
        self.assertIn('Work failed (exit 1)',result.stderr)
        self.assertIn('Checkpoint failed verification/upload (exit 8)',result.stderr)
        self.assertFalse(any(c[0]=='autoninja' and 'chrome_public_apk' in c
                             for c in self.calls()))

    def test_host_execution_gate_runs_after_compile_gate_and_before_apk(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_key_provider_tests archium_key_java',
                              ARCHIUM_RUN_HOST_GATES='true')
        self.assertEqual(result.returncode,0,result.stderr)
        calls=self.calls()
        ninja_indices=[i for i,c in enumerate(calls) if c[0]=='autoninja' and 'obj/archium-fixture.javac.jar' not in c]
        self.assertEqual(len(ninja_indices),3,calls)
        host_index=next(i for i,c in enumerate(calls)
                        if c[0]=='python3' and c[1].endswith('archium-test-gates.py') and c[2]=='host')
        self.assertLess(ninja_indices[0],host_index)
        self.assertLess(host_index,ninja_indices[2])
        self.assertIn('archium_password_manager_tests',calls[ninja_indices[0]])
        self.assertIn('archium_key_provider_tests',calls[ninja_indices[1]])
        self.assertIn('chrome_public_apk',calls[ninja_indices[2]])

    def test_host_execution_gate_failure_blocks_apk(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_key_provider_tests',
                              ARCHIUM_RUN_HOST_GATES='true',
                              MOCK_HOST_GATE_RESULT='7')
        self.assertEqual(result.returncode,7,result.stderr)
        calls=self.calls()
        ninja=[c for c in calls if c[0]=='autoninja' and 'obj/archium-fixture.javac.jar' not in c]
        self.assertEqual(len(ninja),2,calls)
        self.assertIn('archium_password_manager_tests',ninja[0])
        self.assertIn('archium_key_provider_tests',ninja[1])
        self.assertFalse(any('chrome_public_apk' in cmd for cmd in ninja))
        self.assertEqual(self.output.read_text(),'')

    def test_host_execution_gate_is_mandatory_and_cannot_be_disabled(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_key_provider_tests',
                              ARCHIUM_RUN_HOST_GATES='false')
        self.assertEqual(result.returncode,2,result.stderr)
        ninja=[c for c in self.calls() if c[0]=='autoninja' and 'obj/archium-fixture.javac.jar' not in c]
        self.assertEqual(len(ninja),2,self.calls())
        self.assertIn('archium_password_manager_tests',ninja[0])
        self.assertIn('archium_key_provider_tests',ninja[1])
        self.assertFalse(any('chrome_public_apk' in cmd for cmd in ninja))
        self.assertEqual(self.output.read_text(),'')

        if self.trace.exists(): self.trace.unlink()
        self.output.write_text('')
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_key_provider_tests')
        self.assertEqual(result.returncode,0,result.stderr)
        calls=self.calls()
        host=next(c for c in calls if c[0]=='python3' and c[1].endswith('archium-test-gates.py') and c[2]=='host')
        self.assertEqual(host[2],'host')
        self.assertIn('--out',host)
        script=(ROOT / 'scripts/build-archium.sh').read_text()
        self.assertIn('public_android_sdk_platform_version',script)
        self.assertIn('third_party/android_sdk/public/platforms/android-${android_sdk_version}/android.jar',script)
        self.assertNotIn('${ANDROID_HOME:-/opt/android-sdk}/platforms/android-36/android.jar',script)

    def test_slice_timeout_publishes_current_checkpoint_without_completion_claim(self):
        result=self.run_build(ARCHIUM_SOURCE_TAG=SOURCE_TAG, ARCHIUM_SOURCE_COMMIT=SOURCE_COMMIT,
                              MOCK_NINJA_RESULT='124')
        self.assertEqual(result.returncode,0,result.stderr)
        pack=next(c for c in self.calls() if c[0]=='python3' and 'pack' in c)
        self.assertNotIn('--source-commit',pack)
        self.assertEqual(self.output.read_text(),'complete=false\n')

    def test_missing_device_runner_blocks_apk(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_key_provider_tests',
                              MOCK_DEVICE_RUNNER_VERIFY_RESULT='9')
        self.assertEqual(result.returncode,9,result.stderr)
        calls=self.calls()
        self.assertTrue(any(c[0]=='autoninja' and 'archium_key_provider_tests' in c for c in calls))
        self.assertFalse(any(c[0]=='autoninja' and 'chrome_public_apk' in c for c in calls))
        self.assertEqual(self.output.read_text(),'')

    def test_native_gate_outputs_are_resolved_before_apk_compile(self):
        result=self.run_build(ARCHIUM_PREVIOUS_TAG=CURRENT_TAG,
                              ARCHIUM_COMPILE_GATE_TARGETS='archium_key_provider_tests')
        self.assertEqual(result.returncode,0,result.stderr)
        calls=self.calls()
        collect_index=next(i for i,c in enumerate(calls)
                           if c[0]=='python3' and c[1].endswith('archium-test-gates.py') and c[2]=='verify-device-runners')
        apk_index=next(i for i,c in enumerate(calls)
                       if c[0]=='autoninja' and 'chrome_public_apk' in c)
        self.assertLess(collect_index,apk_index)

    def test_build_script_does_not_assume_native_test_object_paths(self):
        script=(ROOT / 'scripts/build-archium.sh').read_text()
        self.assertNotIn('obj/chrome/browser/password_manager/android/archium_key_provider_tests', script)
        self.assertNotIn('obj/components/password_manager/core/browser/password_store/archium_login_database_tests', script)


    def test_host_gate_requires_explicit_pinned_android_jar(self):
        gate = (ROOT / 'scripts/archium-test-gates.py').read_text()
        build = (ROOT / 'scripts/build-archium.sh').read_text()
        self.assertIn("host.add_argument('--android-jar', type=Path, required=True)", gate)
        self.assertNotIn('DEFAULT_ANDROID_JAR', gate)
        self.assertIn("--android-jar", build)
        self.assertIn('public_android_sdk_platform_version', build)

    def test_android_device_gate_uses_pinned_chromium_sdk_not_hardcoded_runner_sdk(self):
        gate = (ROOT / 'scripts/archium-test-gates.py').read_text()
        key = (ROOT / 'scripts/test-android-password-key.py').read_text()
        window = (ROOT / 'scripts/test-android-window-policy.py').read_text()
        self.assertIn('public_android_sdk_platform_version', gate)
        self.assertIn('public_android_sdk_build_tools_version', gate)
        self.assertIn("third_party' / 'android_sdk' / 'public", gate)
        self.assertIn("platform_dir_name = platform_version", gate)
        self.assertNotIn("platform_version.split('.', 1)[0]", gate)
        for source in (gate, key, window):
            self.assertNotIn('/opt/android-sdk', source)
            self.assertNotIn('android-36/android.jar', source)
            self.assertNotIn('build-tools/36.0.0', source)
        self.assertIn("--platform-version", gate)
        self.assertIn("--build-tools-version", gate)

    def test_pinned_sdk_resolver_preserves_full_chromium_platform_version(self):
        spec = importlib.util.spec_from_file_location(
            'archium_test_gates', ROOT / 'scripts/archium-test-gates.py')
        gates = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(gates)
        checkout = self.root / 'sdk-checkout'
        out_dir = checkout / 'out' / 'Archium'
        out_dir.mkdir(parents=True)
        config = checkout / 'build/config/android/config.gni'
        config.parent.mkdir(parents=True)
        config.write_text(
            'public_android_sdk_platform_version = "37.0"\n'
            'public_android_sdk_build_tools_version = "37.0.0"\n')
        sdk = checkout / 'third_party/android_sdk/public'
        android_jar = sdk / 'platforms/android-37.0/android.jar'
        android_jar.parent.mkdir(parents=True)
        android_jar.write_bytes(b'fixture')
        tools = sdk / 'build-tools/37.0.0'
        tools.mkdir(parents=True)
        for tool in ('aapt2', 'd8', 'apksigner'):
            (tools / tool).write_bytes(b'fixture')
        sdk_root, platform, build_tools, resolved_jar = gates.resolve_pinned_android_sdk(out_dir)
        self.assertEqual(sdk_root, sdk)
        self.assertEqual(platform, '37.0')
        self.assertEqual(build_tools, '37.0.0')
        self.assertEqual(resolved_jar, android_jar)

    def test_gate_orchestrator_separates_host_device_and_post_build_execution(self):
        gates=(ROOT / 'scripts/archium-test-gates.py').read_text()
        for label in (
                '//chrome/browser/password_manager/android:archium_key_provider_tests',
                '//components/password_manager/core/browser/password_store:archium_login_database_tests',
                '//components/password_manager/core/browser/import:archium_password_import_tests',
                '//chrome/browser/password_manager/android:archium_password_manager_tests'):
            self.assertIn(label,gates)
        self.assertIn("f'run_{target_name}'",gates)
        self.assertIn('verify_device_runners',gates)
        self.assertIn("'adb', '-s', serial",gates)
        self.assertIn("'--device', serial",gates)
        self.assertIn("'-f', 'Archium*'",gates)
        self.assertIn("sub.add_parser('post-build')",gates)
        self.assertIn("'android.intent.action.MAIN'",gates)
        self.assertIn("'android.intent.category.LAUNCHER'",gates)
        self.assertIn("'-p', package",gates)
        self.assertIn('run_chrome_junit_tests',gates)
        self.assertIn('VerticalTabListCoordinatorUnitTest.*',gates)
        self.assertNotIn('run_chrome_junit_tests_org.chromium.chrome.browser.tasks',gates)
        self.assertNotIn('out/Archium/obj/chrome/browser/password_manager/android',gates)

    def test_workflow_exposes_source_identity_only_to_first_stage(self):
        workflow=(ROOT / '.github/workflows/baseline-build.yml').read_text()
        first=workflow[workflow.index('  stage1:'):workflow.index('  stage2:')]
        self.assertIn('inputs.source_checkpoint',first)
        self.assertIn('inputs.source_commit',first)
        continuation=workflow[workflow.index('  stage2:'):]
        self.assertNotIn('inputs.source_commit',continuation)
        stage=(ROOT / '.github/workflows/archium-stage.yml').read_text()
        self.assertIn('ARCHIUM_SOURCE_COMMIT:',stage)
        self.assertIn('ARCHIUM_COMPILE_GATE_TARGETS:',stage)
        self.assertIn('ARCHIUM_RUN_HOST_GATES:',stage)
        self.assertIn('chrome_junit_tests',stage)
        self.assertNotIn('chrome_junit_tests_org.chromium.chrome.browser.tasks',stage)
        self.assertNotIn('validate_native:',stage)
        baseline=(ROOT / '.github/workflows/baseline-build.yml').read_text()
        self.assertNotIn('validate_native:',baseline)


if __name__=='__main__':unittest.main()
