// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.content.pm.PackageManager;
import android.view.Display;
import android.view.View;
import android.view.Window;

import org.chromium.chrome.browser.desktop_policy.ArchiumWindowMetrics;

/** Arc styling follows the current usable window; independent of vendor or desktop service. */
public final class ArcDesktopAppearance {
    public static final String COLOR_KEY = "frame_color";
    public static final String UI_MODE_KEY = "ui_mode";
    public static final int DEFAULT_COLOR = 0xff53657b;
    // Opaque tint seeds, not transparent or simulated backdrop blur.
    public static final int[] FRAME_COLOR_PRESETS = {
        0xff53657b, 0xff998ac3, 0xff7e9a8d, 0xffb6a17b,
        0xffbe879c, 0xff444750, 0xff438cb8, 0xffda886b
    };

    private ArcDesktopAppearance() {}

    public static boolean isDesktopWindow(Context context) {
        int preference = getUiMode(context);
        if (preference == ArcDesktopPolicy.MODE_ARC) return true;
        if (preference == ArcDesktopPolicy.MODE_MOBILE) return false;
        Configuration configuration = context.getResources().getConfiguration();
        boolean tablet = configuration.smallestScreenWidthDp >= 600;
        boolean desktopUi = (configuration.uiMode & Configuration.UI_MODE_TYPE_MASK)
                == Configuration.UI_MODE_TYPE_DESK;
        boolean pc = context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_PC);
        // Read the visual window, not Activity.getDisplay(): a not-yet-attached Activity
        // can have a nonvisual Context (including during Robolectric view inflation).
        // Only attached decor Views represent a real display; this preserves external
        // display and multi-window detection in real Android Desktop environments.
        boolean desktopActivity = false;
        if (context instanceof Activity activity) {
            Window window = activity.getWindow();
            View decor = window != null ? window.getDecorView() : null;
            Display display = decor != null && decor.isAttachedToWindow()
                    ? decor.getDisplay() : null;
            desktopActivity = activity.isInMultiWindowMode()
                    || (display != null && display.getDisplayId() != Display.DEFAULT_DISPLAY);
        }
        return ArcDesktopPolicy.isArcWindow(
                preference, ArchiumWindowMetrics.currentWidthDp(context),
                tablet || desktopUi || pc || desktopActivity);
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

    public static int foreground(Context context, boolean incognito) {
        return ArcDesktopPolicy.foreground(surface(context, incognito));
    }

    public static int selection(Context context, boolean incognito) {
        return ArcDesktopPolicy.selection(surface(context, incognito));
    }
}
