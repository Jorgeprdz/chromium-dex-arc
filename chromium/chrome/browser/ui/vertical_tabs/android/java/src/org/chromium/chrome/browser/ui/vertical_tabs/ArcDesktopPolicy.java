// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import org.chromium.chrome.browser.desktop_policy.ArchiumWindowClass;

/** Window eligibility and accessible colors, independent of Android and tab models. */
public final class ArcDesktopPolicy {
    private ArcDesktopPolicy() {}

    public static boolean isDesktopWindow(int currentWidthDp) {
        return ArchiumWindowClass.classify(currentWidthDp).usesDesktopNavigation();
    }

    public static int surface(int seed, boolean dark) {
        return blend(seed, dark ? 0xff141414 : 0xfffafafa, dark ? 0.22 : 0.12);
    }

    public static int selection(int surface) {
        return blend(foreground(surface), surface, 0.12);
    }

    public static int foreground(int background) {
        return contrast(background, 0xff000000) >= contrast(background, 0xffffffff)
                ? 0xff000000 : 0xffffffff;
    }

    public static double contrast(int first, int second) {
        double a = luminance(first);
        double b = luminance(second);
        return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    }

    private static double luminance(int color) {
        return linear((color >> 16) & 255) * 0.2126
                + linear((color >> 8) & 255) * 0.7152
                + linear(color & 255) * 0.0722;
    }

    private static double linear(int channel) {
        double value = channel / 255.0;
        return value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
    }

    private static int blend(int foreground, int background, double fraction) {
        int result = 0xff000000;
        for (int shift = 0; shift <= 16; shift += 8) {
            int a = (foreground >> shift) & 255;
            int b = (background >> shift) & 255;
            result |= ((int) Math.round(a * fraction + b * (1 - fraction))) << shift;
        }
        return result;
    }
}
