"""Execute recovery phase routing with disposable CI/native boundaries.
Routing PASS never accredits Chromium, JNI, resources or APK contents.
The assertion leak case executes genuine java and javac between those boundaries.
"""
import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PIN = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'
DEPOT = '8a5434051036b32412a2ecb10c213a72e3f3ccb9'
DRIVER = r'''#!/usr/bin/python3
import json, os, pathlib, sys, subprocess
name=pathlib.Path(sys.argv[0]).name;args=sys.argv[1:]
with open(os.environ['TRACE'],'a') as f:f.write(json.dumps([name]+args)+'\n')
if name=='git' and 'rev-parse' in args:
 print(os.environ.get('BAD_DEPOT',os.environ['DEPOT']) if 'depot_tools' in ' '.join(args) else os.environ.get('BAD_PIN',os.environ['PIN']))
elif name=='python3' and args and args[0].endswith('archium-checkpoint.py'):
 if args[1]=='pack':sys.exit(int(os.environ.get('PACK_EXIT','0')))
 if os.environ.get('RESTORE_EXIT'):sys.exit(int(os.environ['RESTORE_EXIT']))
 w=pathlib.Path(args[2]);s=w/'checkout/src';(s/'out/Archium/apks').mkdir(parents=True)
 (s/'out/Archium/apks/ChromePublic.apk').write_bytes(b'synthetic routing artifact, not APK')
 (s/'out/Archium/args.gn').write_text('previous GN args')
 (s/'LICENSE').write_text('synthetic routing license')
 (s/'build').mkdir();(s/'build/install-build-deps.sh').write_text('#!/bin/sh\nexit 0\n');(s/'build/install-build-deps.sh').chmod(0o755)
 config=s/'build/config/android/config.gni';config.parent.mkdir(parents=True);config.write_text('public_android_sdk_platform_version = "37.0"\npublic_android_sdk_build_tools_version = "37.0.0"\n')
 depot=w/'depot_tools';(depot/'python-bin').mkdir(parents=True);(depot/'ensure_bootstrap').write_text('exit 0\n');(depot/'python-bin/python3').symlink_to(pathlib.Path(sys.argv[0]).resolve())
 runner=s/'out/Archium/bin/run_chrome_junit_tests';runner.parent.mkdir(parents=True);runner.symlink_to(pathlib.Path(sys.argv[0]).resolve())
 tools=s/'third_party/android_sdk/public/build-tools/37.0.0';tools.mkdir(parents=True)
 for tool in ('aapt2','apksigner'):(tools/tool).symlink_to(pathlib.Path(sys.argv[0]).resolve())
 nm=s/'third_party/llvm-build/Release+Asserts/bin/llvm-nm';nm.parent.mkdir(parents=True);nm.symlink_to(pathlib.Path(sys.argv[0]).resolve())
 lib=s/'out/Archium/lib.unstripped/libarchium_password_manager_tests__library.so';lib.parent.mkdir(parents=True);lib.write_bytes(b'synthetic symbol presence')
elif name=='python3' and args and args[0].endswith('archium-autoninja.py'):
 targets=args[2:]
 if 'chrome_junit_tests' in targets and os.environ.get('JAVA_EXIT'):sys.exit(int(os.environ['JAVA_EXIT']))
 if os.environ.get('FAIL_TARGET') in targets:sys.exit(int(os.environ.get('FAIL_EXIT','9')))
 if os.environ.get('REAL_JVM') and 'archium_password_manager_tests' in targets:
  source=pathlib.Path(os.environ['PROBE'])
  r=subprocess.run(['/usr/bin/javac','-d',str(source.parent),str(source)],capture_output=True,text=True)
  if r.returncode or r.stderr:print('JAVAC_STDERR='+r.stderr,file=sys.stderr);sys.exit(83)
elif name=='python3' and args and args[0].endswith('archium-java-preflight.py'):
 pathlib.Path(args[args.index('--targets-file')+1]).write_text('obj/recovery-fixture.javac.jar\n')
elif name=='python3' and args and args[0].endswith('archium-test-gates.py'):
 if args[1]=='host':sys.exit(int(os.environ.get('HOST_EXIT','0')))
 if args[1]=='verify-device-runners':sys.exit(int(os.environ.get('DEVICE_RUNNER_EXIT','0')))
elif name=='python3' and args and args[0].endswith('check-portal-chromium-resources.py'):sys.exit(int(os.environ.get('RESOURCE_EXIT','0')))
elif name=='python3' and args and args[0].endswith('archium-media-preflight.py'):sys.exit(int(os.environ.get('MEDIA_EXIT','0')))
elif name=='python3' and args and args[0].endswith('transition-archium-patches.py'):sys.exit(int(os.environ.get('TRANSITION_EXIT','0')))
elif name=='python3' and args and args[0]=='-':os.execv('/usr/bin/python3',['python3']+args)
elif name=='sudo':
 i=next((i for i,a in enumerate(args) if not a.startswith('--')),len(args));os.execvp(args[i],args[i:])
elif name=='gn':
 if 'check' in args:sys.exit(int(os.environ.get('GN_CHECK_EXIT','0')))
 if 'desc' in args:print('//chrome/browser/payments:impl' if not os.environ.get('MISSING_PAYMENTS') else '//base')
elif name=='llvm-nm':
 if os.environ.get('UNDEFINED_JNI'):print(' U ServiceWorkerPaymentAppBridge::GetInstance()')
elif name=='run_chrome_junit_tests':
 if os.environ.get('ROBO_EXIT'):sys.exit(int(os.environ['ROBO_EXIT']))
 if os.environ.get('REAL_JVM'):
  r=subprocess.run(['/usr/bin/java','-cp',str(pathlib.Path(os.environ['PROBE']).parent),'Probe','assertions'],capture_output=True,text=True)
  if r.returncode:print(r.stderr,file=sys.stderr)
  sys.exit(r.returncode)
elif name=='aapt2':print("package: name='app.archium.android'\nnative-code: 'arm64-v8a'")
elif name=='apksigner':sys.exit(int(os.environ.get('SIGN_EXIT','0')))
elif name=='zipinfo':print('lib/arm64-v8a/libchrome.so')
'''
class RecoveryBuildRoutingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.bin=self.root/'bin';self.bin.mkdir();self.repo=self.root/'repo';self.repo.mkdir()
  shutil.copytree(ROOT/'config',self.repo/'config');self.trace=self.root/'trace';self.output=self.root/'output';self.output.touch()
  driver=self.bin/'driver';driver.write_text(DRIVER);driver.chmod(0o755)
  for name in ('git','python3','sudo','gn','df','ninja','zipinfo'):(self.bin/name).symlink_to(driver)
  self.env={**os.environ,'PATH':str(self.bin)+':'+os.environ['PATH'],'TRACE':str(self.trace),'PIN':PIN,'DEPOT':DEPOT,
   'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'Jorgeprdz/chromium-dex-arc','GITHUB_SHA':'b'*40,
   'GITHUB_REF_NAME':'assistant/archium-r4-recovery','ARCHIUM_EXPECTED_SHA':'b'*40,
   'RUNNER_TEMP':str(self.root/'runner'),'GITHUB_WORKSPACE':str(self.repo),'GITHUB_OUTPUT':str(self.output),
   'ARCHIUM_SOURCE_TAG':'archium-checkpoint-123-1','ARCHIUM_SOURCE_COMMIT':'a'*40,
   'ARCHIUM_CHECKPOINT_TAG':'archium-checkpoint-456-1','ARCHIUM_CHECKPOINT_DIR':str(self.root/'checkpoint'),
   'ARCHIUM_HOST_PYTHON':str(self.bin/'python3')}
  (self.root/'runner').mkdir();(self.root/'checkpoint').mkdir()
  self.env.pop('JAVA_TOOL_OPTIONS',None)
 def build(self,phase='--all',**env):
  return subprocess.run(['bash',str(getattr(self,'script',ROOT/'scripts/build-archium-recovery.sh')),phase],env={**self.env,**env},capture_output=True,text=True,timeout=60)
 def calls(self):return [json.loads(x) for x in self.trace.read_text().splitlines()] if self.trace.exists() else []
 def targets(self):return [c for c in self.calls() if len(c)>1 and c[1].endswith('archium-autoninja.py')]
 def assert_blocked(self,r,code):
  self.assertEqual(r.returncode,code,r.stdout+r.stderr)
  self.assertFalse(any('chrome_public_apk' in c for c in self.targets()),self.calls())
  self.assertNotIn('complete=true',self.output.read_text())
 def test_complete_routing_restores_once_and_reports_only_after_all_gates(self):
  r=self.build();self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertEqual(sum('restore' in c for c in self.calls()),1)
  self.assertIn('complete=true',self.output.read_text());self.assertIn('chrome_public_apk',self.targets()[-1])
 def test_split_steps_restore_only_once(self):
  r=self.build('--prepare');self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(self.targets(),[])
  r=self.build('--work');self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(sum('restore' in c for c in self.calls()),1)
 def test_work_requires_same_job_restore_receipt(self):self.assert_blocked(self.build('--work'),2)
 def test_restore_failure_never_packs_partial_tree(self):
  self.assert_blocked(self.build(RESTORE_EXIT='7'),7);self.assertFalse(any('pack' in c for c in self.calls()))
 def test_wrong_chromium_pin_blocks_transition(self):self.assert_blocked(self.build(BAD_PIN='c'*40),2)
 def test_wrong_depot_pin_blocks_transition(self):self.assert_blocked(self.build(BAD_DEPOT='c'*40),2)
 def test_failed_transition_blocks_gn_and_native(self):self.assert_blocked(self.build(TRANSITION_EXIT='8'),8)
 def test_media_failure_blocks_all_native_actions(self):
  self.assert_blocked(self.build(MEDIA_EXIT='11'),11);self.assertEqual(self.targets(),[])
 def test_gn_check_failure_blocks_native_actions(self):self.assert_blocked(self.build(GN_CHECK_EXIT='12'),12)
 def test_missing_payments_owner_blocks_link(self):self.assert_blocked(self.build(MISSING_PAYMENTS='1'),2)
 def test_real_resource_gate_failure_blocks_java_and_link(self):self.assert_blocked(self.build(RESOURCE_EXIT='13'),13)
 def test_java_action_failure_blocks_robolectric_and_link(self):self.assert_blocked(self.build(FAIL_TARGET='obj/recovery-fixture.javac.jar',FAIL_EXIT='14'),14)
 def test_junit_compile_failure_blocks_runtime_and_link(self):self.assert_blocked(self.build(JAVA_EXIT='15'),15)
 def test_robolectric_failure_blocks_native_link(self):self.assert_blocked(self.build(ROBO_EXIT='16'),16)
 def test_targeted_link_failure_blocks_remaining_fanout(self):self.assert_blocked(self.build(FAIL_TARGET='archium_password_manager_tests',FAIL_EXIT='17'),17)
 def test_unresolved_payment_symbols_block_later_targets(self):self.assert_blocked(self.build(UNDEFINED_JNI='1'),2)
 def test_remaining_native_failure_blocks_apk(self):self.assert_blocked(self.build(FAIL_TARGET='archium_key_provider_tests',FAIL_EXIT='18'),18)
 def test_missing_device_launcher_blocks_apk(self):self.assert_blocked(self.build(DEVICE_RUNNER_EXIT='19'),19)
 def test_complete_host_failure_blocks_apk(self):self.assert_blocked(self.build(HOST_EXIT='20'),20)
 def test_failed_signature_blocks_publication(self):
  r=self.build(SIGN_EXIT='21');self.assertEqual(r.returncode,21,r.stdout+r.stderr);self.assertNotIn('complete=true',self.output.read_text())
 def test_first_failure_survives_failed_checkpoint_pack(self):self.assert_blocked(self.build(MEDIA_EXIT='22',PACK_EXIT='23'),22)
 def test_forced_kill_never_claims_quiescent_pack(self):
  self.assert_blocked(self.build(FAIL_TARGET='archium_password_manager_tests',FAIL_EXIT='137'),137);self.assertFalse(any('pack' in c for c in self.calls()))
 def test_real_jvm_assertions_do_not_leak_into_following_javac(self):
  probe=self.root/'Probe.java';probe.write_text('public class Probe {public static void main(String[] args){if(!Probe.class.desiredAssertionStatus())throw new AssertionError("-ea required");}}')
  r=subprocess.run(['/usr/bin/javac','-d',str(self.root),str(probe)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  self.assertEqual(self.build(REAL_JVM='1',PROBE=str(probe)).returncode,0,'Scoped -ea must run real JVM and preserve empty compiler stderr')

 def test_global_assertion_export_mutant_fails_real_following_javac(self):
  probe=self.root/'Probe.java';probe.write_text('public class Probe {public static void main(String[] args){if(!Probe.class.desiredAssertionStatus())throw new AssertionError("-ea required");}}')
  r=subprocess.run(['/usr/bin/javac','-d',str(self.root),str(probe)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  script=ROOT/'scripts/build-archium-recovery.sh'
  self.script=self.root/'mutant-build.sh'
  source=script.read_text().replace('for suite in '+chr(92), 'export JAVA_TOOL_OPTIONS=" -ea"\nfor suite in '+chr(92),1)
  self.assertNotEqual(source,script.read_text(),'Mutation must inject the historical global leak')
  self.script.write_text(source)
  r=self.build(REAL_JVM='1',PROBE=str(probe))
  self.assertEqual(r.returncode,83,r.stdout+r.stderr);self.assertIn('Picked up JAVA_TOOL_OPTIONS',r.stderr)

 def test_host_timeout_never_packs_without_proven_quiescence(self):
  r=self.build(HOST_EXIT='124')
  self.assert_blocked(r,124)
  self.assertFalse(any('pack' in c for c in self.calls()),'TERM host timeout cannot prove all descendants stopped')
