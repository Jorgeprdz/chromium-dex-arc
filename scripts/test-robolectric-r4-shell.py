#!/usr/bin/env python3
"""Real Android drawable/layout regressions at explicitly bounded Chromium adapters."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests'))
from arc_toolbar_probe import method_body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classpath-file', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    classes=args.work/'classes'; classes.mkdir(exist_ok=True)
    arc=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
    coordinator=(arc/'ArcDesktopCoordinator.java').read_text()
    if 'private void updateNewTabRow(' in coordinator:
        new_tab=method_body(coordinator, r'private void updateNewTabRow\(')
    else:
        start=coordinator.index('        mNewTabRow.setVisibility(View.VISIBLE);')
        end=coordinator.index('        // The native app menu remains reachable while collapsed.',start)
        new_tab='{'+coordinator[start:end]+'}'
    palette=(arc/'ArcCollectionsView.java').read_text()
    style=method_body(palette,r'private void applyAppearance\(')
    background=method_body(palette,r'private GradientDrawable background\(')
    tablet=(ROOT/'.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarTablet.java').read_text()
    native_background=method_body(tablet,r'private void updateBackgroundColor\(')
    glass_background=method_body(tablet,r'public void setArcGlassBackground\(')
    tint=method_body(tablet,r'private int tintArcBackground\(') if 'private int tintArcBackground(' in tablet else '{return nativeColor;}'
    source=r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.content.Context;
import android.graphics.Rect;
import android.graphics.Color;
import android.graphics.drawable.*;
import android.content.res.ColorStateList;
import android.view.*;
import android.widget.*;
import android.text.TextUtils;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

@interface ColorInt {}
class BrandedColorScheme { static final int INCOGNITO=1; }
class OmniboxResourceProvider {
    static int base=Color.WHITE;
    static int getTabletToolbarTextBoxStandbyBackgroundColor(android.content.Context c,int scheme){return base;}
    static int getColorPrimary(android.content.Context c,int scheme){return Color.BLUE;}
}
class ThemeUtils { static int getTextBoxColorForToolbarBackgroundInNonNativePage(android.content.Context c,int color,boolean incognito,boolean custom){return OmniboxResourceProvider.base;} }
class R { static class string { static final int arc_new_tab=android.R.string.ok; } }
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={29,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ShellDrawableProbe {
    static class Compact { void setCompact(boolean compact) {} }
    static class Shell {
        final Activity mActivity;
        final TextView mNewTabRow;
        final View mNativeNewTabButton;
        final View mRail;
        final Drawable mNewTabIcon=new ColorDrawable(Color.BLACK);
        final Compact mCompactOmnibox=new Compact();
        Shell(Activity a) {
            mActivity=a;mNewTabRow=new TextView(a);mNativeNewTabButton=new View(a);
            mRail=new View(a);mRail.layout(0,0,52,500);
            mNewTabIcon.setBounds(0,0,24,24);
        }
        int dp(int n){return n;}
        void updateNewTabRow(boolean expanded) NEW_TAB
    }
    static class Collection {
        int mSurface=0xffe5b09d,mForeground=Color.BLACK,mInteraction=0xffbb8877;
        int dp(int n){return n;}
        GradientDrawable background(int color,int radius) BACKGROUND
        void applyAppearance(ViewGroup group) STYLE
    }
    static class NativePalette extends FrameLayout {
        static class Background extends ColorDrawable {
            void setBackgroundColor(int color){setColor(color);}
            void setStandbyColor(int color){}
        }
        static class Data {int getPrimaryColor(){return Color.WHITE;}}
        final Background mLocationBarBackground=new Background();
        final Data mLocationBarDataProvider=new Data();
        Drawable mArcGlassBackground, mArcGlassLayers;
        final int mModernToolbarBackgroundVerticalOffset=6;
        final Drawable mFocusedPopupDrawable=new ColorDrawable(Color.GRAY);
        Integer mArcSurfaceColor;
        boolean mShowFocusRing;
        int mBrandedColorScheme;
        NativePalette(Activity a){super(a);setBackground(mLocationBarBackground);}
        public void setArcGlassBackground(Drawable surface) GLASS_HOOK_BODY
        int tintArcBackground(int nativeColor) ARC_TINT_BODY
        void updateBackgroundColor() NATIVE_COLOR_BODY
    }
    @Test public void glassFillRetainsNativeBorderAndRestoresNativeBackground() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            NativePalette p=new NativePalette(a);Drawable glass=new ColorDrawable(Color.GRAY);
            p.setPadding(3,5,7,9);p.layout(0,0,200,50);
            p.setArcGlassBackground(glass);assertTrue(p.getBackground() instanceof LayerDrawable);
            LayerDrawable layers=(LayerDrawable)p.getBackground();assertSame(glass,layers.getDrawable(0));
            assertSame(p.mLocationBarBackground,layers.getDrawable(1));
            assertEquals(6,layers.getLayerInsetTop(0));assertEquals(6,layers.getLayerInsetBottom(0));
            assertEquals(5,p.getPaddingTop());assertEquals(9,p.getPaddingBottom());assertEquals(50,p.getHeight());
            for(boolean focus:new boolean[]{false,true}){p.mShowFocusRing=focus;p.updateBackgroundColor();assertEquals(Color.TRANSPARENT,p.mLocationBarBackground.getColor());}
            p.setArcGlassBackground(null);assertSame(p.mLocationBarBackground,p.getBackground());
            assertEquals(Color.WHITE,p.mLocationBarBackground.getColor());
            p.setBackground(p.mFocusedPopupDrawable);p.setArcGlassBackground(glass);assertSame(p.mFocusedPopupDrawable,p.getBackground());
        } finally {a.finish();}
    }
    @Test public void nativeOmniboxUsesArcPaletteWithAndWithoutFocusRing() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            NativePalette p=new NativePalette(a);p.mArcSurfaceColor=0xffe5b09d;
            for(boolean focus:new boolean[]{false,true}) {
                p.mShowFocusRing=focus;p.updateBackgroundColor();
                assertEquals("native background must follow Arc",0xffeeccbf,p.mLocationBarBackground.getColor());
            }
            assertTrue(ArcDesktopPolicy.contrast(p.mLocationBarBackground.getColor(),Color.BLACK)>=4.5);
            OmniboxResourceProvider.base=0xff303030;p.mArcSurfaceColor=0xff774e39;
            p.updateBackgroundColor();
            assertEquals(0xff5e4436,p.mLocationBarBackground.getColor());
            assertTrue(ArcDesktopPolicy.contrast(p.mLocationBarBackground.getColor(),Color.WHITE)>=4.5);
            OmniboxResourceProvider.base=Color.WHITE;
            p.mArcSurfaceColor=null;p.updateBackgroundColor();
            assertEquals(Color.WHITE,p.mLocationBarBackground.getColor());
        } finally {a.finish();}
    }
    @Test public void compactNewTabHasAnActualDrawableAndAnEmptyLabel() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            Shell s=new Shell(a);s.updateNewTabRow(false);
            assertNotNull("compact + must be a native drawable",s.mNewTabRow.getCompoundDrawablesRelative()[0]);
            assertEquals("",s.mNewTabRow.getText().toString());
            assertEquals(14,s.mNewTabRow.getPaddingLeft());
            assertEquals(View.VISIBLE,s.mNewTabRow.getVisibility());
            s.mNativeNewTabButton.setEnabled(false);s.updateNewTabRow(false);
            assertFalse(s.mNewTabRow.isEnabled());
            s.updateNewTabRow(true);
            assertFalse(s.mNewTabRow.getText().toString().isEmpty());
            assertEquals(12,s.mNewTabRow.getPaddingLeft());
        } finally {a.finish();}
    }
    @Test public void favoriteTileIsDistinguishableAndUntinted() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            LinearLayout host=new LinearLayout(a);ImageButton tile=new ImageButton(a);
            tile.setColorFilter(Color.RED);host.addView(tile);
            Collection c=new Collection();c.applyAppearance(host);
            GradientDrawable shape=(GradientDrawable)((RippleDrawable)tile.getBackground()).getDrawable(0);
            assertNotEquals("favorite tile cannot use the rail surface",c.mSurface,shape.getColor().getDefaultColor());
            assertNull(tile.getColorFilter());
        } finally {a.finish();}
    }
}
'''.replace('NEW_TAB',new_tab).replace('BACKGROUND',background).replace('STYLE',style).replace('NATIVE_COLOR_BODY',native_background).replace('GLASS_HOOK_BODY',glass_background).replace('ARC_TINT_BODY',tint)
    test=args.work/'ShellDrawableProbe.java';test.write_text(source)
    policy=ROOT/'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java'
    window=args.work/'ArchiumWindowClass.java'
    window.write_text('package org.chromium.chrome.browser.desktop_policy; public class ArchiumWindowClass { public static ArchiumWindowClass classify(int w){return new ArchiumWindowClass();} public boolean usesDesktopNavigation(){return true;} }')
    cp=args.classpath_file.read_text().strip()
    subprocess.run([str(args.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),str(test),str(policy),str(window)],check=True)
    result=subprocess.run([str(args.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF',
        '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,
        'org.junit.runner.JUnitCore','ShellDrawableProbe'])
    print('SCOPE=real_Android_drawables_layout_extracted_production_methods_with_explicit_native_adapters')
    raise SystemExit(result.returncode)


if __name__=='__main__': main()
