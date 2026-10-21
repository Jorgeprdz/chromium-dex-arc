"""Receipt safety gates: stale/mixed ABI inputs and unobserved cases cannot pass."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/validate-r5-qemu.py'


class QemuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('r5_qemu', SCRIPT)
        cls.qemu = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.qemu)

    def artifact(self, root, abi='arm64-v8a'):
        apk = root / 'Archium-for-Android-arm64.apk'
        with zipfile.ZipFile(apk, 'w') as archive:
            archive.writestr(f'lib/{abi}/libchrome.so', b'test fixture, not executable')
        digest = hashlib.sha256(apk.read_bytes()).hexdigest()
        (root / 'BUILD_REPORT.json').write_text(json.dumps({'source_sha': 'abc', 'run_id': '123'}))
        (root / 'SHA256SUMS').write_text(f'{digest}  {apk.name}\n')
        return apk

    def test_stale_source_or_run_is_rejected_before_android_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.artifact(root)
            for sha, run in [('old', '123'), ('abc', '122')]:
                with self.assertRaises(ValueError):
                    self.qemu.verify_identity(root, sha, run)

    def test_mixed_or_wrong_native_abi_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            apk = self.artifact(root)
            with zipfile.ZipFile(apk, 'a') as archive:
                archive.writestr('lib/x86_64/libchrome.so', b'x86 fixture')
            (root / 'SHA256SUMS').write_text(f'{hashlib.sha256(apk.read_bytes()).hexdigest()}  {apk.name}\n')
            with self.assertRaisesRegex(ValueError, 'ABI'):
                self.qemu.verify_identity(root, 'abc', '123')

    def test_changed_apk_bytes_cannot_use_old_checksum(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            apk = self.artifact(root)
            with apk.open('ab') as stream:
                stream.write(b'tamper')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                self.qemu.verify_identity(root, 'abc', '123')

    def test_cli_stale_artifact_writes_failure_receipt_without_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.artifact(root)
            output = root / 'result'
            result = subprocess.run([sys.executable, str(SCRIPT), '--artifact-dir', str(root), '--source-sha', 'old', '--run-id', '123', '--output-dir', str(output)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            receipt = json.loads((output / 'qemu-receipt.json').read_text())
            self.assertEqual(receipt['status'], 'FAIL')
            self.assertEqual(receipt['artifact_verification'], 'FAIL')
            self.assertNotIn('environment', receipt)
            self.assertTrue(all(case['status'] == 'NOT_TESTED' for case in receipt['cases']))
            self.assertIn('FAIL', (output / 'R5_QEMU_REPORT.md').read_text())

    def test_valid_identity_returns_actual_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            apk = self.artifact(root)
            self.assertEqual(self.qemu.verify_identity(root, 'abc', '123')['apk_sha256'], hashlib.sha256(apk.read_bytes()).hexdigest())

    def test_missing_kvm_and_x86_hosts_are_blocked(self):
        for machine, kvm in [('aarch64', False), ('x86_64', True)]:
            self.assertIsNone(self.qemu.capable_avd(machine, kvm, [{'name': 'r5', 'abi': 'arm64-v8a', 'api': '36'}]))

    def test_native_arm64_kvm_requires_api36_arm64_image(self):
        self.assertEqual(self.qemu.capable_avd('aarch64', True, [{'name': 'r5', 'abi': 'arm64-v8a', 'api': '36'}]), 'r5')
        self.assertIsNone(self.qemu.capable_avd('aarch64', True, [{'name': 'x86', 'abi': 'x86_64', 'api': '36'}]))

    def test_package_comparison_ignores_aapt_platform_format_but_rejects_wrong_version(self):
        old = "package: name='app.archium.android' versionCode='1' versionName='r5' platformBuildVersionName='17'"
        new = "package: name='app.archium.android' versionCode='1' versionName='r5' platformBuildVersionName=''"
        self.assertEqual(self.qemu.package_identity(old), self.qemu.package_identity(new))
        self.assertNotEqual(self.qemu.package_identity(old), self.qemu.package_identity(new.replace("versionCode='1'", "versionCode='2'")))

    def test_one_smoke_pass_never_implies_matrix_pass(self):
        self.assertEqual(self.qemu.matrix_status([{'status': 'PASS'}, {'status': 'NOT_TESTED'}]), 'NOT_TESTED')
        self.assertEqual(self.qemu.matrix_status([{'status': 'FAIL'}]), 'FAIL')
        self.assertEqual(self.qemu.matrix_status([]), 'NOT_TESTED')
        self.assertEqual(self.qemu.matrix_status([{'status': 'PASS'}]), 'NOT_TESTED')
        self.assertEqual(self.qemu.matrix_status([{'id': key, 'status': 'PASS'} for key, _ in self.qemu.CASES]), 'QEMU_TESTS_PASS')


if __name__ == '__main__':
    unittest.main()
