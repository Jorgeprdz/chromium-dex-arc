// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.view.View;
import android.widget.PopupMenu;

import org.chromium.chrome.browser.bookmarks.BookmarkManagerOpener;
import org.chromium.chrome.browser.bookmarks.BookmarkModel;
import org.chromium.chrome.browser.bookmarks.BookmarkModelObserver;
import org.chromium.chrome.browser.bookmarks.BookmarkOpener;
import org.chromium.chrome.browser.bookmarks.BookmarkUtils;
import org.chromium.chrome.browser.bookmarks.R;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabLaunchType;
import org.chromium.components.bookmarks.BookmarkId;
import org.chromium.components.bookmarks.BookmarkItem;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** A transient projection of Chromium's real bookmark bar; it owns no bookmark data. */
public final class ArcNativeBookmarksBridge {
    private final Activity mActivity;
    private final Profile mProfile;
    private final BooleanSupplier mIsCurrentSession;
    private final BookmarkOpener mBookmarkOpener;
    private final Supplier<BookmarkManagerOpener> mManagerOpener;
    private final Supplier<Tab> mCurrentTab;
    private final Consumer<List<BookmarkItem>> mOnChanged;
    private final BookmarkModel mModel;
    private final BookmarkModelObserver mObserver = new BookmarkModelObserver() {
        @Override
        public void bookmarkModelChanged() {
            refresh();
        }
    };
    private List<BookmarkItem> mItems = Collections.emptyList();
    private PopupMenu mMenu;
    private boolean mDestroyed;

    public ArcNativeBookmarksBridge(Activity activity, Profile profile,
            BooleanSupplier isCurrentSession, BookmarkOpener bookmarkOpener,
            Supplier<BookmarkManagerOpener> managerOpener, Supplier<Tab> currentTab,
            Consumer<List<BookmarkItem>> onChanged) {
        mActivity = activity;
        mProfile = profile;
        mIsCurrentSession = isCurrentSession;
        mBookmarkOpener = bookmarkOpener;
        mManagerOpener = managerOpener;
        mCurrentTab = currentTab;
        mOnChanged = onChanged;
        mModel = isActive() ? BookmarkModel.getForProfile(profile) : null;
        if (mModel != null) {
            mModel.addObserver(mObserver);
            // Kick off the same native/partner loading used by the bookmark bar. Our own observer
            // publishes the loaded projection and is removable on destroy. The helper's temporary
            // load observer captures no bridge/session, even if loading outlives this surface.
            mModel.finishLoadingBookmarkModel(() -> {});
        }
        refresh();
    }

    private boolean isActive() {
        return !mDestroyed && mProfile != null && !mProfile.shutdownStarted()
                && mIsCurrentSession.getAsBoolean();
    }

    private boolean isReady() {
        return isActive() && mModel != null && mModel.isBookmarkModelLoaded()
                && BookmarkModel.getForProfile(mProfile) == mModel;
    }

    public List<BookmarkItem> items() {
        return isReady() ? mItems : Collections.emptyList();
    }

    public void refresh() {
        if (!isActive()) return;
        List<BookmarkItem> items = new ArrayList<>();
        if (isReady()) {
            // Chromium's native helper preserves account-before-local ordering and folder IDs.
            for (BookmarkId id : BookmarkUtils.getDesktopBookmarkIds(mModel)) {
                BookmarkItem item = mModel.getBookmarkById(id);
                if (item != null) items.add(item);
            }
        }
        mItems = Collections.unmodifiableList(items);
        mOnChanged.accept(mItems);
    }

    private BookmarkItem currentItem(BookmarkItem snapshot) {
        if (!isReady() || snapshot == null) return null;
        return mModel.getBookmarkById(snapshot.getId());
    }

    public void open(BookmarkItem snapshot) {
        BookmarkItem item = currentItem(snapshot);
        if (item == null) return;
        if (item.isFolder()) showManager(item.getId());
        else mBookmarkOpener.openBookmarkInCurrentTab(item.getId(), mProfile.isOffTheRecord());
    }

    private void showManager(BookmarkId folderId) {
        BookmarkManagerOpener manager = mManagerOpener.get();
        if (manager != null) {
            manager.showBookmarkManager(mActivity, mCurrentTab.get(), mProfile, folderId);
        }
    }

    /** Native opening and editing flows; all other management stays in Chromium's manager. */
    public void showMenu(View anchor, BookmarkItem snapshot) {
        BookmarkItem item = currentItem(snapshot);
        if (item == null) return;
        if (item.isFolder()) {
            showManager(item.getId());
            return;
        }
        if (mMenu != null) mMenu.dismiss();
        PopupMenu menu = new PopupMenu(mActivity, anchor);
        mMenu = menu;
        menu.getMenu().add(0, R.string.contextmenu_open_in_new_tab, 0,
                R.string.contextmenu_open_in_new_tab);
        if (mBookmarkOpener.isOpenInNewWindowSupported()) {
            menu.getMenu().add(0, R.string.contextmenu_open_in_new_window, 1,
                    R.string.contextmenu_open_in_new_window);
        }
        menu.getMenu().add(0, R.string.contextmenu_edit_bookmark_ellipsis, 2,
                R.string.contextmenu_edit_bookmark_ellipsis).setEnabled(item.isEditable());
        menu.getMenu().add(0, R.string.bookmark_item_move, 3,
                R.string.bookmark_item_move).setEnabled(item.isEditable());
        menu.getMenu().add(0, R.string.contextmenu_open_bookmarks_manager, 4,
                R.string.contextmenu_open_bookmarks_manager);
        menu.setOnMenuItemClickListener(command -> {
            BookmarkItem current = currentItem(snapshot);
            if (current == null) return false;
            int id = command.getItemId();
            if (id == R.string.contextmenu_open_in_new_tab) {
                mBookmarkOpener.openBookmarksInNewTabs(List.of(current.getId()),
                        mProfile.isOffTheRecord(), TabLaunchType.FROM_BOOKMARK_BAR_BACKGROUND);
            } else if (id == R.string.contextmenu_open_in_new_window) {
                mBookmarkOpener.openBookmarksInNewWindow(
                        List.of(current.getId()), /* incognito= */ false);
            } else if (id == R.string.contextmenu_open_bookmarks_manager) {
                showManager(current.getParentId());
            } else if (current.isEditable()) {
                BookmarkManagerOpener manager = mManagerOpener.get();
                if (manager == null) return false;
                if (id == R.string.contextmenu_edit_bookmark_ellipsis) {
                    manager.startEditActivity(mActivity, mProfile, current.getId());
                } else if (id == R.string.bookmark_item_move) {
                    manager.startFolderPickerActivity(mActivity, mProfile, current.getId());
                }
            }
            return true;
        });
        menu.show();
    }

    public void destroy() {
        if (mDestroyed) return;
        mDestroyed = true;
        if (mMenu != null) mMenu.dismiss();
        if (mModel != null) mModel.removeObserver(mObserver);
        mItems = Collections.emptyList();
        // BookmarkModel is profile-owned and remains alive for Chromium's other bookmark surfaces.
    }
}
