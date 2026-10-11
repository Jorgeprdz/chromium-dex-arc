"""SDK37 AAPT2 dump linked with the exact pinned Chromium namespace flags."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from archium_portal_content_gate import portal_module, verify_themed_vector


class NamespaceStrippingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiled = (ROOT / 'tests/fixtures/portal/themed-vector-sdk37-no-namespaces.xmltree.txt').read_text()
        portal = portal_module()
        cls.source = portal.expected_resources()[f'{portal.BASE}/drawable/themed_app_icon.xml']

    def test_approved_vector_after_real_chromium_namespace_stripping(self):
        try:
            verify_themed_vector(self.compiled, self.source)
        except ValueError as error:
            self.fail('Approved SDK37 Chromium-linked vector rejected: ' + str(error))

    def test_approved_vector_with_namespaces_and_real_framework_ids(self):
        verify_themed_vector(self.compiled.replace('A: ', 'A: android:'), self.source)

    def test_app_owned_attribute_cannot_impersonate_android_scale(self):
        with self.assertRaisesRegex(ValueError, 'Themed glyph'):
            verify_themed_vector(self.compiled.replace('scaleX(0x01010324)', 'scaleX(0x7f010324)'), self.source)

    def test_namespace_prefix_does_not_override_a_foreign_attribute_id(self):
        qualified = self.compiled.replace('A: ', 'A: android:')
        with self.assertRaisesRegex(ValueError, 'Themed glyph'):
            verify_themed_vector(qualified.replace('scaleX(0x01010324)', 'scaleX(0x7f010324)'), self.source)

    def test_unidentified_extra_attribute_is_not_silently_ignored(self):
        qualified = self.compiled.replace('A: ', 'A: android:')
        with self.assertRaisesRegex(ValueError, 'Themed glyph'):
            verify_themed_vector(qualified + '\n          A: forgedFlag=true', self.source)

    def test_framework_attribute_id_must_match_its_name(self):
        with self.assertRaisesRegex(ValueError, 'Themed glyph'):
            verify_themed_vector(self.compiled.replace('scaleX(0x01010324)', 'scaleX(0x01010325)'), self.source)

    def test_foreign_namespace_cannot_impersonate_android_attribute(self):
        with self.assertRaisesRegex(ValueError, 'Themed glyph'):
            verify_themed_vector(self.compiled.replace('A: scaleX', 'A: foreign:scaleX'), self.source)

    def test_altered_path_still_fails_without_namespaces(self):
        with self.assertRaisesRegex(ValueError, 'Themed glyph'):
            verify_themed_vector(self.compiled.replace('M 177 760 C 213 643', 'M 0 0 C 213 643'), self.source)

    def test_altered_scale_still_fails_without_namespaces(self):
        with self.assertRaisesRegex(ValueError, 'Themed glyph'):
            verify_themed_vector(self.compiled.replace('scaleX(0x01010324)=0.65', 'scaleX(0x01010324)=1'), self.source)

if __name__ == '__main__':
    unittest.main()
