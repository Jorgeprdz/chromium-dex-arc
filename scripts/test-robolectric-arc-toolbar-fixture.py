#!/usr/bin/env python3
"""Execute the delivered toolbar test on real Robolectric at bounded Chrome boundaries.

The test methods and production rectangle method are taken verbatim from this repo.
Android windows/looper are real shadows. Chrome construction, resource IDs and
capture readiness use explicit adapters: this is NOT the full Chromium runner.
No dependencies are installed by this script; provide an existing classpath/JDK.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import toolbar_body

TEST = ROOT / 'chromium/chrome/android/junit/src/org/chromium/chrome/browser/toolbar/top/ArcToolbarReparentingTest.java'
PACKAGE = 'org.chromium.chrome.browser.toolbar.top'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classpath-file', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--sdk-profiles', default='29,36')
    parser.add_argument('--remove-dialog-idle', action='store_true', help='Negative lifecycle regression')
    args = parser.parse_args()
    profiles = args.sdk_profiles.split(',')
    if not profiles or not all(value.isdigit() for value in profiles):
        parser.error('SDK profiles must be comma-separated integers')
    classpath = args.classpath_file.read_text().strip()
    args.work.mkdir(parents=True, exist_ok=True)
    classes = args.work / 'classes'
    classes.mkdir(exist_ok=True)
    test = TEST.read_text().replace(
        'import org.chromium.base.test.BaseRobolectricTestRunner;',
        'import org.robolectric.RobolectricTestRunner;\n'
        'import org.robolectric.annotation.Config;\n'
        'import org.robolectric.annotation.LooperMode;\n'
        'import org.robolectric.annotation.GraphicsMode;\n'
        'import org.robolectric.annotation.SQLiteMode;')
    test = test.replace('@RunWith(BaseRobolectricTestRunner.class)',
        '@RunWith(RobolectricTestRunner.class)\n'
        '@Config(manifest=Config.NONE, sdk={' + ','.join(profiles) + '})\n'
        '@LooperMode(LooperMode.Mode.PAUSED)\n'
        '@GraphicsMode(GraphicsMode.Mode.LEGACY)\n'
        '@SQLiteMode(SQLiteMode.Mode.LEGACY)')
    if args.remove_dialog_idle:
        line = '            shadowOf(Looper.getMainLooper()).idle();\n'
        if line not in test:
            parser.error('Dialog idle mutation absent')
        test = test.replace(line, '', 1)
    sources = {
        'ArcToolbarReparentingTest.java': test,
        'R.java': 'package org.chromium.chrome; public class R { public static class style { '
                  'public static int Theme_BrowserUI_DayNight=android.R.style.Theme_Material; }}',
        'LocationBar.java': 'package org.chromium.chrome.browser.omnibox; public interface LocationBar { '
                            'android.view.View getContainerView(); }',
        'CaptureReadinessResult.java': 'package ' + PACKAGE + '; public class CaptureReadinessResult { '
                                     'public static CaptureReadinessResult readyForced() { return new CaptureReadinessResult(); }}',
        'ToolbarLayout.java': '''package org.chromium.chrome.browser.toolbar.top;
import android.content.Context;
import android.util.AttributeSet;
import android.graphics.Rect;
import android.view.View;
import android.widget.FrameLayout;
import org.chromium.chrome.browser.omnibox.LocationBar;
public abstract class ToolbarLayout extends FrameLayout {
    final int[] mTempPosition=new int[2];
    public ToolbarLayout(Context context,AttributeSet attrs) { super(context,attrs); }
    protected abstract CaptureReadinessResult isReadyForTextureCapture();
    public abstract LocationBar getLocationBar();
    public abstract void requestKeyboardFocus();
    void getLocationBarContentRect(Rect outRect) __BODY__
    // Pinned ViewUtils ancestor-only draw-position contract.
    static class ViewUtils {
        static void getRelativeDrawPosition(View rootView,View childView,int[] outPosition) {
            assert outPosition.length == 2;
            outPosition[0]=outPosition[1]=0;
            if(rootView==null || childView==rootView) return;
            while(childView!=null) {
                outPosition[0]=(int)(outPosition[0]+childView.getX());
                outPosition[1]=(int)(outPosition[1]+childView.getY());
                if(childView.getParent()==rootView) break;
                childView=(View)childView.getParent();
            }
        }
    }
}'''.replace('__BODY__', toolbar_body()),
    }
    paths = []
    for name, text in sources.items():
        path = args.work / name
        path.write_text(text)
        paths.append(str(path))
    subprocess.run([str(args.java_home / 'bin/javac'), '-cp', classpath,
                    '-d', str(classes), *paths], check=True)
    result = subprocess.run([str(args.java_home / 'bin/java'), '-ea',
        '-Drobolectric.conscryptMode=OFF', '-Drobolectric.logging.enabled=true',
        '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
        '-cp', str(classes) + ':' + classpath,
        'org.junit.runner.JUnitCore', PACKAGE + '.ArcToolbarReparentingTest'])
    print('SCOPE=real_Robolectric_windows_with_explicit_Chrome_adapters', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
