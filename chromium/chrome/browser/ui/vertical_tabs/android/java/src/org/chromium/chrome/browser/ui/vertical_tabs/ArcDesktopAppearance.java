// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.view.Display;
import android.view.WindowManager;

/** Arc styling only for the current desktop window, never inferred from width or build flags. */
public final class ArcDesktopAppearance {
    public static final String COLOR_KEY = "frame_color";
    public static final int DEFAULT_COLOR = 0xff53657b;

    private ArcDesktopAppearance() {}

    public static boolean isDesktopWindow(Context context) {
        WindowManager manager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
        if (manager == null) return false;
        Display display = manager.getDefaultDisplay();
        // FEATURE_PC describes the runtime device, unlike IS_DESKTOP_ANDROID which describes
        // this APK and is also true when installed on a phone.
        boolean pc = context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_PC);
        return ArcDesktopPolicy.isDesktopWindow(
                display.getDisplayId() == Display.DEFAULT_DISPLAY,
                isDexConfiguration(context.getResources().getConfiguration()), pc);
    }

    private static boolean isDexConfiguration(Configuration config) {
        // Samsung documents these fields for the WINDOW's Configuration. The global desktopmode
        // service can report DeX active even for an activity still on the phone's screen.
        try {
            Class<?> type = config.getClass();
            int enabled = type.getField("SEM_DESKTOP_MODE_ENABLED").getInt(null);
            return enabled == type.getField("semDesktopModeEnabled").getInt(config);
        } catch (ReflectiveOperationException | SecurityException e) {
            // Unknown vendor/mode stays mobile; do not guess from display size.
            return false;
        }
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
