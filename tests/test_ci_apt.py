"""Runner package sources must avoid the stalled mirror without weakening trust."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CiAptTests(unittest.TestCase):
    def test_normalizes_both_mirror_list_and_deb822_without_changing_trust(self):
        spec = importlib.util.spec_from_file_location(
            'ci_apt', ROOT / 'scripts/configure-archium-apt.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            apt = Path(temporary)
            (apt / 'sources.list.d').mkdir()
            (apt / 'apt.conf.d').mkdir()
            mirror = apt / 'apt-mirrors.txt'
            mirror.write_text('http://azure.archive.ubuntu.com/ubuntu/\n')
            sources = apt / 'sources.list.d/ubuntu.sources'
            sources.write_text(
                'Types: deb\nURIs: http://azure.archive.ubuntu.com/ubuntu\n'
                'Suites: noble noble-updates\nComponents: main universe\n'
                'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n')
            third_party = apt / 'sources.list.d/vendor.list'
            third_party.write_text('deb https://vendor.example/ubuntu noble main\n')
            module.configure(apt)
            self.assertEqual(mirror.read_text(), 'https://archive.ubuntu.com/ubuntu/\n')
            self.assertEqual(sources.read_text(),
                'Types: deb\nURIs: https://archive.ubuntu.com/ubuntu\n'
                'Suites: noble noble-updates\nComponents: main universe\n'
                'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n')
            self.assertEqual(third_party.read_text(),
                             'deb https://vendor.example/ubuntu noble main\n')
            before = {p: p.read_bytes() for p in apt.rglob('*') if p.is_file()}
            module.configure(apt)
            self.assertEqual(before, {p: p.read_bytes() for p in apt.rglob('*') if p.is_file()})

    def test_cli_refuses_to_change_the_host_outside_ci(self):
        import os
        import subprocess
        result = subprocess.run(
            ['python3', str(ROOT / 'scripts/configure-archium-apt.py')],
            env={**os.environ, 'GITHUB_ACTIONS': 'false'},
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('dedicated GitHub Actions', result.stderr)
