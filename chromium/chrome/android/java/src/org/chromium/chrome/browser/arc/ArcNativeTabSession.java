// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import org.chromium.base.ThreadUtils;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabLaunchType;
import org.chromium.chrome.browser.tab.TabSelectionType;
import org.chromium.chrome.browser.tabmodel.TabClosureParams;
import org.chromium.chrome.browser.tabmodel.TabCreator;
import org.chromium.chrome.browser.tabmodel.TabModel;
import org.chromium.chrome.browser.tabmodel.TabModelObserver;
import org.chromium.content_public.browser.LoadUrlParams;

import java.util.List;
import java.util.function.BooleanSupplier;

/** Adapter to one real Chromium model/creator; never acts on an inactive profile's UI. */
public final class ArcNativeTabSession implements ArcTabActions.NativeTabs {
    private final TabModel mModel;
    private final TabCreator mCreator;
    private final BooleanSupplier mIsCurrentModel;
    private final Runnable mOnStateChanged;
    private final ArcTabActions mActions;
    private final TabModelObserver mObserver;
    private boolean mDestroyed;

    public ArcNativeTabSession(TabModel model, TabCreator creator,
            BooleanSupplier isCurrentModel, Runnable onStateChanged) {
        ThreadUtils.assertOnUiThread();
        Profile profile = model.getProfile();
        if (profile == null || profile.shutdownStarted()) {
            throw new IllegalStateException("Arc tab profile is not initialized");
        }
        mModel = model;
        mCreator = creator;
        mIsCurrentModel = isCurrentModel;
        mOnStateChanged = onStateChanged;
        mActions = new ArcTabActions(ArcSidebarProfiles.getForProfile(profile), this);
        mObserver = new TabModelObserver() {
            @Override public void tabClosureCommitted(Tab tab) { confirmedClose(tab.getId()); }
            @Override public void onTabCloseCommitted(List<Tab> tabs, boolean isAllTabs,
                    boolean canRestore, int closingSource) {
                for (Tab tab : tabs) confirmedClose(tab.getId());
            }
        };
        model.addObserver(mObserver);
    }

    public ArcTabActions actions() { return mActions; }

    private boolean active() {
        Profile profile = mModel.getProfile();
        return !mDestroyed && mIsCurrentModel.getAsBoolean()
                && profile != null && !profile.shutdownStarted();
    }

    private void confirmedClose(int tabId) {
        if (mDestroyed) return;
        // Only final closure counts. Removal for reparenting and pending undo are not closure.
        mActions.onTabClosed(tabId);
        if (active()) mOnStateChanged.run();
    }

    @Override public boolean exists(int tabId) {
        return active() && (mModel.getTabById(tabId) != null || mModel.isClosurePending(tabId));
    }

    @Override public int open(String url) {
        if (!active()) return -1;
        Tab tab = mCreator.createNewTab(
                new LoadUrlParams(url), TabLaunchType.FROM_CHROME_UI, null);
        return tab == null ? -1 : tab.getId();
    }

    private Tab restorePendingTab(int tabId) {
        if (!active()) return null;
        if (mModel.isClosurePending(tabId)) mModel.cancelTabClosure(tabId);
        return mModel.getTabById(tabId);
    }

    @Override public void select(int tabId) {
        Tab tab = restorePendingTab(tabId);
        if (tab == null) return;
        for (int i = 0; i < mModel.getCount(); i++) {
            if (mModel.getTabAt(i) == tab) {
                mModel.setIndex(i, TabSelectionType.FROM_USER);
                return;
            }
        }
    }

    @Override public void pin(int tabId) {
        if (restorePendingTab(tabId) != null) {
            mModel.pinTab(tabId, /* showUngroupDialog= */ true);
        }
    }

    @Override public void close(int tabId) {
        if (!active()) return;
        Tab tab = mModel.getTabById(tabId);
        if (tab == null) return;
        mModel.getTabRemover().closeTabs(
                TabClosureParams.closeTab(tab).allowUndo(true).build(), /* allowDialog= */ true);
    }

    public void destroy() {
        if (mDestroyed) return;
        mDestroyed = true;
        mModel.removeObserver(mObserver);
        mActions.destroy();
    }
}
