"""Monitor presentation and post-build update behavior at external command boundaries."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SHA = "0a403f4cf72c74906aaf3a17eb7a8026f6d1dd38"
SERIAL = "192.168.101.105:42437"


def load(name):
    path = ROOT / "scripts/monitoring" / name
    if not path.is_file():
        raise AssertionError("Automatic post-build updater is not implemented")
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompactMonitorTest(unittest.TestCase):
    def test_completed_run_duration_stops_at_last_job_completion(self):
        module = load("monitor-archium-run.py")
        run = {"id": 37905612954, "created_at": "2026-10-09T08:32:46Z",
               "status": "completed", "html_url": "https://example.com/run"}
        jobs = [{"name": "stage1", "status": "completed", "completed_at": "2026-10-09T09:40:42Z"},
                {"name": "stage2", "status": "completed", "completed_at": None}]
        now = datetime(2026, 10, 9, 13, 0, tzinfo=timezone.utc)
        for conclusion in ("failure", "success", "cancelled"):
            with self.subTest(conclusion=conclusion):
                run["conclusion"] = conclusion
                output, _ = module.describe(run, jobs, now)
                self.assertIn("Tiempo transcurrido: 1 h 7 min", output)
        jobs.append({"name": "cleanup", "status": "completed", "completed_at": "2026-10-09T09:42:46Z"})
        output, _ = module.describe(run, jobs, now)
        self.assertIn("Tiempo transcurrido: 1 h 10 min", output)

    def test_running_run_duration_continues_after_finished_job(self):
        module = load("monitor-archium-run.py")
        run = {"id": 1, "created_at": "2026-10-09T08:00:00Z", "status": "in_progress",
               "html_url": "https://example.com/run"}
        jobs = [{"name": "stage1", "status": "completed", "completed_at": "2026-10-09T09:00:00Z"}]
        output, _ = module.describe(run, jobs, datetime(2026, 10, 9, 9, 30, tzinfo=timezone.utc))
        self.assertIn("Tiempo transcurrido: 1 h 30 min", output)

    def test_completed_run_without_job_timestamps_uses_run_finish_timestamp(self):
        module = load("monitor-archium-run.py")
        run = {"id": 1, "created_at": "2026-10-09T08:00:00Z", "status": "completed",
               "updated_at": "2026-10-09T08:30:00Z", "html_url": "https://example.com/run"}
        output, _ = module.describe(run, [], datetime(2026, 10, 9, 13, tzinfo=timezone.utc))
        self.assertIn("Tiempo transcurrido: 0 h 30 min", output)

    def test_compact_panel_has_continuous_borders_and_ten_minute_refresh(self):
        module = load("monitor-archium-run.py")
        text = "Actualizado: 2026-10-09 02:34 UTC\nRun 37871846597: in_progress\nTiempo transcurrido: 0 h 42 min\nEtapa actual: stage1 / build\nPaso: Compile, run gates and checkpoint\nJobs terminados: 0\nUltimos eventos:\nold event"
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            output = module.ascii_window(text)
        self.assertIn("┌", output)
        self.assertIn("─", output)
        self.assertIn("10 min", output)
        self.assertIn("Compilación y pruebas", output)
        self.assertNotIn("ULTIMAS NOVEDADES", output)
        self.assertNotIn("Porcentaje Ninja", output)
        self.assertNotIn("old event", output)
        self.assertLessEqual(len(output.splitlines()), 13)

    def test_connection_error_stays_visible_in_compact_panel(self):
        module = load("monitor-archium-run.py")
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            output = module.ascii_window("Actualizado: hoy\nNo se pudo consultar GitHub.\nHTTP Error 403\n\nUltimos eventos:\nold event")
        self.assertIn("HTTP Error 403", output)
        self.assertIn("Sin conexión", output)

    def test_monitor_uses_authenticated_cli_when_available(self):
        module = load("monitor-archium-run.py")
        payload = '{"status":"in_progress","id":37871846597}'
        import subprocess
        with patch.object(module.shutil, "which", return_value="/usr/bin/gh"), \
             patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess(
                 ["gh"], 0, stdout=payload, stderr="")) as request, \
             patch.object(module.urllib.request, "urlopen", side_effect=AssertionError("Public API must not be used")):
            result = module.get_json("repos/Jorgeprdz/chromium-dex-arc/actions/runs/37871846597")
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(request.call_args.args[0], [
            "gh", "api", "repos/Jorgeprdz/chromium-dex-arc/actions/runs/37871846597"])


class PostBuildUpdateTest(unittest.TestCase):
    def exercise(self, *, status="completed", conclusion="success", sha=SHA,
                 checksum=None, connected=True, package="app.archium.android",
                 signature_ok=True, device_ip=None, installed_hash=None, connect_raises=False):
        module = load("update-archium-run.py")
        self.calls = []
        self.tmp = tempfile.TemporaryDirectory(prefix="arc-update-test-")
        self.addCleanup(self.tmp.cleanup)
        state = Path(self.tmp.name)

        def command(argv, **kwargs):
            self.calls.append(argv)
            if argv[:3] == ["gh", "run", "view"]:
                return json.dumps({"status": status, "conclusion": conclusion, "headSha": sha})
            if argv[:3] == ["gh", "run", "download"]:
                destination = Path(argv[argv.index("--dir") + 1])
                destination.mkdir(parents=True, exist_ok=True)
                apk = destination / "Archium-for-Android-arm64.apk"
                apk.write_bytes(b"fixture APK at the external signer boundary")
                digest = checksum or hashlib.sha256(apk.read_bytes()).hexdigest()
                (destination / "SHA256SUMS").write_text(digest + "  /runner/archium-output/" + apk.name + "\n")
                return ""
            if argv[:3] == ["aapt", "dump", "badging"]:
                return f"package: name='{package}' versionCode='4242' versionName='test'\n"
            if "verify" in argv:
                if not signature_ok:
                    raise RuntimeError("APK signature verification failed")
                return "Verified\n"
            if argv == ["adb", "connect", SERIAL]:
                if connect_raises:
                    raise module.CommandError(argv,"failed to connect: device offline")
                return "connected" if connected else "failed to connect"
            if argv[:3] == ["adb", "-s", SERIAL]:
                if argv[3:] == ["get-state"]:
                    if not connected:
                        raise RuntimeError("device offline")
                    return "device\n"
                if argv[3:] == ["shell", "getprop", "ro.product.manufacturer"]:
                    return "samsung\n"
                if argv[3:] == ["shell", "ip", "-o", "-4", "addr", "show", "wlan0"]:
                    return "45: wlan0 inet 192.168.101.105/24\n"
                if argv[3:5] == ["install", "-r"]:
                    return "Success\n"
                if argv[3:] == ["shell", "dumpsys", "package", "app.archium.android"]:
                    return "versionCode=4242 minSdk=29\n"
                if argv[3:] == ["shell", "pm", "path", "app.archium.android"]:
                    return "package:/data/app/test/base.apk\n"
                if argv[3:] == ["shell", "sha256sum", "/data/app/test/base.apk"]:
                    digest=installed_hash or hashlib.sha256(b"fixture APK at the external signer boundary").hexdigest()
                    return digest+"  /data/app/test/base.apk\n"
            raise AssertionError("Unexpected external command: " + repr(argv))

        with patch.object(module, "command", side_effect=command):
            result = module.process_run("37871846597", state, SERIAL, SHA, device_ip)
        return result, state

    def test_running_build_does_not_download_or_install(self):
        result, _ = self.exercise(status="in_progress", conclusion="")
        self.assertEqual(result, "waiting_build")
        self.assertEqual(len(self.calls), 1)

    def test_failed_build_never_installs(self):
        with self.assertRaisesRegex(RuntimeError, "failure"):
            self.exercise(conclusion="failure")
        self.assertFalse(any("install" in call for call in self.calls))

    def test_wrong_commit_never_downloads(self):
        with self.assertRaisesRegex(RuntimeError, "commit"):
            self.exercise(sha="f" * 40)
        self.assertEqual(len(self.calls), 1)

    def test_corrupted_artifact_never_reaches_device(self):
        with self.assertRaisesRegex(RuntimeError, "SHA256"):
            self.exercise(checksum="0" * 64)
        self.assertFalse(any(call[0] == "adb" for call in self.calls))

    def test_success_preserves_data_and_records_verified_install(self):
        result, state = self.exercise()
        self.assertEqual(result, "installed")
        install = next(call for call in self.calls if "install" in call)
        self.assertEqual(install[:5], ["adb", "-s", SERIAL, "install", "-r"])
        self.assertNotIn("-d", install)
        self.assertFalse(any("uninstall" in call for call in self.calls))
        evidence = json.loads((state / "installed.json").read_text())
        self.assertEqual(evidence["serial"], SERIAL)
        self.assertEqual(evidence["commit"], SHA)
        self.assertEqual(evidence["versionCode"], "4242")
        self.assertEqual(evidence["installedSha256"], evidence["sha256"])
        self.assertEqual(evidence["installedApk"], "/data/app/test/base.apk")

    def test_same_version_with_wrong_installed_apk_is_not_confirmed(self):
        with self.assertRaisesRegex(RuntimeError, "Installed APK SHA256"):
            self.exercise(installed_hash="0"*64)

    def test_monitor_shows_verified_installation_in_compact_panel(self):
        module=load("monitor-archium-run.py")
        output=module.ascii_window("Actualizado: hoy\nRun 123: completed success\nInstalación: CONFIRMADA\nTiempo transcurrido: 1 h 36 min")
        self.assertIn("Instalación: CONFIRMADA",output)

    def test_offline_device_keeps_download_for_later(self):
        result, state = self.exercise(connected=False)
        self.assertEqual(result, "waiting_device")
        self.assertTrue((state / "artifact/Archium-for-Android-arm64.apk").is_file())
        self.assertFalse(any("install" in call for call in self.calls))

    def test_failed_device_reconnect_keeps_worker_waiting(self):
        result,state=self.exercise(connected=False,connect_raises=True)
        self.assertEqual(result,"waiting_device")
        self.assertTrue((state/"artifact/Archium-for-Android-arm64.apk").is_file())
        self.assertFalse(any("install" in call for call in self.calls))

    def test_github_timeout_retains_command_context_for_retry(self):
        import subprocess
        module=load("update-archium-run.py")
        request=["gh","run","view","123"]
        with patch.object(module.subprocess,"run",side_effect=subprocess.TimeoutExpired(request,10)):
            with self.assertRaises(module.CommandError) as error:
                module.command(request,timeout=10)
        self.assertEqual(error.exception.argv,request)

    def test_wrong_package_is_rejected_before_device_access(self):
        with self.assertRaisesRegex(RuntimeError, "package"):
            self.exercise(package="unrelated.app")
        self.assertFalse(any(call[0] == "adb" for call in self.calls))

    def test_invalid_signature_is_rejected_before_device_access(self):
        with self.assertRaisesRegex(RuntimeError, "signature"):
            self.exercise(signature_ok=False)
        self.assertFalse(any(call[0] == "adb" for call in self.calls))

    def test_wrong_device_network_is_rejected_before_install(self):
        with self.assertRaisesRegex(RuntimeError, "authorized IP"):
            self.exercise(device_ip="192.168.101.9")
        self.assertFalse(any("install" in call for call in self.calls))
