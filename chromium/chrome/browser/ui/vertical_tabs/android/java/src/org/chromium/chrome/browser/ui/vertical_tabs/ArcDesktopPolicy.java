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
    public static final int ARC_NAV_ROW_HEIGHT_DP = 48;
    public static final int ARC_NAV_BUTTON_WIDTH_DP = 48;
    public static final int ARC_FULL_CONTROLS_MIN_WIDTH_DP = ARC_NAV_BUTTON_WIDTH_DP * 4;
    public static final int ARC_FULL_CONTROLS_MIN_HEIGHT_DP = 360;
    public static final int ARC_NATIVE_SEARCH_MIN_HEIGHT_DP = ARC_NAV_ROW_HEIGHT_DP * 3;
    public static final int ARC_NATIVE_FOOTER_MIN_HEIGHT_DP = ARC_NAV_ROW_HEIGHT_DP * 2;

    private ArcDesktopPolicy() {}

    // Image measurements are normalized by measured window width, not treated as Android dp.
    public static final int REFERENCE_WINDOW_WIDTH = 1382;
    public static final int REFERENCE_WINDOW_HEIGHT = 863;
    public static final int REFERENCE_SIDEBAR_WIDTH = 334;
    // Leave the native search/tab header before the selected-tab reference band around y305.
    // This bounds a scroll viewport, never positions a selected tab at an absolute coordinate.
    public static final int REFERENCE_HEADER_MAX_HEIGHT = 257;
    public static final int NATIVE_MIN_EXPANDED_WIDTH_DP = 92;
    public static final int NATIVE_MAX_EXPANDED_WIDTH_DP = 500;
    public static final int COLLAPSED_WIDTH_DP = 52;

    /** Native Side UI owns availableWidthPx (including its minimum web-content constraint). */
    public static int expandedSidebarWidth(int windowWidthPx, int availableWidthPx, float density) {
        if (!validDensity(density) || windowWidthPx <= 0 || availableWidthPx <= 0) return 0;
        int nativeMinimum = Math.round(NATIVE_MIN_EXPANDED_WIDTH_DP * density);
        int navigationMinimum = Math.round((ARC_FULL_CONTROLS_MIN_WIDTH_DP + 18) * density);
        int preferred = Math.round((float) windowWidthPx * REFERENCE_SIDEBAR_WIDTH
                / REFERENCE_WINDOW_WIDTH);
        return Math.min(Math.min(windowWidthPx, availableWidthPx),
                Math.min(Math.round(NATIVE_MAX_EXPANDED_WIDTH_DP * density),
                        Math.max(Math.max(nativeMinimum, navigationMinimum), preferred)));
    }

    public static final class Geometry {
        public final int viewportLeft, viewportTop, viewportRight, viewportBottom;
        public final int topInset, endInset, bottomInset, outerRadius, viewportRadius;
        public final int sideInset, headerTopInset, omniboxHeight, navigationHeight;
        public final int quickAccessHeight, quickAccessGap, quickAccessSecondGap, omniboxBottomGap;
        public final int footerHeight, footerBottomInset, sectionGap;

        private Geometry(int width, int height, int sidebar, float density, boolean sidebarOnRight) {
            float scale = referenceScale(width, density);
            topInset = Math.round(12 * scale);
            endInset = Math.round(11 * scale);
            bottomInset = Math.round(11 * scale);
            outerRadius = Math.round(13 * scale);
            viewportRadius = Math.round(11 * scale);
            sideInset = Math.round(9 * scale);
            headerTopInset = Math.round(9 * scale);
            navigationHeight = Math.round(ARC_NAV_ROW_HEIGHT_DP * density);
            omniboxHeight = Math.max(navigationHeight, Math.round(49 * scale));
            quickAccessHeight = Math.max(navigationHeight, Math.round(57 * scale));
            quickAccessGap = Math.round(9 * scale);
            quickAccessSecondGap = Math.round(8 * scale);
            omniboxBottomGap = Math.round(10 * scale);
            sectionGap = Math.round(8 * density);
            footerHeight = navigationHeight;
            footerBottomInset = Math.round(6 * scale);
            int allocatedSidebar = Math.max(0, Math.min(width, sidebar));
            viewportLeft = sidebarOnRight ? Math.min(endInset, width - allocatedSidebar)
                    : allocatedSidebar;
            viewportRight = Math.max(viewportLeft,
                    sidebarOnRight ? width - allocatedSidebar : width - endInset);
            viewportTop = Math.min(topInset, height);
            viewportBottom = Math.max(viewportTop, height - bottomInset);
        }
    }

    /** Window-local physical pixel bounds; Android insets/caption are supplied by native layout. */
    public static Geometry geometry(
            int widthPx, int heightPx, int sidebarPx, float density, boolean sidebarOnRight) {
        return new Geometry(Math.max(0, widthPx), Math.max(0, heightPx), sidebarPx,
                validDensity(density) ? density : 0f, sidebarOnRight);
    }

    public static float referenceScale(int windowWidthPx, float density) {
        if (!validDensity(density) || windowWidthPx <= 0) return 0f;
        // Bound decoration growth on tiny/ultrawide windows while keeping density-aware limits.
        return Math.max(density * 0.5f,
                Math.min(density * 1.5f, (float) windowWidthPx / REFERENCE_WINDOW_WIDTH));
    }

    private static boolean validDensity(float density) {
        return density > 0f && Float.isFinite(density);
    }

    public static final class SidebarBudget {
        public final int headerHeight, footerHeight, tabHeight;

        private SidebarBudget(int height, int caption, int naturalHeader, float density, int footerInset) {
            int available = Math.max(0, height - Math.max(0, caption));
            int target = Math.round(ARC_NAV_ROW_HEIGHT_DP * density);
            // Utilities yield first. For physically tiny windows keep a nonzero native tab area.
            footerHeight = available >= target * 3 ? target + Math.max(0, footerInset) : 0;
            int minimumTabs = available >= target * 2 ? target
                    : Math.min(target, Math.max(available > 0 ? 1 : 0, available / 3));
            int preferredHeader = Math.max(target, Math.round((float) available
                    * REFERENCE_HEADER_MAX_HEIGHT / REFERENCE_WINDOW_HEIGHT));
            headerHeight = Math.max(0, Math.min(Math.min(naturalHeader, preferredHeader),
                    available - footerHeight - minimumTabs));
            tabHeight = available - footerHeight - headerHeight;
        }
    }

    /** Scroll the existing header when necessary, instead of consuming the entire native list. */
    public static SidebarBudget sidebarBudget(
            int heightPx, int captionPx, int naturalHeaderPx, float density) {
        return sidebarBudget(heightPx, captionPx, naturalHeaderPx, density, 0);
    }

    public static SidebarBudget sidebarBudget(
            int heightPx, int captionPx, int naturalHeaderPx, float density, int footerInsetPx) {
        return new SidebarBudget(Math.max(0, heightPx), captionPx,
                Math.max(0, naturalHeaderPx), validDensity(density) ? density : 0f, footerInsetPx);
    }

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

    /** Navigation remains available in short windows if four native-sized buttons fit. */
    public static boolean showNavigationControls(int railWidthPx, float density) {
        return density > 0f && Float.isFinite(density)
                && railWidthPx >= Math.round(ARC_FULL_CONTROLS_MIN_WIDTH_DP * density);
    }

    /** Remaining app-caption height after other top-control layers reserve their space. */
    public static int captionReserveHeight(int appHeaderHeight, int precedingLayersHeight) {
        return Math.max(0, appHeaderHeight - Math.max(0, precedingLayersHeight));
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
