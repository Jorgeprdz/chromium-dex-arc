// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.TouchDelegate;
import android.view.View;
import android.view.ViewConfiguration;
import android.widget.FrameLayout;
import android.widget.ImageButton;
import java.util.function.Consumer;

/** Small white swap capsule and separate horizontal resize gesture; no web surface effects. */
public final class ArcSplitDividerView extends FrameLayout {
    private final ImageButton mButton;
    private final Consumer<Float> mResize;
    private final int mSlop;
    private float mRatio = .5f, mStartRatio, mDownX;
    private int mViewportWidth;
    private boolean mDragging, mBusy;

    public ArcSplitDividerView(Context context, Runnable swap, Consumer<Float> resize, String label) {
        super(context);
        mResize = resize;
        mSlop = ViewConfiguration.get(context).getScaledTouchSlop();
        View line = new View(context);
        line.setBackgroundColor(0x33777777);
        addView(line, new LayoutParams(dp(2), -1, Gravity.CENTER));
        mButton = new ImageButton(context);
        GradientDrawable capsule = new GradientDrawable();
        capsule.setColor(Color.WHITE);
        capsule.setCornerRadius(dp(14));
        mButton.setBackground(capsule);
        mButton.setImageDrawable(new SwapArrows());
        mButton.setPadding(dp(5), dp(5), dp(5), dp(5));
        mButton.setContentDescription(label);
        mButton.setTooltipText(label);
        mButton.setElevation(dp(2));
        mButton.setOnClickListener(v -> { if (!mBusy) swap.run(); });
        addView(mButton, new LayoutParams(dp(28), dp(44), Gravity.CENTER));
        setClipChildren(false);
        setClipToPadding(false);
    }

    public void setGeometry(float ratio, int viewportWidth) {
        mRatio = ratio;
        mViewportWidth = viewportWidth;
    }
    public void setBusy(boolean busy) { mBusy = busy; mButton.setEnabled(!busy); }
    View buttonForTesting() { return mButton; }

    @Override protected void onLayout(boolean changed, int l, int t, int r, int b) {
        super.onLayout(changed, l, t, r, b);
        Rect target = new Rect();
        mButton.getHitRect(target);
        target.inset(-dp(10), -dp(6));
        setTouchDelegate(new TouchDelegate(target, mButton));
    }

    @Override public boolean onInterceptTouchEvent(MotionEvent event) {
        if (mBusy) return false;
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                mDownX = event.getRawX(); mStartRatio = mRatio; mDragging = false;
                break;
            case MotionEvent.ACTION_MOVE:
                if (Math.abs(event.getRawX() - mDownX) > mSlop) {
                    mDragging = true;
                    getParent().requestDisallowInterceptTouchEvent(true);
                    return true;
                }
                break;
        }
        return false;
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (mBusy || mViewportWidth <= 0) return false;
        if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
            mDownX = event.getRawX(); mStartRatio = mRatio;
            return true;
        }
        if (event.getActionMasked() == MotionEvent.ACTION_MOVE) {
            if (mDragging || Math.abs(event.getRawX() - mDownX) > mSlop) {
                mDragging = true;
                mResize.accept(Math.max(.2f, Math.min(.8f,
                        mStartRatio + (event.getRawX() - mDownX) / mViewportWidth)));
            }
            return true;
        }
        if (event.getActionMasked() == MotionEvent.ACTION_UP
                || event.getActionMasked() == MotionEvent.ACTION_CANCEL) {
            mDragging = false;
            return true;
        }
        return false;
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private static final class SwapArrows extends Drawable {
        private final Paint mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        SwapArrows() { mPaint.setColor(0xff333333); mPaint.setStrokeCap(Paint.Cap.ROUND); }
        @Override public void draw(Canvas canvas) {
            Rect b = getBounds();
            float left = b.left + b.width() * .12f, right = b.right - b.width() * .12f;
            float top = b.top + b.height() * .33f, bottom = b.top + b.height() * .67f;
            float tip = b.width() * .22f;
            mPaint.setStrokeWidth(Math.max(1f, b.width() * .085f));
            canvas.drawLine(left, top, right, top, mPaint);
            canvas.drawLine(right - tip, top - tip, right, top, mPaint);
            canvas.drawLine(right - tip, top + tip, right, top, mPaint);
            canvas.drawLine(right, bottom, left, bottom, mPaint);
            canvas.drawLine(left + tip, bottom - tip, left, bottom, mPaint);
            canvas.drawLine(left + tip, bottom + tip, left, bottom, mPaint);
        }
        @Override public void setAlpha(int alpha) { mPaint.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(ColorFilter filter) { mPaint.setColorFilter(filter); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
