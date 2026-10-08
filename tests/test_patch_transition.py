"""Verify actual patch transitions, preserving Ninja inputs and failing before writes."""
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('transition', ROOT / 'scripts/transition-archium-patches.py')
transition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transition)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checkout = self.root / 'src'
        self.originals = self.root / 'originals'
        self.checkout.mkdir(); self.originals.mkdir()
        self.base = {'shared.txt': b'base\n', 'old-only.txt': b'original\n',
                     'unchanged.txt': b'stable\n'}
        for name, data in self.base.items():
            (self.checkout / name).write_bytes(data)
            (self.originals / name).write_bytes(data)
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'Pinned originals')
        self.revision = self.git('rev-parse', 'HEAD').strip()
        self.pin = patch.object(transition, 'REVISION', self.revision)
        self.pin.start(); self.addCleanup(self.pin.stop)
        self.old_state = {'shared.txt': b'old\n', 'old-only.txt': b'old changed\n',
                          'unchanged.txt': b'stable modified\n', 'obsolete.java': b'old source\n'}
        self.new_state = {'shared.txt': b'new\n', 'unchanged.txt': b'stable modified\n',
                          'newdir/new.java': b'new source\n'}
        self.old, self.old_patch = self.bundle('old', self.old_state)
        self.new, self.new_patch = self.bundle('new', self.new_state)
        self.git('apply', str(self.old_patch))
        (self.checkout / 'shared.txt').chmod(0o751)
        for name in self.old_state:
            os.utime(self.checkout / name, ns=(1234567890123456789, 1234567890123456789))

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.checkout), *args], text=True)

    def bundle(self, label, state):
        chunks = []
        for name, after in sorted(state.items()):
            before = self.base.get(name, b'')
            chunks.append(f'diff --git a/{name} b/{name}\n')
            if name not in self.base: chunks.append('new file mode 100644\n')
            chunks.extend(difflib.unified_diff(before.decode().splitlines(True),
                after.decode().splitlines(True), fromfile='a/' + name if name in self.base else '/dev/null',
                tofile='b/' + name))
        p = self.root / (label + '.patch')
        p.write_text(''.join(chunks))
        return {'revision': self.revision,
                'originals': {name: digest(self.base[name]) if name in self.base else None for name in state},
                'modified': {name: digest(data) for name, data in state.items()},
                'patch_sha256': digest(p.read_bytes())}, p

    def apply(self):
        return transition.transition(self.checkout, self.old, self.new,
                                     self.old_patch, self.new_patch, self.originals)

    def snapshot(self):
        return {p.relative_to(self.checkout).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode & 0o777)
                for p in self.checkout.rglob('*') if p.is_file() and '.git' not in p.parts}

    def prepare_chained_transition(self):
        transition.transition(self.checkout, self.old, self.new,
                              self.old_patch, self.new_patch, self.originals,
                              source_commit='1' * 40, implementation_commit='2' * 40)
        third_state = dict(self.new_state, **{'shared.txt': b'third\n'})
        third, third_patch = self.bundle('third', third_state)
        return third, third_patch

    def apply_chained(self, third, third_patch):
        return transition.transition(self.checkout, self.new, third,
                                     self.new_patch, third_patch, self.originals,
                                     source_commit='2' * 40, implementation_commit='3' * 40)

    def test_checkpoint_can_transition_again_with_verified_previous_identity(self):
        third, third_patch = self.prepare_chained_transition()
        before = self.snapshot()
        receipt = self.apply_chained(third, third_patch)
        self.assertEqual((self.checkout / 'shared.txt').read_bytes(), b'third\n')
        self.assertEqual(self.snapshot()['unchanged.txt'], before['unchanged.txt'])
        self.assertEqual(receipt['source_commit'], '2' * 40)
        self.assertEqual(receipt['implementation_commit'], '3' * 40)
        self.assertEqual(receipt['old_patch_sha256'], self.new['patch_sha256'])
        self.assertEqual(receipt['new_patch_sha256'], third['patch_sha256'])
        self.assertEqual(json.loads((self.checkout / transition.RECEIPT).read_text()), receipt)

    def test_chained_interruption_restores_previous_receipt_and_source_timestamps(self):
        third, third_patch = self.prepare_chained_transition()
        before = self.snapshot()
        original_write = transition._write_file
        def interrupt(path, *args):
            if path.name == transition.RECEIPT:
                original_write(path, *args)
                raise KeyboardInterrupt('interrupted receipt replacement')
            return original_write(path, *args)
        with patch.object(transition, '_write_file', interrupt):
            with self.assertRaises(KeyboardInterrupt): self.apply_chained(third, third_patch)
        self.assertEqual(self.snapshot(), before)

    def test_chained_receipt_identity_or_hash_mismatch_rejects_every_write(self):
        third, third_patch = self.prepare_chained_transition()
        path = self.checkout / transition.RECEIPT
        valid = json.loads(path.read_text())
        for field, value in [('schema', 2), ('revision', '0' * 40),
                             ('implementation_commit', '4' * 40),
                             ('source_commit', None), ('old_patch_sha256', 'invalid'),
                             ('new_patch_sha256', '0' * 64)]:
            with self.subTest(field=field):
                path.write_text(json.dumps(dict(valid, **{field: value})))
                before = self.snapshot()
                with self.assertRaises(ValueError): self.apply_chained(third, third_patch)
                self.assertEqual(self.snapshot(), before)

    def test_chained_receipt_does_not_authorize_divergent_source(self):
        third, third_patch = self.prepare_chained_transition()
        (self.checkout / 'shared.txt').write_bytes(b'unsaved external edit\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Checkout input diverged'):
            self.apply_chained(third, third_patch)
        self.assertEqual(self.snapshot(), before)

    def test_chained_receipt_malformed_or_symlink_rejects_every_write(self):
        third, third_patch = self.prepare_chained_transition()
        path = self.checkout / transition.RECEIPT
        for value in [b'{broken', b'[]']:
            path.write_bytes(value)
            before = self.snapshot()
            with self.assertRaises(ValueError): self.apply_chained(third, third_patch)
            self.assertEqual(self.snapshot(), before)
        external = self.root / 'external-receipt'
        external.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(external)
        with self.assertRaises(ValueError): self.apply_chained(third, third_patch)
        self.assertEqual(external.read_bytes(), b'[]')

    def test_reuses_unchanged_inputs_restores_removed_behavior_and_creates_new_source(self):
        before = self.snapshot()
        self.apply()
        self.assertEqual((self.checkout / 'shared.txt').read_bytes(), b'new\n')
        self.assertEqual((self.checkout / 'old-only.txt').read_bytes(), b'original\n')
        self.assertFalse((self.checkout / 'obsolete.java').exists())
        self.assertEqual((self.checkout / 'newdir/new.java').read_bytes(), b'new source\n')
        self.assertEqual(self.snapshot()['unchanged.txt'], before['unchanged.txt'])
        receipt = json.loads((self.checkout / '.archium-transition.json').read_text())
        self.assertEqual(receipt['old_patch_sha256'], self.old['patch_sha256'])
        self.assertEqual(receipt['new_patch_sha256'], self.new['patch_sha256'])

    def test_originals_can_be_verified_directly_from_pinned_git_objects(self):
        transition.transition(self.checkout, self.old, self.new,
                              self.old_patch, self.new_patch)
        self.assertEqual((self.checkout / 'old-only.txt').read_bytes(), b'original\n')

    def test_wrong_original_checksum_rejects_every_write(self):
        (self.originals / 'old-only.txt').write_text('wrong pinned original\n')
        before = self.snapshot()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_divergent_source_rejects_every_write(self):
        (self.checkout / 'shared.txt').write_text('user edit\n')
        before = self.snapshot()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_removed_new_source_requires_exact_old_bytes(self):
        (self.checkout / 'obsolete.java').write_text('preserve user source\n')
        before = self.snapshot()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_wrong_revision_or_patch_hash_rejects_every_write(self):
        for field in ['revision', 'patch_sha256']:
            for manifest in [self.old, self.new]:
                saved = manifest[field]; manifest[field] = '0' * 64
                before = self.snapshot()
                with self.assertRaises(ValueError): self.apply()
                self.assertEqual(self.snapshot(), before)
                manifest[field] = saved

    def test_parent_and_leaf_symlinks_are_rejected(self):
        external = self.root / 'external'; external.mkdir()
        (self.checkout / 'newdir').symlink_to(external, target_is_directory=True)
        before = self.snapshot()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(self.snapshot(), before)
        (self.checkout / 'newdir').unlink()
        data = (self.checkout / 'shared.txt').read_bytes()
        (external / 'shared.txt').write_bytes(data)
        (self.checkout / 'shared.txt').unlink()
        (self.checkout / 'shared.txt').symlink_to(external / 'shared.txt')
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual((external / 'shared.txt').read_bytes(), data)

    def test_path_escape_rejected(self):
        self.new['originals']['../escape'] = None
        self.new['modified']['../escape'] = digest(b'bad')
        before = self.snapshot()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_patch_content_must_match_manifest_even_when_hash_is_valid(self):
        self.new_patch.write_text(self.new_patch.read_text().replace('new source', 'other source'))
        self.new['patch_sha256'] = digest(self.new_patch.read_bytes())
        before = self.snapshot()
        with self.assertRaises(ValueError): self.apply()
        self.assertEqual(self.snapshot(), before)

    def test_interruption_rolls_back_bytes_modes_and_timestamps(self):
        before = self.snapshot()
        original_write = transition._write_file
        count = 0
        def interrupt(*args):
            nonlocal count
            count += 1
            if count == 2: raise KeyboardInterrupt('interrupted mutation')
            return original_write(*args)
        with patch.object(transition, '_write_file', interrupt):
            with self.assertRaises(KeyboardInterrupt): self.apply()
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.checkout / '.archium-transition.json').exists())


if __name__ == '__main__':
    unittest.main()
