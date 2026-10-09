// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.res.ColorStateList;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.InsetDrawable;
import android.util.TypedValue;
import android.view.View;
import android.widget.TextView;

import org.chromium.chrome.browser.desktop_policy.ArchiumWindowMetrics;

import java.util.WeakHashMap;

/** Arc styling follows the current usable window; independent of vendor or desktop service. */
public final class ArcDesktopAppearance {
    public static final String COLOR_KEY = "frame_color";
    public static final String UI_MODE_KEY = "ui_mode";
    public static final int DEFAULT_COLOR = 0xff53657b;
    public static final int WARM_COLOR = 0xffedae9f;

    private static ColorStateList sNewTabBackgroundTint;
    private static int sNewTabBackgroundColor;
    private static final WeakHashMap<View, SidebarBackground> sSidebarBackgrounds = new WeakHashMap<>();
    private static final WeakHashMap<TextView, Float> sOriginalTextSizes = new WeakHashMap<>();
    private static final WeakHashMap<GradientDrawable, Float> sOriginalCornerRadii = new WeakHashMap<>();

    private static final class SidebarBackground {
        final GradientDrawable drawable = new GradientDrawable();
        int start;
        int end;

        SidebarBackground() {
            drawable.setOrientation(GradientDrawable.Orientation.TOP_BOTTOM);
        }
    }

    private ArcDesktopAppearance() {}

    public static boolean isDesktopWindow(Context context) {
        return ArcDesktopPolicy.isArcWindow(getUiMode(context),
                ArchiumWindowMetrics.currentWidthDp(context));
    }

    public static int getUiMode(Context context) {
        int preference = preferences(context).getInt(UI_MODE_KEY, ArcDesktopPolicy.MODE_AUTO);
        if (preference != ArcDesktopPolicy.MODE_ARC
                && preference != ArcDesktopPolicy.MODE_MOBILE) {
            return ArcDesktopPolicy.MODE_AUTO;
        }
        return preference;
    }

    public static void setUiMode(Context context, int preference) {
        if (preference != ArcDesktopPolicy.MODE_AUTO && preference != ArcDesktopPolicy.MODE_ARC
                && preference != ArcDesktopPolicy.MODE_MOBILE) {
            throw new IllegalArgumentException("Invalid Arc appearance mode");
        }
        preferences(context).edit().putInt(UI_MODE_KEY, preference).apply();
    }

    @SuppressWarnings("UseSharedPreferencesManagerFromChromeCheck")
    public static SharedPreferences preferences(Context context) {
        return context.getApplicationContext().getSharedPreferences("arc_appearance", Context.MODE_PRIVATE);
    }

    public static int surface(Context context, boolean incognito) {
        boolean dark = incognito || (context.getResources().getConfiguration().uiMode
                & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
        int seed = preferences(context).getInt(COLOR_KEY, DEFAULT_COLOR);
        return ArcDesktopPolicy.surface(seed, dark);
    }

    private static boolean isDark(Context context, boolean incognito) {
        return incognito || (context.getResources().getConfiguration().uiMode
                & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
    }

    public static int gradientStart(Context context, boolean incognito) {
        return ArcDesktopPolicy.gradientStart(preferences(context).getInt(COLOR_KEY, DEFAULT_COLOR),
                isDark(context, incognito));
    }

    public static int gradientEnd(Context context, boolean incognito) {
        return ArcDesktopPolicy.gradientEnd(preferences(context).getInt(COLOR_KEY, DEFAULT_COLOR),
                isDark(context, incognito));
    }

    public static int foreground(Context context, boolean incognito) {
        return ArcDesktopPolicy.gradientForeground(preferences(context).getInt(COLOR_KEY, DEFAULT_COLOR),
                isDark(context, incognito));
    }

    /** Paint once on the containing native frame; child rails remain transparent. */
    public static void applySidebarBackground(View view, boolean incognito) {
        SidebarBackground background = sSidebarBackgrounds.get(view);
        if (background == null) {
            background = new SidebarBackground();
            sSidebarBackgrounds.put(view, background);
        }
        int start = gradientStart(view.getContext(), incognito);
        int end = gradientEnd(view.getContext(), incognito);
        if (background.start != start || background.end != end) {
            background.start = start;
            background.end = end;
            background.drawable.setColors(new int[] {start, end});
        }
        if (view.getBackground() != background.drawable) view.setBackground(background.drawable);
    }

    /** Keep New Tab quiet at rest while preserving visible native hover, press and focus states. */
    public static ColorStateList newTabBackgroundTint(Context context, boolean incognito) {
        int interaction = selection(context, incognito);
        if (sNewTabBackgroundTint == null || sNewTabBackgroundColor != interaction) {
            sNewTabBackgroundColor = interaction;
            sNewTabBackgroundTint = new ColorStateList(
                    new int[][] {{android.R.attr.state_pressed}, {android.R.attr.state_hovered},
                            {android.R.attr.state_focused}, {}},
                    new int[] {interaction, interaction, interaction, 0x00000000});
        }
        return sNewTabBackgroundTint;
    }

    /** Native SP conversion respects font accessibility; MOBILE restores the measured XML size. */
    public static void applyTabTextSize(TextView title) {
        if (isDesktopWindow(title.getContext())) {
            if (!sOriginalTextSizes.containsKey(title)) sOriginalTextSizes.put(title, title.getTextSize());
            float desired = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP,
                    ArcDesktopPolicy.ARC_TAB_TEXT_SIZE_SP, title.getResources().getDisplayMetrics());
            if (title.getTextSize() != desired) {
                title.setTextSize(TypedValue.COMPLEX_UNIT_SP, ArcDesktopPolicy.ARC_TAB_TEXT_SIZE_SP);
            }
        } else {
            Float original = sOriginalTextSizes.remove(title);
            if (original != null) title.setTextSize(TypedValue.COMPLEX_UNIT_PX, original);
        }
    }

    /** Mutate only the native regular-row shape, preserving native hover tints and focus rings. */
    public static void applyTabCorners(View view) {
        Drawable background = view.getBackground();
        if (background instanceof InsetDrawable inset) background = inset.getDrawable();
        if (!(background instanceof GradientDrawable shape)) return;
        if (isDesktopWindow(view.getContext())) {
            if (!sOriginalCornerRadii.containsKey(shape)) {
                shape.mutate();
                sOriginalCornerRadii.put(shape, shape.getCornerRadius());
            }
            float desired = ArcDesktopPolicy.selectedTabRadius(view.getRootView().getWidth(),
                    view.getResources().getDisplayMetrics().density);
            if (shape.getCornerRadius() != desired) shape.setCornerRadius(desired);
        } else {
            Float original = sOriginalCornerRadii.remove(shape);
            if (original != null) shape.setCornerRadius(original);
        }
    }

    public static int selection(Context context, boolean incognito) {
        return ArcDesktopPolicy.selection(gradientStart(context, incognito));
    }
}
