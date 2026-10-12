"""GN optimizer argument contract; actual Chromium optimization is a CI gate."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('portal_resources', ROOT / 'scripts/check-portal-chromium-resources.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class PortalOptimizerProbeTests(unittest.TestCase):
    def action(self):
        # Argument layout from internal_rules.gni at the Chromium pin.
        return {'script': '//build/android/gyp/optimize_resources.py', 'args': [
            '--aapt2-path', '../../third_party/android_sdk/aapt2',
            '--r-text-in', 'gen/real-apk_R.txt',
            '--input-path', 'gen/real-apk.shrunk.proto.ap_',
            '--optimized-output-path', 'gen/real-apk.optimized.ap_',
            '--resources-config-paths=[ "../../chrome/android/aapt2.config" ]',
            '--resources-path-map-out-path', 'gen/real-apk-path-map.txt']}

    def test_probe_keeps_real_configs_rtxt_and_never_overwrites_native_outputs(self):
        action = self.action()
        before = list(action['args'])
        args = gate.optimization_args(action, Path('/out/raw.ap_'), Path('/sdk/aapt2'), Path('/probe'))
        self.assertEqual(action['args'], before)
        self.assertEqual(args[args.index('--r-text-in') + 1], 'gen/real-apk_R.txt')
        self.assertIn('--resources-config-paths=[ "../../chrome/android/aapt2.config" ]', args)
        self.assertEqual(args[args.index('--input-path') + 1], '/out/raw.ap_')
        self.assertEqual(args[args.index('--optimized-output-path') + 1], '/probe/portal-optimized.ap_')
        self.assertEqual(args[args.index('--resources-path-map-out-path') + 1], '/probe/portal-path-map.txt')
        self.assertEqual(args[args.index('--aapt2-path') + 1], '/sdk/aapt2')

    def test_missing_real_config_never_falls_back_to_unoptimized_pass(self):
        action = self.action()
        action['args'] = [a for a in action['args'] if not a.startswith('--resources-config-paths')]
        with self.assertRaisesRegex(ValueError, 'Incomplete real Chromium'):
            gate.optimization_args(action, Path('/out/raw.ap_'), Path('/sdk/aapt2'), Path('/probe'))

    def test_duplicate_output_is_rejected(self):
        action = self.action()
        action['args'].append('--optimized-output-path=gen/native.ap_')
        with self.assertRaisesRegex(ValueError, 'Duplicate Chromium'):
            gate.optimization_args(action, Path('/out/raw.ap_'), Path('/sdk/aapt2'), Path('/probe'))

    def test_unexpected_optimizer_script_is_rejected(self):
        action = self.action()
        action['script'] = '//build/android/gyp/other.py'
        with self.assertRaisesRegex(ValueError, 'Unexpected Chromium'):
            gate.optimization_args(action, Path('/out/raw.ap_'), Path('/sdk/aapt2'), Path('/probe'))
