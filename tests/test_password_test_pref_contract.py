"""Guard the pref contracts that failed in the real Android native test build.

Pinned testing_pref_service.h only forward-declares PrefRegistrySimple, and
password_manager_pref_names.h exposes clearing-undecryptable only off Android.
This is a source regression, not a replacement for compiling Chromium tests.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PasswordTestPrefContract(unittest.TestCase):
    def sources(self):
        return list((ROOT / 'chromium').rglob('*unittest.cc'))

    def test_pref_registry_calls_include_the_complete_registry_type(self):
        matches = 0
        for source in self.sources():
            text = source.read_text()
            if re.search(r'registry\(\)\s*->\s*Register', text):
                matches += 1
                with self.subTest(source=str(source.relative_to(ROOT))):
                    self.assertTrue(
                        '#include "components/prefs/pref_registry_simple.h"' in text,
                        'Registry calls need the complete PrefRegistrySimple definition')
        self.assertGreater(matches, 0)

    def test_desktop_only_clearing_pref_is_not_registered_on_android(self):
        matches = 0
        for source in self.sources():
            guards = []
            for line in source.read_text().splitlines():
                directive = re.match(r'\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)', line)
                if directive:
                    kind, expression = directive.groups()
                    if kind in ('if', 'ifdef', 'ifndef'):
                        guards.append((kind, expression.strip()))
                    elif kind in ('elif', 'else') and guards:
                        guards[-1] = (kind, expression.strip())
                    elif kind == 'endif' and guards:
                        guards.pop()
                if 'prefs::kClearingUndecryptablePasswords' in line:
                    matches += 1
                    with self.subTest(source=str(source.relative_to(ROOT)), line=line):
                        self.assertIn(('if', '!BUILDFLAG(IS_ANDROID)'), guards)
        self.assertGreater(matches, 0)


if __name__ == '__main__':
    unittest.main()
