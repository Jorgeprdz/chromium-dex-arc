// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

/** Local collection commands scoped to one live native tab model/profile. */
public final class ArcCollectionsController {
    private final ArcSidebarStore mStore;
    private final ArcTabActions mActions;
    private final ArcTabActions.NativeTabs mTabs;
    private boolean mDestroyed;

    public ArcCollectionsController(ArcSidebarStore store, ArcTabActions actions,
            ArcTabActions.NativeTabs tabs) {
        mStore = store;
        mActions = actions;
        mTabs = tabs;
    }

    private void requireLive() {
        if (mDestroyed) throw new IllegalStateException("Arc collections are no longer active");
    }

    public ArcSidebarState state() { requireLive(); return mStore.load(); }

    public void selectSpace(String id) {
        ArcSidebarState draft = state();
        draft.selectSpace(id);
        mStore.save(draft);
        mTabs.onSpaceChanged(draft);
    }

    public String createSpace(String name) {
        ArcSidebarState draft = state();
        String id = draft.addSpace(name);
        draft.selectSpace(id);
        mStore.save(draft);
        mTabs.onSpaceChanged(draft);
        return id;
    }

    public String createFolder(String parentId, String name) {
        ArcSidebarState draft = state();
        String id = draft.addFolder(draft.selectedSpace(), parentId, name);
        mStore.save(draft);
        return id;
    }

    public String rememberTab(int tabId, String url, String title, boolean favorite) {
        requireLive();
        if (!mTabs.exists(tabId)) throw new IllegalStateException("Arc tab is not active");
        ArcSidebarState draft = state();
        String existingId = null;
        for (ArcSidebarState.Entry entry : draft.favorites()) {
            if (Integer.valueOf(tabId).equals(entry.tabId)) existingId = entry.id;
        }
        for (ArcSidebarState.Space space : draft.spaces()) {
            for (ArcSidebarState.Entry entry : draft.entries(space.id)) {
                if (Integer.valueOf(tabId).equals(entry.tabId)) existingId = entry.id;
            }
        }
        if (existingId == null) {
            existingId = favorite ? draft.favorite(url, title, tabId)
                    : draft.pin(draft.selectedSpace(), null, url, title, tabId);
        } else {
            draft.setFavorite(existingId, favorite);
        }
        // Publish metadata before changing the native tab; a failed write leaves it untouched.
        mStore.save(draft);
        mTabs.pin(tabId);
        mTabs.onArcStateChanged(draft);
        return existingId;
    }

    public ArcTabActions.Result open(String id) {
        requireLive();
        return mActions.selectOrOpen(id);
    }

    public void remove(String id) {
        ArcSidebarState draft = state();
        Integer tabId = draft.entry(id).tabId;
        draft.unpin(id);
        mStore.save(draft);
        if (tabId != null && mTabs.exists(tabId)) mTabs.unpin(tabId);
        mTabs.onArcStateChanged(draft);
    }

    public void move(String id, String space, String folder, int index) {
        ArcSidebarState draft = state();
        draft.move(id, space, folder, index);
        mStore.save(draft);
        mTabs.onArcStateChanged(draft);
    }

    public void destroy() { mDestroyed = true; }
}
