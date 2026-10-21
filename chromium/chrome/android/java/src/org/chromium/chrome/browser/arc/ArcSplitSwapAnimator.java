// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.view.animation.AccelerateDecelerateInterpolator;
import java.util.function.Consumer;

/** One bounded transition. Cancellation always settles the native scene before releasing input. */
public final class ArcSplitSwapAnimator {
    public static final long DURATION_MS = 180;
    private ValueAnimator mAnimator;
    private Runnable mFinish;
    private boolean mDestroyed;

    public void start(Consumer<Float> frame, Runnable finish) {
        if (mDestroyed) return;
        settle();
        if (!ValueAnimator.areAnimatorsEnabled()) {
            frame.accept(1f);
            finish.run();
            return;
        }
        ValueAnimator animation = ValueAnimator.ofFloat(0f, 1f);
        mAnimator = animation;
        mFinish = finish;
        animation.setDuration(DURATION_MS);
        animation.setInterpolator(new AccelerateDecelerateInterpolator());
        animation.addUpdateListener(a -> {
            if (mAnimator == animation) frame.accept((Float) a.getAnimatedValue());
        });
        animation.addListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator a) {
                if (mAnimator != animation) return;
                mAnimator = null;
                Runnable done = mFinish;
                mFinish = null;
                if (done != null) done.run();
            }
        });
        frame.accept(0f);
        animation.start();
    }

    public void settle() {
        ValueAnimator animation = mAnimator;
        if (animation != null) animation.end();
    }

    public boolean isRunning() { return mAnimator != null; }
    ValueAnimator animatorForTesting() { return mAnimator; }
    public void destroy() { mDestroyed = true; settle(); }
}
