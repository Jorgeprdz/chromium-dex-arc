// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.text.TextUtils;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.graphics.drawable.StateListDrawable;
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
    private final BoundedScrollView mScroll;
    private final HorizontalScrollView mFavoritesScroll;
    private int mSurface = Color.rgb(238, 238, 238);
    private int mForeground = Color.rgb(32, 32, 32);
    private int mInteraction = Color.rgb(204, 204, 204);

    /** Budget is a maximum, so short collections never reserve a blank panel. */
    private final class BoundedScrollView extends ScrollView {
        private int mBudget = -1;
        BoundedScrollView(Activity activity) { super(activity); }
        void setBudget(int pixels) { mBudget = Math.max(0, pixels); requestLayout(); }
        @Override
        protected void onMeasure(int widthSpec, int heightSpec) {
            int cap = mBudget < 0 ? dp(112) : mBudget;
            if (MeasureSpec.getMode(heightSpec) != MeasureSpec.UNSPECIFIED) {
                cap = Math.min(cap, MeasureSpec.getSize(heightSpec));
            }
            super.onMeasure(widthSpec, MeasureSpec.makeMeasureSpec(cap, MeasureSpec.AT_MOST));
        }
    }
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
        mFavoritesScroll = new HorizontalScrollView(activity);
        mFavoritesScroll.setHorizontalScrollBarEnabled(false);
        mFavoritesScroll.setTag("arc-favorites-mosaic");
        mFavoritesScroll.addView(mFavorites);
        addView(mFavoritesScroll, new LayoutParams(-1, dp(72)));
        mSpace = button("", this::showSpaces);
        mSpace.setTag("arc-current-space");
        mSpace.setContentDescription(activity.getString(R.string.arc_spaces));
        addView(mSpace, new LayoutParams(-1, dp(44)));
        mEntries = new LinearLayout(activity);
        mEntries.setOrientation(VERTICAL);
        mEntries.setContentDescription(activity.getString(R.string.arc_pinned_tabs));
        mScroll = new BoundedScrollView(activity);
        mScroll.setTag("arc-collection-scroll");
        mScroll.addView(mEntries);
        addView(mScroll, new LayoutParams(-1, LayoutParams.WRAP_CONTENT));
        LinearLayout controls = new LinearLayout(activity);
        Button pin = button(activity.getString(R.string.arc_pin_current), () -> remember(false));
        pin.setTag("arc-pin-current");
        Button favorite = button(activity.getString(R.string.arc_favorite_current), () -> remember(true));
        favorite.setTag("arc-favorite-current");
        controls.addView(pin, new LayoutParams(0, dp(44), 1));
        controls.addView(favorite, new LayoutParams(0, dp(44), 1));
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
        mScroll.setBudget(height);
    }

    /** Owns collection styling so site favicons retain their original colors and rounded tiles. */
    public void setAppearance(int surface, int foreground, int interaction) {
        mSurface = surface;
        mForeground = foreground;
        mInteraction = interaction;
        applyAppearance(this);
    }

    private GradientDrawable background(int color, int radius) {
        GradientDrawable result = new GradientDrawable();
        result.setColor(color);
        result.setCornerRadius(dp(radius));
        return result;
    }

    private void applyAppearance(android.view.ViewGroup group) {
        for (int i = 0; i < group.getChildCount(); i++) {
            View child = group.getChildAt(i);
            if (child instanceof ImageButton) {
                ImageButton tile = (ImageButton) child;
                tile.clearColorFilter();
                GradientDrawable shape = background(mSurface, 16);
                tile.setBackground(new RippleDrawable(ColorStateList.valueOf(mInteraction), shape, null));
                tile.setOnHoverListener((view, event) -> {
                    if (event.getAction() == android.view.MotionEvent.ACTION_HOVER_ENTER) shape.setColor(mInteraction);
                    else if (event.getAction() == android.view.MotionEvent.ACTION_HOVER_EXIT) shape.setColor(mSurface);
                    return false;
                });
            } else if (child instanceof Button) {
                Button button = (Button) child;
                button.setTextColor(mForeground);
                StateListDrawable states = new StateListDrawable();
                states.addState(new int[] {android.R.attr.state_hovered}, background(mInteraction, 10));
                states.addState(new int[] {android.R.attr.state_focused}, background(mInteraction, 10));
                states.addState(new int[] {}, background(Color.TRANSPARENT, 10));
                button.setBackground(new RippleDrawable(ColorStateList.valueOf(mInteraction), states, null));
            } else if (child instanceof android.view.ViewGroup) {
                applyAppearance((android.view.ViewGroup) child);
            }
        }
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
            mFavoritesScroll.setVisibility(GONE);
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
        String favoriteFocus = focusedTag(mFavorites);
        String entryFocus = focusedTag(mEntries);
        mFavorites.removeAllViews();
        mFavoritesScroll.setVisibility(state.favorites().isEmpty() ? GONE : VISIBLE);
        for (ArcSidebarState.Entry entry : state.favorites()) {
            ImageButton favorite = new ImageButton(mActivity);
            favorite.setImageResource(android.R.drawable.ic_menu_view);
            favorite.setScaleType(android.widget.ImageView.ScaleType.CENTER_INSIDE);
            favorite.setPadding(dp(16), dp(16), dp(16), dp(16));
            favorite.setContentDescription(entry.title);
            favorite.setTooltipText(entry.title);
            favorite.setTag("arc-entry:" + entry.id);
            favorite.setOnClickListener(view -> runCommand(() -> open(entry.id)));
            favorite.setOnLongClickListener(view -> { showEntryMenu(view, entry); return true; });
            favorite.setOnContextClickListener(view -> { showEntryMenu(view, entry); return true; });
            LayoutParams tileParams = new LayoutParams(dp(64), dp(64));
            tileParams.setMargins(dp(4), dp(4), dp(4), dp(4));
            mFavorites.addView(favorite, tileParams);
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
                Button back = button("‹  " + current.name, () -> mOpenFolder = parent);
                back.setTag("arc-folder-back:" + current.id);
                attachFolderMenu(back, current);
                mEntries.addView(back, new LayoutParams(-1, dp(44)));
            }
        }
        for (ArcSidebarState.Folder folder : folders) {
            if (!java.util.Objects.equals(folder.parentId, mOpenFolder)) continue;
            Button folderRow = button("▸  " + folder.name, () -> mOpenFolder = folder.id);
            folderRow.setTag("arc-folder:" + folder.id);
            attachFolderMenu(folderRow, folder);
            mEntries.addView(folderRow, new LayoutParams(-1, dp(44)));
        }
        for (ArcSidebarState.Entry entry : state.entries(state.selectedSpace())) {
            if (!java.util.Objects.equals(entry.folderId, mOpenFolder)) continue;
            Button row = button(entry.title, () -> open(entry.id));
            row.setTag("arc-entry:" + entry.id);
            row.setOnLongClickListener(view -> { showEntryMenu(view, entry); return true; });
            mEntries.addView(row, new LayoutParams(-1, dp(44)));
        }
        Button newFolder = button(mActivity.getString(R.string.arc_new_folder), () -> {
            String space = state.selectedSpace();
            String parent = mOpenFolder;
            requestName(R.string.arc_new_folder, name -> {
                if (!space.equals(mController.state().selectedSpace())) {
                    throw new IllegalStateException("Space changed");
                }
                mController.createFolder(parent, name);
            });
        });
        newFolder.setTag("arc-new-folder:" + state.selectedSpace());
        mEntries.addView(newFolder, new LayoutParams(-1, dp(44)));
        applyAppearance(this);
        restoreFocus(mFavorites, favoriteFocus);
        restoreFocus(mEntries, entryFocus);
    }

    private static String focusedTag(LinearLayout group) {
        View focused = group.findFocus();
        return focused != null && focused.getTag() instanceof String
                ? (String) focused.getTag() : null;
    }

    private static void restoreFocus(LinearLayout group, String tag) {
        if (tag == null) return;
        View replacement = group.findViewWithTag(tag);
        if (replacement != null) replacement.requestFocus();
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
        menu.getMenu().add(0, spaces.size() + 1, spaces.size() + 1, R.string.arc_delete_space)
                .setEnabled(spaces.size() > 1);
        menu.setOnMenuItemClickListener(item -> {
            runCommand(() -> {
                if (item.getItemId() < spaces.size()) mController.selectSpace(spaces.get(item.getItemId()).id);
                else if (item.getItemId() == spaces.size()) requestName(R.string.arc_new_space, mController::createSpace);
                else {
                    ArcSidebarState.Space target = null;
                    for (ArcSidebarState.Space space : spaces) {
                        if (!space.id.equals(state.selectedSpace())) { target = space; break; }
                    }
                    if (target != null) confirm(R.string.arc_delete_space,
                            mActivity.getString(R.string.arc_delete_space_preserve, target.name),
                            () -> mController.deleteSpace(state.selectedSpace()));
                }
            });
            return true;
        });
        menu.show();
    }

    private void attachFolderMenu(View row, ArcSidebarState.Folder folder) {
        row.setOnLongClickListener(view -> { showFolderMenu(view, folder); return true; });
        row.setOnContextClickListener(view -> { showFolderMenu(view, folder); return true; });
    }

    private void showFolderMenu(View anchor, ArcSidebarState.Folder folder) {
        if (mDestroyed) return;
        PopupMenu menu = new PopupMenu(mActivity, anchor);
        mMenu = menu;
        menu.getMenu().add(0, 0, 0, R.string.arc_delete_folder);
        menu.setOnMenuItemClickListener(item -> {
            confirm(R.string.arc_delete_folder, mActivity.getString(R.string.arc_delete_folder_preserve),
                    () -> mController.deleteFolder(folder.id));
            return true;
        });
        menu.show();
    }

    private void confirm(int title, String message, Runnable command) {
        if (mDestroyed) return;
        mDialog = new AlertDialog.Builder(mActivity).setTitle(title).setMessage(message)
                .setPositiveButton(R.string.arc_delete, (dialog, which) -> runCommand(command))
                .setNegativeButton(android.R.string.cancel, null).create();
        mDialog.show();
        mDialog.getButton(AlertDialog.BUTTON_POSITIVE).setTag("arc-confirm-delete");
        mDialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTag("arc-cancel-delete");
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
