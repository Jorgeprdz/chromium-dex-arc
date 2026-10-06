// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.ScrollView;
import android.widget.Toast;

import org.chromium.chrome.R;

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
    private final LinearLayout mEntries;
    private final Button mSpace;
    private final ScrollView mScroll;
    private String mOpenFolder;
    private String mRenderedSpace;
    private AlertDialog mDialog;
    private PopupMenu mMenu;
    private boolean mDestroyed;

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
        mFavorites = new LinearLayout(activity);
        mFavorites.setContentDescription(activity.getString(R.string.arc_favorites));
        HorizontalScrollView favoritesScroll = new HorizontalScrollView(activity);
        favoritesScroll.setHorizontalScrollBarEnabled(false);
        favoritesScroll.addView(mFavorites);
        addView(favoritesScroll, new LayoutParams(-1, dp(52)));
        mSpace = button("", this::showSpaces);
        mSpace.setTag("arc-current-space");
        mSpace.setContentDescription(activity.getString(R.string.arc_spaces));
        addView(mSpace, new LayoutParams(-1, dp(36)));
        mEntries = new LinearLayout(activity);
        mEntries.setOrientation(VERTICAL);
        mEntries.setContentDescription(activity.getString(R.string.arc_pinned_tabs));
        mScroll = new ScrollView(activity);
        mScroll.addView(mEntries);
        addView(mScroll, new LayoutParams(-1, dp(112)));
        LinearLayout controls = new LinearLayout(activity);
        Button pin = button(activity.getString(R.string.arc_pin_current), () -> remember(false));
        pin.setTag("arc-pin-current");
        Button favorite = button(activity.getString(R.string.arc_favorite_current), () -> remember(true));
        favorite.setTag("arc-favorite-current");
        controls.addView(pin, new LayoutParams(0, dp(36), 1));
        controls.addView(favorite, new LayoutParams(0, dp(36), 1));
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
        result.setTextSize(12);
        result.setMinWidth(0); result.setMinimumWidth(0);
        result.setPadding(dp(8), 0, dp(8), 0);
        result.setSingleLine(true);
        result.setEllipsize(TextUtils.TruncateAt.END);
        result.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        result.setOnClickListener(view -> runCommand(action));
        return result;
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
            mFavorites.removeAllViews();
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
        mFavorites.removeAllViews();
        for (ArcSidebarState.Entry entry : state.favorites()) {
            ImageButton favorite = new ImageButton(mActivity);
            favorite.setImageResource(android.R.drawable.ic_menu_view);
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
                        new LayoutParams(-1, dp(36)));
            }
        }
        for (ArcSidebarState.Folder folder : folders) {
            if (!java.util.Objects.equals(folder.parentId, mOpenFolder)) continue;
            mEntries.addView(button("▸  " + folder.name, () -> mOpenFolder = folder.id),
                    new LayoutParams(-1, dp(36)));
        }
        for (ArcSidebarState.Entry entry : state.entries(state.selectedSpace())) {
            if (!java.util.Objects.equals(entry.folderId, mOpenFolder)) continue;
            Button row = button(entry.title, () -> open(entry.id));
            row.setTag("arc-entry:" + entry.id);
            row.setOnLongClickListener(view -> { showEntryMenu(view, entry); return true; });
            mEntries.addView(row, new LayoutParams(-1, dp(36)));
        }
        mEntries.addView(button(mActivity.getString(R.string.arc_new_folder), () -> {
            String space = state.selectedSpace();
            String parent = mOpenFolder;
            requestName(R.string.arc_new_folder, name -> {
                if (!space.equals(mController.state().selectedSpace())) {
                    throw new IllegalStateException("Space changed");
                }
                mController.createFolder(parent, name);
            });
        }), new LayoutParams(-1, dp(36)));
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
        if (mDialog != null) mDialog.dismiss();
        if (mMenu != null) mMenu.dismiss();
    }
}
