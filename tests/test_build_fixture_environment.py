"""Legacy routing fixtures must retain their own branch under a recovery CI job."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def routing_case():
    spec = importlib.util.spec_from_file_location('legacy_routing_fixture',
        ROOT / 'tests/test_build_routing.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BuildRoutingTests('test_real_java_preflight_precedes_native_and_apk_compilation')


class RoutingFixtureEnvironmentTests(unittest.TestCase):
    def test_recovery_ci_branch_cannot_redirect_legacy_fixture_to_real_dispatch(self):
        ambient = {
            'GITHUB_REF_NAME': 'assistant/archium-r4-recovery',
            'GITHUB_REF': 'refs/heads/assistant/archium-r4-recovery',
            'GITHUB_SHA': '0514027dd41ddb568d033152c8faec76a388ba84',
        }
        with patch.dict(os.environ, ambient):
            case = routing_case()
            try:
                case.setUp()
                result = case.run_build(ARCHIUM_PREVIOUS_TAG='archium-checkpoint-456-1',
                    ARCHIUM_COMPILE_GATE_TARGETS='archium_password_manager_tests')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(case.env['GITHUB_REF_NAME'], 'assistant/archium-r3-visual-fixes')
                self.assertEqual(case.env['GITHUB_REF'],
                    'refs/heads/assistant/archium-r3-visual-fixes')
                self.assertTrue(any(c[0] == 'autoninja' for c in case.calls()))
                self.assertEqual(os.environ['GITHUB_REF_NAME'], ambient['GITHUB_REF_NAME'])
            finally:
                case.doCleanups()
