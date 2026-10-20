// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.Function;
import java.util.function.Supplier;

/** Desktop commands around the one Chromium editor; owns neither history nor input resolution. */
public final class ArcCommandBar {
    public enum State { CLOSED, OPENING, OPEN, CLOSING }
    public static final class Result {
        public final String title, subtitle, action;
        public final Drawable icon;
        public final Runnable activate;
        public Result(String title, String subtitle, String action, Drawable icon, Runnable activate) {
            this.title = title; this.subtitle = subtitle; this.action = action;
            this.icon = icon; this.activate = activate;
        }
    }

    private final Activity mActivity;
    private final ViewGroup mRoot;
    private final View mHolder;
    private final EditText mEditor;
    private final ArcOmniboxPlacement mPlacement;
    private final Supplier<Rect> mViewport;
    private final Runnable mBeginInput, mEndInput, mRestore;
    private final Function<Boolean, List<Result>> mResults;
    private final String mPlaceholder, mActionsLabel;
    private final FrameLayout mOverlay;
    private final LinearLayout mPanel, mHeader, mRows;
    private final ScrollView mScroll;
    private final View mDivider;
    private final TextView mHint;
    private final GradientDrawable mSurface = new GradientDrawable();
    private final TextWatcher mTextWatcher = new TextWatcher() {
        @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
        @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
            if (isShowing() && mState != State.CLOSING) rebuildResults();
        }
        @Override public void afterTextChanged(Editable e) {}
    };
    private final View.OnLayoutChangeListener mLayoutListener =
            (v, l, t, r, b, ol, ot, or, ob) -> resize();
    private final android.view.ViewTreeObserver.OnGlobalLayoutListener mGlobalLayout =
            this::onGlobalLayout;
    private State mState = State.CLOSED;
    private boolean mActions, mDestroyed;
    private int mSelected = -1;
    private int mForeground, mSelection;
    private List<Result> mVisible = List.of();
    private ValueAnimator mAnimator;
    private TextView mProxy;
    private Rect mOrigin = new Rect();
    private Rect mLastVisibleFrame = new Rect();
    private Rect mLastViewport = new Rect();
    private CharSequence mOriginalHint;
    private View mPreviousFocus;
    private Runnable mBoundsChanged = () -> {};

    public ArcCommandBar(Activity activity, ViewGroup root, View holder, EditText editor,
            ArcOmniboxPlacement placement, Supplier<Rect> viewport, Runnable beginInput,
            Runnable endInput, Runnable restore, Function<Boolean, List<Result>> results,
            String placeholder, String actionsLabel) {
        mActivity = activity; mRoot = root; mHolder = holder; mEditor = editor;
        mPlacement = placement; mViewport = viewport; mBeginInput = beginInput;
        mEndInput = endInput; mRestore = restore; mResults = results;
        mPlaceholder = placeholder; mActionsLabel = actionsLabel;
        mOverlay = new FrameLayout(activity);
        mOverlay.setBackgroundColor(0x22000000);
        mOverlay.setOnClickListener(v -> close(true, null));
        mPanel = new LinearLayout(activity); mPanel.setOrientation(LinearLayout.VERTICAL);
        mPanel.setPadding(dp(8), dp(4), dp(8), dp(8));
        mSurface.setCornerRadius(dp(12)); mPanel.setBackground(mSurface);
        mPanel.setElevation(dp(12)); mPanel.setClickable(true);
        mPanel.setAccessibilityPaneTitle(placeholder);
        mHeader = new LinearLayout(activity); mHeader.setGravity(Gravity.CENTER_VERTICAL);
        mHint = new TextView(activity); mHint.setText(actionsLabel); mHint.setTextSize(12);
        mHint.setPadding(dp(8), 0, dp(8), 0); mHint.setFocusable(true);
        mHint.setOnClickListener(v -> toggleActions());
        mHeader.addView(mHint);
        mPanel.addView(mHeader, new LinearLayout.LayoutParams(-1, dp(56)));
        mDivider = new View(activity);
        mPanel.addView(mDivider, new LinearLayout.LayoutParams(-1, dp(1)));
        mScroll = new ScrollView(activity); mScroll.setFillViewport(false);
        mRows = new LinearLayout(activity); mRows.setOrientation(LinearLayout.VERTICAL);
        mScroll.addView(mRows);
        mPanel.addView(mScroll, new LinearLayout.LayoutParams(-1, 0, 1));
        mOverlay.addView(mPanel);
    }

    private int dp(int value) {
        return Math.round(value * mActivity.getResources().getDisplayMetrics().density);
    }
    private void onGlobalLayout() {
        if (!isShowing()) return;
        Rect visible = new Rect(); mRoot.getWindowVisibleDisplayFrame(visible);
        if (!visible.equals(mLastVisibleFrame) || !mViewport.get().equals(mLastViewport)) resize();
        else mBoundsChanged.run();
    }
    public boolean isShowing() { return mState != State.CLOSED; }
    public boolean isActions() { return isShowing() && mActions; }
    public void setBoundsChangedListener(Runnable listener) { mBoundsChanged = listener; }

    public void setAppearance(int surface, int foreground, int selection) {
        mSurface.setColor(surface); mSurface.setStroke(dp(1), (foreground & 0xffffff) | 0x33000000);
        mForeground = foreground; mSelection = selection;
        mHint.setTextColor(foreground); mDivider.setBackgroundColor((foreground & 0xffffff) | 0x22000000);
        if (isShowing()) rebuildResults();
    }

    public void open(boolean actions) {
        open(actions, mBeginInput);
    }

    /** Edit/copy the active address through Chromium's native focus-and-select callback. */
    public void openAddress(Runnable beginAddressInput) {
        open(false, beginAddressInput);
    }

    private void open(boolean actions, Runnable beginInput) {
        if (mDestroyed) return;
        if (isShowing()) {
            if (mState == State.CLOSING) { finishAnimationForTesting(); open(actions, beginInput); }
            return;
        }
        mActions = actions; mState = State.OPENING;
        mPreviousFocus = mRoot.findFocus(); mOriginalHint = mEditor.getHint();
        mOrigin = boundsInRoot(mHolder);
        mRoot.addView(mOverlay, new ViewGroup.LayoutParams(-1, -1));
        mRoot.addOnLayoutChangeListener(mLayoutListener);
        mOverlay.getViewTreeObserver().addOnGlobalLayoutListener(mGlobalLayout);
        mPlacement.move(mHeader, new LinearLayout.LayoutParams(0, -1, 1));
        mHeader.removeView(mHolder); mHeader.addView(mHolder, 0, new LinearLayout.LayoutParams(0, -1, 1));
        mEditor.setHint(mPlaceholder); mEditor.addTextChangedListener(mTextWatcher);
        resize();
        beginInput.run(); rebuildResults();
        mProxy = new TextView(mActivity); mProxy.setText(mOriginalHint);
        mProxy.setTextColor(mForeground); mProxy.setGravity(Gravity.CENTER_VERTICAL);
        mProxy.setPadding(dp(12), 0, dp(12), 0); mProxy.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        mProxy.setClickable(false); mProxy.setFocusable(false);
        GradientDrawable proxySurface = new GradientDrawable(); proxySurface.setColor(mSurface.getColor());
        mProxy.setBackground(proxySurface); mOverlay.addView(mProxy);
        animate(mOrigin, panelBounds(), true, null);
    }

    /** Called before native resolved navigation; restore hierarchy before a Tab/WebContents changes. */
    public void commitNativeNavigation() {
        if (mActions) {
            if (mSelected >= 0 && mSelected < mVisible.size()) close(false, mVisible.get(mSelected).activate);
            return;
        }
        close(false, null);
    }

    public void close(boolean animated, Runnable after) {
        if (mState == State.CLOSED) return;
        if (mState == State.CLOSING) {
            if (!animated) { cancelAnimator(); finishClose(after); }
            return;
        }
        cancelAnimator(); mState = State.CLOSING;
        if (animated && ValueAnimator.areAnimatorsEnabled()) {
            animate(panelBounds(), mOrigin, false, after);
        } else {
            finishClose(after);
        }
    }

    private void finishClose(Runnable after) {
        mEditor.removeTextChangedListener(mTextWatcher);
        mState = State.CLOSED;
        mBoundsChanged.run();
        mEndInput.run(); mEditor.setHint(mOriginalHint);
        mRestore.run(); mRoot.removeOnLayoutChangeListener(mLayoutListener);
        if (mOverlay.getViewTreeObserver().isAlive()) {
            mOverlay.getViewTreeObserver().removeOnGlobalLayoutListener(mGlobalLayout);
        }
        mRoot.removeView(mOverlay); removeProxy();
        mRows.removeAllViews(); mVisible = List.of(); mSelected = -1;
        if (after != null) after.run();
        else if (mPreviousFocus != null && mPreviousFocus != mEditor && mPreviousFocus.isAttachedToWindow()) {
            mPreviousFocus.requestFocus();
        }
        mPreviousFocus = null; mBoundsChanged.run();
    }

    public void resize() {
        if (!isShowing()) return;
        Rect viewport = mViewport.get();
        Rect visibleWindow = new Rect(); mRoot.getWindowVisibleDisplayFrame(visibleWindow);
        mLastVisibleFrame.set(visibleWindow); mLastViewport.set(viewport);
        // getWindowVisibleDisplayFrame uses screen coordinates, unlike omnibox/viewport bounds.
        int[] rootLocation = new int[2]; mRoot.getLocationOnScreen(rootLocation);
        visibleWindow.offset(-rootLocation[0], -rootLocation[1]);
        if (!visibleWindow.isEmpty()) viewport.intersect(visibleWindow);
        int margin = dp(16);
        int width = Math.max(1, Math.min(dp(760), viewport.width() - 2 * margin));
        int height = Math.max(1, Math.min(dp(360), viewport.height() - 2 * margin));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(width, height, Gravity.LEFT | Gravity.TOP);
        lp.leftMargin = viewport.left + Math.max(0, (viewport.width() - width) / 2);
        lp.topMargin = viewport.top + Math.min(dp(48), Math.max(0, (viewport.height() - height) / 3));
        FrameLayout.LayoutParams previous = (FrameLayout.LayoutParams) mPanel.getLayoutParams();
        if (previous == null || previous.width != lp.width || previous.height != lp.height
                || previous.leftMargin != lp.leftMargin || previous.topMargin != lp.topMargin
                || previous.gravity != lp.gravity) mPanel.setLayoutParams(lp);
        mBoundsChanged.run();
        // A resize finishes an opening transaction at current safe bounds, not stale bounds.
        if (mAnimator != null && mState == State.OPENING) finishAnimationForTesting();
    }

    private Rect panelBounds() {
        FrameLayout.LayoutParams lp = (FrameLayout.LayoutParams) mPanel.getLayoutParams();
        return new Rect(lp.leftMargin, lp.topMargin, lp.leftMargin + lp.width, lp.topMargin + lp.height);
    }
    public Rect resultsBoundsInWindow() {
        Rect rect = panelBounds(); int[] location = new int[2]; mRoot.getLocationInWindow(location);
        rect.offset(location[0], location[1]); rect.top += dp(61); return rect;
    }
    private Rect boundsInRoot(View view) {
        if (view.getRootView() != mRoot.getRootView()) return new Rect();
        int[] location = new int[2], root = new int[2];
        view.getLocationInWindow(location); mRoot.getLocationInWindow(root);
        return new Rect(location[0] - root[0], location[1] - root[1],
                location[0] - root[0] + view.getWidth(), location[1] - root[1] + view.getHeight());
    }

    private void animate(Rect from, Rect to, boolean opening, Runnable after) {
        if (!ValueAnimator.areAnimatorsEnabled() || from.isEmpty() || to.isEmpty()) {
            if (opening) finishOpen(); else finishClose(after); return;
        }
        mAnimator = ValueAnimator.ofFloat(0, 1); mAnimator.setDuration(200);
        mAnimator.addUpdateListener(animation -> {
            float progress = (float) animation.getAnimatedValue();
            if (mProxy != null) {
                FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(
                        Math.round(from.width() + (to.width() - from.width()) * progress),
                        Math.round(from.height() + (to.height() - from.height()) * progress), Gravity.LEFT | Gravity.TOP);
                p.leftMargin = Math.round(from.left + (to.left - from.left) * progress);
                p.topMargin = Math.round(from.top + (to.top - from.top) * progress);
                mProxy.setLayoutParams(p);
                ((GradientDrawable) mProxy.getBackground()).setCornerRadius(dp(12) * progress);
                mProxy.setElevation(dp(12) * progress); mProxy.setAlpha(1 - progress);
            }
            float alpha = opening ? progress : 1 - progress;
            mPanel.setAlpha(alpha); mHeader.setAlpha(alpha);
            mDivider.setAlpha(Math.max(0, (alpha - .2f) / .8f));
            mScroll.setAlpha(Math.max(0, (alpha - .35f) / .65f));
        });
        mAnimator.addListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator animation) {
                mAnimator = null;
                if (opening) finishOpen(); else finishClose(after);
            }
        }); mAnimator.start();
    }
    private void finishOpen() {
        mState = State.OPEN; removeProxy();
        mPanel.setAlpha(1); mHeader.setAlpha(1); mDivider.setAlpha(1); mScroll.setAlpha(1);
    }
    private void removeProxy() {
        if (mProxy != null) {mOverlay.removeView(mProxy); mProxy = null;}
    }
    private void cancelAnimator() {
        if (mAnimator != null) {mAnimator.removeAllListeners(); mAnimator.cancel(); mAnimator = null;}
    }

    private void toggleActions() {
        mActions = !mActions; mHint.setText(mActions ? "← " + mActionsLabel : mActionsLabel);
        rebuildResults(); mBoundsChanged.run(); mEditor.requestFocus();
    }
    private void rebuildResults() {
        String query = mEditor.getText().toString().toLowerCase(Locale.ROOT).trim();
        mVisible = new ArrayList<>();
        for (Result result : mResults.apply(mActions)) {
            if (query.isEmpty() || (mActions && (result.title + " " + result.subtitle).toLowerCase(Locale.ROOT).contains(query))) {
                mVisible.add(result);
            }
        }
        mSelected = query.isEmpty() || mActions ? (mVisible.isEmpty() ? -1 : 0) : -1;
        mRows.removeAllViews();
        for (int i = 0; i < mVisible.size(); i++) {
            Result result = mVisible.get(i); int index = i;
            LinearLayout row = new LinearLayout(mActivity); row.setGravity(Gravity.CENTER_VERTICAL);
            row.setPadding(dp(12), dp(6), dp(12), dp(6)); row.setFocusable(true);
            row.setContentDescription(result.title + ", " + result.subtitle + ", " + result.action);
            ImageView icon = new ImageView(mActivity);
            if (result.icon != null) icon.setImageDrawable(result.icon);
            else icon.setImageResource(android.R.drawable.ic_menu_search);
            row.addView(icon, new LinearLayout.LayoutParams(dp(24), dp(24)));
            LinearLayout text = new LinearLayout(mActivity); text.setOrientation(LinearLayout.VERTICAL);
            text.setPadding(dp(12), 0, dp(8), 0);
            TextView title = label(result.title, 14); title.setSingleLine(true);
            text.addView(title);
            if (!result.subtitle.isEmpty()) {TextView subtitle = label(result.subtitle, 11); subtitle.setSingleLine(true); text.addView(subtitle);}
            row.addView(text, new LinearLayout.LayoutParams(0, -2, 1));
            TextView action = label(result.action, 11); action.setSingleLine(true); row.addView(action);
            row.setOnClickListener(v -> close(false, result.activate));
            row.setOnHoverListener((v, event) -> { if (event.getActionMasked() == android.view.MotionEvent.ACTION_HOVER_ENTER) select(index); return false; });
            row.setOnFocusChangeListener((v, focus) -> {if (focus) select(index);});
            mRows.addView(row, new LinearLayout.LayoutParams(-1, dp(52)));
        }
        select(mSelected);
        mBoundsChanged.run();
    }
    private TextView label(String value, int size) {
        TextView view = new TextView(mActivity); view.setText(value); view.setTextSize(size);
        view.setTextColor(mForeground); return view;
    }
    private void select(int selected) {
        mSelected = selected;
        for (int i = 0; i < mRows.getChildCount(); i++) {
            View row = mRows.getChildAt(i); GradientDrawable active = new GradientDrawable();
            active.setColor(mSelection); active.setCornerRadius(dp(6));
            StateListDrawable states = new StateListDrawable();
            states.addState(new int[] {android.R.attr.state_selected}, active);
            states.addState(new int[] {android.R.attr.state_hovered}, active);
            states.addState(new int[] {android.R.attr.state_focused}, active);
            states.addState(new int[] {}, new android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT));
            row.setBackground(states); row.setSelected(i == selected);
        }
        if (selected >= 0 && selected < mRows.getChildCount()) {
            View row = mRows.getChildAt(selected); mScroll.smoothScrollTo(0, row.getTop());
        }
    }
    public boolean dispatchKeyEvent(KeyEvent event) {
        if (!isShowing() || event.isCtrlPressed() || event.isMetaPressed()) return false;
        int key = event.getKeyCode();
        boolean handled = key == KeyEvent.KEYCODE_ESCAPE || key == KeyEvent.KEYCODE_BACK || key == KeyEvent.KEYCODE_TAB
                || ((key == KeyEvent.KEYCODE_DPAD_UP || key == KeyEvent.KEYCODE_DPAD_DOWN) && !mVisible.isEmpty())
                || ((key == KeyEvent.KEYCODE_ENTER || key == KeyEvent.KEYCODE_NUMPAD_ENTER) && (mSelected >= 0 || mActions));
        if (!handled) return false;
        if (event.getAction() != KeyEvent.ACTION_DOWN || event.getRepeatCount() > 0) return true;
        if (key == KeyEvent.KEYCODE_ESCAPE || key == KeyEvent.KEYCODE_BACK) close(true, null);
        else if (key == KeyEvent.KEYCODE_TAB) toggleActions();
        else if (key == KeyEvent.KEYCODE_DPAD_DOWN) select((mSelected + 1) % mVisible.size());
        else if (key == KeyEvent.KEYCODE_DPAD_UP) select((mSelected + mVisible.size() - 1) % mVisible.size());
        else if (mSelected >= 0 && mSelected < mVisible.size()) close(false, mVisible.get(mSelected).activate);
        return true;
    }
    public void destroy() {
        if (mDestroyed) return;
        cancelAnimator(); if (isShowing()) {mState = State.OPEN; close(false, null);}
        mDestroyed = true;
    }
    LinearLayout panelForTesting() { return mPanel; }
    boolean actionsForTesting() { return mActions; }
    void finishAnimationForTesting() { if (mAnimator != null) mAnimator.end(); }
}
