#!/usr/bin/env python3
"""Run delivered Arc holder focus regressions using genuine Robolectric windows.

Compiles verbatim production focus/layout/margin methods and delivered regression
methods. Chrome construction, dimensions, drawables, coordinator notifications and
cosmetic helpers are explicit adapters. This is not the full Chromium test runner.
No dependencies are installed; supply an existing JDK and Robolectric classpath.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_r5_native_command_api import native_definition
REL = Path('chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox')
PACKAGE = 'org.chromium.chrome.browser.omnibox'


def method(source, name, last=False):
    matches = list(re.finditer(r'^    (?:public|private|protected|/\* package \*/).*?\b' + name + r'\(', source, re.M))
    if not matches:
        raise ValueError('Missing production method: ' + name)
    match = matches[-1] if last else matches[0]
    start = source.index('{', match.start())
    depth = 1
    end = start + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[match.start():end].replace('@FuseboxState ', '').replace('@Px ', '').replace('@Nullable ', '')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classpath-file', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--view-utils-source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--sdk-profiles', default='29,36')
    parser.add_argument('--source-stage', choices=['reference', 'modified'], default='modified')
    parser.add_argument('--unsafe-container-mutant', action='store_true')
    parser.add_argument('--test-filter', help='Run one delivered regression method')
    args = parser.parse_args()
    profiles = args.sdk_profiles.split(',')
    if not profiles or not all(value.isdigit() for value in profiles):
        parser.error('SDK profiles must be comma-separated integers')
    source = (ROOT / ('.source-' + args.source_stage) / REL / 'LocationBarTablet.java').read_text()
    tests = (ROOT / '.source-modified' / REL / 'LocationBarTabletUnitTest.java').read_text()
    regressions = tests.split('    // BEGIN ARC HOLDER FOCUS REGRESSIONS\n')[1].split('    // END ARC HOLDER FOCUS REGRESSIONS')[0]
    regressions = re.sub(r'^    @EnableFeatures.*\n|^    @Config.*\n', '', regressions, flags=re.M)
    bodies = [method(source, name) for name in ('onFuseboxStateChanged', 'updateLayoutAndBackground', 'setMarginsForAvailableWidth', 'getAvailableContainerWidth', 'isTooNarrowForExpandedActivationChip')]
    if 'public void setArcCommandBar(' in source:
        bodies.append(method(source, 'setArcCommandBar'))
    native = native_definition((ROOT / '.source-modified' / REL / 'LocationBarLayout.java').read_text())
    native = native[native.index('    private @Nullable '):native.rfind('}')].replace('@Nullable ', '')
    tablet_fields = '\n'.join(re.findall(r'^    private [^\n]+ mArcCommandOriginal[^\n]+;', source, re.M)).replace('@Nullable ', '')
    if 'private View getExpansionContainer(' in source:
        bodies += [method(source, name) for name in ('getExpansionContainer', 'isAncestorOf')]
        if args.unsafe_container_mutant:
            bodies[-2] = '    private View getExpansionContainer() { return mContainerView != null ? mContainerView : getRootView(); }'
    elif args.unsafe_container_mutant:
        parser.error('Container resolver mutation requires modified source')
    viewutils = args.view_utils_source.read_text()
    viewutils_methods = '\n'.join(method(viewutils, name, last=True) for name in ('getRelativeLayoutPosition', 'setAncestorsShouldClipToPadding', 'setAncestorsShouldClipChildren'))
    classes = args.work / 'classes'
    classes.mkdir(parents=True, exist_ok=True)
    test_source = '''package org.chromium.chrome.browser.omnibox;
import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;
import android.app.Activity;
import android.app.Dialog;
import android.os.Looper;
import android.view.View;
import android.view.View.MeasureSpec;
import android.view.ViewGroup;
import android.view.ViewGroup.LayoutParams;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.*;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE, qualifiers="w800dp-xhdpi", sdk={__SDKS__})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class LocationBarTabletFocusFixtureTest {
    Activity mActivity;
    LocationBarTablet mLocationBarTablet;
    FrameLayout mHolderView;
    @Before public void setUp() {
        mActivity=Robolectric.buildActivity(Activity.class).get();
        mActivity.setTheme(android.R.style.Theme_Material);
        LinearLayout root=new LinearLayout(mActivity);
        mHolderView=new FrameLayout(mActivity);
        mLocationBarTablet=new LocationBarTablet(mActivity);
        mHolderView.addView(mLocationBarTablet,new FrameLayout.LayoutParams(280,100));
        root.addView(mHolderView,new LinearLayout.LayoutParams(280,100));
        mActivity.setContentView(root);
        mLocationBarTablet.setHolderAndContainer(mHolderView,null);
    }
__TESTS__
__MEASURE__
}'''.replace('__SDKS__', ','.join(profiles)).replace('__TESTS__', regressions).replace('__MEASURE__', method(tests, 'measureHolder'))
    production = '''package org.chromium.chrome.browser.omnibox;
import android.content.Context;
import android.content.res.Resources;
import android.graphics.Rect;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewGroup.MarginLayoutParams;
import android.view.ViewOutlineProvider;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import java.util.function.BooleanSupplier;
class LocationBarTablet extends BaseLayout {
    private static final float OVERLAY_Z_TRANSLATION=1f, NEUTRAL_Z_TRANSLATION=0f;
    private static final int CENTERING_THRESHOLD_DP=16;
    View mHolder, mContainerView;
    int mMinWidthForExpandedActivationChip=504;
    int mFuseboxState, mLayoutMode, mTargetPopoverWidth, mTargetPopoverLeftOffset;
    boolean mIsReparentedToPopover, mShowFocusRing, mIsGlifActive;
    int mLocationBarTabletFuseboxPopupInset=16, mPopoverAdditionalWidth=16;
__TABLET_FIELDS__
    ViewOutlineProvider mOutlineProvider;
    GradientDrawable mFocusedPopupDrawable=new GradientDrawable(), mLocationBarBackground=new GradientDrawable();
    int[] mPositionArray=new int[2];
    BooleanSupplier mIsFullWidthExpansionAllowedSupplier;
    WindowAndroid mWindowAndroid=new WindowAndroid();
    LocationBarTablet(Context context) {
        super(context);
        UrlBar url=new UrlBar(context);
        url.setId(R.id.url_bar);
        addView(url,new FrameLayout.LayoutParams(260,100));
    }
    void setHolderAndContainer(View holder,View container) { mHolder=holder; mContainerView=container; }
    @Override public Resources getResources() { return new DimensionResources(super.getResources()); }
    private void adjustVerticalTranslationForFuseboxState(int state) {}
    private void updatePopoverAlignmentMargins() {}
    private void adjustBackgroundForSuggestions() {}
    private void updateForegroundAndGlifAnimation() {}
__BODIES__
}
class BaseLayout extends FrameLayout {
    BaseLayout(Context c) { super(c); }
    public void onFuseboxStateChanged(int state) {}
__NATIVE_COMMAND__
}
// Explicit Chrome UrlBar callback adapter. Focus itself is real Android EditText behavior.
class UrlBar extends android.widget.EditText {
    private java.util.function.Consumer<UrlBarFocusChangeInfo> mCallback;
    UrlBar(Context c) { super(c); }
    void setFocusChangeCallback(java.util.function.Consumer<UrlBarFocusChangeInfo> callback) { mCallback=callback; }
    @Override protected void onFocusChanged(boolean focused,int direction,android.graphics.Rect rect) {
        super.onFocusChanged(focused,direction,rect);
        if(mCallback!=null) mCallback.accept(new UrlBarFocusChangeInfo(focused));
    }
}
class UrlBarFocusChangeInfo {
    final boolean hasFocus;
    UrlBarFocusChangeInfo(boolean focused) { hasFocus=focused; }
}
class DimensionResources extends Resources {
    DimensionResources(Resources r) { super(r.getAssets(),r.getDisplayMetrics(),r.getConfiguration()); }
    @Override public int getDimensionPixelSize(int id) {
        if(id==R.dimen.fusebox_min_tablet_width) return 1008;
        if(id==R.dimen.modern_toolbar_tablet_background_size) return 112;
        return 16;
    }
}
class FuseboxState { static final int DISABLED=0, COMPACT=1, EXPANDED=2; }
class FuseboxLayoutMode { static final int SUGGESTIONS_POPOVER=1; }
class DeviceFormFactor { static final int MINIMUM_TABLET_WIDTH_DP=600; }
class WindowAndroid { Object getDisplay() { return this; } }
class DisplayUtil { static int dpToPx(Object display,int dp) { return dp*2; } }
class MathUtils { static final float EPSILON=0.001f; }
class R {
    static class id { static final int url_bar=100; }
    static class style { static final int Theme_BrowserUI_DayNight=android.R.style.Theme_Material; }
    static class dimen {
        static final int fusebox_min_tablet_width=1, modern_toolbar_tablet_background_size=2,
            location_bar_tablet_fusebox_popover_top_padding=3,location_bar_tablet_fusebox_popup_inset=4;
    }
}
class ViewUtils {
__VIEWUTILS__
}'''.replace('__BODIES__', '\n'.join(bodies)).replace('__VIEWUTILS__', viewutils_methods).replace('__NATIVE_COMMAND__', native).replace('__TABLET_FIELDS__', tablet_fields)
    runner = '''package org.chromium.chrome.browser.omnibox;
public class FocusFixtureRunner {
    public static void main(String[] args) {
        org.junit.runner.JUnitCore core=new org.junit.runner.JUnitCore();
        org.junit.runner.Request request=args.length==0
            ? org.junit.runner.Request.aClass(LocationBarTabletFocusFixtureTest.class)
            : org.junit.runner.Request.method(LocationBarTabletFocusFixtureTest.class,args[0]);
        org.junit.runner.Result result=core.run(request);
        for(org.junit.runner.notification.Failure failure:result.getFailures()) System.out.println(failure.getTrace());
        System.out.println("Tests run: "+result.getRunCount()+", failures: "+result.getFailureCount());
        System.exit(result.wasSuccessful()?0:1);
    }
}'''
    paths = []
    for name, contents in [('LocationBarTabletFocusFixtureTest.java', test_source), ('LocationBarTablet.java', production), ('FocusFixtureRunner.java', runner)]:
        path = args.work / name
        path.write_text(contents)
        paths.append(str(path))
    classpath = args.classpath_file.read_text().strip()
    subprocess.run([str(args.java_home / 'bin/javac'), '-cp', classpath, '-d', str(classes), *paths], check=True)
    argv = [str(args.java_home / 'bin/java'), '-ea', '-Drobolectric.conscryptMode=OFF',
            '-Drobolectric.logging.enabled=true', '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
            '-cp', str(classes) + ':' + classpath, PACKAGE + '.FocusFixtureRunner']
    if args.test_filter:
        argv.append(args.test_filter)
    result = subprocess.run(argv)
    print('SCOPE=real_Robolectric_windows_actual_focus_layout_margin_methods_explicit_Chrome_adapters', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
