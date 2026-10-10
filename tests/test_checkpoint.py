import hashlib
import importlib.util
import os
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('checkpoint', Path(__file__).resolve().parents[1] / 'scripts/archium-checkpoint.py')
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


class CheckpointTests(unittest.TestCase):
    def test_round_trip_preserves_ninja_state_modes_symlinks_and_timestamps(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / 'workspace'
            workspace.mkdir()
            ninja = workspace / '.ninja_log'
            ninja.write_text('recorded compilation\n')
            os.utime(ninja, ns=(1234567890123456789, 1234567890123456789))
            executable = workspace / 'compiler'
            executable.write_text('toolchain')
            executable.chmod(0o755)
            (workspace / 'compiler-link').symlink_to('compiler')
            assets = {}
            def fake_gh(*args, capture=False):
                if args[1] == 'api':
                    return subprocess.CompletedProcess(args, 0, stdout=json.dumps({
                        'tag_name': 'tag', 'assets': [
                            {'name': name, 'size': len(data), 'state': 'uploaded',
                             'digest': 'sha256:' + hashlib.sha256(data).hexdigest()}
                            for name, data in assets.items()]}))
                if args[2] == 'upload':
                    p = Path(args[4])
                    assets[p.name] = p.read_bytes()
                elif args[2] == 'download':
                    name = args[args.index('--pattern') + 1]
                    directory = Path(args[args.index('--dir') + 1])
                    (directory / name).write_bytes(assets[name])
            with patch.dict(os.environ, {'GITHUB_SHA': 'test-commit'}), \
                    patch.object(checkpoint, 'run', fake_gh), \
                    patch.object(checkpoint, 'CHUNK_BYTES', 64):
                checkpoint.pack(workspace, 'tag', 'repo')
                # Remove fixture files only, then restore at the exact original path.
                for path in workspace.iterdir():
                    path.unlink()
                with patch.dict(os.environ, {'GITHUB_SHA': 'new-implementation'}):
                    with self.assertRaises(ValueError):
                        checkpoint.restore(workspace, 'tag', 'repo')
                    self.assertEqual(list(workspace.iterdir()), [])
                    checkpoint.restore(workspace, 'tag', 'repo', source_commit='test-commit')
            self.assertEqual(ninja.read_text(), 'recorded compilation\n')
            self.assertEqual(ninja.stat().st_mtime_ns, 1234567890123456789)
            self.assertEqual(executable.stat().st_mode & 0o777, 0o755)
            self.assertTrue((workspace / 'compiler-link').is_symlink())
            self.assertGreater(len(assets), 2)

    def test_artifact_checkpoint_round_trip_and_corruption_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace, folder = root / 'workspace', root / 'bundles'
            workspace.mkdir()
            (workspace / '.ninja_log').write_text('progress')
            os.utime(workspace / '.ninja_log', ns=(1234567890123456789, 1234567890123456789))
            (workspace / 'compiler').write_text('binary')
            (workspace / 'compiler').chmod(0o755)
            (workspace / 'link').symlink_to('compiler')
            with patch.dict(os.environ, {'GITHUB_SHA': 'r3-commit'}), \
                    patch.object(checkpoint, 'CHUNK_BYTES', 80):
                checkpoint.pack_actions(workspace, 'archium-checkpoint-999-1', folder)
                self.assertTrue((folder / 'group-00' / 'checkpoint.json').is_file())
                downloaded = root / 'downloaded'
                downloaded.mkdir()
                for group in folder.iterdir():
                    for part in group.iterdir():
                        (downloaded / part.name).write_bytes(part.read_bytes())
                for item in workspace.iterdir():
                    item.unlink()
                with self.assertRaisesRegex(ValueError, 'tag'):
                    checkpoint.restore_actions(workspace, 'bad-tag', downloaded)
                checkpoint.restore_actions(workspace, 'archium-checkpoint-999-1', downloaded)
                self.assertEqual('progress', (workspace / '.ninja_log').read_text())
                self.assertEqual(1234567890123456789, (workspace / '.ninja_log').stat().st_mtime_ns)
                self.assertTrue((workspace / 'link').is_symlink())
                self.assertEqual([], list(downloaded.iterdir()),
                                 'Verified restore must reclaim staged archive bytes')
                for item in workspace.iterdir():
                    item.unlink()
                # Re-download the same synthetic archive: corruption should be
                # detected before extraction, and failed restores keep evidence.
                for group in folder.iterdir():
                    for part in group.iterdir():
                        (downloaded / part.name).write_bytes(part.read_bytes())
                name = next(downloaded.glob('checkpoint-*.part'))
                bytes_ = bytearray(name.read_bytes())
                bytes_[0] ^= 1
                name.write_bytes(bytes_)
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    checkpoint.restore_actions(workspace, 'archium-checkpoint-999-1', downloaded)
                self.assertEqual([], list(workspace.iterdir()))

    def test_remote_inventory_rejects_missing_corrupt_or_unfinished_assets(self):
        digest = hashlib.sha256(b'x').hexdigest()
        parts = [{'name': 'checkpoint-0000.tar.gz.part', 'bytes': 1, 'sha256': digest}]
        valid = {'name': parts[0]['name'], 'size': 1, 'state': 'uploaded',
                 'digest': 'sha256:' + digest}
        for assets in ([], [dict(valid, size=2)], [dict(valid, digest='sha256:'+'0'*64)],
                       [dict(valid, state='starter')], [dict(valid, digest=None)]):
            with self.subTest(assets=assets), patch.object(checkpoint, 'run', return_value=
                    subprocess.CompletedProcess([], 0, stdout=json.dumps(
                        {'tag_name': 'tag', 'assets': assets}))):
                with self.assertRaises(ValueError):
                    checkpoint.verify_assets(parts, 'tag', 'repo')

    def test_remote_mismatch_never_publishes_commit_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary); (workspace / 'data').write_bytes(b'payload')
            uploads = []
            def fake_gh(*args, capture=False):
                if args[1] == 'api':
                    return subprocess.CompletedProcess(args, 0, stdout=json.dumps(
                        {'tag_name': 'tag', 'assets': []}))
                if args[2] == 'upload': uploads.append(Path(args[4]).name)
            with patch.dict(os.environ, {'GITHUB_SHA': 'test-commit'}), \
                    patch.object(checkpoint, 'run', fake_gh):
                with self.assertRaises(ValueError): checkpoint.pack(workspace, 'tag', 'repo')
            self.assertIn('checkpoint-0000.tar.gz.part', uploads)
            self.assertNotIn('checkpoint.json', uploads)

    def test_release_beyond_first_api_page_can_be_verified(self):
        digest = hashlib.sha256(b'x').hexdigest()
        parts = [{'name': 'checkpoint-0000.tar.gz.part', 'bytes': 1, 'sha256': digest}]
        def api(*args, capture=False):
            # GitHub CLI yields only jq matches. This tag is on the second page.
            body = json.dumps({'tag_name': 'tag', 'assets': [
                {'name': parts[0]['name'], 'size': 1, 'state': 'uploaded',
                 'digest': 'sha256:' + digest}]}) if '--paginate' in args else ''
            return subprocess.CompletedProcess(args, 0, stdout=body)
        with patch.object(checkpoint, 'run', api):
            checkpoint.verify_assets(parts, 'tag', 'repo')

    def test_old_checkpoint_requires_explicit_source_commit(self):
        with patch.dict(os.environ, {'GITHUB_SHA': 'new-implementation'}):
            workspace = Path('/same')
            manifest = {**checkpoint.identity(workspace), 'commit': 'old-implementation',
                        'parts': [{'name': 'checkpoint-0000.tar.gz.part', 'bytes': 1,
                                   'sha256': hashlib.sha256(b'x').hexdigest()}]}
            with self.assertRaises(ValueError):
                checkpoint.validate_manifest(manifest, checkpoint.identity(workspace))
            checkpoint.validate_manifest(manifest,
                checkpoint.identity(workspace, source_commit='old-implementation'))
            with self.assertRaises(ValueError):
                checkpoint.validate_manifest(manifest,
                    checkpoint.identity(workspace, source_commit='different'))
            # Selecting an old source never relaxes revision or workspace checks.
            expected = checkpoint.identity(workspace, source_commit='old-implementation')
            for key in ['workspace', 'revision']:
                with self.assertRaises(ValueError):
                    checkpoint.validate_manifest({**manifest, key: 'wrong'}, expected)

    def test_rejects_incompatible_or_unordered_checkpoint(self):
        expected = {'schema': 1, 'workspace': '/same', 'commit': 'abc', 'revision': 'rev'}
        manifest = {**expected, 'parts': [{'name': 'checkpoint-0000.tar.gz.part',
                    'bytes': 1, 'sha256': hashlib.sha256(b'x').hexdigest()}]}
        checkpoint.validate_manifest(manifest, expected)
        for key in expected:
            with self.assertRaises(ValueError):
                checkpoint.validate_manifest({**manifest, key: 'different'}, expected)
        manifest['parts'][0]['name'] = '../unsafe'
        with self.assertRaises(ValueError):
            checkpoint.validate_manifest(manifest, expected)


if __name__ == '__main__':
    unittest.main()
