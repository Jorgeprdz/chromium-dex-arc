// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.desktop_policy;

import static androidx.window.core.layout.WindowSizeClass.WIDTH_DP_EXPANDED_LOWER_BOUND;
import static androidx.window.core.layout.WindowSizeClass.WIDTH_DP_MEDIUM_LOWER_BOUND;

/** Current-window classes shared by navigation and Archium UI, independent of hardware. */
public enum ArchiumWindowClass {
    COMPACT,
    TABLET,
    DESKTOP;

    public static ArchiumWindowClass classify(int currentWidthDp) {
        if (currentWidthDp >= WIDTH_DP_EXPANDED_LOWER_BOUND) return DESKTOP;
        if (currentWidthDp >= WIDTH_DP_MEDIUM_LOWER_BOUND) return TABLET;
        return COMPACT;
    }

    public boolean usesDesktopNavigation() {
        return this != COMPACT;
    }
}
