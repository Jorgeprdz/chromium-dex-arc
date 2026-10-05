import hashlib
import importlib.util
import os
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
            def fake_gh(*args):
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
                checkpoint.restore(workspace, 'tag', 'repo')
            self.assertEqual(ninja.read_text(), 'recorded compilation\n')
            self.assertEqual(ninja.stat().st_mtime_ns, 1234567890123456789)
            self.assertEqual(executable.stat().st_mode & 0o777, 0o755)
            self.assertTrue((workspace / 'compiler-link').is_symlink())
            self.assertGreater(len(assets), 2)

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
