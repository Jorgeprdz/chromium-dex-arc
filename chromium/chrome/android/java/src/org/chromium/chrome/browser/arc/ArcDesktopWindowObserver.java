// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.content.res.Configuration;

import org.chromium.chrome.browser.lifecycle.ActivityLifecycleDispatcher;
import org.chromium.chrome.browser.lifecycle.ConfigurationChangedObserver;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;

/** Rebuilds native browser UI when an activity changes between phone and desktop displays. */
public final class ArcDesktopWindowObserver implements ConfigurationChangedObserver {
    private final Activity mActivity;
    private final ActivityLifecycleDispatcher mDispatcher;
    private final boolean mDesktopAtCreation;
    private boolean mDestroyed;
    private boolean mRecreationScheduled;

    public ArcDesktopWindowObserver(Activity activity, ActivityLifecycleDispatcher dispatcher) {
        mActivity = activity;
        mDispatcher = dispatcher;
        mDesktopAtCreation = ArcDesktopAppearance.isDesktopWindow(activity);
        dispatcher.register(this);
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        // Dispatch happens after the activity's resources receive the new configuration.
        if (mDestroyed || mRecreationScheduled
                || mDesktopAtCreation == ArcDesktopAppearance.isDesktopWindow(mActivity)) return;
        mRecreationScheduled = true;
        mActivity.getWindow().getDecorView().post(() -> {
            if (mDestroyed || mActivity.isFinishing() || mActivity.isDestroyed()) return;
            if (mDesktopAtCreation == ArcDesktopAppearance.isDesktopWindow(mActivity)) {
                mRecreationScheduled = false;
                return;
            }
            // Use normal Activity save/restore rather than mutating tab models during reparenting.
            mActivity.recreate();
        });
    }

    public void destroy() {
        mDestroyed = true;
        mDispatcher.unregister(this);
    }
}
