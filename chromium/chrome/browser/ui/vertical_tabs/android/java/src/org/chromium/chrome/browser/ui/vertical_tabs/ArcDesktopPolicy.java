// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import org.chromium.chrome.browser.desktop_policy.ArchiumWindowClass;

/** Window eligibility and accessible colors, independent of Android and tab models. */
public final class ArcDesktopPolicy {
    public static final int MODE_AUTO = 0;
    public static final int MODE_ARC = 1;
    public static final int MODE_MOBILE = 2;

    // Semantic Arc frame dimensions. Keep these centralized so layout, clipping and hit testing
    // use one geometry contract instead of repeating magic numbers across views.
    public static final int ARC_OUTER_PADDING_DP = 8;
    public static final int ARC_FRAME_GAP_DP = 8;
    public static final int ARC_CONTENT_RADIUS_DP = 16;
    public static final int ARC_NAV_ROW_HEIGHT_DP = 44;
    public static final int ARC_NAV_BUTTON_WIDTH_DP = 44;
    public static final int ARC_LOCATION_BAR_SIDE_MARGIN_DP = 4;
    public static final int ARC_FULL_CONTROLS_MIN_WIDTH_DP = ARC_NAV_BUTTON_WIDTH_DP * 4;
    public static final int ARC_FULL_CONTROLS_MIN_HEIGHT_DP = 360;
    // Budget measured from the rail, not from the screenshot or the current sidebar width.
    // Nav (3 rows), new tab, footer, fixed collection chrome, rail padding and native tab room.
    private static final int ARC_COLLECTION_FIXED_CHROME_DP = 160;
    private static final int ARC_NEW_TAB_HEIGHT_DP = 44;
    private static final int ARC_MIN_NATIVE_TABS_DP = 112;
    public static final int ARC_MIN_COLLECTION_SCROLL_DP = 80;

    private ArcDesktopPolicy() {}

    /** UI preference only. Native desktop navigation always uses the actual window class. */
    public static boolean isArcWindow(int preference, int currentWidthDp) {
        if (preference == MODE_ARC) return true;
        if (preference == MODE_MOBILE) return false;
        return isDesktopWindow(currentWidthDp);
    }

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


    /** Whether the Arc sidebar has enough real layout space for its expanded controls. */
    public static boolean showFullControls(int railWidthPx, int railHeightPx, float density) {
        if (!(density > 0f)) return false;
        return railWidthPx >= Math.round(ARC_FULL_CONTROLS_MIN_WIDTH_DP * density)
                && railHeightPx >= Math.round(ARC_FULL_CONTROLS_MIN_HEIGHT_DP * density);
    }

    /** Free height for the scrollable collections region while reserving native tabs.
     * A short rail must use compact controls instead of starving the real tab list.
     * captionHeightPx is the native desktop caption spacer and may vary by window manager.
     */
    public static int collectionScrollBudgetPx(int railHeightPx, float density, int captionHeightPx) {
        if (!(density > 0f) || railHeightPx <= 0) return 0;
        int fixedDp = 3 * ARC_NAV_ROW_HEIGHT_DP + ARC_NEW_TAB_HEIGHT_DP
                + ARC_NAV_ROW_HEIGHT_DP + ARC_COLLECTION_FIXED_CHROME_DP
                + 2 * ARC_OUTER_PADDING_DP + ARC_MIN_NATIVE_TABS_DP;
        int remaining = railHeightPx - Math.round(fixedDp * density)
                - Math.max(0, captionHeightPx);
        return Math.min(Math.round(240f * density), Math.max(0, remaining));
    }

    /** Returns whether a point lies inside a rounded content rect. Pure math for UI + tests. */
    public static boolean containsRoundedRectPoint(
            float x, float y, int left, int top, int right, int bottom, float radius) {
        if (right <= left || bottom <= top || x < left || x >= right || y < top || y >= bottom) {
            return false;
        }
        float clampedRadius = Math.max(0f, Math.min(radius,
                Math.min((right - left) / 2f, (bottom - top) / 2f)));
        if (clampedRadius == 0f) return true;

        float innerLeft = left + clampedRadius;
        float innerRight = right - clampedRadius;
        float innerTop = top + clampedRadius;
        float innerBottom = bottom - clampedRadius;
        if ((x >= innerLeft && x < innerRight) || (y >= innerTop && y < innerBottom)) return true;

        float centerX = x < innerLeft ? innerLeft : innerRight;
        float centerY = y < innerTop ? innerTop : innerBottom;
        float dx = x - centerX;
        float dy = y - centerY;
        return dx * dx + dy * dy <= clampedRadius * clampedRadius;
    }

    /** R3 clip hitbox: the bottom-left interior join is square, other corners round. */
    public static boolean containsArcViewportPoint(
            float x, float y, int left, int top, int right, int bottom, float radius) {
        if (right <= left || bottom <= top || x < left || x >= right || y < top || y >= bottom) {
            return false;
        }
        float r = Math.max(0f, Math.min(radius,
                Math.min((right - left) / 2f, (bottom - top) / 2f)));
        if (r == 0f) return true;
        float dx;
        float dy;
        if (x < left + r && y < top + r) {
            dx = x - (left + r);
            dy = y - (top + r);
        } else if (x > right - r && y < top + r) {
            dx = x - (right - r);
            dy = y - (top + r);
        } else if (x > right - r && y > bottom - r) {
            dx = x - (right - r);
            dy = y - (bottom - r);
        } else {
            return true;
        }
        return dx * dx + dy * dy <= r * r;
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
