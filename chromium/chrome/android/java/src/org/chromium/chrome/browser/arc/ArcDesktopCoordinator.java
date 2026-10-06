// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.TextView;

import org.chromium.chrome.R;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
import org.chromium.components.favicon.LargeIconBridge;

import java.util.Locale;
import java.util.function.Consumer;
import java.util.function.Supplier;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tabmodel.TabCreator;
import org.chromium.chrome.browser.tabmodel.TabModel;
import org.chromium.chrome.browser.tabmodel.IncognitoStateProvider;
import org.chromium.chrome.browser.tabmodel.IncognitoStateProvider.IncognitoStateObserver;

import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListViewBinder;
import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayout;
import org.chromium.chrome.browser.toolbar.top.ToolbarTablet;

/** Composes profile-owned Arc collections around Chromium's real vertical tab rail. */
public final class ArcDesktopCoordinator {
    private final Activity mActivity;
    private final ViewGroup mRail;
    private final View mNativeTabs;
    private final LinearLayout mColumn;
    private final LinearLayout mHeader;
    private final LinearLayout mFooter;
    private final Button mAddressButton;
    private final LargeIconBridge mIcons;
    private final Consumer<String> mNavigate;
    private final IncognitoStateProvider mIncognitoStateProvider;
    private final IncognitoStateObserver mIncognitoObserver;
    private final SharedPreferences mPreferences;
    private final SharedPreferences.OnSharedPreferenceChangeListener mPreferenceListener;
    private final View.OnLayoutChangeListener mLayoutListener;
    private final Supplier<TabModel> mCurrentModel;
    private final Supplier<TabCreator> mCurrentCreator;
    private final Supplier<Tab> mCurrentTab;
    private TabModel mSessionModel;
    private ArcNativeTabSession mTabSession;
    private ArcCollectionsController mCollections;
    private ArcCollectionsView mCollectionsView;
    private boolean mDestroyed;
    private AlertDialog mColorDialog;

    public ArcDesktopCoordinator(Activity activity, ViewGroup rail,
            Profile profile, Consumer<String> navigate, Runnable focusOmnibox,
            Runnable openBookmarks, Runnable openPasswordSettings,
            boolean localPasswordsEnabled, IncognitoStateProvider incognitoStateProvider,
            Supplier<TabModel> currentModel, Supplier<TabCreator> currentCreator,
            Supplier<Tab> currentTab) {
        mActivity = activity;
        mRail = rail;
        mNavigate = navigate;
        mIncognitoStateProvider = incognitoStateProvider;
        mCurrentModel = currentModel;
        mCurrentCreator = currentCreator;
        mCurrentTab = currentTab;
        mIncognitoObserver = incognito -> { if (!mDestroyed) { rebindCollections(); applyAppearance(); } };
        mIcons = new LargeIconBridge(profile);
        mPreferences = ArcDesktopAppearance.preferences(activity);
        mNativeTabs = rail.getChildAt(0);
        rail.removeView(mNativeTabs);
        mColumn = column();
        View captionSpacer = new View(activity);
        View nativeSpacer = mNativeTabs.findViewById(R.id.desktop_window_spacer);
        mColumn.addView(captionSpacer, new LinearLayout.LayoutParams(
                -1, nativeSpacer.getLayoutParams().height));
        ((VerticalTabRailLayout) mNativeTabs).setDesktopWindowSpacerHost(captionSpacer);
        mHeader = column();

        LinearLayout navigation = new LinearLayout(activity);
        Button backButton = button("‹", () -> {
            Tab tab = mCurrentTab.get();
            if (tab != null && tab.canGoBack()) tab.goBack();
        });
        backButton.setContentDescription("Back");
        Button forwardButton = button("›", () -> {
            Tab tab = mCurrentTab.get();
            if (tab != null && tab.canGoForward()) tab.goForward();
        });
        forwardButton.setContentDescription("Forward");
        Button reloadButton = button("↻", () -> {
            Tab tab = mCurrentTab.get();
            if (tab != null) tab.reload();
        });
        reloadButton.setContentDescription("Reload");
        for (Button action : new Button[] {backButton, forwardButton, reloadButton}) {
            navigation.addView(action, new LinearLayout.LayoutParams(dp(44), dp(42)));
        }
        mAddressButton = button("Search or enter address", focusOmnibox);
        mAddressButton.setSingleLine(true);
        mAddressButton.setEllipsize(TextUtils.TruncateAt.MIDDLE);
        mAddressButton.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        mAddressButton.setContentDescription("Address and search");
        navigation.addView(mAddressButton, new LinearLayout.LayoutParams(0, dp(42), 1));
        mHeader.addView(navigation);

        LinearLayout actions = new LinearLayout(activity);
        Button bookmarksButton = button(activity.getString(R.string.arc_bookmarks), openBookmarks);
        Button googleButton = button("Google", () -> {});
        googleButton.setOnClickListener(v -> showGoogleMenu(v));
        Button appearanceButton = button("●", this::showColorPicker);
        appearanceButton.setContentDescription(activity.getString(R.string.arc_frame_color));
        for (Button action : new Button[] {bookmarksButton, googleButton, appearanceButton}) {
            actions.addView(action, new LinearLayout.LayoutParams(0, dp(42), 1));
        }
        mHeader.addView(actions);
        mColumn.addView(mHeader);
        mColumn.addView(mNativeTabs, new LinearLayout.LayoutParams(-1, 0, 1));

        mFooter = new LinearLayout(activity);
        Button passwordButton = button(localPasswordsEnabled ? "Passwords" : "Autofill",
                openPasswordSettings);
        passwordButton.setContentDescription(
                localPasswordsEnabled ? "Local passwords" : "Autofill settings");
        Button newTabButton = button("+ New tab", () -> {
            TabCreator creator = mCurrentCreator.get();
            if (creator != null) {
                creator.createNewTab(new org.chromium.content_public.browser.LoadUrlParams("chrome://newtab/"),
                        org.chromium.chrome.browser.tab.TabLaunchType.FROM_CHROME_UI,
                        mCurrentTab.get());
            }
        });
        for (Button action : new Button[] {passwordButton, newTabButton}) {
            mFooter.addView(action, new LinearLayout.LayoutParams(0, dp(42), 1));
        }
        mColumn.addView(mFooter);
        rail.addView(mColumn, new ViewGroup.LayoutParams(-1, -1));
        mPreferenceListener = (prefs, key) -> {
            if (!mDestroyed && ArcDesktopAppearance.COLOR_KEY.equals(key)) {
                // Rebind tab titles/buttons through the native RecyclerView after a palette change.
                refreshNativeRows(mNativeTabs);
                applyAppearance();
                View toolbar = mActivity.findViewById(R.id.toolbar);
                if (toolbar instanceof ToolbarTablet) {
                    ((ToolbarTablet) toolbar).onThemeColorChanged(
                            ArcDesktopAppearance.surface(mActivity, mIncognitoStateProvider.isIncognitoSelected()), false);
                }
            }
        };
        mPreferences.registerOnSharedPreferenceChangeListener(mPreferenceListener);
        mLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> { rebindCollections(); applyAppearance(); };
        rail.addOnLayoutChangeListener(mLayoutListener);
        mIncognitoStateProvider.addIncognitoStateObserverAndTrigger(mIncognitoObserver);
        applyAppearance();
    }

