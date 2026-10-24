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
    // Showing system bars changes insets without necessarily changing the edge-to-edge layout.
    private final android.view.ViewTreeObserver.OnPreDrawListener mBeforeDraw = () -> {
        updateBounds();
        return true;
    };

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
                mDecor.getViewTreeObserver().addOnPreDrawListener(mBeforeDraw);
            } else {
                mDecor.getOverlay().remove(mFade);
                mDecor.removeOnLayoutChangeListener(mLayout);
                mDecor.getViewTreeObserver().removeOnPreDrawListener(mBeforeDraw);
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

    /** Reuse the existing bounded web sampler; this drawable never receives input. */
    public void setBackdrop(@Nullable Drawable backdrop) { mFade.setBackdrop(backdrop); }

    public void getBackdropBounds(Rect out) {
        if (mAttached) out.set(mFade.getBounds());
        else out.setEmpty();
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

    public void destroy() { setBackdrop(null); update(false, Color.TRANSPARENT); }

    /** Own only the status-bar hide requested by compact phone controls. */
    public static final class StatusVisibility {
        private final android.view.Window mWindow;
        private boolean mOwnsHidden;

        public StatusVisibility(android.view.Window window) { mWindow = window; }

        public void update(boolean compact, boolean nativeFullscreen) {
            // Fullscreen's native owner hides/restores system bars itself. Never show over video.
            if (nativeFullscreen) { mOwnsHidden = false; return; }
            View decor = mWindow.getDecorView();
            if (compact == mOwnsHidden) return;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                android.view.WindowInsetsController controller = mWindow.getInsetsController();
                if (controller == null) return;
                if (compact) {
                    WindowInsets insets = decor.getRootWindowInsets();
                    // Do not claim another owner's hide, or guess before system inset delivery.
                    if (insets == null || !insets.isVisible(WindowInsets.Type.statusBars())) return;
                    controller.hide(WindowInsets.Type.statusBars());
                } else controller.show(WindowInsets.Type.statusBars());
            } else {
                int flags = decor.getSystemUiVisibility();
                if (compact && (flags & View.SYSTEM_UI_FLAG_FULLSCREEN) != 0) return;
                decor.setSystemUiVisibility(compact ? flags | View.SYSTEM_UI_FLAG_FULLSCREEN
                        : flags & ~View.SYSTEM_UI_FLAG_FULLSCREEN);
            }
            mOwnsHidden = compact;
        }
    }

    static final class Fade extends Drawable implements Drawable.Callback {
        private final Paint mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private int mSurface;
        private @Nullable Drawable mBackdrop;
        private final Paint mBackdropMask = new Paint(Paint.ANTI_ALIAS_FLAG);

        Fade() {
            mBackdropMask.setXfermode(new android.graphics.PorterDuffXfermode(
                    android.graphics.PorterDuff.Mode.DST_IN));
        }

        void setBackdrop(@Nullable Drawable backdrop) {
            if (mBackdrop == backdrop) return;
            if (mBackdrop != null) mBackdrop.setCallback(null);
            mBackdrop = backdrop;
            if (backdrop != null) { backdrop.setBounds(getBounds()); backdrop.setCallback(this); }
            invalidateSelf();
        }

        @Override public void invalidateDrawable(Drawable who) { invalidateSelf(); }
        @Override public void scheduleDrawable(Drawable who, Runnable what, long when) { scheduleSelf(what, when); }
        @Override public void unscheduleDrawable(Drawable who, Runnable what) { unscheduleSelf(what); }


        void setSurface(int surface) {
            int opaque = surface | 0xff000000;
            if (mSurface == opaque) return;
            mSurface = opaque;
            updateShader();
        }

        static int[] colors(int surface) {
            int rgb = surface & 0x00ffffff;
            return new int[] {0xb3000000 | rgb, 0xaa000000 | rgb, rgb};
        }

        @Override protected void onBoundsChange(Rect bounds) {
            if (mBackdrop != null) mBackdrop.setBounds(bounds);
            updateShader();
        }

        private void updateShader() {
            Rect b = getBounds();
            mPaint.setShader(b.isEmpty() ? null : new LinearGradient(0, b.top, 0, b.bottom,
                    colors(mSurface), new float[] {0f, .70f, 1f}, Shader.TileMode.CLAMP));
            mBackdropMask.setShader(b.isEmpty() ? null : new LinearGradient(0, b.top, 0, b.bottom,
                    new int[] {Color.WHITE, Color.WHITE, 0x00ffffff},
                    new float[] {0f, .70f, 1f}, Shader.TileMode.CLAMP));
            invalidateSelf();
        }

        @Override public void draw(Canvas canvas) {
            Rect bounds = getBounds();
            if (bounds.isEmpty()) return;
            Drawable backdrop = mBackdrop;
            if (backdrop != null) {
                // A status-height layer only; taper sampled blur to the unmodified live page.
                int save = canvas.saveLayer(bounds.left, bounds.top, bounds.right, bounds.bottom, null);
                backdrop.draw(canvas);
                canvas.drawRect(bounds, mBackdropMask);
                canvas.restoreToCount(save);
            }
            canvas.drawRect(bounds, mPaint);
        }
        @Override public void setAlpha(int alpha) { mPaint.setAlpha(alpha); mBackdropMask.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(@Nullable ColorFilter filter) { mPaint.setColorFilter(filter); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
