// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import java.util.Locale;

/** Unsaved picker state. HEX, RGB and presets share one opaque color value. */
public final class ArcColorDraft {
    private static final int[] PRESETS = {
        0xff53657b, 0xff998ac3, 0xff7e9a8d, 0xffb6a17b,
        0xffbe879c, 0xff444750, 0xff438cb8, 0xffda886b
    };
    private final int mOriginal;
    private final int mDefault;
    private int mColor;
    private boolean mValid = true;
    private boolean mClearPreference;

    public ArcColorDraft(int original, int defaultColor) {
        mOriginal = original | 0xff000000;
        mDefault = defaultColor | 0xff000000;
        mColor = mOriginal;
    }

    public static int presetCount() {
        return PRESETS.length;
    }

    public static int presetAt(int index) {
        return PRESETS[index];
    }

    public int color() {
        return mColor;
    }

    public String hex() {
        return String.format(Locale.ROOT, "#%06X", mColor & 0xffffff);
    }

    public boolean isValid() {
        return mValid;
    }

    public boolean shouldClearPreference() {
        return mClearPreference;
    }

    public boolean setHex(String value) {
        String text = value == null ? "" : value.trim();
        mValid = text.matches("#[0-9a-fA-F]{6}");
        if (mValid) {
            mColor = 0xff000000 | Integer.parseInt(text.substring(1), 16);
            mClearPreference = false;
        }
        return mValid;
    }

    public void setRgb(int red, int green, int blue) {
        if (red < 0 || red > 255 || green < 0 || green > 255 || blue < 0 || blue > 255) {
            throw new IllegalArgumentException("RGB channel outside 0..255");
        }
        mColor = 0xff000000 | (red << 16) | (green << 8) | blue;
        mValid = true;
        mClearPreference = false;
    }

    public int selectedPreset() {
        if (mValid) {
            for (int i = 0; i < PRESETS.length; i++) {
                if (PRESETS[i] == mColor) return i;
            }
        }
        return -1;
    }

    public void reset() {
        mColor = mDefault;
        mValid = true;
        mClearPreference = true;
    }

    public void cancel() {
        mColor = mOriginal;
        mValid = true;
        mClearPreference = false;
    }
}
