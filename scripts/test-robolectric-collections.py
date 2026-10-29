#!/usr/bin/env python3
"""Complete collections views/state on Android; synthetic R and native-tab boundary."""
import argparse,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);classes=a.work/'classes';classes.mkdir(exist_ok=True)
arc=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
source=(arc/'ArcCollectionsView.java').read_text()
names=sorted(set(re.findall(r'R.string.(\w+)',source)))
r=a.work/'R.java';r.write_text('package org.chromium.chrome; public class R {public static class string {'+'\n'.join('public static final int '+n+'=android.R.string.ok;' for n in names)+'}}')
sources=[arc/(n+'.java') for n in ['ArcSidebarState','ArcSidebarStore','ArcTabActions','ArcCollectionsController','ArcCollectionsView']]
sources += [ROOT/'chromium/chrome/browser/desktop_policy/android/java/src/org/chromium/chrome/browser/desktop_policy/ArchiumWindowClass.java',ROOT/'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcCollectionsFocusTest.java',r]
import importlib.util
spec=importlib.util.spec_from_file_location('window_core',ROOT/'scripts/fetch-window-core.py')
window=importlib.util.module_from_spec(spec);spec.loader.exec_module(window)
cp=a.classpath_file.read_text().strip()+':'+str(window.ensure_jar())
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,sources)],check=True)
raise SystemExit(subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','org.chromium.chrome.browser.arc.ArcCollectionsFocusTest']).returncode)
