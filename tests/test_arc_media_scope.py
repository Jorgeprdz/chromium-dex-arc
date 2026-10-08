"""Exercise scope-specific gates without treating omitted vault tests as passed."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load_gates():
    spec=importlib.util.spec_from_file_location('scope_gates',ROOT/'scripts/archium-test-gates.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArcMediaScopeTests(unittest.TestCase):
    def test_arc_scope_requires_real_robolectric_runner_presence(self):
        gates=load_gates()
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'out/Archium';out.mkdir(parents=True)
            with self.assertRaisesRegex(SystemExit,'Robolectric runner'):
                gates.verify_device_runners(out,'arc-media')
            runner=out/'bin/run_chrome_junit_tests';runner.parent.mkdir()
            runner.write_text('runner presence fixture, never executed')
            gates.verify_device_runners(out,'arc-media')
            self.assertEqual(gates.native_test_targets('arc-media'),())

    def test_full_scope_still_requires_native_password_runners(self):
        gates=load_gates()
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(SystemExit,'archium_key_provider_tests'):
                gates.verify_device_runners(Path(temp),'full')
        self.assertEqual(len(gates.native_test_targets('full')),4)
        with self.assertRaises(ValueError): gates.native_test_targets('unknown')

    def test_alternate_workflow_and_configuration_have_explicit_scope(self):
        args=(ROOT/'config/archium-args.gn').read_text()
        self.assertIn('enable_archium_local_passwords = false',args)
        self.assertIn('proprietary_codecs = true',args)
        self.assertIn('ffmpeg_branding = "Chrome"',args)
        stage=(ROOT/'.github/workflows/archium-stage.yml').read_text()
        self.assertIn("ARCHIUM_BUILD_SCOPE: 'arc-media'",stage)
        self.assertIn("ARCHIUM_COMPILE_GATE_TARGETS: 'chrome_junit_tests'",stage)
        self.assertIn("ARCHIUM_RUN_HOST_GATES: 'true'",stage)
        baseline=(ROOT/'.github/workflows/baseline-build.yml').read_text()
        self.assertIn('group: archium-build-staged-${{ github.ref }}',baseline)
        self.assertIn('cancel-in-progress: false',baseline)


if __name__=='__main__':unittest.main()
