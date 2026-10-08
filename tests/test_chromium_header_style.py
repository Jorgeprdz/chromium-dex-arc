"""Source regression for the real Chromium 157 inline-virtual build failure.

FindBadConstructsConsumer::CheckVirtualBodies rejects nonempty inline virtual
bodies in headers. This scans our delivered headers; it is not an execution of
Chromium's Clang plugin or a replacement for the native build gate.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ChromiumHeaderStyleTests(unittest.TestCase):
    def test_delivered_headers_have_no_nonempty_inline_virtual_override(self):
        manifest = json.loads((ROOT / 'patches/upstream-files.json').read_text())
        forbidden = re.compile(
            r'(?:\b(?:override|final)\s*|\bvirtual\s+[^;{}]*?)'
            r'\{\s*(?!\})([^{}]+)\}', re.DOTALL)
        headers = [p for p in manifest['modified'] if p.endswith('.h')]
        self.assertTrue(headers)
        for name in headers:
            source = ROOT / ('chromium' if manifest['originals'][name] is None
                             else '.source-modified') / name
            with self.subTest(source=name):
                text = re.sub(r'/\*.*?\*/|//[^\n]*', '', source.read_text(),
                              flags=re.DOTALL)
                self.assertIsNone(forbidden.search(text),
                    'Chromium 157 requires nonempty virtual bodies out of line')


if __name__ == '__main__':
    unittest.main()
