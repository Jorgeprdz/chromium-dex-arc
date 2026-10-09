#!/usr/bin/env python3
"""Download and install the authorized Archium update after its exact run succeeds."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

REPO = "Jorgeprdz/chromium-dex-arc"
RUN = "37871846597"
COMMIT = "0a403f4cf72c74906aaf3a17eb7a8026f6d1dd38"
PACKAGE = "app.archium.android"
ARTIFACT = "Archium-for-Android-arm64"
APK = ARTIFACT + ".apk"


class CommandError(RuntimeError):
    def __init__(self, argv, message):
        self.argv = argv
        super().__init__(message)


def command(argv, timeout=300):
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        # Retain the executable for the existing retry classifier: GitHub timeouts retry;
        # signing/install timeouts do not become false success or bypass verification.
        raise CommandError(argv, "Command timed out: " + argv[0]) from error
    if result.returncode:
        raise CommandError(argv, (result.stdout + result.stderr).strip())
    return result.stdout


def verify_installed_apk(serial, expected_digest):
    paths = command(["adb", "-s", serial, "shell", "pm", "path", PACKAGE])
    bases = [line.removeprefix("package:").strip() for line in paths.splitlines()
             if line.startswith("package:") and line.endswith("/base.apk")]
    if len(bases) != 1 or not re.fullmatch(r"/data/app/[A-Za-z0-9_./~+=-]+/base\.apk", bases[0]):
        raise RuntimeError("Installed base APK path could not be verified")
    output = command(["adb", "-s", serial, "shell", "sha256sum", bases[0]])
    installed_digest = output.split()[0] if output.split() else ""
    if installed_digest != expected_digest:
        raise RuntimeError("Installed APK SHA256 does not match the successful run artifact")
    return bases[0], installed_digest


def process_run(run_id, state, serial, expected_commit, device_ip=None):
    state.mkdir(parents=True, exist_ok=True)
    run = json.loads(command(["gh", "run", "view", run_id, "--repo", REPO,
                              "--json", "status,conclusion,headSha"]))
    if run["headSha"] != expected_commit:
        raise RuntimeError("Unexpected build commit; update refused")
    if run["status"] != "completed":
        return "waiting_build"
    if run["conclusion"] != "success":
        raise RuntimeError("Build ended with " + str(run["conclusion"]))
    marker = state / "installed.json"
    if marker.exists():
        previous = json.loads(marker.read_text())
        if previous["commit"] == expected_commit and previous["serial"] == serial:
            try:
                verify_installed_apk(serial, previous["sha256"])
            except (CommandError, subprocess.TimeoutExpired):
                return "waiting_device"
            return "installed"

    artifact = state / "artifact"
    apk = artifact / APK
    sums = artifact / "SHA256SUMS"
    if not apk.is_file() or not sums.is_file():
        staging = Path(tempfile.mkdtemp(prefix="download-", dir=state))
        command(["gh", "run", "download", run_id, "--repo", REPO,
                 "--name", ARTIFACT, "--dir", str(staging)], timeout=1200)
        artifact.mkdir(exist_ok=True)
        for name in (APK, "SHA256SUMS"):
            shutil.copy2(staging / name, artifact / name)
    matches = [line.split()[0] for line in sums.read_text().splitlines()
               if len(line.split()) == 2 and Path(line.split()[1].lstrip("*")).name == APK]
    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    if matches != [digest]:
        raise RuntimeError("Artifact SHA256 verification failed")
    badging = command(["aapt", "dump", "badging", str(apk)])
    info = re.search(r"package: name='([^']+)' versionCode='(\d+)'", badging)
    if not info or info.group(1) != PACKAGE:
        raise RuntimeError("Unexpected APK package; update refused")
    version = info.group(2)
    signer = shutil.which("apksigner")
    if signer:
        command([signer, "verify", "--print-certs", str(apk)])
    else:
        java = str(Path(os.environ["JAVA_HOME"]) / "bin/java") if os.environ.get("JAVA_HOME") else "java"
        command([java, "-jar", "/opt/android-sdk/build-tools/37.0.0/lib/apksigner.jar",
                 "verify", "--print-certs", str(apk)])
    try:
        if command(["adb", "-s", serial, "get-state"]).strip() != "device":
            return "waiting_device"
    except (RuntimeError, subprocess.TimeoutExpired):
        if ":" in serial:
            try:
                command(["adb", "connect", serial])
            except (RuntimeError, subprocess.TimeoutExpired):
                pass
        return "waiting_device"
    manufacturer = command(["adb", "-s", serial, "shell", "getprop", "ro.product.manufacturer"])
    if manufacturer.strip().lower() != "samsung":
        raise RuntimeError("The authorized Samsung device is not connected")
    if device_ip:
        addresses = command(["adb", "-s", serial, "shell", "ip", "-o", "-4", "addr", "show", "wlan0"])
        if not re.search(r"\binet " + re.escape(device_ip) + r"/", addresses):
            raise RuntimeError("Connected device does not match the authorized IP")
    result = command(["adb", "-s", serial, "install", "-r", str(apk)])
    if "Success" not in result.splitlines():
        raise RuntimeError("ADB did not confirm installation")
    installed = command(["adb", "-s", serial, "shell", "dumpsys", "package", PACKAGE])
    if not re.search(r"\bversionCode=" + re.escape(version) + r"\b", installed):
        raise RuntimeError("Installed package version could not be verified")
    installed_apk, installed_digest = verify_installed_apk(serial, digest)
    marker.write_text(json.dumps({"run": run_id, "commit": expected_commit, "serial": serial,
                                 "package": PACKAGE, "versionCode": version,
                                 "sha256": digest, "apk": str(apk),
                                 "installedApk": installed_apk, "installedSha256": installed_digest,
                                 "installedAt": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
    return "installed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", default=RUN)
    parser.add_argument("--commit", default=COMMIT)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--device-ip")
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--interval", type=int, default=600)
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    if args.state_dir is None:
        args.state_dir = Path(__file__).resolve().parent / "archium-update" / args.run
    if not args.run.isdigit() or not re.fullmatch(r"[a-f0-9]{40}", args.commit) or args.interval < 10:
        parser.error("Invalid run, commit or interval")
    args.state_dir.mkdir(parents=True, exist_ok=True)
    with (args.state_dir / "update.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Update worker is already active")
        (args.state_dir / "update.pid").write_text(str(os.getpid()) + "\n")
        while True:
            fatal = False
            try:
                stage = process_run(args.run, args.state_dir, args.serial, args.commit, args.device_ip)
                detail = {"stage": stage}
            except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
                transient = isinstance(error, CommandError) and error.argv[0] == "gh"
                stage = "retrying" if transient else "error"
                detail = {"stage": stage, "error": str(error)}
                fatal = not transient
            detail["updatedAt"] = datetime.now(timezone.utc).isoformat()
            (args.state_dir / "status.json").write_text(json.dumps(detail, indent=2) + "\n")
            print(json.dumps(detail), flush=True)
            if fatal:
                raise SystemExit(1)
            if stage == "installed" or not args.wait:
                return
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
