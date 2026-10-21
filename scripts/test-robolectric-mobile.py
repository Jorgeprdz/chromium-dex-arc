#!/usr/bin/env python3
"""Mobile chrome against Android views; Chromium host operations remain an explicit boundary."""
import argparse,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);cp=a.classpath_file.read_text().strip()
sources=[ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcMobileHomeView.java',ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcMobileControls.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcMobileControlsTest.java']
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(a.work),*map(str,sources)],check=True)
raise SystemExit(subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(a.work)+':'+cp,'org.junit.runner.JUnitCore','org.chromium.chrome.browser.arc.ArcMobileControlsTest']).returncode)
