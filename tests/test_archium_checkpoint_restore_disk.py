#!/usr/bin/env python3
"""Exercise actual checksum -> extract -> cleanup chain on a tiny local archive."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import errno
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("archium_checkpoint", ROOT / "scripts/archium-checkpoint.py")
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)
SOURCE_COMMIT = "507f28e1265fb98551d3bc1a66f4739fb48d2625"
TAG = "archium-checkpoint-38018166249-1"

class CheckpointDiskRecoveryTests(unittest.TestCase):
    def test_enospc_restore_preserves_all_downloaded_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, stage = self.make_artifact(Path(tmp))
            before = {p.name: p.read_bytes() for p in stage.iterdir()}
            with patch.object(checkpoint.subprocess, 'Popen', side_effect=OSError(errno.ENOSPC, 'disk full')):
                with self.assertRaises(OSError) as error:
                    checkpoint.restore_actions(workspace, TAG, stage, source_commit=SOURCE_COMMIT)
            self.assertEqual(error.exception.errno, errno.ENOSPC)
            self.assertEqual(before, {p.name: p.read_bytes() for p in stage.iterdir()})

    def test_failed_tar_keeps_downloaded_checkpoint_and_no_restore_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, stage = self.make_artifact(Path(tmp))
            receipt = json.loads((stage / 'checkpoint.json').read_text())
            for part in receipt['parts']:
                data = b'invalid tar payload'
                (stage / part['name']).write_bytes(data)
                part.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            (stage / 'checkpoint.json').write_text(json.dumps(receipt))
            before = {p.name: p.read_bytes() for p in stage.iterdir()}
            with self.assertRaises((RuntimeError, BrokenPipeError)):
                checkpoint.restore_actions(workspace, TAG, stage, source_commit=SOURCE_COMMIT)
            self.assertEqual(before, {p.name: p.read_bytes() for p in stage.iterdir()})
    def make_artifact(self, parent, *, tamper=False):
        source = parent / "source"
        source.mkdir()
        (source / "payload.txt").write_text("incremental-output-preserved")
        compressed = parent / "checkpoint.tar.gz"
        with tarfile.open(compressed, "w:gz") as archive:
            archive.add(source / "payload.txt", arcname="checkout/src/payload.txt")
        data = compressed.read_bytes()
        stage = parent / "downloaded"
        stage.mkdir()
        chunks = [data[:len(data)//2], data[len(data)//2:]]
        parts = []
        for i, data_part in enumerate(chunks):
            name = f"checkpoint-{i:04d}.tar.gz.part"
            (stage / name).write_bytes(data_part)
            parts.append({"name": name, "bytes": len(data_part), "sha256": hashlib.sha256(data_part).hexdigest()})
        destination = parent / "chromium-archium"
        manifest = {**checkpoint.identity(destination, source_commit=SOURCE_COMMIT),
                    "tag": TAG, "parts": parts}
        (stage / "checkpoint.json").write_text(json.dumps(manifest))
        if tamper:
            (stage / parts[0]["name"]).write_bytes(b"broken" + chunks[0][6:])
        return destination, stage

    def test_restores_all_bytes_and_reclaims_archive_before_future_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, stage = self.make_artifact(Path(tmp))
            checkpoint.restore_actions(workspace, TAG, stage, source_commit=SOURCE_COMMIT)
            self.assertEqual((workspace / "checkout/src/payload.txt").read_text(),
                             "incremental-output-preserved")
            self.assertEqual(list(stage.iterdir()), [], "24GiB archive must not remain on runner")
            self.assertTrue(stage.is_dir(), "pack_actions needs an empty stage directory")

    def test_corrupt_download_rejected_without_deletion_or_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, stage = self.make_artifact(Path(tmp), tamper=True)
            with self.assertRaisesRegex(ValueError, "checksum|size|hash"):
                checkpoint.restore_actions(workspace, TAG, stage, source_commit=SOURCE_COMMIT)
            self.assertTrue((stage / "checkpoint.json").exists())
            self.assertFalse(workspace.exists())

    def test_source_metadata_preserves_post_download_disk_reserve(self):
        spec = importlib.util.spec_from_file_location('remote', ROOT / 'scripts/check-recovery-checkpoint.py')
        remote = importlib.util.module_from_spec(spec); spec.loader.exec_module(remote)
        item = {'id': 1, 'name': TAG + '-00', 'expired': False,
                'expires_at': '2099-01-01T00:00:00Z', 'size_in_bytes': 1000,
                'digest': 'sha256:' + 'a' * 64,
                'workflow_run': {'head_sha': SOURCE_COMMIT}}
        with self.assertRaisesRegex(ValueError, 'disk'):
            remote.validate_inventory([item], TAG, SOURCE_COMMIT, 75000000999, 2000000)
        groups = remote.validate_inventory([item], TAG, SOURCE_COMMIT, 75000001000, 2000000)
        self.assertEqual(groups, [item])

if __name__ == "__main__":
    unittest.main()
