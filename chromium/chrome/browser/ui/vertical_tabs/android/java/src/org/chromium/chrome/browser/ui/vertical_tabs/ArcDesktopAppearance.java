// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Configuration;

import org.chromium.chrome.browser.desktop_policy.ArchiumWindowMetrics;

/** Arc styling follows the current usable window; independent of vendor or desktop service. */
public final class ArcDesktopAppearance {
    public static final String COLOR_KEY = "frame_color";
    public static final int DEFAULT_COLOR = 0xff53657b;

    private ArcDesktopAppearance() {}

    public static boolean isDesktopWindow(Context context) {
        return ArcDesktopPolicy.isDesktopWindow(ArchiumWindowMetrics.currentWidthDp(context));
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
