// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

/** Window-local identities only. TabModel retains ownership of every Tab/WebContents. */
public final class ArcSplitState {
    private int mLeft = -1;
    private int mRight = -1;
    private int mActive = -1;
    private float mRatio = .5f;

    public boolean start(int leftId, int rightId) {
        if (leftId < 0 || rightId < 0 || leftId == rightId) return false;
        mLeft = leftId;
        mRight = rightId;
        mActive = leftId;
        mRatio = .5f;
        return true;
    }

    public boolean activate(int tabId) {
        if (tabId < 0 || (tabId != mLeft && tabId != mRight)) return false;
        mActive = tabId;
        return true;
    }

    /** Swap physical positions while preserving active identity and physical left width. */
    public void swap() {
        if (!isSplit()) return;
        int previousLeft = mLeft;
        mLeft = mRight;
        mRight = previousLeft;
    }

    public void setRatio(float ratio) {
        if (!Float.isFinite(ratio)) throw new IllegalArgumentException("Non-finite split ratio");
        mRatio = Math.max(.2f, Math.min(.8f, ratio));
    }

    public void remove(int tabId) {
        if (tabId < 0 || (tabId != mLeft && tabId != mRight)) return;
        int survivor = tabId == mLeft ? mRight : mLeft;
        mLeft = survivor;
        mRight = -1;
        mActive = survivor;
        mRatio = .5f;
    }

    /** Leave both native tabs alive; only the active one remains presented. */
    public void exit() {
        mLeft = mActive;
        mRight = -1;
        mRatio = .5f;
    }

    public boolean isSplit() { return mLeft >= 0 && mRight >= 0; }
    public int leftId() { return mLeft; }
    public int rightId() { return mRight; }
    public int activeId() { return mActive; }
    public float ratio() { return mRatio; }
}
