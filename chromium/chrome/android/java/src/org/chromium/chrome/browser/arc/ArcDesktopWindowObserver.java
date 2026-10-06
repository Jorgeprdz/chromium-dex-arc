// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.content.res.Configuration;
import android.content.SharedPreferences;

import org.chromium.chrome.browser.lifecycle.ActivityLifecycleDispatcher;
import org.chromium.chrome.browser.lifecycle.ConfigurationChangedObserver;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;

/** Rebuilds native browser UI when an activity changes between phone and desktop displays. */
public final class ArcDesktopWindowObserver implements ConfigurationChangedObserver {
    private final Activity mActivity;
    private final ActivityLifecycleDispatcher mDispatcher;
    private final boolean mDesktopAtCreation;
    private final SharedPreferences mPreferences;
    private final SharedPreferences.OnSharedPreferenceChangeListener mPreferenceListener;
    private final Runnable mRecreateUi = this::recreateUiIfNeeded;
    private boolean mDestroyed;
    private boolean mRecreationScheduled;

    public ArcDesktopWindowObserver(Activity activity, ActivityLifecycleDispatcher dispatcher) {
        mActivity = activity;
        mDispatcher = dispatcher;
        mDesktopAtCreation = ArcDesktopAppearance.isDesktopWindow(activity);
        mPreferences = ArcDesktopAppearance.preferences(activity);
        mPreferenceListener = (preferences, key) -> {
            if (ArcDesktopAppearance.UI_MODE_KEY.equals(key)) scheduleUiUpdate();
        };
        mPreferences.registerOnSharedPreferenceChangeListener(mPreferenceListener);
        dispatcher.register(this);
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        // Dispatch happens after the activity's resources receive the new configuration.
        scheduleUiUpdate();
    }

    private void scheduleUiUpdate() {
        if (mDestroyed || mRecreationScheduled
                || mDesktopAtCreation == ArcDesktopAppearance.isDesktopWindow(mActivity)) return;
        mRecreationScheduled = true;
        mActivity.getWindow().getDecorView().post(mRecreateUi);
    }

    private void recreateUiIfNeeded() {
        mRecreationScheduled = false;
        if (mDestroyed || mActivity.isFinishing() || mActivity.isDestroyed()) return;
        if (mDesktopAtCreation == ArcDesktopAppearance.isDesktopWindow(mActivity)) return;
        // Use the existing Chromium Activity restoration path without mutating tab models.
        mActivity.recreate();
    }

    public void destroy() {
        if (mDestroyed) return;
        mDestroyed = true;
        mPreferences.unregisterOnSharedPreferenceChangeListener(mPreferenceListener);
        mActivity.getWindow().getDecorView().removeCallbacks(mRecreateUi);
        mDispatcher.unregister(this);
    }
}
