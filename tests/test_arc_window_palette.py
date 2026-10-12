"""Execute production palette/contrast policy on JVM; no rendered-window claim."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ArcWindowPaletteTest(unittest.TestCase):
    def test_custom_palette_remains_visible_and_accessible(self):
        spec = importlib.util.spec_from_file_location(
            'window_core', ROOT / 'scripts/fetch-window-core.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        jar = module.ensure_jar()
        sources = list((ROOT / 'chromium').rglob('ArcDesktopPolicy.java'))
        sources += list((ROOT / 'chromium').rglob('ArchiumWindowClass.java'))
        sources += [ROOT / 'tests/java/ArcDesktopPolicyTest.java']
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(['javac', '-cp', str(jar), '-d', directory,
                *map(str, sources)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(['java', '-ea', '-cp', directory,
                'ArcDesktopPolicyTest'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
