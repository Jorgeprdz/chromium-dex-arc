// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.animation.ValueAnimator;
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
import android.view.KeyEvent;
import android.view.PointerIcon;
import android.view.MotionEvent;
import android.view.TouchDelegate;
import android.view.View;
import android.view.ViewConfiguration;
import android.widget.FrameLayout;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupWindow;
import java.util.function.Consumer;

/** White resize grip with an anchored action capsule; never changes web surface ownership. */
public final class ArcSplitDividerView extends FrameLayout {
    private final ImageButton mButton;
    private final Consumer<Float> mResize;
    private final Runnable mSwap, mExit;
    private final String mSwapLabel, mExitLabel;
    private PopupWindow mPopup;
    private View mActions, mSwapButton, mExitButton;
    private boolean mDestroyed;
    private final int mSlop;
    private float mRatio = .5f, mStartRatio, mDownX;
    private int mViewportWidth;
    private boolean mDragging, mBusy, mResizeTarget;

    public ArcSplitDividerView(Context context, Runnable swap, Runnable exit,
            Consumer<Float> resize, String label, String swapLabel, String exitLabel) {
        super(context);
        mResize = resize; mSwap = swap; mExit = exit;
        mSwapLabel = swapLabel; mExitLabel = exitLabel;
        mSlop = ViewConfiguration.get(context).getScaledTouchSlop();
        mButton = new ImageButton(context);
        GradientDrawable capsule = new GradientDrawable();
        capsule.setColor(Color.WHITE);
        capsule.setCornerRadius(dp(14));
        mButton.setBackground(capsule);
        mButton.setImageDrawable(new ControlIcon(0));
        mButton.setPadding(dp(5), dp(5), dp(5), dp(5));
        mButton.setContentDescription(label);
        mButton.setTooltipText(label);
        mButton.setElevation(dp(2));
        mButton.setOnClickListener(v -> { if (!mBusy && !mDestroyed) toggleActions(); });
        mButton.setPointerIcon(PointerIcon.getSystemIcon(context, PointerIcon.TYPE_HORIZONTAL_DOUBLE_ARROW));
        setPointerIcon(PointerIcon.getSystemIcon(context, PointerIcon.TYPE_HORIZONTAL_DOUBLE_ARROW));
        addView(mButton, new LayoutParams(dp(28), dp(44), Gravity.CENTER));
        setClipChildren(false);
        setClipToPadding(false);
    }

