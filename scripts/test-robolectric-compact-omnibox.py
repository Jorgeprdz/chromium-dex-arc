#!/usr/bin/env python3
"""Run the complete compact helper on genuine Robolectric Android views.

Only Chromium resource IDs and tablet background touch forwarding are adapted.
Production helper compiles verbatim. No URL/focus/view classes are mocked.
"""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'org.chromium.chrome.browser.arc'
PRODUCTION = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCompactOmnibox.java'
TEST = ROOT / 'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcCompactOmniboxTest.java'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classpath-file', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--sdk-profiles', default='29,36')
    parser.add_argument('--baseline', action='store_true', help='Absent-helper negative regression')
    parser.add_argument('--keep-url-hit-bounds', action='store_true',
                        help='Negative regression: the clipped editor intercepts favicon taps')
    args = parser.parse_args()
    profiles = args.sdk_profiles.split(',')
    if not profiles or not all(value.isdigit() for value in profiles):
        parser.error('SDK profiles must be comma-separated integers')
    classpath = args.classpath_file.read_text().strip()
    classes = args.work / 'classes'
    classes.mkdir(parents=True, exist_ok=True)
    production = PRODUCTION.read_text() if not args.baseline else (
        'package ' + PACKAGE + '; public class ArcCompactOmnibox { '
        'public ArcCompactOmnibox(android.view.View host) {} '
        'public void setCompact(boolean compact) {} public void restore() {} '
        'public void destroy() {} }')
    if args.keep_url_hit_bounds:
        line = '            mUrl.layout(mUrl.getLeft(), mUrl.getTop(), mUrl.getLeft(), mUrl.getBottom());'
        if line not in production:
            parser.error('URL bounds mutation absent')
        production = production.replace(line, '', 1)
    source = TEST.read_text().replace('sdk = {29, 36}', 'sdk = {' + ','.join(profiles) + '}')
    ids = ['location_bar', 'location_bar_status', 'location_bar_status_icon',
           'url_bar', 'action_buttons_segment', 'focus_thief']
    resources = 'package org.chromium.chrome; public class R { public static class id {'
    resources += ''.join('public static final int ' + name + '=' + str(5000 + i) + ';'
                         for i, name in enumerate(ids)) + '}}'
    paths = []
    for name, text in [('ArcCompactOmnibox.java', production),
                       ('ArcCompactOmniboxTest.java', source), ('R.java', resources)]:
        path = args.work / name
        path.write_text(text)
        paths.append(str(path))
    subprocess.run([str(args.java_home / 'bin/javac'), '-cp', classpath, '-d', str(classes), *paths], check=True)
    result = subprocess.run([str(args.java_home / 'bin/java'), '-ea',
        '-Drobolectric.conscryptMode=OFF',
        '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
        '-cp', str(classes) + ':' + classpath, 'org.junit.runner.JUnitCore',
        PACKAGE + '.ArcCompactOmniboxTest'])
    print('SCOPE=complete_production_helper_real_Android_views_resource_ID_and_tablet_touch_adapters', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
