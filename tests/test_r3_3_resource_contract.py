"""R3.3 R-01: executed typed synthetic-R resource gate; not native Chromium."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-arc-preparation.py'
XML = ROOT / 'chromium/chrome/android/java/res/values/arc_strings.xml'


def load():
    spec = importlib.util.spec_from_file_location('arc_preparation', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SyntheticRContractTests(unittest.TestCase):
    def test_compiles_real_picker_array_and_new_tab_references(self):
        if not shutil.which('javac') or not shutil.which('java'):
            self.skipTest('javac/java unavailable')
        body = load().synthetic_chromium_r(XML)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r_path = root / 'org/chromium/chrome/R.java'
            r_path.parent.mkdir(parents=True)
            r_path.write_text('package org.chromium.chrome;\n' + body + '\n')
            (root / 'Probe.java').write_text("""import org.chromium.chrome.R;
public class Probe {
    public static void main(String[] args) {
        if (R.id.new_tab_button == 0 ||
            R.array.arc_frame_palette_names == 0 ||
            R.array.arc_frame_rgb_names == 0 ||
            R.string.arc_frame_color == 0) throw new AssertionError();
    }
}
""")
            subprocess.run(['javac', '-d', str(root), str(r_path),
                            str(root / 'Probe.java')], check=True, capture_output=True)
            subprocess.run(['java', '-cp', str(root), 'Probe'],
                           check=True, capture_output=True)

    def test_arrays_are_not_misdeclared_as_strings(self):
        body = load().synthetic_chromium_r(XML)
        string_body = body.split('class string {', 1)[1].split('}', 1)[0]
        self.assertNotIn('arc_frame_palette_names', string_body)
        self.assertNotIn('arc_frame_rgb_names', string_body)

    def test_fails_closed_when_required_array_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'broken.xml'
            path.write_text('<resources><string-array name="arc_frame_palette_names"/></resources>')
            with self.assertRaisesRegex(ValueError, 'arc_frame_rgb_names'):
                load().synthetic_chromium_r(path)

    def test_pinned_rail_references_real_new_tab_id(self):
        path = ROOT / '.source-reference/chrome/android/features/tab_ui/java/src/' \
               'org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabRailLayout.java'
        self.assertIn('findViewById(R.id.new_tab_button)', path.read_text())

    def test_rejects_duplicate_string_names_within_string_namespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'duplicates.xml'
            path.write_text('<resources><string name="duplicate"/><string name="duplicate"/>'
                            '<string-array name="arc_frame_palette_names"/>'
                            '<string-array name="arc_frame_rgb_names"/></resources>')
            with self.assertRaisesRegex(ValueError, 'Duplicate Android resource'):
                load().synthetic_chromium_r(path)

    def test_rejects_duplicate_array_names_across_array_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'duplicates.xml'
            path.write_text('<resources><string-array name="arc_frame_palette_names"/>'
                            '<integer-array name="arc_frame_palette_names"/>'
                            '<string-array name="arc_frame_rgb_names"/></resources>')
            with self.assertRaisesRegex(ValueError, 'Duplicate Android resource'):
                load().synthetic_chromium_r(path)

    def test_allows_same_name_in_different_namespaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'valid.xml'
            path.write_text('<resources><string name="arc_frame_palette_names"/>'
                            '<string-array name="arc_frame_palette_names"/>'
                            '<string-array name="arc_frame_rgb_names"/></resources>')
            body = load().synthetic_chromium_r(path)
            self.assertIn('class string {', body)
            self.assertIn('class array {', body)


if __name__ == '__main__':
    unittest.main()
