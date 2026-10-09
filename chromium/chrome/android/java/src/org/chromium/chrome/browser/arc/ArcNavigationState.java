// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.widget.ImageButton;

import org.chromium.base.Callback;
import org.chromium.base.ThreadUtils;
import org.chromium.base.supplier.NullableObservableSupplier;
import org.chromium.chrome.R;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabObserver;
import org.chromium.content_public.browser.NavigationHandle;

/** Native state and actions for the existing Arc Back, Forward and Reload/Stop buttons. */
public final class ArcNavigationState {
    private final NullableObservableSupplier<Tab> mCurrentTab;
    private final ImageButton mBack;
    private final ImageButton mForward;
    private final ImageButton mReload;
    private final Callback<Tab> mSupplierObserver = this::onCurrentTabChanged;
    private Tab mObservedTab;
    private TabObserver mTabObserver;
    private boolean mActive = true;
    private boolean mDestroyed;

    public ArcNavigationState(NullableObservableSupplier<Tab> currentTab,
            ImageButton back, ImageButton forward, ImageButton reload) {
        ThreadUtils.assertOnUiThread();
        mCurrentTab = currentTab;
        mBack = back;
        mForward = forward;
        mReload = reload;
        back.setOnClickListener(v -> navigateBack());
        forward.setOnClickListener(v -> navigateForward());
        reload.setOnClickListener(v -> stopOrReload());
        // Synchronous replay includes null; model-selection notifications can precede this supplier.
        currentTab.addSyncObserverAndCall(mSupplierObserver);
    }

    private void onCurrentTabChanged(Tab tab) {
        if (!mDestroyed && mActive) bind(tab);
    }

    /** Pause native tab subscriptions in MOBILE, resuming the latest authoritative tab in ARC. */
    public void setActive(boolean active) {
        ThreadUtils.assertOnUiThread();
        if (mDestroyed || mActive == active) return;
        mActive = active;
        bind(active ? mCurrentTab.get() : null);
    }

    /** Bind only the current activity tab; never use an earlier TabModel selection as authority. */
    public void bind(Tab tab) {
        ThreadUtils.assertOnUiThread();
        if (mDestroyed) return;
        if (!mActive || tab != mCurrentTab.get() || (tab != null && tab.isDestroyed())) tab = null;
        if (tab != mObservedTab) {
            releaseTabObserver();
            mObservedTab = tab;
            if (tab != null) {
                mTabObserver = createTabObserver(tab);
                tab.addObserver(mTabObserver);
            }
        }
        updateButtons(tab);
    }

    private TabObserver createTabObserver(Tab observedTab) {
        // A fresh observer captures this tab even for the parameterless history callback. A late
        // event from a removed observer therefore cannot refresh the next tab's controls.
        return new TabObserver() {
            @Override public void onLoadStarted(Tab tab, boolean toDifferentDocument) {
                refreshIfCurrent(observedTab);
            }
            @Override public void onLoadStopped(Tab tab, boolean toDifferentDocument) {
                refreshIfCurrent(observedTab);
            }
            @Override public void onNavigationStateChanged() {
                refreshIfCurrent(observedTab);
            }
            @Override public void onDidFinishNavigationInPrimaryMainFrame(
                    Tab tab, NavigationHandle navigation) {
                refreshIfCurrent(observedTab);
            }
            @Override public void onNavigationEntriesAppended(Tab tab) {
                refreshIfCurrent(observedTab);
            }
            @Override public void onNavigationEntriesDeleted(Tab tab) {
                refreshIfCurrent(observedTab);
            }
            @Override public void onContentChanged(Tab tab) {
                refreshIfCurrent(observedTab);
            }
            @Override public void onClosingStateChanged(Tab tab, boolean closing) {
                refreshIfCurrent(observedTab);
            }
            @Override public void onDestroyed(Tab tab) {
                if (isCurrentObservedTab(observedTab)) bind(null);
            }
        };
    }

    private boolean isCurrentObservedTab(Tab tab) {
        return !mDestroyed && mActive && tab == mObservedTab && tab == mCurrentTab.get();
    }

    private void refreshIfCurrent(Tab tab) {
        if (isCurrentObservedTab(tab)) updateButtons(tab);
    }

    private void updateButtons(Tab tab) {
        boolean available = mActive && tab != null && !tab.isDestroyed() && !tab.isClosing();
        mBack.setEnabled(available && tab.canGoBack());
        mForward.setEnabled(available && tab.canGoForward());
        mReload.setEnabled(available);
        boolean loading = available && tab.isLoading();
        mReload.setImageLevel(mReload.getResources().getInteger(loading
                ? R.integer.reload_button_level_stop : R.integer.reload_button_level_reload));
        mReload.setContentDescription(mReload.getResources().getString(loading
                ? R.string.accessibility_btn_stop_loading : R.string.accessibility_btn_refresh));
    }

    private Tab tabForAction() {
        if (mDestroyed || !mActive) return null;
        Tab tab = mCurrentTab.get();
        // Re-read authority at click time, including when a caller has not yet processed selection.
        if (tab != mObservedTab) bind(tab);
        return tab != null && !tab.isDestroyed() && !tab.isClosing() ? tab : null;
    }

    private void navigateBack() {
        Tab tab = tabForAction();
        if (tab != null && tab.canGoBack()) tab.goBack();
        if (!mDestroyed && mActive) bind(mCurrentTab.get());
    }

    private void navigateForward() {
        Tab tab = tabForAction();
        if (tab != null && tab.canGoForward()) tab.goForward();
        if (!mDestroyed && mActive) bind(mCurrentTab.get());
    }

    private void stopOrReload() {
        Tab tab = tabForAction();
        if (tab != null) {
            if (tab.isLoading()) tab.stopLoading();
            else tab.reload();
        }
        if (!mDestroyed && mActive) bind(mCurrentTab.get());
    }

    private void releaseTabObserver() {
        if (mObservedTab != null && mTabObserver != null) mObservedTab.removeObserver(mTabObserver);
        mObservedTab = null;
        mTabObserver = null;
    }

    public void destroy() {
        ThreadUtils.assertOnUiThread();
        if (mDestroyed) return;
        mDestroyed = true;
        mActive = false;
        mCurrentTab.removeObserver(mSupplierObserver);
        releaseTabObserver();
        updateButtons(null);
        mBack.setOnClickListener(null);
        mForward.setOnClickListener(null);
        mReload.setOnClickListener(null);
    }
}