    public void setGeometry(float ratio, int viewportWidth) {
        mRatio = ratio;
        mViewportWidth = viewportWidth;
        if (isExpanded()) { int[] at = actionPosition(); mPopup.update(at[0], at[1], -1, -1); }
    }
    public void setBusy(boolean busy) {
        mBusy = busy; mButton.setEnabled(!busy);
        if (busy) dismissActions();
    }
    private void toggleActions() {
        if (isExpanded()) { dismissActions(); return; }
        if (getWindowToken() == null || getVisibility() != VISIBLE) return;
        // Native PopupWindow handles Escape/Back. Also handle Escape at our content
        // boundary, before focused children, when a host forwards keys directly here.
        LinearLayout actions = new LinearLayout(getContext()) {
            @Override public boolean dispatchKeyEvent(KeyEvent event) {
                if (event.getKeyCode() == KeyEvent.KEYCODE_ESCAPE) {
                    dismissActions(); return true;
                }
                return super.dispatchKeyEvent(event);
            }
        };
        actions.setGravity(Gravity.CENTER);
        GradientDrawable bg = new GradientDrawable(); bg.setColor(Color.WHITE); bg.setCornerRadius(dp(24));
        actions.setBackground(bg); actions.setElevation(dp(4));
        mSwapButton = action(new ControlIcon(1), mSwapLabel, mSwap);
        mExitButton = action(new ControlIcon(2), mExitLabel, mExit);
        ImageButton grip = action(new ControlIcon(0), mButton.getContentDescription().toString(), () -> {});
        grip.setOnTouchListener((v, event) -> onExpandedGripTouch(event));
        actions.addView(mSwapButton, new LinearLayout.LayoutParams(dp(44), dp(48)));
        actions.addView(grip, new LinearLayout.LayoutParams(dp(32), dp(48)));
        actions.addView(mExitButton, new LinearLayout.LayoutParams(dp(44), dp(48)));
        mActions = actions;
        PopupWindow popup = new PopupWindow(actions, dp(120), dp(48), true);
        mPopup = popup; popup.setBackgroundDrawable(bg); popup.setOutsideTouchable(true);
        popup.setElevation(dp(4)); popup.setAnimationStyle(0);
        actions.setFocusableInTouchMode(true);
        popup.setOnDismissListener(() -> {
            actions.animate().cancel();
            if (mPopup == popup) { mPopup = null; mActions = null; }
            if (isShown() && !mDestroyed) mButton.requestFocus();
        });
        int[] at = actionPosition();
        popup.showAtLocation(this, Gravity.TOP | Gravity.LEFT, at[0], at[1]);
        actions.requestFocus();
        if (ValueAnimator.areAnimatorsEnabled()) {
            actions.setPivotX(dp(60)); actions.setPivotY(dp(24));
            actions.setScaleX(.3f); actions.setAlpha(0f);
            actions.animate().scaleX(1f).alpha(1f).setDuration(150).start();
        }
    }
    private int[] actionPosition() {
        int[] at = new int[2]; mButton.getLocationInWindow(at);
        int[] root = new int[2]; getRootView().getLocationInWindow(root);
        return new int[] {
            Math.max(root[0], Math.min(at[0] + mButton.getWidth()/2 - dp(60),
                    root[0] + getRootView().getWidth() - dp(120))),
            Math.max(root[1], Math.min(at[1] + mButton.getHeight()/2 - dp(24),
                    root[1] + getRootView().getHeight() - dp(48)))
        };
    }
    private boolean onExpandedGripTouch(MotionEvent event) {
        if (mBusy || mDestroyed || mViewportWidth <= 0) return false;
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                mDownX = event.getRawX(); mStartRatio = mRatio; mDragging = false;
                return false; // Preserve the button's normal click to collapse.
            case MotionEvent.ACTION_MOVE:
                if (mDragging || Math.abs(event.getRawX()-mDownX) > mSlop) {
                    mDragging = true; resizeTo(event.getRawX()); return true;
                }
                return false;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                if (mDragging) { mDragging = false; dismissActions(); return true; }
                return false;
            default: return false;
        }
    }
    private void resizeTo(float rawX) {
        mResize.accept(Math.max(.2f, Math.min(.8f, mStartRatio + (rawX-mDownX)/mViewportWidth)));
    }
    private ImageButton action(Drawable icon, String label, Runnable action) {
        ImageButton button = new ImageButton(getContext());
        button.setBackgroundColor(Color.TRANSPARENT); button.setImageDrawable(icon);
        button.setPadding(dp(12), dp(12), dp(12), dp(12));
        button.setContentDescription(label); button.setTooltipText(label);
        button.setPointerIcon(PointerIcon.getSystemIcon(getContext(), PointerIcon.TYPE_HAND));
        button.setOnClickListener(v -> {
            if (mBusy || mDestroyed || !isExpanded()) return;
            dismissActions(); action.run();
        });
        return button;
    }
    public void dismissActions() {
        if (mActions != null) mActions.animate().cancel();
        if (mPopup != null) mPopup.dismiss();
        mPopup = null; mActions = null;
    }
    public void destroy() { mDestroyed = true; dismissActions(); mButton.setOnClickListener(null); }
    boolean isExpanded() { return mPopup != null && mPopup.isShowing(); }
    boolean isExpandedForTesting() { return isExpanded(); }
    View swapForTesting() { return mSwapButton; }
    View exitForTesting() { return mExitButton; }
    @Override public boolean dispatchKeyEvent(KeyEvent event) {
        if (event.getKeyCode() == KeyEvent.KEYCODE_ESCAPE && isExpanded()) {
            dismissActions(); return true;
        }
        return super.dispatchKeyEvent(event);
    }
    @Override protected void onVisibilityChanged(View changed, int visibility) {
        super.onVisibilityChanged(changed, visibility);
        if (visibility != VISIBLE) dismissActions();
    }
    @Override protected void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(visibility);
        if (visibility != VISIBLE) dismissActions();
    }
    @Override protected void onDetachedFromWindow() { dismissActions(); super.onDetachedFromWindow(); }
    View buttonForTesting() { return mButton; }

    @Override protected void onLayout(boolean changed, int l, int t, int r, int b) {
        super.onLayout(changed, l, t, r, b);
        Rect target = new Rect();
        mButton.getHitRect(target);
        target.inset(-dp(10), -dp(6));
        setTouchDelegate(new TouchDelegate(target, mButton));
    }

    @Override public boolean onInterceptTouchEvent(MotionEvent event) {
        if (mBusy || mDestroyed) return false;
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                mDownX = event.getRawX(); mStartRatio = mRatio; mDragging = false;
                mResizeTarget = Math.abs(event.getX()-getWidth()/2f) <= dp(4)
                        || (event.getY() >= mButton.getTop()-dp(6) && event.getY() <= mButton.getBottom()+dp(6));
                break;
            case MotionEvent.ACTION_MOVE:
                if (mResizeTarget && Math.abs(event.getRawX() - mDownX) > mSlop) {
                    mDragging = true; dismissActions();
                    getParent().requestDisallowInterceptTouchEvent(true);
                    return true;
                }
                break;
        }
        return false;
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (mBusy || mDestroyed || mViewportWidth <= 0) return false;
        if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
            if (!mResizeTarget) return false;
            mDownX = event.getRawX(); mStartRatio = mRatio;
            return true;
        }
        if (event.getActionMasked() == MotionEvent.ACTION_MOVE) {
            if (mDragging || Math.abs(event.getRawX() - mDownX) > mSlop) {
                mDragging = true;
                resizeTo(event.getRawX());
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
    private static final class ControlIcon extends Drawable {
        private final int mKind;
        private final Paint mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        ControlIcon(int kind) { mKind = kind; mPaint.setColor(0xff333333); mPaint.setStrokeCap(Paint.Cap.ROUND); }
        @Override public void draw(Canvas canvas) {
            Rect b = getBounds();
            mPaint.setStrokeWidth(Math.max(1f, b.width() * .085f));
            if (mKind == 0) {
                canvas.drawLine(b.exactCenterX(), b.top+b.height()*.25f,
                        b.exactCenterX(), b.top+b.height()*.75f, mPaint); return;
            }
            if (mKind == 2) {
                float pad = b.width()*.24f;
                canvas.drawLine(b.left+pad,b.top+pad,b.right-pad,b.bottom-pad,mPaint);
                canvas.drawLine(b.right-pad,b.top+pad,b.left+pad,b.bottom-pad,mPaint); return;
            }
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
