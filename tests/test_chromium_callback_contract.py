"""Guard the real BindOnce/BindRepeating contract in delivered native sources.

Pinned Chromium bind_internal.h rejects stateful functors, including capturing
lambdas. Captures used by gmock, standard algorithms or BindLambdaForTesting
are separate contracts and are deliberately outside this check.
This source regression does not replace compiling or running native tests.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ChromiumCallbackContract(unittest.TestCase):
    def test_direct_base_bind_callbacks_are_stateless(self):
        sources = []
        for tree in ('chromium', '.source-modified'):
            sources.extend((ROOT / tree).rglob('*.cc'))
        self.assertTrue(sources, 'No delivered native sources inspected')
        binding = re.compile(r'base::Bind(?:Once|Repeating)\s*\(\s*\[([^\]]*)\]')
        callbacks = 0
        for source in sources:
            text = source.read_text()
            for match in binding.finditer(text):
                callbacks += 1
                line = text.count('\n', 0, match.start()) + 1
                with self.subTest(source=str(source.relative_to(ROOT)), line=line):
                    self.assertEqual(match.group(1).strip(), '',
                                     'Bind arguments explicitly; base::Bind rejects captures')
        self.assertGreater(callbacks, 0, 'No direct lambda bindings inspected')


if __name__ == '__main__':
    unittest.main()
