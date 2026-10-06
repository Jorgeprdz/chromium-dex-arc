// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.desktop_policy;

import android.content.Context;
import android.content.res.Configuration;
import android.graphics.Insets;
import android.os.Build;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.view.WindowMetrics;

/** Reads the current usable window. Callers must provide their window-scoped Context. */
public final class ArchiumWindowMetrics {
    private ArchiumWindowMetrics() {}

    public static int configurationWidthDp(Configuration configuration) {
        return Math.max(0, configuration.screenWidthDp);
    }

    public static int currentWidthDp(Context context) {
        // Application/display contexts do not represent an Activity's freeform or split window.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !context.isUiContext()) return 0;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            WindowManager manager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
            if (manager != null) {
                try {
                    WindowMetrics metrics = manager.getCurrentWindowMetrics();
                    Insets insets = metrics.getWindowInsets().getInsetsIgnoringVisibility(
                            WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                    int widthPixels = metrics.getBounds().width() - insets.left - insets.right;
                    float density = context.getResources().getDisplayMetrics().density;
                    if (widthPixels > 0 && density > 0) return (int) Math.floor(widthPixels / density);
                } catch (IllegalStateException | UnsupportedOperationException exception) {
                    // During window attachment the metrics can be unavailable; window Configuration
                    // remains the adaptive fallback. Never use getDefaultDisplay or panel dimensions.
                }
            }
        }
        return configurationWidthDp(context.getResources().getConfiguration());
    }
}
