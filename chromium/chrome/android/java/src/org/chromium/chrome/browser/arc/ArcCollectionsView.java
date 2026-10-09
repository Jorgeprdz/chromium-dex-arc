// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Bitmap;
import android.graphics.Typeface;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.ScrollView;
import android.widget.Toast;

import org.chromium.chrome.R;
import org.chromium.chrome.browser.ui.favicon.FaviconUtils;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
import org.chromium.components.bookmarks.BookmarkItem;
import org.chromium.url.GURL;

import java.util.List;
import java.util.function.BiConsumer;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** Real local collection controls; native TabModel continues owning the open tabs. */
public final class ArcCollectionsView extends LinearLayout {
    public static final class CurrentTab {
        public final int id;
        public final String url;
        public final String title;
        public CurrentTab(int id, String url, String title) {
            this.id = id; this.url = url; this.title = title;
        }
    }
    private final Activity mActivity;
    private final ArcCollectionsController mController;
    private final Supplier<CurrentTab> mCurrentTab;
    private final BiConsumer<ArcSidebarState.Entry, ImageButton> mLoadIcon;
    private final LinearLayout mFavorites;
    private final ScrollView mFavoritesScroll;
    private ArcNativeBookmarksBridge mNativeBookmarks;
    private BiConsumer<BookmarkItem, ImageButton> mLoadNativeIcon;
    private final LinearLayout mEntries;
    private final Button mSpace;
    private final ScrollView mScroll;
    private String mOpenFolder;
    private String mRenderedSpace;
    private AlertDialog mDialog;
    private PopupMenu mMenu;
    private boolean mDestroyed;
    private boolean mIncognito;
    private ArcDesktopPolicy.Geometry mGeometry;

