// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.animation.Animator;
import android.animation.ValueAnimator;
import android.transition.Transition;
import android.transition.TransitionValues;
import android.view.View;
import android.view.ViewGroup;

import org.chromium.build.annotations.Nullable;

import java.util.function.IntConsumer;

/** Joins the native SideUi transition so the content edge moves with the rail. */
public final class ArcViewportTransition extends Transition {
    private static final String WIDTH = "archium:viewport:reservedWidth";
    private final View mViewport;
    private final int mStartWidth;
    private final int mEndWidth;
    private final IntConsumer mUpdateWidth;

    public ArcViewportTransition(View viewport, int startWidth, int endWidth,
            IntConsumer updateWidth) {
        mViewport = viewport;
        mStartWidth = Math.max(0, startWidth);
        mEndWidth = Math.max(0, endWidth);
        mUpdateWidth = updateWidth;
        addTarget(viewport);
    }

    @Override
    public void captureStartValues(TransitionValues values) {
        if (values.view == mViewport) values.values.put(WIDTH, mStartWidth);
    }

    @Override
    public void captureEndValues(TransitionValues values) {
        if (values.view == mViewport) values.values.put(WIDTH, mEndWidth);
    }

    @Override
    public String[] getTransitionProperties() {
        return new String[] {WIDTH};
    }

    @Override
    public @Nullable Animator createAnimator(ViewGroup sceneRoot,
            @Nullable TransitionValues startValues, @Nullable TransitionValues endValues) {
        if (startValues == null || endValues == null) return null;
        Object start = startValues.values.get(WIDTH);
        Object end = endValues.values.get(WIDTH);
        if (!(start instanceof Integer) || !(end instanceof Integer) || start.equals(end)) return null;
        ValueAnimator animator = ValueAnimator.ofInt((Integer) start, (Integer) end);
        animator.addUpdateListener(value -> mUpdateWidth.accept((Integer) value.getAnimatedValue()));
        // Duration and interpolation come from the owning native TransitionSet.
        return animator;
    }
}
