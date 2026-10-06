### Task 2: Persistent Favorites, pinned entries and local Spaces

**Files:**
- Create: `chrome/android/java/src/org/chromium/chrome/browser/arc/ArcSidebarState.java`.
- Create: `chrome/android/java/src/org/chromium/chrome/browser/arc/ArcSidebarStore.java`.
- Create: `chrome/android/java/src/org/chromium/chrome/browser/arc/ArcTabActions.java`.
- Modify: `ArcDesktopCoordinator.java`, native tab/vertical-tabs integration and `chrome_java_sources.gni`.
- Test: pure state/store tests and native TabModel integration tests.

**Interfaces:**
- `ArcSidebarState` defines versioned persisted Space, Folder, PinnedEntry and Favorite identities. A pinned entry stores canonical URL/title and optional native tab association; favorites are shared between local Spaces.
- `ArcSidebarStore.load(): ArcSidebarState`, `save(ArcSidebarState): void`; persist through Chromium profile preferences with versioned migration, no credentials or web content.
- `ArcTabActions.selectOrOpen(entryId)`, `closeTab(tabId)`, `pin(tabId, spaceId)`, `move(entryId, targetSpaceId, folderId, index)`; adapter to TabModel/TabCreator/bookmark models.

- [ ] Write RED tests: stable entry identity/order after reload; closing pinned tab preserves entry/canonical URL; reopening selects/creates exactly one tab; moving between Spaces/folders preserves identity; normal and incognito state cannot mix; invalid persisted association recovers by reopening.
- [ ] Implement state model, persistence and migrations. Bridge native tab events without representing pinned tabs as a list of unrelated header bookmarks.
- [ ] Wire real local Spaces only if they are shown in the reference; selecting one changes its visible pinned/open collections. No visual dots without function.
- [ ] Run state/native tests. Expected all operations survive restart and no duplicate or lost native tabs.
- [ ] Commit model, adapters and tests.