    public ArcCollectionsView(Activity activity, ArcCollectionsController controller,
            Supplier<CurrentTab> currentTab,
            BiConsumer<ArcSidebarState.Entry, ImageButton> loadIcon) {
        super(activity);
        mActivity = activity;
        mController = controller;
        mCurrentTab = currentTab;
        mLoadIcon = loadIcon;
        setOrientation(VERTICAL);
        setPadding(dp(8), dp(4), dp(8), dp(4));
        mFavorites = new ArcFavoriteTiles(activity);
        mFavorites.setContentDescription(activity.getString(R.string.arc_favorites));
        mFavoritesScroll = new ScrollView(activity);
        mFavoritesScroll.setVerticalScrollBarEnabled(false);
        mFavoritesScroll.addView(mFavorites);
        addView(mFavoritesScroll, new LayoutParams(-1, dp(52)));
        mSpace = button("", this::showSpaces);
        mSpace.setTag("arc-current-space");
        mSpace.setContentDescription(activity.getString(R.string.arc_spaces));
        mSpace.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        mSpace.setTextSize(ArcDesktopPolicy.ARC_PRINCIPAL_TEXT_SIZE_SP);
        addView(mSpace, new LayoutParams(-1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        mEntries = new LinearLayout(activity);
        mEntries.setOrientation(VERTICAL);
        mEntries.setContentDescription(activity.getString(R.string.arc_pinned_tabs));
        mScroll = new ScrollView(activity);
        mScroll.setVerticalScrollBarEnabled(false);
        mScroll.addView(mEntries);
        addView(mScroll, new LayoutParams(-1, dp(112)));
        LinearLayout controls = new LinearLayout(activity);
        Button pin = button(activity.getString(R.string.arc_pin_current), () -> remember(false));
        pin.setTag("arc-pin-current");
        pin.setTextSize(ArcDesktopPolicy.ARC_SECONDARY_TEXT_SIZE_SP);
        Button favorite = button(activity.getString(R.string.arc_favorite_current), () -> remember(true));
        favorite.setTag("arc-favorite-current");
        favorite.setTextSize(ArcDesktopPolicy.ARC_SECONDARY_TEXT_SIZE_SP);
        controls.addView(pin, new LayoutParams(0, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP), 1));
        controls.addView(favorite, new LayoutParams(0, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP), 1));
        addView(controls);
        refresh();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private Button button(String text, Runnable action) {
        Button result = new Button(mActivity);
        result.setText(text);
        result.setAllCaps(false);
        result.setTextSize(ArcDesktopPolicy.ARC_TAB_TEXT_SIZE_SP);
        result.setMinWidth(0); result.setMinimumWidth(0);
        result.setMinHeight(0); result.setMinimumHeight(0);
        result.setPadding(dp(8), 0, dp(8), 0);
        result.setSingleLine(true);
        result.setEllipsize(TextUtils.TruncateAt.END);
        result.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        styleAction(result);
        result.setOnClickListener(view -> runCommand(action));
        return result;
    }

    private void styleAction(Button button) {
        button.setBackgroundTintList(null);
        button.setStateListAnimator(null);
        button.setElevation(0);
        button.setTextColor(ArcDesktopAppearance.rowTextColor(mActivity, false, mIncognito));
        button.setBackground(ArcDesktopAppearance.controlBackground(mActivity, mIncognito, 12));
    }

    private void styleFavorite(ImageButton favorite) {
        favorite.setBackgroundTintList(null);
        favorite.setStateListAnimator(null);
        favorite.setElevation(0);
        favorite.setBackground(ArcDesktopAppearance.favoriteBackground(mActivity, mIncognito, 12));
    }

    /** Repaint only collection controls; native bookmark and favorite icons retain their colors. */
    public void applyAppearance(boolean incognito) {
        mIncognito = incognito;
        styleCollectionControls(this);
    }

    private void styleCollectionControls(View view) {
        if (view instanceof ImageButton) styleFavorite((ImageButton) view);
        else if (view instanceof Button) styleAction((Button) view);
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) styleCollectionControls(group.getChildAt(i));
        }
    }

    private void initializeFavoriteIcon(ImageButton favorite) {
        favorite.setImageBitmap(FaviconUtils.createGenericFaviconBitmap(mActivity, dp(24), null));
    }

    /** Consume both bitmap and fallback results from Chromium's profile-bound LargeIconBridge. */
    public static void applyFavoriteIcon(ImageButton button, GURL url, Bitmap icon, int fallbackColor) {
        button.clearColorFilter();
        button.setImageTintList(null);
        int size = Math.round(24 * button.getResources().getDisplayMetrics().density);
        if (icon == null && (url == null || url.isEmpty())) {
            button.setImageBitmap(FaviconUtils.createGenericFaviconBitmap(button.getContext(), size, null));
            return;
        }
        button.setImageDrawable(FaviconUtils.getIconDrawableWithoutFilter(icon, url, fallbackColor,
                FaviconUtils.createRoundedRectangleIconGenerator(button.getContext()),
                button.getResources(), size));
    }

    private void runCommand(Runnable command) {
        if (mDestroyed) return;
        try { command.run(); refresh(); }
        catch (RuntimeException failure) {
            Toast.makeText(mActivity, R.string.arc_collection_error, Toast.LENGTH_SHORT).show();
        }
    }

    public void setCollectionHeight(int height) {
        android.view.ViewGroup.LayoutParams params = mScroll.getLayoutParams();
        if (params.height != height) { params.height = height; mScroll.setLayoutParams(params); }
    }

    /** Size the existing favorite buttons; retain their bookmark/collection handlers and icons. */
    public void applyGeometry(ArcDesktopPolicy.Geometry geometry, int availableWidthPx) {
        mGeometry = geometry;
        setPadding(0, 0, 0, 0);
        mFavoritesScroll.setVisibility(mFavorites.getChildCount() == 0 ? View.GONE : View.VISIBLE);
        LayoutParams space = (LayoutParams) mSpace.getLayoutParams();
        if (space.bottomMargin != geometry.sectionGap) {
            space.bottomMargin = geometry.sectionGap;
            mSpace.setLayoutParams(space);
        }
        LayoutParams row = (LayoutParams) mFavoritesScroll.getLayoutParams();
        int rows = (mFavorites.getChildCount() + 2) / 3;
        // Keep the native tab rail reachable even when the user's bookmark bar is very large.
        // The vertical ScrollView retains every tile below this three-row viewport.
        int visibleRows = Math.min(rows, 3);
        int height = visibleRows * geometry.quickAccessHeight
                + Math.max(0, visibleRows - 1) * geometry.sectionGap;
        if (row.height != height || row.bottomMargin != geometry.sectionGap) {
            row.height = height;
            row.bottomMargin = geometry.sectionGap;
            mFavoritesScroll.setLayoutParams(row);
        }
        int tilesWidth = Math.max(0, availableWidthPx
                - geometry.quickAccessGap - geometry.quickAccessSecondGap);
        for (int i = 0; i < mFavorites.getChildCount(); i++) {
            View favorite = mFavorites.getChildAt(i);
            LayoutParams tile = (LayoutParams) favorite.getLayoutParams();
            int column = i % 3;
            int width = (column + 1) * tilesWidth / 3 - column * tilesWidth / 3;
            int gap = i + 1 == mFavorites.getChildCount() || column == 2 ? 0
                    : column == 1 ? geometry.quickAccessSecondGap : geometry.quickAccessGap;
            int rowGap = i / 3 + 1 < rows ? geometry.sectionGap : 0;
            if (tile.width != width || tile.height != geometry.quickAccessHeight
                    || tile.getMarginEnd() != gap || tile.bottomMargin != rowGap) {
                tile.width = width;
                tile.height = geometry.quickAccessHeight;
                tile.setMarginEnd(gap);
                tile.bottomMargin = rowGap;
                favorite.setLayoutParams(tile);
            }
        }
    }

    @Override
    protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
        super.onLayout(changed, left, top, right, bottom);
        if (!mDestroyed && mGeometry != null) applyGeometry(mGeometry, getWidth());
    }

    private void remember(boolean favorite) {
        CurrentTab tab = mCurrentTab.get();
        if (tab == null) throw new IllegalStateException("No active tab");
        String title = tab.title == null || tab.title.isEmpty() ? tab.url : tab.title;
        if (title.length() > 256) title = title.substring(0, 256);
        mController.rememberTab(tab.id, tab.url, title, favorite);
    }

    public void refresh() {
        if (mDestroyed) return;
        ArcSidebarState state;
        try {
            state = mController.state();
        } catch (RuntimeException damagedOrUnavailableState) {
            // Preserve the original bytes for recovery. A metadata read failure
            // must not crash browser startup or silently replace a user's data.
            refreshFavorites(java.util.Collections.emptyList());
            mEntries.removeAllViews();
            mSpace.setText(R.string.arc_collection_error);
            findViewWithTag("arc-pin-current").setEnabled(false);
            findViewWithTag("arc-favorite-current").setEnabled(false);
            return;
        }
        findViewWithTag("arc-pin-current").setEnabled(true);
        findViewWithTag("arc-favorite-current").setEnabled(true);
        if (!state.selectedSpace().equals(mRenderedSpace)) {
            mOpenFolder = null;
            mRenderedSpace = state.selectedSpace();
        }
        refreshFavorites(state.favorites());
        for (ArcSidebarState.Space space : state.spaces()) {
            if (space.id.equals(state.selectedSpace())) mSpace.setText(space.name + "  ▾");
        }
        mEntries.removeAllViews();
        List<ArcSidebarState.Folder> folders = state.folders(state.selectedSpace());
        if (mOpenFolder != null) {
            ArcSidebarState.Folder current = null;
            for (ArcSidebarState.Folder folder : folders) {
                if (folder.id.equals(mOpenFolder)) current = folder;
            }
            if (current == null) mOpenFolder = null;
            else {
                String parent = current.parentId;
                mEntries.addView(button("‹  " + current.name, () -> mOpenFolder = parent),
                        new LayoutParams(-1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
            }
        }
        for (ArcSidebarState.Folder folder : folders) {
            if (!java.util.Objects.equals(folder.parentId, mOpenFolder)) continue;
            mEntries.addView(button("▸  " + folder.name, () -> mOpenFolder = folder.id),
                    new LayoutParams(-1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        }
        for (ArcSidebarState.Entry entry : state.entries(state.selectedSpace())) {
            if (!java.util.Objects.equals(entry.folderId, mOpenFolder)) continue;
            Button row = button(entry.title, () -> open(entry.id));
            row.setTag("arc-entry:" + entry.id);
            row.setOnLongClickListener(view -> { showEntryMenu(view, entry); return true; });
            mEntries.addView(row, new LayoutParams(-1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        }
        mFavoritesScroll.setVisibility(mFavorites.getChildCount() == 0 ? View.GONE : View.VISIBLE);
        mEntries.addView(button(mActivity.getString(R.string.arc_new_folder), () -> {
            String space = state.selectedSpace();
            String parent = mOpenFolder;
            requestName(R.string.arc_new_folder, name -> {
                if (!space.equals(mController.state().selectedSpace())) {
                    throw new IllegalStateException("Space changed");
                }
                mController.createFolder(parent, name);
            });
        }), new LayoutParams(-1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
    }

    /** The bridge projects native bookmarks without persisting them in Arc's collection store. */
    public void setNativeBookmarks(ArcNativeBookmarksBridge bookmarks,
            BiConsumer<BookmarkItem, ImageButton> loadIcon) {
        if (mDestroyed) return;
        mNativeBookmarks = bookmarks;
        mLoadNativeIcon = loadIcon;
        refresh();
    }

    private void refreshFavorites(List<ArcSidebarState.Entry> entries) {
        mFavorites.removeAllViews();
        if (mNativeBookmarks != null) {
            for (BookmarkItem item : mNativeBookmarks.items()) {
                ImageButton favorite = new ImageButton(mActivity);
                if (item.isFolder()) favorite.setImageResource(android.R.drawable.ic_menu_agenda);
                else initializeFavoriteIcon(favorite);
                styleFavorite(favorite);
                favorite.setScaleType(android.widget.ImageView.ScaleType.CENTER_INSIDE);
                favorite.setPadding(dp(12), dp(12), dp(12), dp(12));
                favorite.setContentDescription(item.getTitle());
                favorite.setTooltipText(item.getTitle());
                favorite.setTag("arc-bookmark:" + item.getId());
                favorite.setOnClickListener(view -> runCommand(() -> mNativeBookmarks.open(item)));
                favorite.setOnLongClickListener(view -> {
                    if (!mDestroyed && mNativeBookmarks != null) mNativeBookmarks.showMenu(view, item);
                    return true;
                });
                mFavorites.addView(favorite, new LayoutParams(dp(52), dp(48)));
                if (!item.isFolder() && mLoadNativeIcon != null) mLoadNativeIcon.accept(item, favorite);
            }
        }
        for (ArcSidebarState.Entry entry : entries) {
            ImageButton favorite = new ImageButton(mActivity);
            initializeFavoriteIcon(favorite);
            styleFavorite(favorite);
            favorite.setScaleType(android.widget.ImageView.ScaleType.CENTER_INSIDE);
            favorite.setPadding(dp(12), dp(12), dp(12), dp(12));
            favorite.setContentDescription(entry.title);
            favorite.setTooltipText(entry.title);
            favorite.setTag("arc-entry:" + entry.id);
            favorite.setOnClickListener(view -> runCommand(() -> open(entry.id)));
            favorite.setOnLongClickListener(view -> { showEntryMenu(view, entry); return true; });
            mFavorites.addView(favorite, new LayoutParams(dp(52), dp(48)));
            mLoadIcon.accept(entry, favorite);
        }
        mFavoritesScroll.setVisibility(mFavorites.getChildCount() == 0 ? View.GONE : View.VISIBLE);
        if (mGeometry != null) applyGeometry(mGeometry, getWidth());
    }

    private void open(String id) {
        ArcTabActions.Result result = mController.open(id);
        if (result == ArcTabActions.Result.NOT_OPENED || result == ArcTabActions.Result.PERSISTENCE_ERROR) {
            throw new IllegalStateException("Arc entry could not be opened or stored");
        }
    }

    private void showSpaces() {
        if (mDestroyed) return;
        ArcSidebarState state = mController.state();
        List<ArcSidebarState.Space> spaces = state.spaces();
        PopupMenu menu = new PopupMenu(mActivity, mSpace);
        mMenu = menu;
        for (int i = 0; i < spaces.size(); i++) menu.getMenu().add(0, i, i, spaces.get(i).name);
        menu.getMenu().add(0, spaces.size(), spaces.size(), R.string.arc_new_space);
        menu.setOnMenuItemClickListener(item -> {
            runCommand(() -> {
                if (item.getItemId() < spaces.size()) mController.selectSpace(spaces.get(item.getItemId()).id);
                else requestName(R.string.arc_new_space, mController::createSpace);
            });
            return true;
        });
        menu.show();
    }

    private void showEntryMenu(View anchor, ArcSidebarState.Entry entry) {
        if (mDestroyed) return;
        PopupMenu menu = new PopupMenu(mActivity, anchor);
        mMenu = menu;
        menu.getMenu().add(0, 0, 0, R.string.arc_remove_entry);
        if (!entry.favorite) menu.getMenu().add(0, 1, 1, R.string.arc_move_to_folder);
        menu.setOnMenuItemClickListener(item -> {
            runCommand(() -> {
                if (item.getItemId() == 0) mController.remove(entry.id);
                else showFolderChoices(anchor, entry);
            });
            return true;
        });
        menu.show();
    }

    private void showFolderChoices(View anchor, ArcSidebarState.Entry entry) {
        List<ArcSidebarState.Folder> folders = mController.state().folders(entry.spaceId);
        PopupMenu menu = new PopupMenu(mActivity, anchor);
        mMenu = menu;
        menu.getMenu().add(0, 0, 0, R.string.arc_folder_root);
        for (int i = 0; i < folders.size(); i++) menu.getMenu().add(0, i + 1, i + 1, folders.get(i).name);
        menu.setOnMenuItemClickListener(item -> {
            runCommand(() -> mController.move(entry.id, entry.spaceId,
                    item.getItemId() == 0 ? null : folders.get(item.getItemId() - 1).id, 0));
            return true;
        });
        menu.show();
    }

    private void requestName(int title, Consumer<String> save) {
        if (mDestroyed) return;
        EditText input = new EditText(mActivity);
        input.setSingleLine(true);
        input.setHint(R.string.arc_name);
        input.setFilters(new android.text.InputFilter[] {new android.text.InputFilter.LengthFilter(256)});
        mDialog = new AlertDialog.Builder(mActivity).setTitle(title).setView(input)
                .setPositiveButton(android.R.string.ok, null)
                .setNegativeButton(android.R.string.cancel, null).create();
        AlertDialog dialog = mDialog;
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(view -> {
            String name = input.getText().toString().trim();
            if (name.isEmpty()) { input.setError(mActivity.getString(R.string.arc_name)); return; }
            runCommand(() -> save.accept(name));
            dialog.dismiss();
        }));
        dialog.show();
    }

    public void destroy() {
        if (mDestroyed) return;
        mDestroyed = true;
        mNativeBookmarks = null;
        mLoadNativeIcon = null;
        if (mDialog != null) mDialog.dismiss();
        if (mMenu != null) mMenu.dismiss();
    }
}
