// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.graphics.Canvas;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.text.TextPaint;
import android.text.TextUtils;
import android.graphics.drawable.ColorDrawable;
import android.view.View;
import android.view.ViewGroup;

/** Phone overscroll presentation. Moves the surface and its input hierarchy without web relayout. */
public final class ArcPhonePullReveal {
    private final View mContent;
    private final Runnable mOnReveal;
    private final ColorDrawable mFill = new ColorDrawable();
    private final View mGap;
    private final float mDensity;
    private Bitmap mFavicon;
    private String mSite = "", mTitle = "";
    private final TextPaint mTextPaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final Paint mImagePaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final Paint mCornerPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path mCornerPath = new Path();
    private final RectF mIconBounds = new RectF();
    private boolean mCornersAttached;
    // ViewOverlay Drawables have no touch/accessibility target and do not clip the compositor.
    private final Drawable mCorners = new Drawable() {
        @Override public void draw(Canvas canvas) {
            float width = getBounds().width(), radius = getBounds().height();
            if (radius <= 0) return;
            int save = canvas.save();
            canvas.clipRect(getBounds());
            mCornerPath.reset(); mCornerPath.setFillType(Path.FillType.EVEN_ODD);
            mCornerPath.addRect(0, 0, width, radius, Path.Direction.CW);
            mCornerPath.addRoundRect(0, 0, width, radius * 2, radius, radius, Path.Direction.CW);
            canvas.drawPath(mCornerPath, mCornerPaint);
            canvas.restoreToCount(save);
        }
        @Override public void setAlpha(int alpha) { mCornerPaint.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(ColorFilter filter) { mCornerPaint.setColorFilter(filter); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    };
    private final float mExtent;
    private final float mMinimumPull;
    private final float mRefreshPull;
    private final float mNativePullScale;
    private final View.OnLayoutChangeListener mLayout;
    private ValueAnimator mAnimation;
    private boolean mEnabled;
    private boolean mDestroyed;
    private boolean mPulling;
    private boolean mLatched;
    private boolean mOwnsTranslation;
    private float mOriginalTranslation;
    private float mOffset;
    private float mPull;
    private float mInitialOffset;

    public ArcPhonePullReveal(View content, Runnable onReveal) {
        mContent = content;
        mOnReveal = onReveal;
        float density = content.getResources().getDisplayMetrics().density;
        mDensity = density;
        mExtent = 64 * density;
        mMinimumPull = 24 * density;
        mRefreshPull = 120 * density;
        // Pinned SwipeRefreshLayout uses a 64dp trigger and .5 drag rate. Map only the
        // second stage into that unchanged native range; never scale the web content.
        mNativePullScale = (2 * 64 * density) / (mRefreshPull - mExtent);
        mGap = new View(content.getContext()) {
            @Override protected void onDraw(Canvas canvas) { mFill.draw(canvas); drawIdentity(canvas); }
        };
        mGap.setWillNotDraw(false);
        mGap.setEnabled(false);
        mGap.setClickable(false);
        mGap.setFocusable(false);
        mGap.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        mLayout = (v,l,t,r,b,ol,ot,or,ob) -> {
            if (l != ol || t != ot || r != or || b != ob) reset(false);
        };
        content.addOnLayoutChangeListener(mLayout);
    }

    public void setEnabled(boolean enabled) {
        mEnabled = enabled && !mDestroyed;
        if (!mEnabled) reset(false);
    }

    /** Native page palette, or its native theme fallback; never force white in dark mode. */
    public void setSurface(int color) {
        int surface = color | 0xff000000;
        mFill.setColor(surface); mCornerPaint.setColor(surface);
        mTextPaint.setColor(Color.luminance(surface) > .179 ? Color.BLACK : Color.WHITE);
        mCorners.invalidateSelf(); mGap.invalidate();
    }

    /** Borrow the native cached icon; never fetch, copy or recycle tab-owned bitmaps. */
    public void setIdentity(Bitmap favicon, String site, String title) {
        mFavicon = favicon;
        mSite = site == null ? "" : site;
        mTitle = title == null || title.equals(mSite) ? "" : title;
        mGap.invalidate();
    }

    private void drawIdentity(Canvas canvas) {
        var bounds = mFill.getBounds();
        if (bounds.isEmpty() || bounds.width() < 64 * mDensity) return;
        int save = canvas.save(); canvas.clipRect(bounds);
        float x = bounds.left + 16 * mDensity, center = bounds.exactCenterY();
        float size = 22 * mDensity;
        mIconBounds.set(x, center - size / 2, x + size, center + size / 2);
        if (mFavicon != null && !mFavicon.isRecycled()) {
            canvas.drawBitmap(mFavicon, null, mIconBounds, mImagePaint);
        } else {
            mTextPaint.setTextSize(18 * mDensity); mTextPaint.setTypeface(Typeface.DEFAULT);
            canvas.drawText(mSite.isEmpty() ? "A" : mSite.substring(0, 1).toUpperCase(java.util.Locale.ROOT),
                    x + 4 * mDensity, center + 6 * mDensity, mTextPaint);
        }
        x += size + 12 * mDensity;
        float available = Math.max(0, bounds.right - 16 * mDensity - x);
        mTextPaint.setTextSize(14 * mDensity); mTextPaint.setTypeface(Typeface.DEFAULT_BOLD);
        canvas.drawText(TextUtils.ellipsize(mSite.isEmpty() ? "Archium" : mSite,
                mTextPaint, available, TextUtils.TruncateAt.END).toString(),
                x, center + (mTitle.isEmpty() ? 5 : -2) * mDensity, mTextPaint);
        if (!mTitle.isEmpty()) {
            mTextPaint.setTextSize(11 * mDensity); mTextPaint.setTypeface(Typeface.DEFAULT);
            canvas.drawText(TextUtils.ellipsize(mTitle, mTextPaint, available,
                    TextUtils.TruncateAt.END).toString(), x, center + 14 * mDensity, mTextPaint);
        }
        canvas.restoreToCount(save);
    }

    public boolean isRevealed() { return mOffset > 0 || mLatched; }

    /** A subsequent ordinary page scroll dismisses the gap, not an overscroll still in progress. */
    public void onPageScroll() { if (!mPulling && isRevealed()) reset(true); }

    public boolean start() {
        if (!mEnabled || !(mContent.getParent() instanceof ViewGroup)) return false;
        cancelAnimation();
        if (!mOwnsTranslation) {
            mOriginalTranslation = mContent.getTranslationY();
            mOwnsTranslation = true;
        }
        mPulling = true;
        mInitialOffset = mOffset;
        mPull = 0;
        mOnReveal.run();
        return true;
    }

    /** Consume the reveal stage; only excess movement reaches Chromium's refresh indicator. */
    public float pull(float delta) {
        if (!mPulling) return 0;
        float previousExcess = Math.max(0, mPull - mExtent);
        mPull = Math.max(0, mPull + delta);
        setOffset(Math.min(mExtent, mInitialOffset + mPull));
        return (Math.max(0, mPull - mExtent) - previousExcess) * mNativePullScale;
    }

    /** Chromium retains the refresh threshold, accessibility, haptics and reload implementation. */
    public boolean release(boolean allowRefresh) {
        if (!mPulling) return false;
        mPulling = false;
        boolean refreshDistance = mPull >= mRefreshPull;
        if (!allowRefresh || mPull < mMinimumPull) {
            reset(true);
            return false;
        }
        mLatched = true;
        settle(mExtent, true);
        return refreshDistance;
    }

    public void reset(boolean animate) {
        mPulling = false;
        mLatched = false;
        mPull = 0;
        settle(0, animate && !mDestroyed && mEnabled);
    }

    private void cancelAnimation() {
        ValueAnimator previous = mAnimation;
        mAnimation = null;
        if (previous != null) previous.cancel();
    }

    private void settle(float target, boolean animate) {
        cancelAnimation();
        if (!animate || !ValueAnimator.areAnimatorsEnabled() || mOffset == target) {
            setOffset(target);
            return;
        }
        ValueAnimator animation = ValueAnimator.ofFloat(mOffset, target);
        mAnimation = animation;
        animation.setDuration(180);
        animation.addUpdateListener(value -> setOffset((float)value.getAnimatedValue()));
        animation.addListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator ended) {
                if (mAnimation != ended) return;
                mAnimation = null;
                setOffset(target);
            }
        });
        animation.start();
    }

    private void setOffset(float offset) {
        mOffset = offset;
        if (!mOwnsTranslation) return;
        mContent.setTranslationY(mOriginalTranslation + offset);
        if (offset <= 0) {
            mOwnsTranslation = false;
            mFill.setBounds(0,0,0,0);
            mCorners.setBounds(0,0,0,0);
            if (mCornersAttached) { mContent.getOverlay().remove(mCorners); mCornersAttached = false; }
            detachGap();
            return;
        }
        if (!(mContent.getParent() instanceof ViewGroup parent)) { reset(false); return; }
        if (mGap.getParent() == null) {
            // Behind the surface AND controls: a parent Drawable overlay would cover the pill.
            parent.addView(mGap, parent.indexOfChild(mContent), new ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            mGap.layout(0,0,parent.getWidth(),parent.getHeight());
        }
        int left = Math.round(mContent.getX());
        int top = Math.round(mContent.getTop() + mOriginalTranslation);
        mFill.setBounds(left, top, left + mContent.getWidth(), top + Math.round(offset));
        int radius = Math.round(Math.min(offset, Math.min(16 * mDensity, mContent.getWidth() / 2f)));
        mCorners.setBounds(0, 0, mContent.getWidth(), radius);
        if (!mCornersAttached) { mContent.getOverlay().add(mCorners); mCornersAttached = true; }
        mGap.invalidate();
    }

    private void detachGap() {
        if (!(mGap.getParent() instanceof ViewGroup parent)) return;
        if (parent.isInLayout()) {
            // Do not mutate the parent's child list from a child's layout callback.
            mGap.post(() -> { if (mOffset == 0 && mGap.getParent() == parent) parent.removeView(mGap); });
        } else parent.removeView(mGap);
    }

    public void destroy() {
        mDestroyed = true;
        mEnabled = false;
        reset(false);
        mFavicon = null;
        mContent.removeOnLayoutChangeListener(mLayout);
    }
}
