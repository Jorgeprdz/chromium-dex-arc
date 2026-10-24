// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.Shader;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.view.View;
import android.view.WindowInsets;

import org.chromium.build.annotations.Nullable;

/** Phone-only visual protection of status indicators; never owns layout, input or web insets. */
public final class ArcPhoneStatusFade {
    private final View mDecor;
    private final Fade mFade = new Fade();
    private final View.OnLayoutChangeListener mLayout = (v,l,t,r,b,ol,ot,or,ob) -> updateBounds();
    private boolean mAttached;

    public ArcPhoneStatusFade(View decor) { mDecor = decor; }

    /** Metadata changes only: a dead band prevents a neutral page palette from flipping icons. */
    public static int selectSurface(int pageColor, int previous) {
        double luminance = Color.luminance(pageColor | 0xff000000);
        if (luminance < .18) return 0xff202124;
        if (luminance > .30) return Color.WHITE;
        return previous == Color.WHITE ? Color.WHITE : 0xff202124;
    }

    public void update(boolean enabled, int surface) {
        mFade.setSurface(surface);
        if (enabled != mAttached) {
            mAttached = enabled;
            if (enabled) {
                // Drawable overlays cannot receive touches or accessibility focus. System icons
                // belong to a separate system window above the Activity overlay.
                mDecor.getOverlay().add(mFade);
                mDecor.addOnLayoutChangeListener(mLayout);
            } else {
                mDecor.getOverlay().remove(mFade);
                mDecor.removeOnLayoutChangeListener(mLayout);
            }
        }
        if (enabled) updateBounds();
    }

    /** Stable system geometry prevents a transient zero inset on fullscreen/IME exit. */
    public static int toolbarTopInset(WindowInsets raw) {
        int top = Build.VERSION.SDK_INT >= Build.VERSION_CODES.R
                ? raw.getInsetsIgnoringVisibility(WindowInsets.Type.statusBars()).top
                : raw.getSystemWindowInsetTop();
        android.view.DisplayCutout cutout = raw.getDisplayCutout();
        return cutout == null ? top : Math.max(top, cutout.getSafeInsetTop());
    }

    private void updateBounds() {
        WindowInsets raw = mDecor.getRootWindowInsets();
        int top = raw == null ? 0 : Build.VERSION.SDK_INT >= Build.VERSION_CODES.R
                ? raw.getInsets(WindowInsets.Type.statusBars()).top : raw.getSystemWindowInsetTop();
        // End before the toolbar: its approved color, shadow and size must remain untouched.
        // Hidden status bars give zero; navigation/IME insets never enlarge this overlay.
        Rect next = new Rect(0, 0, mDecor.getWidth(), Math.min(top, mDecor.getHeight()));
        if (!mFade.getBounds().equals(next)) mFade.setBounds(next);
    }

    public void destroy() { update(false, Color.TRANSPARENT); }

    static final class Fade extends Drawable {
        private final Paint mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private int mSurface;

        void setSurface(int surface) {
            int opaque = surface | 0xff000000;
            if (mSurface == opaque) return;
            mSurface = opaque;
            updateShader();
        }

        static int[] colors(int surface) {
            int rgb = surface & 0x00ffffff;
            return new int[] {0xd9000000 | rgb, 0xcc000000 | rgb, rgb};
        }

        @Override protected void onBoundsChange(Rect bounds) { updateShader(); }

        private void updateShader() {
            Rect b = getBounds();
            mPaint.setShader(b.isEmpty() ? null : new LinearGradient(0, b.top, 0, b.bottom,
                    colors(mSurface), new float[] {0f, .70f, 1f}, Shader.TileMode.CLAMP));
            invalidateSelf();
        }

        @Override public void draw(Canvas canvas) {
            if (!getBounds().isEmpty()) canvas.drawRect(getBounds(), mPaint);
        }
        @Override public void setAlpha(int alpha) { mPaint.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(@Nullable ColorFilter filter) { mPaint.setColorFilter(filter); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
