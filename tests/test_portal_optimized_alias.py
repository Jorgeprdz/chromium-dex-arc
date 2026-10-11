"""Real AAPT2 resource-path optimization must not break the Portal verifier.

This is a resource fixture with a synthetic manifest; Chromium merge is a distinct CI gate.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class OptimizedAliasTest(unittest.TestCase):
    def test_real_aapt2_shortened_alias_and_foreign_manifest_rejection(self):
        aapt2 = os.environ.get('ARCHIUM_TEST_AAPT2') or shutil.which('aapt2')
        android = os.environ.get('ARCHIUM_TEST_ANDROID_JAR')
        self.assertTrue(aapt2 and android, 'Genuine AAPT2 and Android SDK are required for resource regression')
        spec = importlib.util.spec_from_file_location('fixture', ROOT / 'scripts/check_portal_aapt2_fixture.py')
        fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
        fixture.run_aapt2_fixture(Path(android), Path(aapt2), optimize=True, verify_negative=True)
        fixture.run_aapt2_fixture(Path(android), Path(aapt2), optimize=True,
                                 verify_negative=True, chromium_images=True)
