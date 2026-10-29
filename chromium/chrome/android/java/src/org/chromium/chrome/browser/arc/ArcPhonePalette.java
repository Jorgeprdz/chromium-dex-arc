// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Color;

/** Metadata-only phone color roles. The approved reveal resolver is never changed here. */
final class ArcPhonePalette {
    static final int FALLBACK = 0xff3b82f6;
    private ArcPhonePalette() {}

    static int accent(int page, boolean dark) {
        float[] hsv = new float[3];
        Color.colorToHSV(page, hsv);
        if (Color.alpha(page) == 0 || hsv[1] < .06f) Color.colorToHSV(FALLBACK, hsv);
        hsv[1] = Math.max(.30f, Math.min(dark ? .58f : .70f, hsv[1]));
        hsv[2] = dark ? .96f : .80f;
        return Color.HSVToColor(hsv);
    }

    static int statusTint(int page, int surface) {
        if (Color.alpha(page) == 0) return surface | 0xff000000;
        float[] hsv = new float[3]; Color.colorToHSV(page, hsv);
        boolean light = Color.luminance(surface) > .45;
        // Keep hue, but constrain the backing luminance to the native indicator contrast role.
        hsv[1] *= light ? .12f : .22f;
        hsv[2] = light ? 1f : .13f;
        return Color.HSVToColor(hsv);
    }

    static int statusOpacity(int page, int surface) {
        boolean light = Color.luminance(surface) > .45;
        if (Color.alpha(page) == 0) return 170;
        double luminance = Color.luminance(page | 0xff000000);
        double mismatch = light ? 1 - luminance : luminance;
        return (light ? 138 : 176) + (int) Math.round(12 * mismatch);
    }
}
