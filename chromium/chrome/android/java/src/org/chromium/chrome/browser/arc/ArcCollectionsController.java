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

    public void deleteFolder(String id) {
        ArcSidebarState draft = state();
        draft.deleteFolder(id);
        mStore.save(draft);
        mTabs.onArcStateChanged(draft);
    }

    public void deleteSpace(String id) {
        ArcSidebarState draft = state();
        draft.deleteSpace(id);
        mStore.save(draft);
        mTabs.onSpaceChanged(draft);
    }

    public String rememberTab(int tabId, String url, String title, boolean favorite) {
        return rememberTab(tabId, url, title, favorite, null);
    }

    public String rememberTab(int tabId, String url, String title, boolean favorite,
            String folderId) {
        requireLive();
        if (!mTabs.exists(tabId)) throw new IllegalStateException("Arc tab is not active");
        ArcSidebarState draft = state();
        String existingId = null;
        for (ArcSidebarState.Entry entry : draft.favorites()) {
            if (favorite ? url.equals(entry.url) : Integer.valueOf(tabId).equals(entry.tabId)) {
                existingId = entry.id;
            }
        }
        for (ArcSidebarState.Space space : draft.spaces()) {
            for (ArcSidebarState.Entry entry : draft.entries(space.id)) {
                if (existingId == null && Integer.valueOf(tabId).equals(entry.tabId)
                        && (!favorite || url.equals(entry.url))) existingId = entry.id;
            }
        }
        if (favorite && (existingId == null || draft.entry(existingId).tabId == null)) {
            // A tab may navigate away from its saved URL. Release only its live association;
            // preserve the old favorite and its canonical URL/title.
            draft.tabClosed(tabId);
        }
        if (existingId == null) {
            existingId = favorite ? draft.favorite(url, title, tabId)
                    : draft.pin(draft.selectedSpace(), folderId, url, title, tabId);
        } else {
            draft.setFavorite(existingId, favorite);
            ArcSidebarState.Entry existing = draft.entry(existingId);
            if (!favorite && (!draft.selectedSpace().equals(existing.spaceId)
                    || !java.util.Objects.equals(folderId, existing.folderId))) {
                int end = draft.entries(draft.selectedSpace()).size()
                        - (draft.selectedSpace().equals(existing.spaceId) ? 1 : 0);
                draft.move(existingId, draft.selectedSpace(), folderId, end);
            }
        }
        draft.updateMetadata(existingId, url, title);
        if (draft.entry(existingId).tabId == null) draft.bindTab(existingId, tabId);
        // Publish metadata before changing the native tab; a failed write leaves it untouched.
        mStore.save(draft);
        mTabs.pin(draft.entry(existingId).tabId);
        mTabs.onArcStateChanged(draft);
        return existingId;
    }

    /** Project native title/URL edits without changing identity, order, Space or live tabs. */
    public void updateFavorite(String id, String url, String title) {
        ArcSidebarState draft = state();
        if (!draft.entry(id).favorite) return;
        draft.updateMetadata(id, url, title);
        mStore.save(draft);
        mTabs.onArcStateChanged(draft);
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

    public boolean canClose(String id) {
        Integer tabId = state().entry(id).tabId;
        return tabId != null && mTabs.exists(tabId);
    }

    /** Closing is a native undoable operation, independent of removing the saved entry. */
    public void close(String id) {
        Integer tabId = state().entry(id).tabId;
        if (tabId != null) mActions.closeTab(tabId);
    }

    public void move(String id, String space, String folder, int index) {
        ArcSidebarState draft = state();
        draft.move(id, space, folder, index);
        mStore.save(draft);
        mTabs.onArcStateChanged(draft);
    }

    public void destroy() { mDestroyed = true; }
}
