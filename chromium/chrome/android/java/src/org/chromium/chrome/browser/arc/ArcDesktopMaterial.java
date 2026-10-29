// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Outline;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.Shader;
import android.graphics.drawable.Drawable;

/** Desktop-only frosted finish for regions without web pixels behind them. Not window blur. */
public final class ArcDesktopMaterial extends Drawable {
    public static final String INTENSITY_KEY = "desktop_material_intensity";
    public static final int DEFAULT_INTENSITY = 60;
    private final Paint mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private int mSurface, mIntensity = -1, mAlpha = 255;
    private int[] mColors;
    private int mViewportHeight, mOffsetY;
    private final int[] mPosition = new int[2];
    public void setViewport(int height, int offsetY) {
        if (mViewportHeight == height && mOffsetY == offsetY) return;
        mViewportHeight = height; mOffsetY = offsetY; updateShader(); invalidateSelf();
    }

    /** All frame regions sample the same vertical ramp, including the native top toolbar. */
    public void alignWithFrame(android.view.View target, android.view.View frame) {
        if (target == null || frame == null) return;
        frame.getLocationInWindow(mPosition); int top = mPosition[1];
        target.getLocationInWindow(mPosition);
        setViewport(frame.getHeight(), mPosition[1] - top);
    }

    public static int clamp(int value) { return Math.max(0, Math.min(100, value)); }
    public static int savedIntensity(SharedPreferences prefs) {
        return clamp(prefs.getInt(INTENSITY_KEY, DEFAULT_INTENSITY));
    }
    static int foreground(int color) {
        return contrast(color, Color.BLACK) >= contrast(color, Color.WHITE) ? Color.BLACK : Color.WHITE;
    }
    static double contrast(int a, int b) {
        double x = Color.luminance(a), y = Color.luminance(b);
        return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
    }
    private static int mix(int a, int b, double amount) {
        return Color.rgb((int)Math.round(Color.red(a) * (1 - amount) + Color.red(b) * amount),
                (int)Math.round(Color.green(a) * (1 - amount) + Color.green(b) * amount),
                (int)Math.round(Color.blue(a) * (1 - amount) + Color.blue(b) * amount));
    }
    private static int safeTone(int surface, int light, double amount) {
        int fg = foreground(surface);
        if (contrast(mix(surface, light, amount), fg) >= 4.5) return mix(surface, light, amount);
        double low = 0, high = amount;
        for (int i = 0; i < 16; i++) {
            double mid = (low + high) / 2;
            if (contrast(mix(surface, light, mid), fg) >= 4.5) low = mid; else high = mid;
        }
        return mix(surface, light, low);
    }
    static int[] ramp(int surface, int intensity) {
        double strength = clamp(intensity) / 100.0;
        return new int[] {safeTone(surface, Color.WHITE, .40 * strength), surface,
                safeTone(surface, Color.BLACK, .09 * strength)};
    }
    public void setAppearance(int surface, int intensity) {
        intensity = clamp(intensity);
        if (mColors != null && mSurface == surface && mIntensity == intensity) return;
        mSurface = surface; mIntensity = intensity; mColors = ramp(surface, intensity);
        updateShader(); invalidateSelf();
    }
    private void updateShader() {
        if (mColors == null) return;
        Rect b = getBounds();
        int top = mViewportHeight > 0 ? b.top - mOffsetY : b.top;
        int bottom = mViewportHeight > 0 ? top + mViewportHeight : b.bottom;
        mPaint.setShader(new LinearGradient(b.left, top, b.left, Math.max(top + 1, bottom),
                mColors, new float[] {0, .48f, 1}, Shader.TileMode.CLAMP));
    }
    @Override protected void onBoundsChange(Rect bounds) { updateShader(); }
    @Override public void draw(Canvas canvas) {
        if (mColors == null) return;
        mPaint.setAlpha(mAlpha); canvas.drawRect(getBounds(), mPaint);
    }
    @Override public void getOutline(Outline outline) { outline.setRect(getBounds()); outline.setAlpha(.12f); }
    @Override public void setAlpha(int alpha) { mAlpha = alpha; invalidateSelf(); }
    @Override public void setColorFilter(ColorFilter filter) { mPaint.setColorFilter(filter); invalidateSelf(); }
    @Override public int getOpacity() { return mAlpha == 255 ? PixelFormat.OPAQUE : PixelFormat.TRANSLUCENT; }
}
