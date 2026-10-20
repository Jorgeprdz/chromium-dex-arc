// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Rect;
import android.graphics.RectF;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.components.embedder_support.view.ContentView;
import java.util.IdentityHashMap;
import java.util.Map;

/** Attach existing native ContentViews; never creates, navigates or destroys a Tab/WebContents. */
public final class ArcSplitContentHost {
    private final ViewGroup mParent;
    private final Map<ContentView, Saved> mSaved = new IdentityHashMap<>();
    private Tab mLeft, mRight;
    private final RectF mLeftBounds = new RectF(), mRightBounds = new RectF();
    private static final class Saved {
        final ViewGroup.LayoutParams params;
        final int offset;
        Saved(ContentView view) { params = view.getLayoutParams(); offset = view.getContentOffsetXPix(); }
    }
    public ArcSplitContentHost(ViewGroup parent) { mParent = parent; }

    public boolean show(Tab left, Tab right, Rect viewport, float ratio) {
        if (left == null || right == null || left == right || left.isDestroyed() || right.isDestroyed()
                || left.getId() == right.getId() || !Float.isFinite(ratio)
                || viewport.width() < 2 || viewport.height() <= 0) return false;
        ContentView leftView = left.getContentView(), rightView = right.getContentView();
        if (leftView == null || rightView == null || leftView == rightView
                || left.getView() != leftView || right.getView() != rightView) return false;
        if (!mSaved.containsKey(leftView) || !mSaved.containsKey(rightView)) clear();
        mSaved.computeIfAbsent(leftView, Saved::new);
        mSaved.computeIfAbsent(rightView, Saved::new);
        mLeft = left; mRight = right;
        int middle = viewport.left + Math.round(viewport.width() * Math.max(.2f, Math.min(.8f, ratio)));
        mLeftBounds.set(viewport.left, viewport.top, middle, viewport.bottom);
        mRightBounds.set(middle, viewport.top, viewport.right, viewport.bottom);
        place(leftView, mLeftBounds, 1);
        place(rightView, mRightBounds, 2);
        return true;
    }

    private void place(ContentView view, RectF bounds, int index) {
        if (view.getParent() != mParent) {
            if (view.getParent() instanceof ViewGroup parent) parent.removeView(view);
            mParent.addView(view, Math.min(index, mParent.getChildCount()));
        }
        FrameLayout.LayoutParams current = view.getLayoutParams() instanceof FrameLayout.LayoutParams p ? p : null;
        int width = Math.round(bounds.width()), x = Math.round(bounds.left);
        if (current == null || current.width != width || current.height != -1
                || current.leftMargin != x || current.rightMargin != 0 || current.gravity != (android.view.Gravity.LEFT | android.view.Gravity.TOP)) {
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(width, -1,
                    android.view.Gravity.LEFT | android.view.Gravity.TOP);
            params.leftMargin = x;
            view.setLayoutParams(params);
        }
        // Android already translates the event/container origin into this pane.
        view.setContentOffsetXPix(0);
        view.setVisibility(View.VISIBLE);
    }

    public void setAttached(boolean attached) {
        for (ContentView view : mSaved.keySet()) {
            if (!attached && view.getParent() == mParent) mParent.removeView(view);
        }
        if (attached && mLeft != null && mRight != null) {
            ContentView left=mLeft.getContentView(), right=mRight.getContentView();
            // A tab can replace/drop its native view while the Activity surface is hidden.
            // Reconciliation will bind fresh views; never partially attach a stale pair.
            if(left==null || right==null || !mSaved.containsKey(left) || !mSaved.containsKey(right)) return;
            place(left, mLeftBounds, 1);
            place(right, mRightBounds, 2);
        }
    }

    /** Synchronize native focus on selection without displacing address/modal editing. */
    public boolean focus(Tab selected, View urlBar, boolean blocked) {
        if(blocked || !contains(selected) || (urlBar!=null && urlBar.hasFocus())) return false;
        ContentView target=selected.getContentView();
        if(target==null || target.getParent()!=mParent)return false;
        View focused=mParent.getRootView().findFocus();
        if(focused instanceof android.widget.EditText && !isPaneDescendant(focused))return false;
        return target.requestFocus();
    }
    private boolean isPaneDescendant(View view) {
        for(View current=view;current!=null;) {
            if(mSaved.containsKey(current))return true;
            current=current.getParent() instanceof View parent?parent:null;
        }
        return false;
    }
    public boolean contains(Tab tab) { return tab != null && (tab == mLeft || tab == mRight); }
    public RectF bounds(Tab tab) {
        return tab == mLeft ? new RectF(mLeftBounds) : tab == mRight ? new RectF(mRightBounds) : new RectF();
    }
    public Tab tabAt(float x, float y) {
        return mLeftBounds.contains(x,y) ? mLeft : mRightBounds.contains(x,y) ? mRight : null;
    }
    public void clear() {
        for (Map.Entry<ContentView, Saved> entry : mSaved.entrySet()) {
            ContentView view = entry.getKey();
            // A different window may have acquired the same native tab since the last frame.
            if (view.getParent() != null && view.getParent() != mParent) continue;
            if (view.getParent() == mParent) mParent.removeView(view);
            Saved saved = entry.getValue();
            view.setLayoutParams(saved.params != null ? saved.params : new FrameLayout.LayoutParams(-1,-1));
            view.setContentOffsetXPix(saved.offset);
        }
        mSaved.clear(); mLeft = null; mRight = null;
        mLeftBounds.setEmpty(); mRightBounds.setEmpty();
    }
}