    private LinearLayout column() {
        LinearLayout result = new LinearLayout(mActivity);
        result.setOrientation(LinearLayout.VERTICAL);
        return result;
    }

    private int dp(int value) {
        return Math.round(value * mActivity.getResources().getDisplayMetrics().density);
    }

    private Button button(String text, Runnable action) {
        Button button = new Button(mActivity);
        button.setText(text);
        button.setAllCaps(false);
        button.setTextSize(12);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        button.setPadding(dp(4), 0, dp(4), 0);
        button.setOnClickListener(v -> action.run());
        return button;
    }

    private void clearCollections() {
        if (mCollectionsView != null) {
            mCollectionsView.destroy();
            mHeader.removeView(mCollectionsView);
        }
        if (mCollections != null) mCollections.destroy();
        if (mTabSession != null) mTabSession.destroy();
        mCollectionsView = null;
        mCollections = null;
        mTabSession = null;
        mSessionModel = null;
    }

    private void rebindCollections() {
        if (mDestroyed) return;
        TabModel model = mCurrentModel.get();
        if (model == mSessionModel && mTabSession != null) return;
        clearCollections();
        if (model == null || model.getProfile() == null || model.getProfile().shutdownStarted()) return;
        TabCreator creator = mCurrentCreator.get();
        if (creator == null) return;
        ArcNativeTabSession session = new ArcNativeTabSession(model, creator,
                () -> mCurrentModel.get() == model, () -> {
                    if (!mDestroyed && mCollectionsView != null && mSessionModel == model) {
                        mCollectionsView.refresh();
                        applyAppearance();
                    }
                });
        mTabSession = session;
        mSessionModel = model;
        mCollections = new ArcCollectionsController(session.store(), session.actions(), session);
        mCollectionsView = new ArcCollectionsView(mActivity, mCollections, () -> {
            Tab tab = mCurrentTab.get();
            if (tab == null || mCurrentModel.get() != model || !session.exists(tab.getId())) return null;
            return new ArcCollectionsView.CurrentTab(tab.getId(), tab.getUrl().getSpec(), tab.getTitle());
        }, (entry, button) -> {
            // Avoid issuing regular-profile favicon fetches for private collections.
            if (model.getProfile().isOffTheRecord()) return;
            mIcons.getLargeIconForUrl(new org.chromium.url.GURL(entry.url), dp(24),
                    (icon, color, fallback, type) -> {
                        if (!mDestroyed && mTabSession == session && icon != null) button.setImageBitmap(icon);
                    });
        });
        mHeader.addView(mCollectionsView, 0);
    }

