import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from media_gn_probe import GN, ROOT, evaluate


def module():
    path = ROOT / 'scripts/archium-media-preflight.py'
    assert path.is_file(), 'Effective-media gate has not been implemented'
    spec = importlib.util.spec_from_file_location('archium_media_preflight', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipUnless(GN, 'Set ARCHIUM_TEST_GN to run the pinned real-GN characterization')
class PinnedMediaConfigurationTests(unittest.TestCase):
    def test_arm64_enables_native_media_and_preserves_open_codecs(self):
        values = module().parse_args(evaluate((ROOT / 'config/archium-args.gn').read_text()))
        self.assertEqual(module().issues(values), [])
        self.assertIs(values['enable_platform_hevc'], True)
        self.assertIs(values['enable_hls_demuxer'], True)
        self.assertIs(values['enable_widevine'], True)
        self.assertIs(values['enable_library_cdms'], False)

    def test_original_configuration_demonstrates_missing_formats(self):
        args = (ROOT / 'config/archium-args.gn').read_text()
        args = re.sub(r'^\s*(proprietary_codecs|ffmpeg_branding)\s*=.*$', '', args, flags=re.M)
        values = module().parse_args(evaluate(args))
        self.assertIs(values['proprietary_codecs'], False)
        self.assertEqual(values['ffmpeg_branding'], 'Chromium')
        self.assertIs(values['enable_hls_demuxer'], False)
        self.assertTrue(module().issues(values))

    def test_x64_uses_same_media_capabilities_and_package(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/archium-build-config.py'),
                                 '--target-cpu', 'x64'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = module().parse_args(evaluate(result.stdout))
        self.assertEqual(values['target_cpu'], 'x64')
        self.assertEqual(values['chrome_public_manifest_package'], 'app.archium.android')
        self.assertEqual(module().issues(values), [])


class EffectiveMediaGateTests(unittest.TestCase):
    def valid(self):
        return dict(target_os='android', target_cpu='arm64', proprietary_codecs=True,
                    ffmpeg_branding='Chrome', media_use_ffmpeg=True, media_use_libvpx=True,
                    enable_av1_decoder=True, enable_hls_demuxer=True,
                    enable_mse_mpeg2ts_stream_parser=True, enable_platform_hevc=True,
                    enable_widevine=True, enable_library_cdms=False,
                    is_chrome_branded=False, chrome_public_manifest_package='app.archium.android')

    def test_valid_platform_configuration_has_no_errors(self):
        self.assertEqual(module().issues(self.valid()), [])

    def test_missing_values_fail_closed(self):
        self.assertTrue(module().issues({}))
        values = self.valid(); del values['ffmpeg_branding']
        self.assertTrue(module().issues(values))

    def test_wrong_types_and_flavor_are_rejected(self):
        for key, value in [('proprietary_codecs', 'true'), ('ffmpeg_branding', 'Chromium'),
                           ('target_cpu', 'riscv64'), ('enable_av1_decoder', False),
                           ('is_chrome_branded', True)]:
            values = self.valid(); values[key] = value
            self.assertTrue(module().issues(values), (key, value))

    def test_gn_parser_ignores_comments_and_rejects_duplicate_values(self):
        m = module()
        self.assertEqual(m.parse_args('proprietary_codecs = true\n# ffmpeg_branding = "Chrome"\n'),
                         {'proprietary_codecs': True})
        with self.assertRaises(ValueError):
            m.parse_args('proprietary_codecs = true\nproprietary_codecs = false\n')
        with self.assertRaises(ValueError):
            m.parse_args('proprietary_codecs = maybe\n')

    def test_failed_gn_invocation_cannot_publish_pass_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            gn = Path(tmp) / 'gn'; gn.write_text('#!/bin/sh\nexit 7\n'); gn.chmod(0o755)
            report = Path(tmp) / 'report.json'; report.write_text('{"status":"PASS"}')
            r = subprocess.run([sys.executable, str(ROOT / 'scripts/archium-media-preflight.py'),
                                '--gn', str(gn), '--out', tmp, '--report', str(report)],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(json.loads(report.read_text())['status'], 'FAIL')


class ArchitectureConfigurationTests(unittest.TestCase):
    def test_default_render_preserves_common_configuration(self):
        r = subprocess.run([sys.executable, str(ROOT / 'scripts/archium-build-config.py')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, (ROOT / 'config/archium-args.gn').read_text())

    def test_unknown_architecture_never_creates_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'args.gn'
            r = subprocess.run([sys.executable, str(ROOT / 'scripts/archium-build-config.py'),
                                '--target-cpu', 'arm', '--output', str(output)],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(output.exists())
