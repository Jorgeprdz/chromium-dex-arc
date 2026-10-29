"""Compile delivered LocationBar command fields/methods with Chromium's TYPE_USE Nullable.

Only the Android superclass/context constructor is adapted. Production declarations,
method bodies and imports are copied verbatim; this is not full Chromium compilation.
"""
import os
import importlib.util
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
_probe_spec = importlib.util.spec_from_file_location('arc_toolbar_probe', ROOT / 'tests/arc_toolbar_probe.py')
_probe = importlib.util.module_from_spec(_probe_spec)
_probe_spec.loader.exec_module(_probe)
method_body = _probe.method_body
SOURCE = ROOT / '.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarLayout.java'
TABLET = SOURCE.with_name('LocationBarTablet.java')


def native_definition(source):
    # There are earlier nullable members. Select the contiguous new command API explicitly.
    declaration = re.search(r'^    private @Nullable [^;\n]+ mArcCommandResults;', source, re.M)
    if declaration is None:
        raise ValueError('Delivered command bounds field absent')
    start = declaration.start()
    end = source.index('    /* package */ void updateVisualsForState(', start)
    body = source[start:end]
    required = ['setArcCommandBar(', 'getArcCommandResults(', 'isArcCommandActions(',
                'finishArcCommandNavigation(', 'closeArcCommandBarForInputEnd(']
    if any(name not in body for name in required):
        raise ValueError('Incomplete delivered native command API')
    imports = '\n'.join(re.findall(
        r'^import (?:android\.graphics\.Rect|org\.chromium\.build\.annotations\.Nullable);$', source, re.M))
    return imports + '\npublic class LocationBarLayout extends android.widget.FrameLayout {\n' + (
        'public LocationBarLayout(android.content.Context context){super(context);}\n'
        'public void setArcSurfaceColor(Integer color){}\n') + body + '\n}'


class NativeCommandApiCompileTests(unittest.TestCase):
    def compile_tablet_snapshot(self, source):
        # ConstraintLayout declares its own nested LayoutParams. Preserve that Java scope;
        # using FrameLayout as the sole superclass would incorrectly accept a shadowed import.
        self.assertIn('extends ConstraintLayout', SOURCE.read_text())
        fields = '\n'.join(re.findall(r'^    private [^\n]+ mArcCommandOriginal[^\n]+;', source, re.M))
        body = method_body(source, r'public void setArcCommandBar\(')
        imports = '\n'.join(re.findall(r'^import (?:android\.graphics\.Rect|android\.view\.ViewGroup\.MarginLayoutParams|android\.widget\.FrameLayout(?:\.LayoutParams)?|org\.chromium\.build\.annotations\.Nullable);$', source, re.M))
        definition = imports + '''
class LocationBarLayout extends android.widget.FrameLayout {
    public static class LayoutParams extends android.view.ViewGroup.MarginLayoutParams {
        LayoutParams(int w,int h){super(w,h);}
    }
    LocationBarLayout(android.content.Context c){super(c);}
    android.graphics.Rect getArcCommandResults(){return null;}
    public void setArcCommandBar(android.graphics.Rect r,boolean a,Runnable b,Runnable e){}
}
public class LocationBarTablet extends LocationBarLayout {
    LocationBarTablet(android.content.Context c){super(c);}
    android.graphics.drawable.Drawable mArcGlassBackground;
    public void setArcGlassBackground(android.graphics.drawable.Drawable surface){}
    void updateLayoutAndBackground(){}
''' + fields + '\npublic void setArcCommandBar(@Nullable android.graphics.Rect results,boolean actions,Runnable beforeNavigation,Runnable inputEnd) '.replace('@Nullable android.graphics.Rect', '@Nullable Rect') + body + '\n}'
        android = os.environ.get('ARCHIUM_TEST_ANDROID_JAR', '/opt/android-sdk/platforms/android-36/android.jar')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tablet = root / 'LocationBarTablet.java'; tablet.write_text(definition)
            annotation = root / 'Nullable.java'
            annotation.write_text('package org.chromium.build.annotations; @java.lang.annotation.Target(java.lang.annotation.ElementType.TYPE_USE) public @interface Nullable {}')
            return subprocess.run(['javac', '-cp', android, '-d', str(root / 'classes'), str(annotation), str(tablet)],capture_output=True,text=True,timeout=60)

    def test_tablet_snapshot_compiles_with_inherited_constraint_layout_params(self):
        result = self.compile_tablet_snapshot(TABLET.read_text())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_inherited_layout_params_must_reject_an_ambiguous_import(self):
        source = TABLET.read_text()
        source = re.sub(r'private [^\n]+ mArcCommandOriginalChildParams;', 'private @Nullable LayoutParams mArcCommandOriginalChildParams;', source)
        source = source.replace('import android.widget.FrameLayout;', 'import android.widget.FrameLayout;\nimport android.widget.FrameLayout.LayoutParams;')
        result = self.compile_tablet_snapshot(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('incompatible types', result.stderr)

    def compile(self, source):
        android = Path(os.environ.get('ARCHIUM_TEST_ANDROID_JAR', '/opt/android-sdk/platforms/android-36/android.jar'))
        self.assertTrue(android.is_file(), 'Real Android SDK required')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            layout = root / 'LocationBarLayout.java'
            layout.write_text('package org.chromium.chrome.browser.omnibox;\n' + native_definition(source))
            annotation = root / 'Nullable.java'
            # Exact @Target/@Retention from cfd94726 build/android/java/.../Nullable.java.
            annotation.write_text('package org.chromium.build.annotations;\n'
                '@java.lang.annotation.Target(java.lang.annotation.ElementType.TYPE_USE)\n'
                '@java.lang.annotation.Retention(java.lang.annotation.RetentionPolicy.CLASS)\n'
                'public @interface Nullable {}\n')
            return subprocess.run(['javac', '-cp', str(android), '-d', str(root / 'classes'),
                str(annotation), str(layout)], capture_output=True, text=True, timeout=60)

    def test_delivered_native_api_compiles_with_real_type_use_contract(self):
        result = self.compile(SOURCE.read_text())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_historical_qualified_nullable_must_fail_before_restore(self):
        source = SOURCE.read_text().replace('@Nullable Rect', '@Nullable android.graphics.Rect')
        result = self.compile(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr, r'type annotation .* is not expected here|scoping construct cannot be annotated')


if __name__ == '__main__':
    unittest.main()
