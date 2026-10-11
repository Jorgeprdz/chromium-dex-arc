"""The retired push bridge must never contact or dispatch GitHub."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RetiredDispatchTest(unittest.TestCase):
    def test_legacy_push_bridge_fails_before_any_github_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / 'gh-called'
            gh = root / 'gh'
            gh.write_text('#!/bin/sh\nprintf called > "$TEST_GH_TRACE"\nprintf "%s\\n" "$GITHUB_SHA"\n')
            gh.chmod(0o755)
            env = {**os.environ, 'PATH': str(root) + ':' + os.environ['PATH'],
                   'TEST_GH_TRACE': str(trace), 'GH_TOKEN': 'test-fixture-no-network',
                   'GITHUB_SHA': 'b'*40, 'GITHUB_EVENT_NAME': 'push',
                   'GITHUB_REPOSITORY': 'Jorgeprdz/chromium-dex-arc',
                   'GITHUB_REF_NAME': 'assistant/archium-r3-visual-fixes'}
            result = subprocess.run(['bash', str(ROOT/'scripts/dispatch-archium-r3-1-build.sh')],
                                    env=env, capture_output=True, text=True)
            self.assertFalse(trace.exists(), 'Retired helper contacted GitHub')
            self.assertEqual(result.returncode, 2)
            self.assertIn('retired', result.stderr)
