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
import android.widget.GridLayout;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.ScrollView;
import android.widget.Toast;

import org.chromium.chrome.R;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

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
    private final GridLayout mFavorites;
    private final Button mFavoritesMenu;
    private final LinearLayout mEntries;
    private final LinearLayout mControls;
    private final Button mSpace;
    private final Button mNewFolder;
    private final BoundedScrollView mScroll;
    private final BoundedScrollView mFavoritesScroll;
    private int mCollectionHeight = -1;
    private boolean mCompactRequested;
    private android.graphics.drawable.Drawable mPinGlyph, mFavoriteGlyph, mFavoriteFilledGlyph, mSpaceChevron;
    private void updateGlyphs() {
        mSpaceChevron = new ArcDesktopIcons(ArcDesktopIcons.Kind.CHEVRON_DOWN, mForeground);
        mSpaceChevron.setBounds(0, 0, dp(16), dp(16));
        mPinGlyph = new ArcDesktopIcons(ArcDesktopIcons.Kind.PIN, mForeground);
        mFavoriteGlyph = new ArcDesktopIcons(ArcDesktopIcons.Kind.FAVORITE, mForeground);
        mFavoriteFilledGlyph = new ArcDesktopIcons(ArcDesktopIcons.Kind.FAVORITE_FILLED, mForeground);
        for (var glyph : new android.graphics.drawable.Drawable[] {mPinGlyph, mFavoriteGlyph, mFavoriteFilledGlyph}) {
            glyph.setBounds(0, 0, dp(20), dp(20));
        }
    }
    private int mSurface = Color.rgb(238, 238, 238);
    private int mForeground = Color.rgb(32, 32, 32);
    private int mInteraction = Color.rgb(204, 204, 204);

    /** Budget is a maximum, so short collections never reserve a blank panel. */
    private final class BoundedScrollView extends ScrollView {
        private int mBudget = -1;
        BoundedScrollView(Activity activity) { super(activity); }
        void setBudget(int pixels) {
            int budget = Math.max(0, pixels);
            if (mBudget == budget) return;
            mBudget = budget; requestLayout();
        }
        @Override
        protected void onMeasure(int widthSpec, int heightSpec) {
            int cap = mBudget < 0 ? dp(112) : mBudget;
            if (MeasureSpec.getMode(heightSpec) != MeasureSpec.UNSPECIFIED) {
                cap = Math.min(cap, MeasureSpec.getSize(heightSpec));
            }
            super.onMeasure(widthSpec, MeasureSpec.makeMeasureSpec(cap, MeasureSpec.AT_MOST));
        }
    }
    private Runnable mSaveNativeFavorite;
    public void setNativeFavoriteAction(Runnable action) { mSaveNativeFavorite = action; }
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
        updateGlyphs();
        mController = controller;
        mCurrentTab = currentTab;
        mLoadIcon = loadIcon;
        setOrientation(VERTICAL);
        setPadding(dp(8), dp(4), dp(8), dp(8));
        mFavorites = new GridLayout(activity);
        mFavorites.setColumnCount(2);
        mFavorites.setContentDescription(activity.getString(R.string.arc_favorites));
        mFavorites.setAccessibilityHeading(true);
        mFavoritesScroll = new BoundedScrollView(activity);
        mFavoritesScroll.setBudget(Integer.MAX_VALUE);
        mFavoritesScroll.setTag("arc-favorites-mosaic");
        mFavoritesScroll.addView(mFavorites);
        addView(mFavoritesScroll, new LayoutParams(-1, LayoutParams.WRAP_CONTENT));
        mFavoritesMenu = button(activity.getString(R.string.arc_favorites) + " ▾", this::showFavorites);
        mFavoritesMenu.setTag("arc-favorites-menu");
        mFavoritesMenu.setText("");
        mFavoritesMenu.setGravity(Gravity.CENTER);
        mFavoritesMenu.setCompoundDrawablesRelative(mFavoriteGlyph, null, null, null);
        mFavoritesMenu.setVisibility(GONE);
        addView(mFavoritesMenu, new LayoutParams(-1, dp(44)));
        mSpace = button("", this::showSpaces);
        mSpace.setTag("arc-current-space");
        mSpace.setAccessibilityHeading(true);
        mSpace.setContentDescription(activity.getString(R.string.arc_spaces));
        mSpace.setTypeface(android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL));
        mSpace.setPadding(dp(10), 0, dp(10), 0);
        mSpace.setCompoundDrawablePadding(dp(8));
        mSpace.setCompoundDrawablesRelative(null, null, mSpaceChevron, null);
        LayoutParams spaceParams = new LayoutParams(-1, dp(44));
        spaceParams.topMargin = dp(8); spaceParams.bottomMargin = dp(2);
        addView(mSpace, spaceParams);
        mEntries = new LinearLayout(activity);
        mEntries.setOrientation(VERTICAL);
        mEntries.setContentDescription(activity.getString(R.string.arc_pinned_tabs));
        mEntries.setAccessibilityHeading(true);
        mScroll = new BoundedScrollView(activity);
        mScroll.setTag("arc-collection-scroll");
        mScroll.addView(mEntries);
        addView(mScroll, new LayoutParams(-1, LayoutParams.WRAP_CONTENT));
        mNewFolder = button(mActivity.getString(R.string.arc_new_folder), () -> {
            String space = mController.state().selectedSpace();
            String parent = mOpenFolder;
            requestName(R.string.arc_new_folder, name -> {
                if (!space.equals(mController.state().selectedSpace())) {
                    throw new IllegalStateException("Space changed");
                }
                mController.createFolder(parent, name);
            });
        });
        // Keep the action outside the scrolling entries so the boundary below collections
        // cannot expose only the top of its normal 44dp target.
        addView(mNewFolder, new LayoutParams(-1, dp(44)));
        LinearLayout controls = new LinearLayout(activity);
        mControls = controls;
        Button pin = button(activity.getString(R.string.arc_pin_current), () -> remember(false));
        pin.setTag("arc-pin-current");
        Button favorite = button(activity.getString(R.string.arc_favorite_current), () -> remember(true));
        favorite.setTag("arc-favorite-current");
        controls.addView(pin, new LayoutParams(0, dp(44), 1));
        controls.addView(favorite, new LayoutParams(0, dp(44), 1));
        addView(controls);
        refresh();
    }

    /** Zero denotes the accessible menu; a mosaic never has a single column. */
    static int favoriteColumns(int availablePx, int slotPx) {
        if (slotPx <= 0 || availablePx / slotPx < 2) return 0;
        return availablePx / slotPx;
    }

    @Override
    protected void onMeasure(int widthSpec, int heightSpec) {
        int available = Math.max(0, MeasureSpec.getSize(widthSpec) - getPaddingLeft() - getPaddingRight());
        int columns = favoriteColumns(available, dp(56));
        // Favorite refreshes may arrive without a coordinator geometry update.
        updateCompactViews();
        updateCollectionBudgets(columns);
        boolean empty = mFavorites.getChildCount() == 0;
        boolean menuOnly = columns == 0 || mFavoritesScroll.mBudget < dp(56);
        mFavoritesScroll.setVisibility(!empty && !menuOnly ? VISIBLE : GONE);
        mFavoritesMenu.setVisibility(!empty && menuOnly ? VISIBLE : GONE);
        if (columns >= 2 && columns != mFavorites.getColumnCount()) {
            // Clear previous explicit column constraints before shrinking the grid.
            for (int i = 0; i < mFavorites.getChildCount(); i++) {
                GridLayout.LayoutParams params = (GridLayout.LayoutParams) mFavorites.getChildAt(i).getLayoutParams();
                params.columnSpec = GridLayout.spec(GridLayout.UNDEFINED);
                params.rowSpec = GridLayout.spec(GridLayout.UNDEFINED);
                mFavorites.getChildAt(i).setLayoutParams(params);
            }
            mFavorites.setColumnCount(columns);
            for (int i = 0; i < mFavorites.getChildCount(); i++) {
                View tile = mFavorites.getChildAt(i);
                GridLayout.LayoutParams params = (GridLayout.LayoutParams) tile.getLayoutParams();
                params.rowSpec = GridLayout.spec(i / columns);
                params.columnSpec = GridLayout.spec(i % columns);
                tile.setLayoutParams(params);
            }
        }
        compactAction(findViewWithTag("arc-pin-current"), R.string.arc_pin_current,
                mPinGlyph, available / 2 < dp(144));
        compactAction(findViewWithTag("arc-favorite-current"), R.string.arc_favorite_current,
                findViewWithTag("arc-favorite-current").isSelected() ? mFavoriteFilledGlyph : mFavoriteGlyph,
                available / 2 < dp(144));
        super.onMeasure(widthSpec, heightSpec);
    }

    private void compactAction(Button action, int label, android.graphics.drawable.Drawable icon, boolean compact) {
        String text = compact ? "" : mActivity.getString(label);
        if (!text.contentEquals(action.getText())) {
            action.setText(text);
            action.setGravity((compact ? Gravity.CENTER : Gravity.START | Gravity.CENTER_VERTICAL));
        }
        if (action.getCompoundDrawablesRelative()[0] != (compact ? icon : null)) {
            action.setCompoundDrawablesRelative(compact ? icon : null, null, null, null);
        }
    }

    private void showFavorites() {
        if (mDestroyed) return;
        List<ArcSidebarState.Entry> entries = mController.state().favorites();
        PopupMenu menu = new PopupMenu(mActivity, mFavoritesMenu);
        mMenu = menu;
        for (int i = 0; i < entries.size(); i++) menu.getMenu().add(0, i, i, entries.get(i).title);
        menu.setOnMenuItemClickListener(item -> {
            runCommand(() -> open(entries.get(item.getItemId()).id));
            return true;
        });
        menu.show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private Button button(String text, Runnable action) {
        Button result = new Button(mActivity);
        result.setText(text);
        result.setContentDescription(text);
        result.setTooltipText(text);
        result.setAllCaps(false);
        result.setTextSize(14);
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

    /** Compact native rail keeps favorites accessible without expanded collection chrome. */
    public void setCompact(boolean compact) {
        mCompactRequested = compact;
        updateCompactViews();
    }

    private void updateCompactViews() {
        int minimumExpanded = dp(142) + getPaddingTop() + getPaddingBottom()
                + (mFavorites.getChildCount() == 0 ? 0 : dp(44));
        boolean compact = mCompactRequested
                || (mCollectionHeight >= 0 && mCollectionHeight < minimumExpanded);
        mSpace.setVisibility(compact ? GONE : VISIBLE);
        mScroll.setVisibility(compact ? GONE : VISIBLE);
        mControls.setVisibility(compact ? GONE : VISIBLE);
        mNewFolder.setVisibility(compact ? GONE : VISIBLE);
    }

    public void setCollectionHeight(int height) {
        mCollectionHeight = height;
        // Visibility changes request a measure even if both scroll budgets remain zero.
        updateCompactViews();
        updateCollectionBudgets(mFavorites.getColumnCount());
    }

    private void updateCollectionBudgets(int columns) {
        if (mCollectionHeight < 0) return;
        // Reserve space selector (44dp + 8dp/2dp margins), the fixed New Folder
        // action and the pin/favorite action row before assigning scrollable content.
        int rows = Math.max(0, mCollectionHeight - dp(142) - getPaddingTop() - getPaddingBottom());
        int slot = dp(56);
        int count = mFavorites.getChildCount();
        int wantedRows = columns < 2 ? 0 : (count + columns - 1) / columns;
        int visibleRows = Math.min(wantedRows, rows / slot);
        int favorites = visibleRows * slot;
        mFavoritesScroll.setBudget(favorites);
        // A menu fallback still consumes a 44dp row inside the same shared budget.
        int occupied = count > 0 && favorites == 0 ? dp(44) : favorites;
        mScroll.setBudget(Math.max(0, rows - occupied) / dp(44) * dp(44));
    }

    /** Owns collection styling so site favicons retain their original colors and rounded tiles. */
    public void setAppearance(int surface, int foreground, int interaction) {
        mSurface = surface;
        if (mForeground != foreground) { mForeground = foreground; updateGlyphs(); }
        mFavoritesMenu.setCompoundDrawablesRelative(mFavoriteGlyph, null, null, null);
        mSpace.setCompoundDrawablesRelative(null, null, mSpaceChevron, null);
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
                int tileSurface = ArcDesktopPolicy.activeTabSurface(mSurface);
                GradientDrawable shape = background(tileSurface, 13);
                tile.setBackground(new RippleDrawable(ColorStateList.valueOf(mInteraction), shape, null));
                tile.setOnHoverListener((view, event) -> {
                    if (event.getAction() == android.view.MotionEvent.ACTION_HOVER_ENTER) shape.setColor(mInteraction);
                    else if (event.getAction() == android.view.MotionEvent.ACTION_HOVER_EXIT) shape.setColor(tileSurface);
                    return false;
                });
            } else if (child instanceof Button) {
                Button button = (Button) child;
                button.setTextColor(mForeground);
                StateListDrawable states = new StateListDrawable();
                GradientDrawable focus = background(mInteraction, 10);
                focus.setStroke(dp(2), mForeground);
                states.addState(new int[] {android.R.attr.state_enabled,android.R.attr.state_focused}, focus);
                states.addState(new int[] {android.R.attr.state_enabled,android.R.attr.state_hovered}, background(mInteraction, 10));
                states.addState(new int[] {}, background(Color.TRANSPARENT, 10));
                button.setBackground(new RippleDrawable(ColorStateList.valueOf(mInteraction), states, null));
            } else if (child instanceof android.view.ViewGroup) {
                applyAppearance((android.view.ViewGroup) child);
            }
        }
    }

    /** Neutral domain initial; the optical box is identical before and after native icon loading. */
    private android.graphics.drawable.Drawable fallbackIcon(String url, int color) {
        String domain;
        try { domain = android.net.Uri.parse(url).getHost(); }
        catch (RuntimeException invalid) { domain = null; }
        if (domain != null && domain.startsWith("www.")) domain = domain.substring(4);
        final String initial = domain == null || domain.isEmpty() ? "•"
                : domain.substring(0, 1).toUpperCase(java.util.Locale.ROOT);
        return new android.graphics.drawable.Drawable() {
            final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            @Override public void draw(android.graphics.Canvas canvas) {
                var bounds = getBounds(); paint.setColor(color); paint.setTextAlign(android.graphics.Paint.Align.CENTER);
                paint.setTextSize(Math.min(bounds.width(), bounds.height()) * .72f);
                canvas.drawText(initial, bounds.exactCenterX(), bounds.exactCenterY()
                        - (paint.ascent() + paint.descent()) / 2, paint);
            }
            @Override public int getIntrinsicWidth() { return dp(24); }
            @Override public int getIntrinsicHeight() { return dp(24); }
            @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
            @Override public void setColorFilter(android.graphics.ColorFilter filter) { paint.setColorFilter(filter); }
            @Override public int getOpacity() { return android.graphics.PixelFormat.TRANSLUCENT; }
        };
    }

    private void remember(boolean favorite) {
        if (favorite && mSaveNativeFavorite != null) { mSaveNativeFavorite.run(); return; }
        CurrentTab tab = mCurrentTab.get();
        if (tab == null) throw new IllegalStateException("No active tab");
        String title = tab.title == null || tab.title.isEmpty() ? tab.url : tab.title;
        if (title.length() > 256) title = title.substring(0, 256);
        mController.rememberTab(tab.id, tab.url, title, favorite, favorite ? null : mOpenFolder);
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
            mFavoritesMenu.setVisibility(GONE);
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
        CurrentTab favoriteCurrent = mCurrentTab.get();
        boolean saved = favoriteCurrent != null && state.favorites().stream().anyMatch(e -> e.url.equals(favoriteCurrent.url));
        findViewWithTag("arc-favorite-current").setSelected(saved);
        String favoriteFocus = focusedTag(mFavorites);
        String entryFocus = focusedTag(mEntries);
        mFavorites.removeAllViews();
        mFavoritesScroll.setVisibility(state.favorites().isEmpty() ? GONE : VISIBLE);
        for (ArcSidebarState.Entry entry : state.favorites()) {
            ImageButton favorite = new ImageButton(mActivity);
            favorite.setImageDrawable(fallbackIcon(entry.url, mForeground));
            favorite.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);
            favorite.setPadding(dp(12), dp(12), dp(12), dp(12));
            favorite.setContentDescription(entry.title);
            favorite.setTooltipText(entry.title);
            favorite.setTag("arc-entry:" + entry.id);
            favorite.setOnClickListener(view -> runCommand(() -> open(entry.id)));
            favorite.setOnLongClickListener(view -> { showEntryMenu(view, entry); return true; });
            favorite.setOnContextClickListener(view -> { showEntryMenu(view, entry); return true; });
            GridLayout.LayoutParams tileParams = new GridLayout.LayoutParams();
            tileParams.width = dp(50); tileParams.height = dp(50);
            int index = mFavorites.getChildCount(), columns = mFavorites.getColumnCount();
            tileParams.rowSpec = GridLayout.spec(index / columns);
            tileParams.columnSpec = GridLayout.spec(index % columns);
            tileParams.setMargins(dp(3), dp(3), dp(3), dp(3));
            mFavorites.addView(favorite, tileParams);
            mLoadIcon.accept(entry, favorite);
        }
        for (ArcSidebarState.Space space : state.spaces()) {
            if (space.id.equals(state.selectedSpace())) {
                mSpace.setText(space.name);
                mSpace.setSelected(true);
                String description = mActivity.getString(R.string.arc_current_space, space.name);
                mSpace.setContentDescription(description);
                mSpace.setTooltipText(description);
            }
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
            row.setOnContextClickListener(view -> { showEntryMenu(view, entry); return true; });
            row.setTooltipText(mActivity.getString(R.string.arc_pinned_entry_actions));
            mEntries.addView(row, new LayoutParams(-1, dp(44)));
        }
        mNewFolder.setTag("arc-new-folder:" + state.selectedSpace());
        applyAppearance(this);
        restoreFocus(mFavorites, favoriteFocus);
        restoreFocus(mEntries, entryFocus);
    }

    private static String focusedTag(android.view.ViewGroup group) {
        View focused = group.findFocus();
        return focused != null && focused.getTag() instanceof String
                ? (String) focused.getTag() : null;
    }

    private static void restoreFocus(android.view.ViewGroup group, String tag) {
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
        for (int i = 0; i < spaces.size(); i++) {
            menu.getMenu().add(0, i, i, spaces.get(i).name)
                    .setCheckable(true)
                    .setChecked(spaces.get(i).id.equals(state.selectedSpace()));
        }
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
        ArcSidebarState state;
        ArcSidebarState.Entry selected;
        boolean canClose;
        try {
            state = mController.state();
            selected = state.entry(entry.id);
            canClose = mController.canClose(selected.id);
        } catch (RuntimeException unavailable) {
            Toast.makeText(mActivity, R.string.arc_collection_error, Toast.LENGTH_SHORT).show();
            return;
        }
        PopupMenu menu = new PopupMenu(mActivity, anchor);
        mMenu = menu;
        String removeLabel = mActivity.getString(R.string.arc_remove_entry);
        if (!selected.favorite) {
            for (ArcSidebarState.Space space : state.spaces()) {
                if (space.id.equals(selected.spaceId)) {
                    removeLabel = mActivity.getString(R.string.arc_remove_from_space, space.name);
                    break;
                }
            }
        }
        menu.getMenu().add(0, 0, 0, removeLabel);
        if (!selected.favorite) menu.getMenu().add(0, 1, 1, R.string.arc_move_to_folder);
        if (canClose) menu.getMenu().add(0, 2, 2, R.string.arc_close_tab);
        menu.setOnMenuItemClickListener(item -> {
            runCommand(() -> {
                if (item.getItemId() == 0) mController.remove(selected.id);
                else if (item.getItemId() == 2) mController.close(selected.id);
                else showFolderChoices(anchor, selected);
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
