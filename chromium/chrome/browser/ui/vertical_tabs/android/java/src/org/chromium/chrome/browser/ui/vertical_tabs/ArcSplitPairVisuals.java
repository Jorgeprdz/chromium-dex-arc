// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.text.TextPaint;
import android.text.TextUtils;

/** Presentation only: retains the native favicon artwork and two independently ellipsized titles. */
public final class ArcSplitPairVisuals {
    private ArcSplitPairVisuals() {}

    public static CharSequence title(
            CharSequence left, CharSequence right, TextPaint paint, float width) {
        String separator = " | ";
        float half = Math.max(0, (width - paint.measureText(separator)) / 2);
        return TextUtils.concat(TextUtils.ellipsize(left, paint, half, TextUtils.TruncateAt.END),
                separator, TextUtils.ellipsize(right, paint, half, TextUtils.TruncateAt.END));
    }

    public static Drawable icons(Drawable left, Drawable right, int dividerColor) {
        return new Drawable() {
            private final Paint mPaint = new Paint();
            @Override public void draw(Canvas canvas) {
                Rect b = getBounds();
                int middle = b.left + (b.width() - 1) / 2;
                fit(canvas, left, new Rect(b.left, b.top, middle, b.bottom));
                fit(canvas, right, new Rect(middle + 1, b.top, b.right, b.bottom));
                mPaint.setColor(dividerColor);
                canvas.drawRect(middle, b.top, middle + 1, b.bottom, mPaint);
            }
            @Override public void setAlpha(int alpha) { mPaint.setAlpha(alpha); }
            @Override public void setColorFilter(ColorFilter filter) {}
            @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
        };
    }

    private static void fit(Canvas canvas, Drawable icon, Rect area) {
        if (area.isEmpty()) return;
        Rect original = new Rect(icon.getBounds());
        int iw = Math.max(1, icon.getIntrinsicWidth());
        int ih = Math.max(1, icon.getIntrinsicHeight());
        float scale = Math.min((float) area.width() / iw, (float) area.height() / ih);
        int width = Math.round(iw * scale), height = Math.round(ih * scale);
        int x = area.left + (area.width() - width) / 2;
        int y = area.top + (area.height() - height) / 2;
        try {
            icon.setBounds(x, y, x + width, y + height);
            icon.draw(canvas);
        } finally {
            icon.setBounds(original);
        }
    }
}
