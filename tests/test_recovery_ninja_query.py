"""Execute the recovery query with genuine Ninja on a tiny Siso-marked graph.

Other native/CI commands use existing routing boundaries. The PATH wrapper
models its observed rejection; only the pinned-path query is genuine Ninja.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RecoveryNinjaQueryTests(unittest.TestCase):
    def fixture(self, include_target=True):
        spec = importlib.util.spec_from_file_location('query_routing_fixture',
            ROOT / 'tests/test_recovery_build_routing.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        case = module.RecoveryBuildRoutingTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        result = case.build('--prepare')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        src = case.root / 'runner/chromium-archium/checkout/src'
        out = src / 'out/Archium'
        ninja = src / 'third_party/ninja/ninja'
        real_ninja = os.environ.get('ARCHIUM_TEST_NINJA') or shutil.which('ninja')
        self.assertTrue(real_ninja, 'Genuine Ninja is required; no skip or fallback')
        ninja.unlink()  # Disposable command fixture, never an actual Chromium output.
        ninja.symlink_to(real_ninja)
        graph = 'rule forbidden\n  command = touch unexpected-compilation\n'
        graph += 'build library.so: forbidden input.cc\n'
        if include_target:
            graph += 'build archium_password_manager_tests: phony library.so\n'
        (out / 'build.ninja').write_text(graph)
        for name in ('.siso_deps', '.ninja_log', '.ninja_deps', 'input.cc'):
            (out / name).write_bytes(b'preserved incremental fixture\n')
        return case, out

    def test_siso_query_uses_pinned_binary_without_writing_incremental_state(self):
        case, out = self.fixture()
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in out.iterdir() if p.is_file()}
        result = case.build('--work', REJECT_SISO_WRAPPER='1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        query = (case.root / 'runner/archium-native-query.txt').read_text()
        self.assertIn('archium_password_manager_tests:', query)
        self.assertIn('library.so', query)
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                                 for p in out.iterdir() if p.is_file() and p.name in before})
        self.assertFalse((out / 'unexpected-compilation').exists())

    def test_real_gn_manifest_can_be_queried_without_touching_siso_logs(self):
        gn = os.environ.get('ARCHIUM_TEST_GN') or shutil.which('gn')
        ninja = os.environ.get('ARCHIUM_TEST_NINJA') or shutil.which('ninja')
        self.assertTrue(gn and ninja, 'Real GN and Ninja required; no skip')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.gn').write_text('buildconfig = "//BUILDCONFIG.gn"\n')
            (root / 'BUILDCONFIG.gn').write_text('set_default_toolchain("//:default")\n')
            (root / 'BUILD.gn').write_text('toolchain("default") { tool("stamp") { command = "touch {{output}}" } }\ngroup("archium_password_manager_tests") { }\n')
            result = subprocess.run([gn, 'gen', 'out'], cwd=root, text=True,
                                    capture_output=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            out = root / 'out'
            states = [out / name for name in ('.siso_deps', '.ninja_log', '.ninja_deps')]
            for state in states:
                state.write_bytes(b'original recovery state\n')
            before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in states]
            report = root / 'query.txt'
            result = subprocess.run(['python3', str(ROOT / 'scripts/archium-ninja-query.py'),
                '--out', str(out), '--ninja', ninja,
                '--target', 'archium_password_manager_tests', '--report', str(report)],
                text=True, capture_output=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('archium_password_manager_tests:', report.read_text())
            self.assertEqual(before, [(p.read_bytes(), p.stat().st_mtime_ns) for p in states])

    def test_manifest_cannot_redirect_logs_or_includes_outside_snapshot(self):
        spec = importlib.util.spec_from_file_location('isolated_query',
            ROOT / 'scripts/archium-ninja-query.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / 'out'; out.mkdir()
            log = out / '.ninja_log'; log.write_bytes(b'preserved\n')
            before = (log.read_bytes(), log.stat().st_mtime_ns)
            for directive in ('builddir = ../out', 'include ../external.ninja'):
                with self.subTest(directive=directive):
                    (out / 'build.ninja').write_text(directive + '\n')
                    with self.assertRaises(ValueError):
                        module.query(out, Path('/nonexistent/ninja'), 'target', root / 'report')
                    self.assertEqual(before, (log.read_bytes(), log.stat().st_mtime_ns))
                    self.assertFalse((root / 'report').exists())

    def test_query_failure_stops_fanout_and_requests_quiescent_checkpoint(self):
        case, out = self.fixture(include_target=False)
        result = case.build('--work', REJECT_SISO_WRAPPER='1')
        case.assert_blocked(result, 1)
        self.assertIn('unknown target', result.stderr)
        self.assertTrue(any('pack' in call for call in case.calls()))
        self.assertFalse(any('archium_key_provider_tests' in call for call in case.targets()))
        self.assertFalse((out / 'unexpected-compilation').exists())
