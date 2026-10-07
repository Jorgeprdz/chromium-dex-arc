"""Guard Archium's raw JNI local references against Chromium 157's private ctor.

Pinned java_refs.h exposes Adopt(env, obj) for ownership transfer; the raw
ScopedJavaLocalRef(env, jobject) constructor is private. Empty RAII refs and
construction from JavaRef remain valid. This is a source contract, not a native
Chromium build or a JVM lifetime test.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PasswordBridgeJniOwnershipTest(unittest.TestCase):
    def test_archium_raw_local_refs_do_not_use_private_constructor(self):
        incompatible = re.compile(
            r'\bScopedJavaLocalRef\s*<[^>]+>\s*'
            r'(?:\w+\s*)?[({]\s*env\s*,')
        sources = list((ROOT / 'chromium').rglob('*.cc'))
        self.assertTrue(sources)
        for source in sources:
            with self.subTest(source=source.relative_to(ROOT).as_posix()):
                self.assertIsNone(
                    incompatible.search(source.read_text()),
                    'Use the public Adopt API for raw JNI local references; '
                    'Chromium 157 makes the ownership constructor private.')


if __name__ == '__main__':
    unittest.main()
