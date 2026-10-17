// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import android.app.Activity;
import android.content.Context;
import android.content.ContextWrapper;

import java.util.WeakHashMap;
import android.content.pm.PackageManager;
import android.os.Build;
import android.view.Display;
import android.view.WindowManager;
import android.content.SharedPreferences;
import android.content.res.Configuration;

import org.chromium.chrome.browser.desktop_policy.ArchiumWindowMetrics;

/** Arc styling follows the current usable window; independent of vendor or desktop service. */
public final class ArcDesktopAppearance {
    public static final String UI_FONT_KEY = "ui_font";
    public static final String COLOR_KEY = "frame_color";
    public static final String UI_MODE_KEY = "ui_mode";
    public static final String ADDRESS_BAR_POSITION_KEY = "address_bar_position";
    public static final int ADDRESS_SIDEBAR = 0;
    public static final int ADDRESS_TOP = 1;
    public static final int DEFAULT_COLOR = 0xff53657b;

    // UI-thread only. A draft belongs to its Activity, never another window or saved profile.
    private static final WeakHashMap<Context, Integer> PREVIEW_COLORS = new WeakHashMap<>();

    private ArcDesktopAppearance() {}

    public static int getAddressBarPosition(Context context) {
        return preferences(context).getInt(ADDRESS_BAR_POSITION_KEY, ADDRESS_SIDEBAR) == ADDRESS_TOP
                ? ADDRESS_TOP : ADDRESS_SIDEBAR;
    }

    public static void setAddressBarPosition(Context context, int position) {
        if (position != ADDRESS_SIDEBAR && position != ADDRESS_TOP) {
            throw new IllegalArgumentException("Invalid address bar position");
        }
        preferences(context).edit().putInt(ADDRESS_BAR_POSITION_KEY, position).apply();
    }

    public static int getUiFont(Context context) {
        int font = preferences(context).getInt(UI_FONT_KEY, 0);
        return font >= 0 && font <= 3 ? font : 0;
    }

    public static void setUiFont(Context context, int font) {
        if (font < 0 || font > 3) throw new IllegalArgumentException("Invalid UI font");
        preferences(context).edit().putInt(UI_FONT_KEY, font).apply();
    }

    /** Apply only to browser controls/settings, never a page or compositor subtree. */
    public static void applyUiFont(android.view.View controls) {
        String[] families = {"sans-serif", "sans-serif-medium", "serif", "monospace"};
        applyUiFont(controls, families[getUiFont(controls.getContext())]);
    }

    private static void applyUiFont(android.view.View view, String family) {
        if (view instanceof android.widget.TextView text) {
            android.graphics.Typeface current = text.getTypeface();
            android.graphics.Typeface selected = android.graphics.Typeface.create(
                    family, current == null ? 0 : current.getStyle());
            if (!selected.equals(current)) text.setTypeface(selected);
        }
        if (view instanceof android.view.ViewGroup group) {
            for (int i = 0; i < group.getChildCount(); i++) applyUiFont(group.getChildAt(i), family);
        }
    }

    private static Context visualContext(Context context) {
        while (!(context instanceof Activity) && context instanceof ContextWrapper wrapper) {
            Context base = wrapper.getBaseContext();
            if (base == context) break;
            context = base;
        }
        return context;
    }

    public static void setPreviewColor(Context context, Integer color) {
        Context window = visualContext(context);
        if (color == null) PREVIEW_COLORS.remove(window);
        else PREVIEW_COLORS.put(window, color);
    }

    public static boolean isDesktopWindow(Context context) {
        int mode = getUiMode(context);
        if (mode == ArcDesktopPolicy.MODE_ARC) return true;
        if (mode == ArcDesktopPolicy.MODE_MOBILE) return false;
        Configuration config = context.getResources().getConfiguration();
        boolean desktop = config.smallestScreenWidthDp >= 600
                || (config.uiMode & Configuration.UI_MODE_TYPE_MASK) == Configuration.UI_MODE_TYPE_DESK
                || context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_PC);
        if (context instanceof Activity activity) {
            Display display = activityDisplay(activity);
            desktop |= activity.isInMultiWindowMode()
                    || (display != null && display.getDisplayId() != Display.DEFAULT_DISPLAY);
        }
        return desktop && ArcDesktopPolicy.isArcWindow(mode,
                ArchiumWindowMetrics.currentWidthDp(context));
    }

    @SuppressWarnings("deprecation")
    static Display activityDisplay(Activity activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Display display = activity.getDisplay();
                if (display != null) return display;
            } catch (UnsupportedOperationException unavailableVisualContext) {
                // The Activity's WindowManager is the API 29/nonvisual fallback.
            }
        }
        WindowManager manager = activity.getWindowManager();
        return manager == null ? null : manager.getDefaultDisplay();
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
        Integer preview = PREVIEW_COLORS.get(visualContext(context));
        if (preview != null) return ArcDesktopPolicy.surface(preview, dark);
        SharedPreferences saved = preferences(context);
        if (!saved.contains(COLOR_KEY)) return ArcDesktopPolicy.defaultSurface(dark);
        return ArcDesktopPolicy.surface(saved.getInt(COLOR_KEY, DEFAULT_COLOR), dark);
    }

    public static int activeTabSurface(Context context, boolean incognito) {
        if (incognito) return selection(context, true);
        boolean custom = PREVIEW_COLORS.containsKey(visualContext(context))
                || preferences(context).contains(COLOR_KEY);
        return custom ? ArcDesktopPolicy.activeTabSurface(surface(context, false)) : 0xffffffff;
    }

    public static int foreground(Context context, boolean incognito) {
        return ArcDesktopPolicy.foreground(surface(context, incognito));
    }

    public static int selection(Context context, boolean incognito) {
        return ArcDesktopPolicy.selection(surface(context, incognito));
    }
}
