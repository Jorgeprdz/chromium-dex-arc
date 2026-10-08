"""Keep repository failures ahead of expensive checkpoint restore and compilation."""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_fetcher():
    spec = importlib.util.spec_from_file_location(
        'repository_gn', ROOT / 'scripts/fetch-repository-gn.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RepositoryPreflightTests(unittest.TestCase):
    def archive(self, data):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('gn', data)
        stream.seek(0)
        return stream

    def test_gn_download_checks_content_before_publishing_executable(self):
        fetcher = load_fetcher()
        data = b'controlled download boundary; never executed'
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
                fetcher.DIGESTS, {'amd64': hashlib.sha256(data).hexdigest()}), patch.object(
                fetcher.urllib.request, 'urlopen', return_value=self.archive(data)):
            path = fetcher.ensure_gn(Path(tmp), 'x86_64')
            self.assertEqual(path.read_bytes(), data)
            self.assertTrue(os.access(path, os.X_OK))

    def test_changed_download_cannot_leave_a_published_gn(self):
        fetcher = load_fetcher()
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                fetcher.urllib.request, 'urlopen', return_value=self.archive(b'wrong binary')):
            with self.assertRaisesRegex(ValueError, 'checksum'):
                fetcher.ensure_gn(Path(tmp), 'x86_64')
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_cached_gn_is_rechecked_and_corruption_fails_closed(self):
        fetcher = load_fetcher()
        data = b'controlled cached tool boundary; never executed'
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
                fetcher.DIGESTS, {'arm64': hashlib.sha256(data).hexdigest()}):
            cache = Path(tmp)
            tool = cache / 'gn-linux-arm64'
            tool.write_bytes(data); tool.chmod(0o755)
            self.assertEqual(fetcher.ensure_gn(cache, 'aarch64'), tool.resolve())
            tool.write_bytes(b'corrupted cached binary')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                fetcher.ensure_gn(cache, 'aarch64')

    def test_unknown_host_architecture_is_rejected_without_downloading(self):
        fetcher = load_fetcher()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'architecture'):
                fetcher.ensure_gn(Path(tmp), 'unsupported')
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_repository_test_failure_propagates_before_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gn = root / 'gn'
            gn.write_text('#!/bin/bash\nexit 0\n')
            gn.chmod(0o755)
            python = root / 'python3'
            python.write_text('#!/bin/bash\n'
                              'if [[ "$*" == *"fetch-repository-gn.py"* ]]; then\n'
                              '  printf "%s\\n" "$GN_FIXTURE"\n'
                              'elif [[ "$*" == *"-m unittest discover"* ]]; then\n'
                              '  exit 7\n'
                              'fi\n')
            python.chmod(0o755)
            restored = root / 'restore-started'
            result = subprocess.run([
                'bash', '-e', '-c',
                'bash "$1"; touch "$2"', 'preflight-test',
                str(ROOT / 'scripts/check-archium-repository.sh'), str(restored),
            ], env={**os.environ, 'ARCHIUM_REPOSITORY_PYTHON': str(python),
                    'GN_FIXTURE': str(gn)},
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertFalse(restored.exists())

    def test_stage_checks_repository_unconditionally_before_restore(self):
        workflow = (ROOT / '.github/workflows/archium-stage.yml').read_text()
        self.assertIn('run: bash scripts/check-archium-repository.sh', workflow)
        quick = workflow.index('run: bash scripts/check-archium-repository.sh')
        restore = workflow.index('run: bash scripts/build-archium.sh --prepare')
        self.assertLess(quick, restore)
        step = workflow[workflow.rfind('      - name:', 0, quick):restore]
        self.assertNotIn('continue-on-error:', step)
        self.assertNotIn('if:', step)
        self.assertIn('ARCHIUM_REPOSITORY_PYTHON: /usr/bin/python3', workflow)
