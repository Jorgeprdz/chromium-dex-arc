"""Execute the real binder color methods at explicit Java service boundaries.

This establishes the R3 white-capsule contract, not Chromium UI rendering.
"""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import method_body

ROOT = Path(__file__).resolve().parents[1]
BINDER = ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java'


class R3ActiveTabColorTest(unittest.TestCase):
    def test_regular_capsule_white_incognito_and_mobile_preserved(self):
        source = BINDER.read_text()
        background = method_body(source, r'private static ColorStateList getBackgroundTintList\(')
        foreground = method_body(source, r'private static @ColorInt int getTextColor\(')
        java = r'''
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
public class BinderColorProbe {
    static class Context {
        boolean arc=true;
        int getColor(int id) { return id; }
    }
    static class Color { static final int WHITE=0xffffffff, TRANSPARENT=0; }
    static class ColorStateList {
        final int value;
        ColorStateList(int color) { value=color; }
        static ColorStateList valueOf(int color) { return new ColorStateList(color); }
    }
    static class ArcDesktopAppearance {
        static int seed;
        static boolean isDesktopWindow(Context c) { return c.arc; }
        static int surface(Context c,boolean incognito) { return ArcDesktopPolicy.surface(seed,incognito); }
        static int selection(Context c,boolean incognito) { return ArcDesktopPolicy.selection(surface(c,incognito)); }
    }
    static class SemanticColorUtils {
        static int getColorSurface(Context c) { return 0xffeeeeee; }
        static int getColorOnSurface(Context c) { return 0xff111111; }
        static int getDefaultTextColorSecondary(Context c) { return 0xff333333; }
    }
    static class TabUiThemeUtil {
        static int getTabStripMultiSelectedTabColor(Context c,boolean incognito) { return 0xff222222; }
    }
    static class R { static class color {
        static int default_bg_color_dark=0xff101010;
        static int default_text_color_light=0xffeeeeee;
        static int incognito_tab_title_color=0xffcccccc;
    } }
    private static ColorStateList getBackgroundTintList(Context context,boolean isSelected,boolean isMultiSelected,boolean isIncognito) __BACKGROUND__
    private static int getTextColor(Context context,boolean isSelected,boolean isIncognito) __FOREGROUND__
    static void eq(int expected,int actual) {
        if(expected!=actual) throw new AssertionError(Integer.toHexString(expected)+" != "+Integer.toHexString(actual));
    }
    public static void main(String[] args) {
        Context c=new Context();
        for(int seed:new int[]{0xff53657b,0xffeeeeee,0xff000000,0xffee4400,0xff0044ee}) {
            ArcDesktopAppearance.seed=seed;
            eq(Color.WHITE,getBackgroundTintList(c,true,false,false).value);
            eq(Color.TRANSPARENT,getBackgroundTintList(c,false,false,false).value);
            eq(ArcDesktopAppearance.selection(c,true),getBackgroundTintList(c,true,false,true).value);
            eq(ArcDesktopAppearance.selection(c,false),getBackgroundTintList(c,false,true,false).value);
            eq(0xff000000,getTextColor(c,true,false));
        }
        c.arc=false;
        eq(0xffeeeeee,getBackgroundTintList(c,true,false,false).value);
        eq(0xff101010,getBackgroundTintList(c,true,false,true).value);
        eq(0xff111111,getTextColor(c,true,false));
        System.out.println("PASS: white regular active tab; incognito, multi-select, mobile preserved");
    }
}
'''.replace('__BACKGROUND__', background).replace('__FOREGROUND__', foreground)
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            probe = work / 'BinderColorProbe.java'
            probe.write_text(java)
            production = list((ROOT / 'chromium').rglob('ArcDesktopPolicy.java')) + list((ROOT / 'chromium').rglob('ArchiumWindowClass.java'))
            spec = importlib.util.spec_from_file_location('window_core', ROOT / 'scripts/fetch-window-core.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            jar = module.ensure_jar()
            result = subprocess.run(['javac', '-cp', str(jar), '-d', str(work), *map(str, production), str(probe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(['java', '-ea', '-cp', str(work), 'BinderColorProbe'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
