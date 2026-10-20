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
import android.view.GestureDetector;
import android.graphics.drawable.StateListDrawable;
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
    private Runnable mBalance, mFocus;
    private String mFocusLabel;
    private final String mControlsLabel;
    private boolean mFocused, mMagnetic;
    private final GestureDetector mTaps;
    private View mTapTarget;
    private ValueAnimator mGlow;
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
        mControlsLabel = label; mBalance = () -> mResize.accept(.5f);
        mTaps = new GestureDetector(context, new GestureDetector.SimpleOnGestureListener() {
            @Override public boolean onDown(MotionEvent e) { return true; }
            @Override public boolean onSingleTapUp(MotionEvent e) {
                if (!mBusy && !mDestroyed && mTapTarget != null) mTapTarget.performClick();
                return true;
            }
            @Override public boolean onDoubleTap(MotionEvent e) {
                if (!mBusy && !mDestroyed && !mFocused) {
                    dismissActions(); mBalance.run(); pulseCenter();
                }
                return true;
            }
        });
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
        mButton.setOnClickListener(v -> {
            if (!mBusy && !mDestroyed) { if (mFocused && mFocus != null) mFocus.run(); else toggleActions(); }
        });
        mButton.setOnTouchListener(this::onGripTouch);
        mButton.setOnHoverListener((v,e) -> {
            capsule.setColor(e.getActionMasked()==MotionEvent.ACTION_HOVER_EXIT ? Color.WHITE : 0xfff3f4f6);
            return false;
        });
        mButton.setPointerIcon(PointerIcon.getSystemIcon(context, PointerIcon.TYPE_HORIZONTAL_DOUBLE_ARROW));
        setPointerIcon(PointerIcon.getSystemIcon(context, PointerIcon.TYPE_HORIZONTAL_DOUBLE_ARROW));
        addView(mButton, new LayoutParams(dp(28), dp(44), Gravity.CENTER));
        setClipChildren(false);
        setClipToPadding(false);
    }

    public void setBalanceAction(Runnable balance) { mBalance = balance; }
    public void setFocusAction(Runnable focus, String label) { mFocus = focus; mFocusLabel = label; }
    public void setFocusedMode(boolean focused, String restoreLabel) {
        if (mFocused == focused) return;
        dismissActions(); mFocused = focused;
        mButton.setImageDrawable(new ControlIcon(focused ? 3 : 0));
        mButton.setContentDescription(focused ? restoreLabel : mControlsLabel);
        mButton.setTooltipText(focused ? restoreLabel : mControlsLabel);
        mButton.setPointerIcon(PointerIcon.getSystemIcon(getContext(), focused
                ? PointerIcon.TYPE_HAND : PointerIcon.TYPE_HORIZONTAL_DOUBLE_ARROW));
    }
    public void setGeometry(float ratio, int viewportWidth) {
        mRatio = ratio;
        mViewportWidth = viewportWidth;
        if (isExpanded()) { int[] at = actionPosition(); mPopup.update(at[0], at[1], -1, -1); }
    }
    public void setBusy(boolean busy) {
        mBusy = busy; mButton.setEnabled(!busy);
        if (busy) { dismissActions(); stopGlow(); }
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
        actions.setBackground(bg); actions.setElevation(dp(4)); actions.setClipToOutline(true);
        mSwapButton = action(new ControlIcon(1), mSwapLabel, mSwap);
        mExitButton = action(new ControlIcon(2), mExitLabel, mExit);
        ImageButton grip = action(new ControlIcon(0), mButton.getContentDescription().toString(), () -> {});
        grip.setOnTouchListener(this::onGripTouch);
        actions.addView(mSwapButton, new LinearLayout.LayoutParams(dp(44), dp(48)));
        actions.addView(grip, new LinearLayout.LayoutParams(dp(32), dp(48)));
        if (mFocus != null) actions.addView(action(new ControlIcon(3),mFocusLabel,mFocus),
                new LinearLayout.LayoutParams(dp(44),dp(48)));
        actions.addView(mExitButton, new LinearLayout.LayoutParams(dp(44), dp(48)));
        mActions = actions;
        PopupWindow popup = new PopupWindow(actions, actionWidth(), dp(48), true);
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
    private int actionWidth() { return dp(mFocus != null ? 164 : 120); }
    private int[] actionPosition() {
        int[] at = new int[2]; mButton.getLocationInWindow(at);
        int[] root = new int[2]; getRootView().getLocationInWindow(root);
        return new int[] {
            Math.max(root[0], Math.min(at[0] + mButton.getWidth()/2 - dp(60),
                    root[0] + getRootView().getWidth() - actionWidth())),
            Math.max(root[1], Math.min(at[1] + mButton.getHeight()/2 - dp(24),
                    root[1] + getRootView().getHeight() - dp(48)))
        };
    }
    private boolean onGripTouch(View grip, MotionEvent event) {
        if (mBusy || mDestroyed) return false;
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            mTapTarget = grip; mDownX = event.getRawX(); mStartRatio = mRatio;
            mDragging = false; mMagnetic = false; grip.setPressed(true);
        }
        if (!mFocused && action == MotionEvent.ACTION_MOVE && mViewportWidth > 0
                && (mDragging || Math.abs(event.getRawX()-mDownX) > mSlop)) {
            mDragging = true; resizeTo(event.getRawX()); return true;
        }
        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            grip.setPressed(false);
            if (mDragging) {
                mDragging = false;
                MotionEvent cancel = MotionEvent.obtain(event); cancel.setAction(MotionEvent.ACTION_CANCEL);
                mTaps.onTouchEvent(cancel); cancel.recycle(); dismissActions(); return true;
            }
        }
        MotionEvent screen = MotionEvent.obtain(event);
        screen.setLocation(event.getRawX(),event.getRawY());
        boolean handled = mTaps.onTouchEvent(screen); screen.recycle(); return handled;
    }
    private void resizeTo(float rawX) {
        float ratio = ArcSplitResizePolicy.snap(mStartRatio + (rawX-mDownX)/mViewportWidth,mMagnetic);
        boolean capture = ratio == .5f;
        if (capture && !mMagnetic) pulseCenter();
        mMagnetic = capture; mResize.accept(ratio);
    }
    private ImageButton action(Drawable icon, String label, Runnable action) {
        ImageButton button = new ImageButton(getContext());
        StateListDrawable states = new StateListDrawable();
        for (int state : new int[]{android.R.attr.state_pressed,android.R.attr.state_focused,android.R.attr.state_hovered}) {
            GradientDrawable highlight = new GradientDrawable(); highlight.setColor(0x12000000); highlight.setCornerRadius(dp(12));
            states.addState(new int[]{state},highlight);
        }
        states.addState(new int[]{},new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));
        button.setBackground(states); button.setImageDrawable(icon);
        button.setPadding(dp(12), dp(12), dp(12), dp(12));
        button.setContentDescription(label); button.setTooltipText(label);
        button.setPointerIcon(PointerIcon.getSystemIcon(getContext(), PointerIcon.TYPE_HAND));
        button.setOnClickListener(v -> {
            if (mBusy || mDestroyed || !isExpanded()) return;
            dismissActions(); action.run();
        });
        return button;
    }
    private void cancelGestures() {
        if (mTaps != null) {
            long now=android.os.SystemClock.uptimeMillis();
            MotionEvent cancel=MotionEvent.obtain(now,now,MotionEvent.ACTION_CANCEL,0,0,0);
            mTaps.onTouchEvent(cancel);cancel.recycle();
        }
        if(mButton!=null)mButton.setPressed(false);
        mTapTarget=null;mDragging=false;
    }
    private void stopGlow() {
        if (mGlow != null) { mGlow.cancel(); mGlow = null; }
        if (mButton != null && mButton.getBackground() instanceof GradientDrawable bg) bg.setStroke(0,Color.TRANSPARENT);
    }
    private void pulseCenter() {
        stopGlow();
        if (!ValueAnimator.areAnimatorsEnabled()) return;
        mGlow = ValueAnimator.ofInt(150,0); mGlow.setDuration(180);
        mGlow.addUpdateListener(a -> {
            if (mButton.getBackground() instanceof GradientDrawable bg)
                bg.setStroke(dp(1),Color.argb((Integer)a.getAnimatedValue(),70,105,135));
        });
        mGlow.start();
    }
    public void dismissActions() {
        if (mActions != null) mActions.animate().cancel();
        if (mPopup != null) mPopup.dismiss();
        mPopup = null; mActions = null;
    }
    public void destroy() { mDestroyed = true; cancelGestures(); stopGlow(); dismissActions(); mButton.setOnClickListener(null); }
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
        if (visibility != VISIBLE) { dismissActions(); stopGlow(); cancelGestures(); }
    }
    @Override protected void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(visibility);
        if (visibility != VISIBLE) { dismissActions(); stopGlow(); cancelGestures(); }
    }
    @Override protected void onDetachedFromWindow() { dismissActions(); stopGlow(); cancelGestures(); super.onDetachedFromWindow(); }
    View buttonForTesting() { return mButton; }

    @Override protected void onLayout(boolean changed, int l, int t, int r, int b) {
        super.onLayout(changed, l, t, r, b);
        Rect target = new Rect();
        mButton.getHitRect(target);
        target.inset(-dp(10), -dp(6));
        setTouchDelegate(new TouchDelegate(target, mButton));
        if (isExpanded()) { int[] at=actionPosition(); mPopup.update(at[0],at[1],-1,-1); }
    }

    @Override public boolean onInterceptTouchEvent(MotionEvent event) {
        if (mBusy || mDestroyed || mFocused) return false;
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                mDownX = event.getRawX(); mStartRatio = mRatio; mDragging = false; mMagnetic = false;
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
        if (mBusy || mDestroyed || mFocused || mViewportWidth <= 0) return false;
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
            if (mKind == 3) {
                float pad=b.width()*.2f, size=b.width()*.25f;
                canvas.drawLine(b.left+pad,b.top+pad,b.left+pad+size,b.top+pad,mPaint);
                canvas.drawLine(b.left+pad,b.top+pad,b.left+pad,b.top+pad+size,mPaint);
                canvas.drawLine(b.right-pad,b.bottom-pad,b.right-pad-size,b.bottom-pad,mPaint);
                canvas.drawLine(b.right-pad,b.bottom-pad,b.right-pad,b.bottom-pad-size,mPaint); return;
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
