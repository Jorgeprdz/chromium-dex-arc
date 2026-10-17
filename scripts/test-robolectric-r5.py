#!/usr/bin/env python3
"""Complete R5 Android helpers on Robolectric; Chromium Tab is an explicit adapter."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARC = Path('chrome/android/java/src/org/chromium/chrome/browser/arc')
JUNIT = Path('chrome/android/junit/src/org/chromium/chrome/browser/arc')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--classpath-file', type=Path, required=True)
    p.add_argument('--java-home', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--navigation-only', action='store_true')
    p.add_argument('--mutation', choices=['sidebar-order', 'actions-enter', 'rtl', 'closing'])
    a = p.parse_args()
    classes = a.work / 'classes'
    classes.mkdir(parents=True, exist_ok=True)
    adapters = {
        'Tab.java': 'package org.chromium.chrome.browser.tab; public interface Tab { boolean canGoBack(); boolean canGoForward(); boolean isDestroyed(); void goBack(); void goForward(); void reload(); void addObserver(TabObserver o); void removeObserver(TabObserver o); }',
        'TabObserver.java': 'package org.chromium.chrome.browser.tab; public interface TabObserver { default void onUrlUpdated(Tab t){} default void onNavigationEntriesDeleted(Tab t){} default void onLoadStarted(Tab t,boolean different){} default void onLoadStopped(Tab t,boolean different){} default void onDestroyed(Tab t){} }',
    }
    sources = []
    for name, contents in adapters.items():
        path = a.work / name
        path.write_text(contents)
        sources.append(str(path))
    names = ['ArcNavigationControls']
    if not a.navigation_only:
        names += ['ArcOmniboxPlacement', 'ArcCommandBar']
    for name in names:
        production = ROOT / 'chromium' / ARC / (name + '.java')
        if a.mutation:
            contents = production.read_text()
            if a.mutation == 'sidebar-order' and name == 'ArcOmniboxPlacement':
                contents = contents.replace('Math.min(index, destination.getChildCount())', 'destination.getChildCount()')
            if a.mutation == 'actions-enter' and name == 'ArcCommandBar':
                contents = contents.replace('(mSelected >= 0 || mActions)', 'mSelected >= 0')
            if a.mutation == 'rtl' and name == 'ArcCommandBar':
                contents = contents.replace('Gravity.LEFT | Gravity.TOP', '-1')
            if a.mutation == 'closing' and name == 'ArcCommandBar':
                contents = contents.replace('if (!animated) { cancelAnimator(); finishClose(after); }', '')
            production = a.work / (name + '.java')
            production.write_text(contents)
        sources += [str(production), str(ROOT / 'chromium' / JUNIT / (name + 'Test.java'))]
    cp = a.classpath_file.read_text().strip()
    subprocess.run([str(a.java_home / 'bin/javac'), '-cp', cp, '-d', str(classes), *sources], check=True)
    result = subprocess.run([str(a.java_home / 'bin/java'), '-ea',
        '-Drobolectric.conscryptMode=OFF',
        '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
        '-cp', str(classes) + ':' + cp, 'org.junit.runner.JUnitCore',
        *['org.chromium.chrome.browser.arc.' + n + 'Test' for n in names]])
    print('SCOPE=complete_R5_Android_helpers_Tab_adapter_NOT_APK_RUNTIME', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
