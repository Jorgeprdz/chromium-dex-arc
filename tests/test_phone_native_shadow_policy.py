"""Fail preflight before restoration if the delivered phone test adds application shadows."""
from pathlib import Path
import hashlib
import unittest
ROOT = Path(__file__).resolve().parents[1]
class PhoneNativeShadowPolicyTests(unittest.TestCase):
    def test_phone_suite_uses_explicit_boundaries_instead_of_application_shadows(self):
        source = (ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcPhoneNavigationTest.java').read_text()
        # This suite needs no custom shadows, so forbid the declaration rather than maintaining
        # a separate relaxed allowlist. The JVM runner also runs Chromium's actual checker.
        self.assertNotIn('@Implements(', source)
        self.assertNotIn('shadows=', source.replace(' ', ''))
        self.assertGreaterEqual(source.count('@Test public void '), 28, 'Existing phone coverage must remain')
        glass = (ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcPhoneGlassTest.java').read_text()
        self.assertNotIn('@Implements(', glass)
        self.assertNotIn('shadows=', glass.replace(' ', ''))
        self.assertGreaterEqual(glass.count('@Test public void '), 5)
    def test_pinned_discovery_checker_is_not_relaxed(self):
        fixture = ROOT/'tests/fixtures/chromium-junit'
        import json
        manifest = json.loads((fixture/'pinned.json').read_text())
        self.assertEqual('cfd94726b7b5fb48aedcc32662f2f3fbdbadec35', manifest['revision'])
        for name, digest in manifest['sha256'].items():
            self.assertEqual(digest, hashlib.sha256((fixture/name).read_bytes()).hexdigest(), name)
        policy = (fixture/'shadows-allowlist.txt').read_text()
        self.assertIn('-org.chromium', policy)
        runner = (ROOT/'scripts/test-robolectric-phone-navigation.py').read_text()
        self.assertIn('PhoneNativeShadowPolicyProbe', runner)
