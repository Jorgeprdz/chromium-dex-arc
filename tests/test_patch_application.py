import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PatchApplicationTest(unittest.TestCase):
    def setUp(self):
        script = ROOT / 'scripts/apply-arc-patches.py'
        self.assertTrue(script.exists(), 'patch application tool must exist')
        spec = importlib.util.spec_from_file_location('arc_apply', script)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'src'
        self.repo.mkdir()
        self.git('init', '-q')
        (self.repo / 'One.java').write_text('old\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'base')
        self.rev = self.git('rev-parse', 'HEAD').strip()
        self.patch = Path(self.temp.name) / 'change.patch'
        self.patch.write_text('diff --git a/One.java b/One.java\n--- a/One.java\n+++ b/One.java\n@@ -1 +1 @@\n-old\n+new\n' +
            'diff --git a/Added.java b/Added.java\nnew file mode 100644\n--- /dev/null\n+++ b/Added.java\n@@ -0,0 +1 @@\n+added\n')
        self.manifest = {'One.java': hashlib.sha256(b'old\n').hexdigest(), 'Added.java': None}

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def apply(self, revision=None, check_only=False):
        self.tool.apply_to_checkout(self.repo, self.patch, self.manifest,
            self.rev if revision is None else revision, check_only=check_only)

    def test_real_patch_applies(self):
        self.apply()
        self.assertEqual((self.repo / 'One.java').read_text(), 'new\n')
        self.assertEqual((self.repo / 'Added.java').read_text(), 'added\n')

    def test_check_only_does_not_mutate(self):
        self.apply(check_only=True)
        self.assertEqual((self.repo / 'One.java').read_text(), 'old\n')
        self.assertFalse((self.repo / 'Added.java').exists())

    def test_wrong_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'revision'):
            self.apply('0' * 40)
        self.assertEqual((self.repo / 'One.java').read_text(), 'old\n')

    def test_changed_source_rejected_before_any_write(self):
        (self.repo / 'One.java').write_text('user change\n')
        with self.assertRaisesRegex(ValueError, 'source'):
            self.apply()
        self.assertFalse((self.repo / 'Added.java').exists())
        self.assertEqual((self.repo / 'One.java').read_text(), 'user change\n')

    def test_existing_new_file_rejected(self):
        (self.repo / 'Added.java').write_text('user file\n')
        with self.assertRaisesRegex(ValueError, 'exists'):
            self.apply()
        self.assertEqual((self.repo / 'One.java').read_text(), 'old\n')

    def test_conflicting_hunk_rejected_before_any_write(self):
        self.patch.write_text(self.patch.read_text().replace('-old\n', '-absent\n'))
        with self.assertRaises(subprocess.CalledProcessError):
            self.apply()
        self.assertEqual((self.repo / 'One.java').read_text(), 'old\n')
        self.assertFalse((self.repo / 'Added.java').exists())

    def test_symlink_source_rejected(self):
        target = Path(self.temp.name) / 'outside'
        target.write_text('old\n')
        (self.repo / 'One.java').unlink()
        (self.repo / 'One.java').symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'path'):
            self.apply()
        self.assertEqual(target.read_text(), 'old\n')


if __name__ == '__main__':
    unittest.main()
