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

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.BooleanSupplier;

/** Adapter to one real Chromium model/creator; never acts on an inactive profile's UI. */
public final class ArcNativeTabSession implements ArcTabActions.NativeTabs {
    private enum RestoreState { RESTORE_PENDING, RESTORE_COMPLETE }

    private final TabModel mModel;
    private final TabCreator mCreator;
    private final BooleanSupplier mIsCurrentModel;
    private final Runnable mOnStateChanged;
    private final ArcTabActions mActions;
    private final ArcSidebarStore mStore;
    private final TabModelObserver mObserver;
    private RestoreState mRestoreState;
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
        mStore = ArcSidebarProfiles.getForProfile(profile);
        mActions = new ArcTabActions(mStore, this);
        mRestoreState = model.isTabModelRestored()
                ? RestoreState.RESTORE_COMPLETE : RestoreState.RESTORE_PENDING;
        mObserver = new TabModelObserver() {
            @Override
            public void didAddTab(
                    Tab tab, int type, int creationState, boolean markedForSelection) {
                // A didAddTab before restoreCompleted() can still be a restored tab. Preserve any
                // persisted owner and defer adoption of unknown IDs until restore is authoritative.
                if (restoreComplete()) adoptTab(tab.getId());
                if (active()) mOnStateChanged.run();
            }

            @Override public void didSelectTab(Tab tab, int type, int lastId) {
                // Selection during restore is presentation-only; it must never reassign ownership.
                if (active()) mOnStateChanged.run();
            }

            @Override public void restoreCompleted() {
                if (mDestroyed || restoreComplete()) return;
                mRestoreState = RestoreState.RESTORE_COMPLETE;
                reconcileTabsAfterRestore();
                selectForActiveSpaceAfterRestore();
                if (active()) mOnStateChanged.run();
            }

            @Override public void tabClosureCommitted(Tab tab) { confirmedClose(tab.getId()); }
            @Override public void onTabCloseCommitted(List<Tab> tabs, boolean isAllTabs,
                    boolean canRestore, int closingSource) {
                for (Tab tab : tabs) confirmedClose(tab.getId());
            }
        };
        model.addObserver(mObserver);
        // If this session attaches after Chromium already completed restore, the model itself is
        // authoritative and the restoreCompleted callback is not required to arrive again.
        if (restoreComplete()) {
            reconcileTabsAfterRestore();
            selectForActiveSpaceAfterRestore();
        }
    }

    public ArcTabActions actions() { return mActions; }
    public ArcSidebarStore store() { return mStore; }

    private boolean active() {
        Profile profile = mModel.getProfile();
        return !mDestroyed && mIsCurrentModel.getAsBoolean()
                && profile != null && !profile.shutdownStarted();
    }

    private void adoptTab(int tabId) {
        if (mDestroyed || tabId < 0) return;
        try {
            ArcSidebarState state = mStore.load();
            if (state.isFavoriteTab(tabId) || state.hasTabSpace(tabId)) return;
            state.associateTab(tabId, state.selectedSpace());
            mStore.save(state);
        } catch (RuntimeException ignored) {
            // A metadata failure must never mutate or close the native tab.
        }
    }

    private boolean restoreComplete() {
        return mRestoreState == RestoreState.RESTORE_COMPLETE;
    }

    private Set<Integer> liveTabIds() {
        Set<Integer> live = new HashSet<>();
        for (int i = 0; i < mModel.getCount(); i++) {
            Tab tab = mModel.getTabAt(i);
            if (tab != null) live.add(tab.getId());
        }
        return live;
    }

    private void reconcileTabsAfterRestore() {
        if (mDestroyed || !restoreComplete()) return;
        try {
            ArcSidebarState state = mStore.load();
            Set<Integer> live = liveTabIds();
            String before = state.serialize();
            state.reconcileTabsAfterRestore(live);
            for (int tabId : live) {
                if (!state.isFavoriteTab(tabId) && !state.hasTabSpace(tabId)) {
                    state.associateTab(tabId, state.selectedSpace());
                }
            }
            if (!before.equals(state.serialize())) mStore.save(state);
        } catch (RuntimeException ignored) {
            // Keep Chromium's TabModel authoritative if Arc metadata is unavailable.
        }
    }

    /** Presentation predicate consumed by the native vertical-tab model. Fail open on metadata IO. */
    public boolean isTabVisibleForActiveSpace(int tabId) {
        // A predicate can briefly outlive the selected TabModel while profile/incognito selection
        // is rebinding. Never project one profile's Space metadata onto another model.
        if (!active() || tabId < 0) return true;
        try {
            return mStore.load().visibleTabForPresentation(tabId, restoreComplete());
        } catch (RuntimeException ignored) {
            return true;
        }
    }

    private void selectForActiveSpaceAfterRestore() {
        if (!active() || !restoreComplete()) return;
        try {
            selectForActiveSpace(mStore.load());
        } catch (RuntimeException ignored) {
            // Metadata failure must not close, move, or otherwise mutate native tabs.
        }
    }

    private void selectForActiveSpace(ArcSidebarState state) {
        Tab current = mModel.getCurrentTabSupplier().get();
        if (current != null && state.visibleTab(current.getId())) return;
        for (int i = 0; i < mModel.getCount(); i++) {
            Tab tab = mModel.getTabAt(i);
            if (tab != null && state.visibleTab(tab.getId())) {
                select(tab.getId());
                return;
            }
        }
        int created = open("chrome://newtab/");
        if (created >= 0) {
            adoptTab(created);
            select(created);
        }
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

    @Override public void unpin(int tabId) {
        if (active() && mModel.getTabById(tabId) != null) mModel.unpinTab(tabId);
    }

    @Override
    public void onArcStateChanged(ArcSidebarState state) {
        if (active()) mOnStateChanged.run();
    }

    @Override
    public void onSpaceChanged(ArcSidebarState state) {
        if (!active()) return;
        // Do not create/select based on an incomplete restore. The persisted Space selection is
        // already committed; once restoreCompleted() arrives we choose a valid real tab.
        if (restoreComplete()) selectForActiveSpace(state);
        mOnStateChanged.run();
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
