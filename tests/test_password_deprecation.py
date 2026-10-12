"""Retired Archium passwords must not be enabled or linked into the R4 APK."""
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

from media_gn_probe import ROOT, evaluate


def gate_module():
    spec = importlib.util.spec_from_file_location('deprecation_gate',
        ROOT / 'scripts/check-archium-password-deprecation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PasswordDeprecationTests(unittest.TestCase):
    def test_real_gn_arm64_and_x64_disable_retired_feature(self):
        for cpu in ('arm64', 'x64'):
            with self.subTest(cpu=cpu):
                config = subprocess.run([sys.executable,
                    str(ROOT / 'scripts/archium-build-config.py'), '--target-cpu', cpu],
                    text=True, capture_output=True, check=True).stdout
                effective = evaluate(config)
                self.assertRegex(effective, r'(?m)^enable_archium_local_passwords = false$')

    def test_true_flag_or_retired_dependencies_cannot_pass(self):
        gate = gate_module()
        self.assertEqual(gate.issues('enable_archium_local_passwords = false\n',
            '//chrome/browser/payments:impl\n//chrome/browser/password_manager:impl\n'), [])
        self.assertTrue(gate.issues('enable_archium_local_passwords = true\n', ''))
        self.assertTrue(gate.issues('', ''))
        for target in ('archium_key_provider', 'archium_key_java',
                       'archium_local_password_manager', 'archium_password_csv_java',
                       'archium_import_preview'):
            with self.subTest(target=target):
                self.assertTrue(gate.issues('enable_archium_local_passwords = false\n',
                    f'//chrome/browser/password_manager/android:{target}\n'))

    def test_recovery_does_not_compile_retired_password_targets(self):
        spec = importlib.util.spec_from_file_location('routing',
            ROOT / 'tests/test_recovery_build_routing.py')
        routing = importlib.util.module_from_spec(spec); spec.loader.exec_module(routing)
        case = routing.RecoveryBuildRoutingTests(); case.setUp()
        self.addCleanup(case.doCleanups)
        result = case.build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        targets = [arg for call in case.targets() for arg in call]
        self.assertFalse(any(re.fullmatch(r'archium_(?:password|key|login).*', t)
                             for t in targets), targets)
        self.assertIn('libchrome', targets, 'Actual APK native library must remain link-gated')
