// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import java.util.HashMap;
import java.util.Map;

/** Coordinates Arc metadata with the existing Chromium tab commands in one profile/model. */
public final class ArcTabActions {
    public interface NativeTabs {
        boolean exists(int tabId);
        /** Returns the native ID, or a negative value when no tab was created. */
        int open(String url);
        void select(int tabId);
        void close(int tabId);
        void pin(int tabId);
        void unpin(int tabId);
        default void onSpaceChanged(ArcSidebarState state) {}
    }
    public enum Result { OPENED, SELECTED, NOT_OPENED, PERSISTENCE_ERROR }

    private final ArcSidebarStore mStore;
    private final NativeTabs mTabs;
    // Keep a newly created tab reachable if storing its metadata fails. Retrying a click
    // must select that same native tab, rather than create another one.
    private final Map<String, Integer> mUncommittedTabs = new HashMap<>();
    private boolean mDestroyed;

    public ArcTabActions(ArcSidebarStore store, NativeTabs tabs) {
        mStore = store;
        mTabs = tabs;
    }

    public Result selectOrOpen(String entryId) {
        if (mDestroyed) return Result.NOT_OPENED;
        ArcSidebarState.Entry entry;
        try { entry = mStore.load().entry(entryId); }
        catch (RuntimeException failure) { return Result.PERSISTENCE_ERROR; }
        Integer tabId = mUncommittedTabs.get(entryId);
        if (tabId == null || !mTabs.exists(tabId)) tabId = entry.tabId;
        boolean created = tabId == null || !mTabs.exists(tabId);
        if (created) {
            tabId = mTabs.open(entry.url);
            if (tabId < 0 || !mTabs.exists(tabId)) return Result.NOT_OPENED;
            mUncommittedTabs.put(entryId, tabId);
        }
        mTabs.pin(tabId);
        mTabs.select(tabId);
        if (created || mUncommittedTabs.containsKey(entryId)) {
            try {
                // Native creation can notify other observers synchronously. Edit the latest
                // state rather than overwrite any metadata they just published.
                ArcSidebarState current = mStore.load();
                current.bindTab(entryId, tabId);
                mStore.save(current);
                mUncommittedTabs.remove(entryId);
            } catch (RuntimeException failure) {
                return Result.PERSISTENCE_ERROR;
            }
        }
        return created ? Result.OPENED : Result.SELECTED;
    }

    public void closeTab(int tabId) {
        if (!mDestroyed && mTabs.exists(tabId)) mTabs.close(tabId);
        // An ungroup/close dialog may cancel. Only native confirmation changes the record.
    }

    public boolean onTabClosed(int tabId) {
        if (mDestroyed) return false;
        mUncommittedTabs.values().removeIf(id -> id == tabId);
        try {
            ArcSidebarState current = mStore.load();
            current.tabClosed(tabId);
            mStore.save(current);
            return true;
        } catch (RuntimeException failure) {
            return false;
        }
    }

    public void destroy() {
        mDestroyed = true;
        mUncommittedTabs.clear();
    }
}
