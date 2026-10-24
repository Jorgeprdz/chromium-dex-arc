"""Compile the delivered field against Android SDK with TYPE_USE nullability.

This catches annotation placement; it is not a full ToolbarManager compilation.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ToolbarTypeAnnotationTest(unittest.TestCase):
    def test_compact_animation_field_compiles_with_type_use_nullable(self):
        sdk = Path(os.environ.get('ARCHIUM_TEST_ANDROID_JAR',
                                  '/opt/android-sdk/platforms/android-37.0/android.jar'))
        self.assertTrue(sdk.is_file(), 'Android SDK android.jar required')
        source = (ROOT / '.source-modified/chrome/android/java/src/org/chromium/'
                  'chrome/browser/toolbar/ToolbarManager.java').read_text()
        field = re.search(r'^\s*private[^\n;]*\bmArcPhoneCompactAnimation\s*;',
                          source, re.M).group(0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            probe = root / 'AnimationFieldProbe.java'
            probe.write_text('import java.lang.annotation.*;\n'
                             '@Target(ElementType.TYPE_USE) @interface Nullable {}\n'
                             'class AnimationFieldProbe {\n' + field + '\n}\n')
            compiled = subprocess.run(['javac', '-cp', str(sdk), '-d', directory,
                                       str(probe)], capture_output=True, text=True)
            self.assertEqual(0, compiled.returncode, compiled.stdout + compiled.stderr)
