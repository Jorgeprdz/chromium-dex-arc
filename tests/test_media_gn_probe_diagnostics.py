"""Injected GN errors must surface diagnostic evidence; never certify mock GN as real."""
import tempfile
from pathlib import Path
import unittest
from unittest import mock
import media_gn_probe as probe


class MediaGNProbeDiagnosticsTests(unittest.TestCase):
    def test_gn_exit_two_keeps_stderr_and_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            fixture = base / 'fixture'; fixture.mkdir()
            (fixture / 'BUILDCONFIG.synthetic.gn').write_text('set_default_toolchain("//:default")\n')
            gn = base / 'gn'
            gn.write_text('#!/bin/sh\n'
                          'if [ "$1" = "--version" ]; then echo pinned-mock-123; exit 0; fi\n'
                          'echo "SYNTHETIC BAD TOOLCHAIN" >&2\nexit 2\n')
            gn.chmod(0o755)
            diagnostics = base / 'diagnostics'
            with mock.patch.object(probe, 'GN', str(gn)), \
                 mock.patch.object(probe, 'FIXTURES', fixture), \
                 mock.patch.dict('os.environ', {'ARCHIUM_GN_DIAGNOSTICS_DIR': str(diagnostics)}):
                with self.assertRaises(RuntimeError) as caught:
                    probe.evaluate('target_os = "android"\n')
            error = str(caught.exception)
            for expected in ('GN_MEDIA_FIXTURE_FAILED code=2', 'stderr:',
                             'SYNTHETIC BAD TOOLCHAIN', 'pinned-mock-123',
                             'diagnostic_bundle=', 'command=', 'cwd='):
                self.assertIn(expected, error)
            bundles = list(diagnostics.glob('media-gn-failure-*/fixture'))
            self.assertEqual(len(bundles), 1)
            self.assertTrue((bundles[0] / 'out/args.gn').is_file())
            self.assertTrue((bundles[0] / '.gn').is_file())

    def test_missing_gn_fails_closed(self):
        with mock.patch.object(probe, 'GN', None):
            with self.assertRaisesRegex(RuntimeError, 'Real GN is required'):
                probe.evaluate('')
