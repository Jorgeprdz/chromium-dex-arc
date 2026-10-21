#!/usr/bin/env python3
"""Complete appearance preference suite on Android shadows; window metrics adapter."""
import argparse, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args()
a.work.mkdir(parents=True,exist_ok=True);classes=a.work/'classes';classes.mkdir(exist_ok=True)
metrics=a.work/'ArchiumWindowMetrics.java';metrics.write_text('package org.chromium.chrome.browser.desktop_policy; public class ArchiumWindowMetrics {public static int currentWidthDp(android.content.Context c){return c.getResources().getConfiguration().screenWidthDp;}}')
sources=[metrics,*ROOT.glob('chromium/**/ArcDesktopAppearance.java'),*ROOT.glob('chromium/**/ArcDesktopPolicy.java'),*ROOT.glob('chromium/**/ArchiumWindowClass.java'),*ROOT.glob('chromium/**/ArcDesktopAppearanceTest.java')]
cp=a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,sources)],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearanceTest'])
raise SystemExit(r.returncode)
