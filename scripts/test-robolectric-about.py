#!/usr/bin/env python3
"""Execute the real About dialog with Android package/resource boundaries."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--classpath-file', type=Path, required=True)
parser.add_argument('--java-home', type=Path, required=True)
parser.add_argument('--work', type=Path, required=True)
args = parser.parse_args()
classes = args.work / 'classes'
classes.mkdir(parents=True, exist_ok=True)
cp = args.classpath_file.read_text().strip()
sources = [ROOT / ('chromium/chrome/android/' + path) for path in (
    'java/src/org/chromium/chrome/browser/arc/ArcAboutDialog.java',
    'junit/src/org/chromium/chrome/browser/arc/ArcAboutDialogTest.java')]
subprocess.run([str(args.java_home / 'bin/javac'), '-cp', cp, '-d', str(classes),
                *map(str, sources)], check=True)
raise SystemExit(subprocess.run([
    str(args.java_home / 'bin/java'), '-ea', '-Drobolectric.conscryptMode=OFF',
    '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
    '-cp', str(classes) + ':' + cp, 'org.junit.runner.JUnitCore',
    'org.chromium.chrome.browser.arc.ArcAboutDialogTest']).returncode)
