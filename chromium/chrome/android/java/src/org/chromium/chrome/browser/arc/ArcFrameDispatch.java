// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.view.View;

import java.util.function.BooleanSupplier;

/** A queued frame belongs to a live coordinator and the current desktop mode. */
public final class ArcFrameDispatch {
    private final BooleanSupplier mEligible;
    private View mHost;
    private Runnable mPending;
    private int mGeneration;
    private boolean mDestroyed;

    public ArcFrameDispatch(BooleanSupplier eligible) {
        mEligible = eligible;
    }

    public void schedule(View host, Runnable frame) {
        cancel();
        if (mDestroyed || !mEligible.getAsBoolean()) return;
        int generation = mGeneration;
        mHost = host;
        mPending = () -> {
            if (mDestroyed || generation != mGeneration || !mEligible.getAsBoolean()) return;
            mHost = null;
            mPending = null;
            frame.run();
        };
        host.post(mPending);
    }

    public void cancel() {
        mGeneration++;
        if (mHost != null && mPending != null) {
            mHost.removeCallbacks(mPending);
        }
        mHost = null;
        mPending = null;
    }

    public void destroy() {
        mDestroyed = true;
        cancel();
    }
}
