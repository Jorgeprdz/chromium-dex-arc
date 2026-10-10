#!/usr/bin/env python3
"""Catch native Android JNI linkage risks and lost-checkpoint regressions early."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NativeLinkAndCheckpointTest(unittest.TestCase):
    def test_jni_heavy_tests_use_apk_registration(self):
        for path, target in (
            ("components/password_manager/core/browser/password_store/BUILD.gn", "archium_login_database_tests"),
            ("chrome/browser/password_manager/android/BUILD.gn", "archium_password_manager_tests"),
        ):
            with self.subTest(target=target):
                source = (ROOT / ".source-modified" / path).read_text()
                expected = 'test("' + target + '") {\n    use_raw_android_executable = false'
                self.assertIn(expected, source)
                gates = (ROOT / "scripts/archium-test-gates.py").read_text()
                self.assertIn(target, gates)

    def test_checkpoint_upload_executes_after_compiler_failure(self):
        workflow = (ROOT / ".github/workflows/archium-stage.yml").read_text()
        lines = workflow.splitlines()
        names = [i for i, line in enumerate(lines)
                 if line.startswith("      - name: Upload checkpoint artifact group ")]
        self.assertEqual(8, len(names))
        for i in names:
            self.assertEqual(
                "        if: ${{ always() && steps.compile.outputs.complete == 'false' }}",
                lines[i + 1],
            )
        self.assertIn("ARCHIUM_CHECKPOINT_STORAGE: artifact", workflow)

    def test_patch_and_inputs_keep_verified_hashes(self):
        manifest = json.loads((ROOT / "patches/upstream-files.json").read_text())
        patch = (ROOT / "patches/archium-desktop.patch").read_bytes()
        self.assertEqual(manifest["patch_sha256"], hashlib.sha256(patch).hexdigest())
        for path in (
            "components/password_manager/core/browser/password_store/BUILD.gn",
            "chrome/browser/password_manager/android/BUILD.gn",
        ):
            data = (ROOT / ".source-modified" / path).read_bytes()
            self.assertEqual(manifest["modified"][path], hashlib.sha256(data).hexdigest())

    def test_payments_link_owner_and_early_native_probe(self):
        source = (ROOT / ".source-modified/chrome/browser/password_manager/android/BUILD.gn").read_text()
        section = source.split('test("archium_password_manager_tests") {', 1)[1].split('\n  }', 1)[0]
        self.assertIn('"//chrome/browser/payments:impl"', section)
        build = (ROOT / "scripts/build-archium.sh").read_text()
        self.assertIn("NATIVE_LINK_PROBE: archium_password_manager_tests first", build)
        self.assertLess(build.index("compile_slice archium_password_manager_tests"),
                        build.index('compile_slice "${validation_targets[@]}"'))

    def test_resume_uses_cross_run_actions_artifacts(self):
        workflow = (ROOT / ".github/workflows/baseline-build.yml").read_text()
        stage = (ROOT / ".github/workflows/archium-stage.yml").read_text()
        checkpoint = (ROOT / "scripts/archium-checkpoint.py").read_text()
        self.assertIn("archium-checkpoint-38018166249-1", workflow)
        self.assertIn("source_run_id:", workflow)
        self.assertIn("github-token: ${{ github.token }}", stage)
        self.assertIn("fromJSON(inputs.source_run_id)", stage)
        self.assertIn("source_commit=args.source_commit", checkpoint)
        self.assertIn("ARCHIUM_SOURCE_RUN_ID", checkpoint)

if __name__ == "__main__":
    unittest.main()