    private void showGoogleMenu(View anchor) {
        PopupMenu menu = new PopupMenu(mActivity, anchor);
        String[] labels = {mActivity.getString(R.string.arc_google_login), "Gmail", "Drive",
                "Calendar", "Docs", "YouTube"};
        String[] urls = {"https://accounts.google.com/", "https://mail.google.com/",
                "https://drive.google.com/", "https://calendar.google.com/",
                "https://docs.google.com/", "https://www.youtube.com/"};
        for (int i = 0; i < labels.length; i++) menu.getMenu().add(0, i, i, labels[i]);
        menu.setOnMenuItemClickListener(item -> {
            mNavigate.accept(urls[item.getItemId()]);
            return true;
        });
        menu.show();
    }

    private void showColorPicker() {
        if (mDestroyed) return;
        EditText input = new EditText(mActivity);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        input.setSingleLine(true);
        input.setText(String.format(Locale.ROOT, "#%06X",
                mPreferences.getInt(ArcDesktopAppearance.COLOR_KEY,
                        ArcDesktopAppearance.DEFAULT_COLOR) & 0xffffff));
        input.setSelectAllOnFocus(true);
        mColorDialog = new AlertDialog.Builder(mActivity)
                .setTitle(R.string.arc_frame_color).setView(input)
                .setPositiveButton(android.R.string.ok, null)
                .setNegativeButton(android.R.string.cancel, null)
                .setNeutralButton(R.string.arc_reset_color, (dialog, which) ->
                        mPreferences.edit().remove(ArcDesktopAppearance.COLOR_KEY).apply()).create();
        mColorDialog.setOnShowListener(dialog -> mColorDialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String value = input.getText().toString().trim();
                    if (!value.matches("#[0-9a-fA-F]{6}")) {
                        input.setError(mActivity.getString(R.string.arc_color_format));
                        return;
                    }
                    mPreferences.edit().putInt(ArcDesktopAppearance.COLOR_KEY,
                            Color.parseColor(value)).apply();
                    mColorDialog.dismiss();
                }));
        mColorDialog.show();
    }

    private void applyAppearance() {
        if (mDestroyed) return;
        boolean desktop = ArcDesktopAppearance.isDesktopWindow(mActivity);
        boolean showChrome = desktop && mRail.getWidth() >= dp(100)
                && mRail.getHeight() >= dp(360);
        mHeader.setVisibility(showChrome ? View.VISIBLE : View.GONE);
        mFooter.setVisibility(showChrome ? View.VISIBLE : View.GONE);
        if (!desktop) return;
        Tab current = mCurrentTab.get();
        String currentUrl = current == null || current.getUrl() == null
                ? "" : current.getUrl().getSpec();
        mAddressButton.setText(currentUrl.isEmpty() ? "Search or enter address" : currentUrl);
        if (mCollectionsView != null) {
            mCollectionsView.setCollectionHeight(Math.max(dp(80), Math.min(dp(240), mRail.getHeight() / 4)));
        }
        // Leave native tab selection, incognito and favicon rendering to its binders.
        boolean incognito = mIncognitoStateProvider.isIncognitoSelected();
        if (mNativeTabs instanceof VerticalTabRailLayout) {
            VerticalTabListViewBinder.refreshArcAppearance((VerticalTabRailLayout) mNativeTabs, incognito);
        }
        int surface = ArcDesktopAppearance.surface(mActivity, incognito);
        int foreground = ArcDesktopPolicy.foreground(surface);
        mColumn.setBackgroundColor(surface);
        tintHeader(mHeader, foreground, ArcDesktopPolicy.selection(surface));
        tintHeader(mFooter, foreground, ArcDesktopPolicy.selection(surface));
    }

    private void tintHeader(View view, int foreground, int selection) {
        if (view instanceof TextView) ((TextView) view).setTextColor(foreground);
        if (view instanceof Button || view instanceof ImageButton) {
            GradientDrawable background = new GradientDrawable();
            background.setColor(selection);
            background.setCornerRadius(dp(8));
            view.setBackground(background);
        }
        // Website favicons are intentionally never tinted.
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                tintHeader(group.getChildAt(i), foreground, selection);
            }
        }
    }

    private void refreshNativeRows(View view) {
        if (view instanceof androidx.recyclerview.widget.RecyclerView) {
            androidx.recyclerview.widget.RecyclerView.Adapter<?> adapter =
                    ((androidx.recyclerview.widget.RecyclerView) view).getAdapter();
            if (adapter != null) adapter.notifyDataSetChanged();
        } else if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) refreshNativeRows(group.getChildAt(i));
        }
    }

    public void destroy() {
        if (mDestroyed) return;
        mDestroyed = true;
        mIncognitoStateProvider.removeObserver(mIncognitoObserver);
        ((VerticalTabRailLayout) mNativeTabs).setDesktopWindowSpacerHost(null);
        clearCollections();
        mPreferences.unregisterOnSharedPreferenceChangeListener(mPreferenceListener);
        mRail.removeOnLayoutChangeListener(mLayoutListener);
        if (mColorDialog != null) mColorDialog.dismiss();
        mIcons.destroy();
        mColumn.removeView(mNativeTabs);
        mRail.removeView(mColumn);
        mRail.addView(mNativeTabs, new ViewGroup.LayoutParams(-1, -1));
    }
}
