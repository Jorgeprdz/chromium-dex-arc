#!/usr/bin/env python3
"""Run delivered sidebar branches/methods on Android views; not a Chromium APK test.

Full-controls and extension-budget expressions come from the actual consumer.
The frame/tab/resource construction boundary is explicit; no WebContents/GPU.
"""
import argparse
import importlib.util
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import method_body


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--classpath-file', type=Path, required=True)
    p.add_argument('--java-home', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    classes = a.work / 'classes'
    classes.mkdir(exist_ok=True)
    arc = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
    source = (arc / 'ArcDesktopCoordinator.java').read_text()
    expanded = re.search(r'boolean expanded =\s*(.*?);', source, re.S).group(1)
    budget = re.search(r'tablet.updateArcExtensionsWidth\((.*?)\);', source, re.S).group(1)
    collections = re.search(r'mCollectionsView.setVisibility\(\s*(.*?)\);', source[source.index('int collectionBudget ='):], re.S).group(1)
    test = r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.*;
import android.view.*;
import android.widget.*;
import android.text.TextUtils;
import org.junit.*;
import org.junit.runner.RunWith;
import org.robolectric.*;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class R {static class string {static int arc_new_tab=android.R.string.ok;}}
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class SidebarGeometryProbe {
    org.robolectric.android.controller.ActivityController<Activity> controller;
    Activity activity;
    @Before public void setup(){controller=Robolectric.buildActivity(Activity.class).setup();activity=controller.get();}
    @After public void close(){controller.pause().stop().destroy();}
    static class Shell {
        final Activity mActivity;
        final View mRail,mMenuButtonWrapper,mNativeNewTabButton;
        final TextView mNewTabRow;
        final Drawable mNewTabIcon=new ColorDrawable(Color.BLACK);
        int mPaletteSurface=0xffedc3ae;
        float mDensity=1f;
        Shell(Activity a){mActivity=a;mRail=new View(a);mMenuButtonWrapper=new View(a);
            mNativeNewTabButton=new View(a);mNewTabRow=new TextView(a);mNewTabIcon.setBounds(0,0,24,24);}
        int dp(int n){return Math.round(n*mDensity);}
        boolean fullControls(int collectionBudget){float density=1f;return EXPANDED;}
        int extensionWidth(){boolean expanded=true;return BUDGET;}
        boolean canExpandControls() CAN_EXPAND
        int collectionVisibility(boolean expanded,int collectionBudget){return COLLECTIONS;}
        void updateNewTabRow(boolean expanded) NEW_TAB
        void styleInteraction(View view,int foreground,int selection) INTERACTION
    }
    @Test public void wideShortRailDoesNotCollapseNavigationWhenCollectionsHaveNoRoom(){
        Shell s=new Shell(activity);s.mRail.layout(0,0,216,500);
        assertTrue("Collection budget must not hide full navigation in a wide rail",s.fullControls(0));
    }
    @Test public void compactAndVeryShortRailsStillUseCompactControls(){
        Shell s=new Shell(activity);s.mRail.layout(0,0,52,800);assertFalse(s.fullControls(240));
        s.mRail.layout(0,0,216,300);assertFalse(s.fullControls(0));
        s.mRail.layout(0,0,216,800);assertTrue(s.fullControls(240));
    }
    @Test public void zeroCollectionScrollBudgetRetainsAccessibleCollectionChrome(){
        Shell s=new Shell(activity);// The budget controls scrolling; native collection chrome remains reachable.
        assertEquals(View.VISIBLE,s.collectionVisibility(true,0));
        assertEquals(View.VISIBLE,s.collectionVisibility(true,120));
        assertEquals(View.VISIBLE,s.collectionVisibility(false,120));
    }
    @Test public void extensionBudgetOwnsFullSecondRowAfterRailInsets(){
        Shell s=new Shell(activity);s.mRail.layout(0,0,216,800);s.mRail.setPadding(4,0,4,0);
        s.mMenuButtonWrapper.measure(View.MeasureSpec.makeMeasureSpec(64,View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(44,View.MeasureSpec.EXACTLY));
        assertEquals("Second row receives216 minus rail insets8",208,s.extensionWidth());
    }
    @Test public void extensionBudgetKeepsFullUsableWidthAtFractionalDensity(){
        Shell s=new Shell(activity);s.mDensity=2.625f;s.mRail.layout(0,0,567,1000);
        s.mRail.setPadding(11,0,11,0);
        s.mMenuButtonWrapper.measure(View.MeasureSpec.makeMeasureSpec(168,View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(116,View.MeasureSpec.EXACTLY));
        // Browser controls occupy the first row and do not reduce native extension width.
        assertEquals("567 minus insets22",545,s.extensionWidth());
    }
    @Test public void compactPlusCentersInsideItsOwnRowAndSurvivesExpansion(){
        Shell s=new Shell(activity);s.mRail.layout(0,0,52,800);s.mRail.setPadding(8,0,8,0);
        s.mNewTabRow.layout(0,0,36,44);s.updateNewTabRow(false);
        assertEquals("24px icon must fit a 36px row",6,s.mNewTabRow.getPaddingLeft());
        assertEquals(6,s.mNewTabRow.getPaddingRight());
        s.updateNewTabRow(true);assertEquals(12,s.mNewTabRow.getPaddingLeft());
        assertFalse(s.mNewTabRow.getText().toString().isEmpty());
        s.mRail.setPadding(0,0,0,0);s.mNewTabRow.layout(0,0,52,44);s.updateNewTabRow(false);
        assertEquals(14,s.mNewTabRow.getPaddingLeft());assertEquals("",s.mNewTabRow.getText().toString());
    }
    @Test public void compactPlusFollowsRailShrinkBeforeTheChildLayoutPass(){
        Shell s=new Shell(activity);s.mRail.layout(0,0,52,800);
        s.mNewTabRow.layout(0,0,216,44);s.updateNewTabRow(false);
        assertEquals("Expanded child bounds are stale while the rail is collapsing",14,
            s.mNewTabRow.getPaddingLeft());
    }
    @Test public void disabledOwnedControlDoesNotShowHoverOrPressedHighlight(){
        Shell s=new Shell(activity);ImageButton b=new ImageButton(activity);s.styleInteraction(b,Color.BLACK,Color.RED);
        StateListDrawable background=(StateListDrawable)b.getBackground();
        for(int state:new int[]{android.R.attr.state_hovered,android.R.attr.state_pressed,android.R.attr.state_focused}){
            background.setState(new int[]{-android.R.attr.state_enabled,state});
            assertEquals("Disabled controls must keep idle background",Color.TRANSPARENT,
                ((GradientDrawable)background.getCurrent()).getColor().getDefaultColor());
        }
    }
    @Test public void enabledHoverFocusAndPressedKeepVisibleFeedback(){
        Shell s=new Shell(activity);ImageButton b=new ImageButton(activity);s.styleInteraction(b,Color.BLACK,Color.RED);
        StateListDrawable background=(StateListDrawable)b.getBackground();
        for(int state:new int[]{android.R.attr.state_hovered,android.R.attr.state_pressed,android.R.attr.state_focused}){
            background.setState(new int[]{android.R.attr.state_enabled,state});
            assertEquals(Color.RED,((GradientDrawable)background.getCurrent()).getColor().getDefaultColor());
        }
    }
}
'''
    for key, value in {'EXPANDED': expanded, 'BUDGET': budget, 'COLLECTIONS': collections,
            'CAN_EXPAND': method_body(source, r'private boolean canExpandControls\('),
            'NEW_TAB': method_body(source, r'private void updateNewTabRow\('),
            'INTERACTION': method_body(source, r'private void styleInteraction\(')}.items():
        test = test.replace(key, value)
    java = a.work / 'SidebarGeometryProbe.java'
    java.write_text(test)
    spec = importlib.util.spec_from_file_location('window_core', ROOT / 'scripts/fetch-window-core.py')
    window_core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(window_core)
    cp = a.classpath_file.read_text().strip() + ':' + str(window_core.ensure_jar())
    sources = [java, *ROOT.glob('chromium/**/ArcDesktopPolicy.java'),
               *ROOT.glob('chromium/**/ArchiumWindowClass.java')]
    subprocess.run([str(a.java_home / 'bin/javac'), '-cp', cp, '-d', str(classes),
                    *map(str, sources)], check=True)
    result = subprocess.run([str(a.java_home / 'bin/java'), '-ea',
        '-Drobolectric.conscryptMode=OFF', '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
        '-cp', str(classes) + ':' + cp, 'org.junit.runner.JUnitCore', 'SidebarGeometryProbe'])
    print('SCOPE=real_Android_views_drawables_delivered_UI_methods_and_consumer_expressions_NOT_APK_GPU')
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
