// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;

/** Transfers the native holder as a unit, keeping LocationBarTablet's direct parent intact. */
public final class ArcOmniboxPlacement {
    private final View mHolder;
    private final ViewGroup mOriginalParent;
    private final int mOriginalIndex;
    private final ViewGroup.LayoutParams mOriginalParams;

    public ArcOmniboxPlacement(View holder) {
        if (!(holder.getParent() instanceof ViewGroup)) {
            throw new IllegalArgumentException("Native omnibox holder must have a parent");
        }
        mHolder = holder;
        mOriginalParent = (ViewGroup) holder.getParent();
        mOriginalIndex = mOriginalParent.indexOfChild(holder);
        mOriginalParams = holder.getLayoutParams();
    }

    public void move(ViewGroup destination, ViewGroup.LayoutParams params) {
        move(destination, destination.getChildCount(), params);
    }

    public void move(ViewGroup destination, int index, ViewGroup.LayoutParams params) {
        if (mHolder.getParent() == destination) return;
        transfer(destination, Math.min(index, destination.getChildCount()), params);
    }

    public void restore() {
        if (mHolder.getParent() == mOriginalParent) return;
        transfer(mOriginalParent, Math.min(mOriginalIndex, mOriginalParent.getChildCount()), mOriginalParams);
    }

    private void transfer(ViewGroup parent, int index, ViewGroup.LayoutParams params) {
        View focused = mHolder.findFocus();
        int start = focused instanceof EditText editor ? editor.getSelectionStart() : -1;
        int end = focused instanceof EditText editor ? editor.getSelectionEnd() : -1;
        if (mHolder.getParent() instanceof ViewGroup previous) previous.removeView(mHolder);
        parent.addView(mHolder, index, params);
        // Native input listeners remain installed. Never copy text to another editor.
        if (focused != null) focused.requestFocus();
        if (focused instanceof EditText editor && start >= 0 && end >= 0) {
            editor.setSelection(Math.min(start, editor.length()), Math.min(end, editor.length()));
        }
    }
}
