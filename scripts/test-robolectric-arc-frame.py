#!/usr/bin/env python3
"""Real Android view/palette probes; explicit compositor/window-metrics boundaries.

The frame method is extracted verbatim. This is not the full Chromium activity.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import method_body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--classpath-file', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--white-rail-mutant', action='store_true')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    classes = args.work / 'classes'
    classes.mkdir(exist_ok=True)
    arc = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
    appearance = ROOT / 'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs'
    coordinator = (arc / 'ArcDesktopCoordinator.java').read_text()
    body = method_body(coordinator, r'private void applyFrameGeometry\(')
    outline = method_body(coordinator, r'public void getOutline\(')
    frame = method_body(coordinator, r'private int frameSurface\(')
    material = method_body(coordinator, r'private void updateMaterial\(')
    if args.white_rail_mutant:
        mutation = ('        if (!(mRail.getBackground() instanceof ColorDrawable railColor)\n'
                    '                || railColor.getColor() != surface) mRail.setBackground(new ColorDrawable(surface));')
        if mutation not in body:
            parser.error('Rail background mutation absent')
        body = body.replace(mutation, '', 1)
    source = r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.view.ContextThemeWrapper;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.Rect;
import android.graphics.drawable.ColorDrawable;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewOutlineProvider;
import android.widget.FrameLayout;
import org.junit.Test;
import org.junit.After;
import org.robolectric.android.controller.ActivityController;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import org.chromium.chrome.browser.arc.ArcDesktopMaterial;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE, sdk={29,36}, qualifiers="notnight-mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class FramePaletteProbe {
    private final java.util.List<ActivityController<Activity>> controllers = new java.util.ArrayList<>();
    private Activity activity() {
        ActivityController<Activity> controller=Robolectric.buildActivity(Activity.class).setup();
        controllers.add(controller);return controller.get();
    }
    @After public void releaseActivities() {
        for (ActivityController<Activity> controller:controllers) controller.pause().stop().destroy();
    }
    static final class Incognito { boolean isIncognitoSelected() { return false; } }
    static final class Frame {
        final Activity mActivity;
        static class Compositor extends FrameLayout {
            Compositor(android.content.Context c){super(c);}
            void setArcContentOffsetForRail(int n) {} // offset method is exercised in transition probe.
        }
        final FrameLayout mRail, mFrameRoot;
        final Compositor mCompositorViewHolder;
        final int mOriginalRailPaddingLeft=0,mOriginalRailPaddingRight=0;
        final int mOriginalContentMarginLeft=0,mOriginalContentMarginTop=0;
        final int mOriginalContentMarginRight=0,mOriginalContentMarginBottom=0;
        final Incognito mIncognitoStateProvider=new Incognito();
        final ArcDesktopMaterial mDesktopRailMaterial=new ArcDesktopMaterial(),mDesktopFrameMaterial=new ArcDesktopMaterial();
        final int[] mMaterialPosition=new int[2];int mMaterialPreview=-1;
        android.content.SharedPreferences mPreferences;
        void updateMaterial(View target,ArcDesktopMaterial material,int surface) __MATERIAL__
        final ViewOutlineProvider mArcContentOutlineProvider=new ViewOutlineProvider() {
            public void getOutline(View view,Outline outline) __OUTLINE__
        };
        boolean mDestroyed,mArcFrameActive,mRailViewportTransition;
        Integer mPreviewFrameColor;
        Frame(Activity a) {
            mActivity=a;mPreferences=ArcDesktopAppearance.preferences(a);
            mFrameRoot=new FrameLayout(a);mRail=new FrameLayout(a);
            mCompositorViewHolder=new Compositor(a);
            mRail.setBackgroundColor(Color.WHITE);
            mFrameRoot.addView(mRail,new FrameLayout.LayoutParams(52,480));
            mFrameRoot.addView(mCompositorViewHolder,new FrameLayout.LayoutParams(320,480));
            ArcDesktopAppearance.setUiMode(a,ArcDesktopPolicy.MODE_ARC);
        }
        int dp(int n) { return n; }
        int reservedLeftWidth() { return 52; }
        int arcClipLeftForView(View v) {return reservedLeftWidth();}
        void applyActiveSurfaceClip() {} // Native compositor is outside this bounded view probe.
        int frameSurface(boolean incognito) __FRAME__
        void applyFrameGeometry() __BODY__
    }
    int materialSurface(android.graphics.drawable.Drawable material) throws Exception {
        var field=ArcDesktopMaterial.class.getDeclaredField("mSurface");field.setAccessible(true);return field.getInt(material);
    }
    @Test public void railPaddingUsesTheFramePalette() throws Exception {
        Activity a=activity();
        try {
            Frame f=new Frame(a);f.applyFrameGeometry();
            assertEquals(8,f.mRail.getPaddingTop());assertEquals(8,f.mRail.getPaddingBottom());
            int expected=ArcDesktopAppearance.surface(a,false);
            assertEquals(expected,materialSurface(f.mRail.getBackground()));
            assertEquals(expected,materialSurface(f.mFrameRoot.getBackground()));
            ArcDesktopAppearance.preferences(a).edit().putInt(ArcDesktopAppearance.COLOR_KEY,0xff0044ee).commit();
            f.applyFrameGeometry();
            assertEquals(ArcDesktopAppearance.surface(a,false),materialSurface(f.mRail.getBackground()));
        } finally { a.finish(); }
    }
    @Test public void draftIsSharedBySameWindowAndNeverWrittenUntilApply() {
        Activity a=activity();
        Activity other=activity();
        try {
            ArcDesktopAppearance.preferences(a).edit().putInt(ArcDesktopAppearance.COLOR_KEY,0xff0044ee).commit();
            int saved=ArcDesktopAppearance.surface(a,false);
            ContextThemeWrapper wrapped=new ContextThemeWrapper(a,android.R.style.Theme_Material);
            ArcDesktopAppearance.setPreviewColor(a,0xffee4400);
            assertEquals(0xfff28458,ArcDesktopAppearance.surface(wrapped,false));
            assertEquals(0xfffce0d5,ArcDesktopAppearance.activeTabSurface(wrapped,false));
            assertEquals(saved,ArcDesktopAppearance.surface(other,false));
            assertEquals(0xff0044ee,ArcDesktopAppearance.preferences(a).getInt(ArcDesktopAppearance.COLOR_KEY,0));
            ArcDesktopAppearance.setPreviewColor(a,null);
            assertEquals(saved,ArcDesktopAppearance.surface(wrapped,false));
            ArcDesktopAppearance.preferences(a).edit().putInt(ArcDesktopAppearance.COLOR_KEY,0xffee4400).commit();
            assertEquals(0xfff28458,ArcDesktopAppearance.surface(a,false));
        } finally { ArcDesktopAppearance.setPreviewColor(a,null);a.finish();other.finish(); }
    }
    @Test public void holderRectClipExcludesTheSidebarAndFrameGap() {
        Frame f=new Frame(activity());
        f.mCompositorViewHolder.layout(8,8,328,488);
        f.applyFrameGeometry();
        assertEquals(new Rect(52,0,320,480),f.mCompositorViewHolder.getClipBounds());
    }
    @Test public void surfaceOutlineSupportsFourRoundedCorners() {
        Frame f=new Frame(activity());f.mCompositorViewHolder.layout(0,0,320,480);
        Outline outline=new Outline();f.mArcContentOutlineProvider.getOutline(f.mCompositorViewHolder,outline);
        Rect bounds=new Rect();assertTrue(outline.canClip());assertTrue(outline.getRect(bounds));
        assertEquals(new Rect(52,0,320,480),bounds);
        assertFalse(ArcDesktopPolicy.containsArcContentPoint(319,479,52,0,320,480,16));
        assertEquals(16f,outline.getRadius(),0f);
        for (float[] corner : new float[][] {{52,0},{319,0},{52,479},{319,479}}) {
            assertFalse(ArcDesktopPolicy.containsArcContentPoint(corner[0],corner[1],52,0,320,480,16));
        }
    }
    @Test public void chosenPaletteKeepsVisibleHueAndContrast() {
        Activity a=activity();
        try {
            ArcDesktopAppearance.preferences(a).edit().putInt(ArcDesktopAppearance.COLOR_KEY,0xff0044ee).commit();
            int s=ArcDesktopAppearance.surface(a,false);
            assertTrue((s&255)-((s>>16)&255)>=100);
            assertTrue(ArcDesktopPolicy.contrast(s,ArcDesktopPolicy.foreground(s))>=4.5);
        } finally { a.finish(); }
    }
}
'''.replace('__BODY__', body).replace('__FRAME__', frame).replace('__OUTLINE__',outline).replace('__MATERIAL__',material)
    test = args.work / 'FramePaletteProbe.java'
    test.write_text(source)
    metrics = args.work / 'ArchiumWindowMetrics.java'
    metrics.write_text('package org.chromium.chrome.browser.desktop_policy; public class ArchiumWindowMetrics { public static int currentWidthDp(android.content.Context c) { return 1100; }}')
    window = args.work / 'ArchiumWindowClass.java'
    window.write_text('package org.chromium.chrome.browser.desktop_policy; public class ArchiumWindowClass { final int w; ArchiumWindowClass(int v){w=v;} public static ArchiumWindowClass classify(int w){return new ArchiumWindowClass(w);} public boolean usesDesktopNavigation(){return w>=600;} }')
    cp = args.classpath_file.read_text().strip()
    sources = [arc / 'ArcDesktopMaterial.java', appearance / 'ArcDesktopAppearance.java', appearance / 'ArcDesktopPolicy.java', test, metrics, window]
    subprocess.run([str(args.java_home/'bin/javac'), '-cp', cp, '-d', str(classes), *map(str,sources)], check=True)
    result = subprocess.run([str(args.java_home/'bin/java'), '-ea', '-Drobolectric.conscryptMode=OFF',
        '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2', '-cp', str(classes)+':'+cp,
        'org.junit.runner.JUnitCore', 'FramePaletteProbe'])
    print('SCOPE=real_Robolectric_views_palette_with_explicit_compositor_and_metrics_boundaries', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
