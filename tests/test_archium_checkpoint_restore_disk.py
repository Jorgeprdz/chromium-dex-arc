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

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("archium_checkpoint", ROOT / "scripts/archium-checkpoint.py")
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)
SOURCE_COMMIT = "507f28e1265fb98551d3bc1a66f4739fb48d2625"
TAG = "archium-checkpoint-38018166249-1"

class CheckpointDiskRecoveryTests(unittest.TestCase):
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

    def test_shell_uses_resume_budget_only_with_archived_manifest(self):
        build=(ROOT / "scripts/build-archium.sh").read_text()
        self.assertIn('required_bytes=75000000000', build)
        self.assertIn('required_bytes=100000000000', build)
        self.assertIn('&& -f "${ARCHIUM_CHECKPOINT_DIR:-}/checkpoint.json"', build)
        self.assertIn('if (( available_bytes < 30000000000 ))', build)
        code=(ROOT / "scripts/archium-checkpoint.py").read_text()
        self.assertIn('ACTIONS_CHECKPOINT_INPUT_CLEANUP=PASS', code)

if __name__ == "__main__":
    unittest.main()
