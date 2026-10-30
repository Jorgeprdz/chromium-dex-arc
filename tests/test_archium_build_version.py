"""Execute allocation and APK identity checks; no native build is inferred."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class BuildVersionTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'scripts/archium-build-version.py'
        self.assertTrue(path.exists(), 'Independent Archium build identity is missing')
        spec = importlib.util.spec_from_file_location('build_version', path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_new_builds_increment_and_resumed_source_is_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            a = self.module.allocate(checkout, 'a' * 40, '201', '20001')
            self.assertEqual(a['version'], '0.9.201')
            resource = checkout / self.module.RESOURCE
            stamp = resource.stat().st_mtime_ns
            resumed = self.module.allocate(checkout, 'a' * 40, '202', '20002')
            self.assertEqual(resumed, a)
            self.assertEqual(resource.stat().st_mtime_ns, stamp)
            b = self.module.allocate(checkout, 'b' * 40, '203', '20003')
            self.assertEqual(b['version'], '0.9.203')

    def test_counter_never_moves_backwards_even_if_workflow_number_does(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            self.module.allocate(checkout, 'a' * 40, '500', '20001')
            b = self.module.allocate(checkout, 'b' * 40, '4', '20002')
            self.assertEqual(b['version'], '0.9.501')

    def test_corrupt_previous_identity_fails_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            resource = checkout / self.module.RESOURCE
            resource.parent.mkdir(parents=True)
            resource.write_text('{corrupt')
            with self.assertRaises(ValueError):
                self.module.allocate(checkout, 'a' * 40, '1', '1')
            self.assertEqual(resource.read_text(), '{corrupt')

    def test_packaged_asset_must_match_allocated_source_and_version(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            data = self.module.allocate(checkout, 'a' * 40, '201', '20001')
            apk = checkout / 'test.apk'
            with zipfile.ZipFile(apk, 'w') as archive:
                archive.writestr('assets/archium-build.json', json.dumps(data))
            self.module.verify_apk(checkout, apk)
            with zipfile.ZipFile(apk, 'w') as archive:
                archive.writestr('assets/archium-build.json', json.dumps({**data, 'version': '0.9.2'}))
            with self.assertRaises(ValueError):
                self.module.verify_apk(checkout, apk)

    def test_invalid_inputs_do_not_create_an_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            for sha, number, run in [('bad', '1', '1'), ('a'*40, '0', '1'), ('a'*40, '1', 'bad')]:
                with self.assertRaises(ValueError):
                    self.module.allocate(checkout, sha, number, run)
            self.assertFalse((checkout / self.module.RESOURCE).exists())


if __name__ == '__main__':
    unittest.main()
