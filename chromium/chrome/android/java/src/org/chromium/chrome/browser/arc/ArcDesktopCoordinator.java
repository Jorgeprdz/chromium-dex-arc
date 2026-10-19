// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.ColorDrawable;
import android.text.TextUtils;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.content.res.ColorStateList;
import android.view.MotionEvent;
import android.view.View;
import android.view.Gravity;
import android.view.ViewOutlineProvider;
import android.view.ViewGroup;
import android.view.KeyEvent;
import android.widget.EditText;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.TextView;

import org.chromium.chrome.R;
import org.chromium.chrome.browser.compositor.CompositorViewHolder;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
import org.chromium.components.browser_ui.widget.TouchEventObserver;
import org.chromium.components.favicon.LargeIconBridge;

import java.util.function.Consumer;
import java.util.function.Supplier;
import java.util.Objects;
import java.util.ArrayList;
import java.util.List;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tabmodel.TabCreator;
import org.chromium.chrome.browser.tabmodel.TabModel;
import org.chromium.chrome.browser.tab.TabSelectionType;
import org.chromium.chrome.browser.tabmodel.IncognitoStateProvider;
import org.chromium.chrome.browser.tabmodel.IncognitoStateProvider.IncognitoStateObserver;

import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinator;
import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListViewBinder;
import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayout;
import org.chromium.chrome.browser.toolbar.top.ToolbarTablet;
import org.chromium.chrome.browser.omnibox.LocationBarLayout;

/** Composes profile-owned Arc collections around Chromium's real vertical tab rail. */
public final class ArcDesktopCoordinator {
    private final Activity mActivity;
    private final ViewGroup mRail;
    private final View mNativeTabs;
    private final View mNativeNewTabButton;
    private final int mNativeNewTabVisibility;
    private final TextView mNewTabRow;
    private final Drawable mNewTabIcon;
    private final View mCaptionSpacer;
    private final ArcNavigationControls mNavigationState;
    private final LinearLayout mColumn;
    private final LinearLayout mHeader;
    private final LinearLayout mNavigationRow;
    private final LinearLayout mNavigationControls;
    private final View mMenuButtonWrapper;
    private final ViewGroup mMenuButtonOriginalParent;
    private final int mMenuButtonOriginalIndex;
    private final ViewGroup.LayoutParams mMenuButtonOriginalLayoutParams;
    private View mExtensionsToolbarHost;
    private ViewGroup mExtensionsToolbarOriginalParent;
    private int mExtensionsToolbarOriginalIndex;
    private ViewGroup.LayoutParams mExtensionsToolbarOriginalLayoutParams;
    private int mExtensionsToolbarOriginalVisibility;
    private final View mCollapseButton;
    private final ViewGroup mCollapseButtonOriginalParent;
    private final int mCollapseButtonOriginalIndex;
    private final ViewGroup.LayoutParams mCollapseButtonOriginalLayoutParams;
    private final LinearLayout mHeaderActions;
    private final LinearLayout mFooter;
    private final ImageButton mAppearanceButton;
    private final ArcCompactOmnibox mCompactOmnibox;
    private final ArcOmniboxPlacement mOmniboxPlacement;
    private ArcCommandBar mCommandBar;
    private Runnable mFocusAddressBar;
    private Runnable mOpenSettings;
    private Runnable mEndAddressInput = () -> {};
    private final View mLocationBarHost;
    private final ViewGroup mLocationBarOriginalParent;
    private final int mLocationBarOriginalIndex;
    private final ViewGroup.LayoutParams mLocationBarOriginalLayoutParams;
    private final CompositorViewHolder mCompositorViewHolder;
    private final View mFrameRoot;
    private final Drawable mOriginalFrameBackground;
    private final Drawable mOriginalRailBackground;
    private final ColorStateList mOriginalRailBackgroundTint;
    private final ViewOutlineProvider mOriginalContentOutlineProvider;
    private final boolean mOriginalContentClipToOutline;
    private final Rect mOriginalContentClipBounds;
    private final int mOriginalContentMarginLeft;
    private final int mOriginalContentMarginTop;
    private final int mOriginalContentMarginRight;
    private final int mOriginalContentMarginBottom;
    private final int mOriginalRailPaddingLeft;
    private final int mOriginalRailPaddingTop;
    private final int mOriginalRailPaddingRight;
    private final int mOriginalRailPaddingBottom;
    private final Supplier<Integer> mReservedLeftWidth;
    private final Consumer<Boolean> mSetToolbarSuppressed;
    private final LargeIconBridge mIcons;
    private final Consumer<String> mNavigate;
    private final IncognitoStateProvider mIncognitoStateProvider;
    private final IncognitoStateObserver mIncognitoObserver;
    private final SharedPreferences mPreferences;
    private final SharedPreferences.OnSharedPreferenceChangeListener mPreferenceListener;
    private final View.OnLayoutChangeListener mLayoutListener;
    private final View.OnLayoutChangeListener mContentLayoutListener;
    private final ViewOutlineProvider mArcContentOutlineProvider;
    private final TouchEventObserver mArcTouchEventObserver;
    private final View.OnAttachStateChangeListener mSurfaceAttachStateListener;
    private final Supplier<TabModel> mCurrentModel;
    private final Supplier<TabCreator> mCurrentCreator;
    private final Supplier<Tab> mCurrentTab;
    private final VerticalTabListCoordinator mNativeTabListCoordinator;
    private TabModel mSessionModel;
    private ArcNativeTabSession mTabSession;
    private ArcCollectionsController mCollections;
    private ArcCollectionsView mCollectionsView;
    private boolean mDestroyed;
    private boolean mArcToolbarCompositionActive;
    private boolean mArcFrameActive;
    private boolean mRejectingRoundedCornerGesture;
    private View mClippedSurface;
    private ViewOutlineProvider mClippedSurfaceOriginalOutlineProvider;
    private boolean mClippedSurfaceOriginalClipToOutline;
    private Rect mClippedSurfaceOriginalClipBounds;
    private AlertDialog mColorDialog;
    private AlertDialog mAboutDialog;
    private boolean mPaletteInitialized;
    private int mPaletteSurface;
    private boolean mPaletteDesktop;
    private boolean mPaletteIncognito;
    private final ArcFrameDispatch mFrameDispatch;
    private final ArcFrameDispatch mAppearanceDispatch;
    private final android.view.ViewTreeObserver.OnGlobalLayoutListener mFontLayoutListener;
    private boolean mRailViewportTransition;
    private int mTransitionOtherInset;

    public ArcDesktopCoordinator(Activity activity, ViewGroup rail,
            Profile profile, Consumer<String> navigate,
            Runnable openBookmarks, Runnable openPasswordSettings,
            boolean localPasswordsEnabled, IncognitoStateProvider incognitoStateProvider,
            VerticalTabListCoordinator nativeTabListCoordinator,
            CompositorViewHolder compositorViewHolder, Supplier<Integer> reservedLeftWidth,
            Consumer<Boolean> setToolbarSuppressed, Supplier<TabModel> currentModel,
            Supplier<TabCreator> currentCreator, Supplier<Tab> currentTab) {
        mActivity = activity;
        mFrameDispatch = new ArcFrameDispatch(
                () -> !mDestroyed && ArcDesktopAppearance.isDesktopWindow(mActivity));
        mAppearanceDispatch = new ArcFrameDispatch(() -> !mDestroyed);
        mRail = rail;
        mNavigate = navigate;
        mIncognitoStateProvider = incognitoStateProvider;
        mNativeTabListCoordinator = nativeTabListCoordinator;
        mCompositorViewHolder = compositorViewHolder;
        mReservedLeftWidth = reservedLeftWidth;
        mSetToolbarSuppressed = setToolbarSuppressed;
        mCurrentModel = currentModel;
        mCurrentCreator = currentCreator;
        mCurrentTab = currentTab;
        mIncognitoObserver = incognito -> {
            if (!mDestroyed) {
                if (mCommandBar != null) mCommandBar.close(false, null);
                rebindCollections(); applyAppearance();
            }
        };
        mIcons = new LargeIconBridge(profile);
        mPreferences = ArcDesktopAppearance.preferences(activity);
        mOriginalRailBackground = rail.getBackground();
        mOriginalRailBackgroundTint = rail.getBackgroundTintList();
        mOriginalRailPaddingLeft = rail.getPaddingLeft();
        mOriginalRailPaddingTop = rail.getPaddingTop();
        mOriginalRailPaddingRight = rail.getPaddingRight();
        mOriginalRailPaddingBottom = rail.getPaddingBottom();

        // Validate all native views before mutating either the rail or Chromium toolbar hierarchy.
        // Arc must fail before reparenting anything rather than leave a partially dismantled shell.
        View toolbarRoot = activity.findViewById(R.id.toolbar);
        if (toolbarRoot == null) {
            throw new IllegalStateException("Arc requires Chromium's toolbar root");
        }
        View nativeTabs = rail.getChildCount() == 0 ? null : rail.getChildAt(0);
        if (!(nativeTabs instanceof VerticalTabRailLayout)) {
            throw new IllegalStateException("Arc requires Chromium's VerticalTabRailLayout");
        }
        View nativeSpacer = nativeTabs.findViewById(R.id.desktop_window_spacer);
        if (nativeSpacer == null || nativeSpacer.getLayoutParams() == null) {
            throw new IllegalStateException("Arc requires Chromium's desktop window spacer");
        }
        View collapseButton = nativeTabs.findViewById(R.id.collapse_button);
        if (collapseButton == null || !(collapseButton.getParent() instanceof ViewGroup)) {
            throw new IllegalStateException("Arc requires Chromium's real collapse button");
        }
        View menuButtonWrapper = activity.findViewById(R.id.menu_button_wrapper);
        if (menuButtonWrapper == null || !(menuButtonWrapper.getParent() instanceof ViewGroup)) {
            throw new IllegalStateException("Arc requires Chromium's real app-menu button");
        }
        // ExtensionsToolbarCoordinator inflates this container during native initialization when
        // extension UI is enabled. Preserve that already-initialized native surface if present.
        View extensionsToolbarHost = activity.findViewById(R.id.extensions_toolbar_container);
        if (extensionsToolbarHost != null
                && !(extensionsToolbarHost.getParent() instanceof ViewGroup)) {
            throw new IllegalStateException("Arc requires an attached extensions toolbar");
        }
        View locationBarView = activity.findViewById(R.id.location_bar);
        if (locationBarView == null || !(locationBarView.getParent() instanceof ViewGroup)) {
            throw new IllegalStateException("Arc requires Chromium's real LocationBar view");
        }
        View locationBarHolder = activity.findViewById(R.id.location_bar_holder);
        View locationBarHost = locationBarHolder instanceof ViewGroup
                        && locationBarView.getParent() == locationBarHolder
                        && locationBarHolder.getParent() instanceof ViewGroup
                ? locationBarHolder
                : locationBarView;
        if (!(locationBarHost.getParent() instanceof ViewGroup)) {
            throw new IllegalStateException("Arc requires an attached Chromium LocationBar host");
        }

        mFrameRoot = activity.findViewById(R.id.coordinator);
        mOriginalFrameBackground = mFrameRoot == null ? null : mFrameRoot.getBackground();
        mOriginalContentOutlineProvider = compositorViewHolder.getOutlineProvider();
        mOriginalContentClipToOutline = compositorViewHolder.getClipToOutline();
        mOriginalContentClipBounds = compositorViewHolder.getClipBounds();
        ViewGroup.LayoutParams rawContentLayoutParams = compositorViewHolder.getLayoutParams();
        if (rawContentLayoutParams instanceof ViewGroup.MarginLayoutParams) {
            ViewGroup.MarginLayoutParams margins = (ViewGroup.MarginLayoutParams) rawContentLayoutParams;
            mOriginalContentMarginLeft = margins.leftMargin;
            mOriginalContentMarginTop = margins.topMargin;
            mOriginalContentMarginRight = margins.rightMargin;
            mOriginalContentMarginBottom = margins.bottomMargin;
        } else {
            mOriginalContentMarginLeft = 0;
            mOriginalContentMarginTop = 0;
            mOriginalContentMarginRight = 0;
            mOriginalContentMarginBottom = 0;
        }
        mNativeTabs = nativeTabs;
        mNativeNewTabButton = nativeTabs.findViewById(R.id.new_tab_button);
        if (mNativeNewTabButton == null) {
            throw new IllegalStateException("Arc requires the native new-tab action");
        }
        mNativeNewTabVisibility = mNativeNewTabButton.getVisibility();
        mMenuButtonWrapper = menuButtonWrapper;
        mMenuButtonOriginalParent = (ViewGroup) mMenuButtonWrapper.getParent();
        mMenuButtonOriginalIndex = mMenuButtonOriginalParent.indexOfChild(mMenuButtonWrapper);
        mMenuButtonOriginalLayoutParams = mMenuButtonWrapper.getLayoutParams();
        mExtensionsToolbarHost = extensionsToolbarHost;
        if (mExtensionsToolbarHost != null) {
            mExtensionsToolbarOriginalParent = (ViewGroup) mExtensionsToolbarHost.getParent();
            mExtensionsToolbarOriginalIndex =
                    mExtensionsToolbarOriginalParent.indexOfChild(mExtensionsToolbarHost);
            mExtensionsToolbarOriginalLayoutParams = mExtensionsToolbarHost.getLayoutParams();
            mExtensionsToolbarOriginalVisibility = mExtensionsToolbarHost.getVisibility();
        } else {
            mExtensionsToolbarOriginalParent = null;
            mExtensionsToolbarOriginalIndex = -1;
            mExtensionsToolbarOriginalLayoutParams = null;
            mExtensionsToolbarOriginalVisibility = View.GONE;
        }
        mCollapseButton = collapseButton;
        mCollapseButtonOriginalParent = (ViewGroup) mCollapseButton.getParent();
        mCollapseButtonOriginalIndex = mCollapseButtonOriginalParent.indexOfChild(mCollapseButton);
        mCollapseButtonOriginalLayoutParams = mCollapseButton.getLayoutParams();
        mLocationBarHost = locationBarHost;
        mOmniboxPlacement = new ArcOmniboxPlacement(locationBarHost);
        mCompactOmnibox = new ArcCompactOmnibox(locationBarHost);
        mLocationBarOriginalParent = (ViewGroup) mLocationBarHost.getParent();
        mLocationBarOriginalIndex = mLocationBarOriginalParent.indexOfChild(mLocationBarHost);
        mLocationBarOriginalLayoutParams = mLocationBarHost.getLayoutParams();

        rail.removeView(mNativeTabs);
        mColumn = column();
        View captionSpacer = new View(activity);
        mCaptionSpacer = captionSpacer;
        mColumn.addView(captionSpacer, new LinearLayout.LayoutParams(
                -1, nativeSpacer.getLayoutParams().height));
        ((VerticalTabRailLayout) mNativeTabs).setDesktopWindowSpacerHost(captionSpacer);
        mHeader = column();

        mNavigationRow = new LinearLayout(activity);
        mCollapseButtonOriginalParent.removeView(mCollapseButton);
        mNavigationRow.addView(
                mCollapseButton,
                new LinearLayout.LayoutParams(
                        dp(ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP),
                        dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        mNavigationControls = new LinearLayout(activity);
        // ToolbarPhone does not expose forward/reload Views in Chromium 157, while ARC can be
        // explicitly forced in a narrow window. Keep navigation real by dispatching directly to
        // the currently selected Chromium Tab instead of depending on a ToolbarTablet hierarchy.
        ImageButton back = navigationButton(R.drawable.btn_back,
                R.string.accessibility_toolbar_btn_back,
                tab -> { if (tab.canGoBack()) tab.goBack(); });
        ImageButton forward = navigationButton(R.drawable.btn_forward,
                R.string.accessibility_toolbar_btn_forward,
                tab -> { if (tab.canGoForward()) tab.goForward(); });
        ImageButton reload = navigationButton(R.drawable.btn_reload_stop,
                R.string.accessibility_btn_refresh, Tab::reload);
        mNavigationControls.addView(back);
        mNavigationControls.addView(forward);
        mNavigationControls.addView(reload);
        mNavigationState = new ArcNavigationControls(currentTab, back, forward, reload);
        mNavigationRow.addView(
                mNavigationControls,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        mHeader.addView(
                mNavigationRow,
                new LinearLayout.LayoutParams(
                        -1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        // Tablet Chromium keeps the real omnibox inside a dedicated FrameLayout. Reparent that
        // holder as a unit so LocationBarTablet keeps its original direct parent and child layout
        // params. Future layouts fall back to the real LocationBar view validated above.
        mLocationBarOriginalParent.removeView(mLocationBarHost);
        LinearLayout.LayoutParams locationBarParams = new LinearLayout.LayoutParams(
                -1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP));
        locationBarParams.setMarginStart(dp(ArcDesktopPolicy.ARC_LOCATION_BAR_SIDE_MARGIN_DP));
        locationBarParams.setMarginEnd(dp(ArcDesktopPolicy.ARC_LOCATION_BAR_SIDE_MARGIN_DP));
        mHeader.addView(mLocationBarHost, locationBarParams);

        mHeaderActions = new LinearLayout(activity);
        Button bookmarksButton = button(activity.getString(R.string.arc_bookmarks), openBookmarks);
        Button googleButton = button("Google", () -> {});
        googleButton.setOnClickListener(v -> showGoogleMenu(v));
        ImageButton appearanceButton = new ImageButton(activity);
        mAppearanceButton = appearanceButton;
        GradientDrawable wheel = new GradientDrawable();
        wheel.setShape(GradientDrawable.OVAL);
        wheel.setGradientType(GradientDrawable.SWEEP_GRADIENT);
        wheel.setColors(new int[] {0xffef5350, 0xffffca28, 0xff66bb6a, 0xff26c6da,
                0xff42a5f5, 0xffab47bc, 0xffef5350});
        wheel.setSize(dp(14), dp(14));
        appearanceButton.setImageDrawable(wheel);
        appearanceButton.setScaleType(android.widget.ImageView.ScaleType.CENTER_INSIDE);
        appearanceButton.setPadding(dp(10), dp(10), dp(10), dp(10));
        appearanceButton.setOnClickListener(v -> showColorPicker());
        appearanceButton.setOnLongClickListener(v -> {
            ArcAppearanceDialog.createAddressBarPosition(mActivity, this::applyAppearance).show();
            return true;
        });
        appearanceButton.setTooltipText(activity.getString(R.string.arc_frame_color));
        bookmarksButton.setText("☆\n" + activity.getString(R.string.arc_bookmarks));
        bookmarksButton.setTextSize(10);
        bookmarksButton.setGravity(Gravity.CENTER);
        googleButton.setText("G\nGoogle");
        googleButton.setTextSize(10);
        googleButton.setGravity(Gravity.CENTER);
        appearanceButton.setContentDescription(activity.getString(R.string.arc_frame_color));
        for (View action : new View[] {bookmarksButton, googleButton}) {
            action.setTag("arc-header-tile");
            LinearLayout.LayoutParams tile = new LinearLayout.LayoutParams(0, dp(52), 1);
            tile.setMargins(dp(4), dp(4), dp(4), dp(4));
            mHeaderActions.addView(action, tile);
        }
        mHeader.addView(mHeaderActions);
        mColumn.addView(mHeader);
        mNewTabRow = new TextView(activity);
        mNewTabIcon = Objects.requireNonNull(activity.getDrawable(R.drawable.ic_add_24dp)).mutate();
        mNewTabIcon.setBounds(0, 0, dp(24), dp(24));
        mNewTabRow.setText("+  " + activity.getString(R.string.arc_new_tab));
        mNewTabRow.setContentDescription(activity.getString(R.string.arc_new_tab));
        mNewTabRow.setTooltipText(activity.getString(R.string.arc_new_tab));
        mNewTabRow.setGravity(Gravity.CENTER_VERTICAL);
        mNewTabRow.setFocusable(true);
        mNewTabRow.setClickable(true);
        mNewTabRow.setPadding(dp(12), 0, dp(12), 0);
        mNewTabRow.setOnClickListener(v -> {
            if (!mDestroyed && mNativeNewTabButton.isEnabled()) {
                openCommandBar();
            }
        });
        mColumn.addView(mNewTabRow, new LinearLayout.LayoutParams(-1, dp(44)));
        mColumn.addView(mNativeTabs, new LinearLayout.LayoutParams(-1, 0, 1));

        mFooter = new LinearLayout(activity);
        // VerticalTabRailLayout already owns Chromium's real new-tab button and handler.
        // The deprecated password/Autofill shortcut is omitted from the Arc footer.
        // Preserve Chromium's native app menu and extension actions after ToolbarTablet itself is
        // removed from layout. These Views retain their existing coordinators/listeners; Arc only
        // changes their parent. The extension container is optional when ExtensionUi is disabled.
        mMenuButtonOriginalParent.removeView(mMenuButtonWrapper);
        mFooter.addView(
                mMenuButtonWrapper,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        if (mExtensionsToolbarHost != null) {
            mExtensionsToolbarOriginalParent.removeView(mExtensionsToolbarHost);
            mFooter.addView(
                    mExtensionsToolbarHost,
                    new LinearLayout.LayoutParams(
                            ViewGroup.LayoutParams.WRAP_CONTENT,
                            dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        }
        mColumn.addView(mFooter);
        ImageButton about = new ImageButton(activity);
        about.setImageResource(android.R.drawable.ic_menu_info_details);
        about.setContentDescription(activity.getString(R.string.arc_about));
        about.setTooltipText(activity.getString(R.string.arc_about));
        about.setOnClickListener(v -> {
            if (mDestroyed) return;
            if (mAboutDialog != null) mAboutDialog.dismiss();
            mAboutDialog = ArcAboutDialog.show(activity, activity.getString(R.string.arc_about),
                    activity.getString(R.string.arc_version));
        });
        mFooter.addView(about, new LinearLayout.LayoutParams(dp(44), dp(44)));
        mFooter.addView(appearanceButton, new LinearLayout.LayoutParams(dp(44), dp(44)));
        rail.addView(mColumn, new ViewGroup.LayoutParams(-1, -1));

        mArcContentOutlineProvider =
                new ViewOutlineProvider() {
                    @Override
                    public void getOutline(View view, Outline outline) {
                        int left = arcClipLeftForView(view);
                        if (view.getWidth() <= left || view.getHeight() <= 0) {
                            outline.setEmpty();
                            return;
                        }
                        float radius = Math.min(dp(ArcDesktopPolicy.ARC_CONTENT_RADIUS_DP),
                                Math.min((view.getWidth() - left) / 2f, view.getHeight() / 2f));
                        // SurfaceControl supports a round rect, not asymmetric Path corners.
                        // Crop below the visible bottom to make the sidebar junction square.
                        outline.setRoundRect(left, 0, view.getWidth(), view.getHeight() + Math.round(radius), radius);
                    }
                };
        mArcTouchEventObserver =
                new TouchEventObserver() {
                    @Override
                    public boolean onInterceptTouchEvent(MotionEvent event) {
                        return false;
                    }

                    @Override
                    public boolean mayInterceptTouchSequenceInWebContents() {
                        // Only rounded-corner dead zones are intercepted, but Chromium must know
                        // that this observer can consume a WebContents sequence before dispatch.
                        return true;
                    }

                    @Override
                    public boolean dispatchTouchEvent(MotionEvent event) {
                        if (!mArcFrameActive) {
                            mRejectingRoundedCornerGesture = false;
                            return false;
                        }
                        int action = event.getActionMasked();
                        if (action == MotionEvent.ACTION_DOWN) {
                            mRejectingRoundedCornerGesture = !isInsideArcContent(
                                    event.getX(), event.getY());
                        }
                        boolean consume = mRejectingRoundedCornerGesture;
                        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                            mRejectingRoundedCornerGesture = false;
                        }
                        return consume;
                    }
                };
        mSurfaceAttachStateListener =
                new View.OnAttachStateChangeListener() {
                    @Override
                    public void onViewAttachedToWindow(View view) {
                        if (!mDestroyed && mArcFrameActive) {
                            mFrameDispatch.schedule(view, ArcDesktopCoordinator.this::applyFrameGeometry);
                        }
                    }

                    @Override
                    public void onViewDetachedFromWindow(View view) {
                        if (!mDestroyed && mArcFrameActive) {
                            mFrameDispatch.schedule(
                                    mCompositorViewHolder, ArcDesktopCoordinator.this::applyFrameGeometry);
                        }
                    }
                };
        mCompositorViewHolder.addTouchEventObserver(mArcTouchEventObserver);
        mContentLayoutListener =
                (v, l, t, r, b, ol, ot, or, ob) -> {
                    if (mArcFrameActive) mFrameDispatch.schedule(v, this::applyFrameGeometry);
                };
        mCompositorViewHolder.addOnLayoutChangeListener(mContentLayoutListener);

        // The real LocationBar is already detached into the Arc header. Suppressing the toolbar
        // now removes its layer from TopControlsStacker, so it contributes no height or hitbox.
        mSetToolbarSuppressed.accept(true);
        mArcToolbarCompositionActive = true;
        mPreferenceListener = (prefs, key) -> {
            if (mDestroyed) return;
            if (ArcDesktopAppearance.COLOR_KEY.equals(key)) {
                // Rebind tab titles/buttons through the native RecyclerView after a palette change.
                refreshNativeRows(mNativeTabs);
                applyAppearance();
                View toolbar = mActivity.findViewById(R.id.toolbar);
                if (toolbar instanceof ToolbarTablet) {
                    ((ToolbarTablet) toolbar).onThemeColorChanged(
                            ArcDesktopAppearance.surface(
                                    mActivity, mIncognitoStateProvider.isIncognitoSelected()),
                            false);
                }
            } else if (ArcDesktopAppearance.UI_MODE_KEY.equals(key)
                    || ArcDesktopAppearance.ADDRESS_BAR_POSITION_KEY.equals(key)
                    || ArcDesktopAppearance.UI_FONT_KEY.equals(key)) {
                if (mCommandBar != null) mCommandBar.close(false, null);
                // AUTO/ARC/MOBILE can change while this coordinator still exists. Re-evaluate the
                // shell synchronously so ToolbarTablet is never left suppressed in MOBILE.
                refreshNativeRows(mNativeTabs);
                applyAppearance();
            }
        };
        mPreferences.registerOnSharedPreferenceChangeListener(mPreferenceListener);
        mLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> {
            if (l == ol && t == ot && r == or && b == ob) return;
            scheduleAppearance();
        };
        rail.addOnLayoutChangeListener(mLayoutListener);
        mMenuButtonWrapper.addOnLayoutChangeListener(mLayoutListener);
        mNewTabRow.addOnLayoutChangeListener(mLayoutListener);
        mIncognitoStateProvider.addIncognitoStateObserverAndTrigger(mIncognitoObserver);
        mFontLayoutListener = () -> {
            if (mDestroyed) return;
            ArcDesktopAppearance.applyUiFont(mColumn);
            if (mExtensionsToolbarHost == null
                    && mActivity.findViewById(R.id.extensions_toolbar_container) != null) scheduleAppearance();
            View controls = mActivity.findViewById(R.id.control_container);
            if (controls != null) ArcDesktopAppearance.applyUiFont(controls);
        };
        mColumn.getViewTreeObserver().addOnGlobalLayoutListener(mFontLayoutListener);
        applyAppearance();
        // Initialization may run before the rail has its first measured size.
        scheduleAppearance();
    }

    private void scheduleAppearance() {
        mAppearanceDispatch.schedule(mRail, () -> {
            rebindCollections();
            applyAppearance();
        });
    }

    /** Called with the native Side UI target; hovering remains an overlay. */
    public void onSideUiTransition(int reservedWidth, int renderedWidth) {
        int oldInset = reservedLeftWidth();
        mRailViewportTransition = reservedWidth == renderedWidth;
        mTransitionOtherInset = Math.max(0, oldInset - mRail.getWidth());
        if (mRailViewportTransition && reservedWidth < oldInset) {
            mCompositorViewHolder.beginArcRailViewportResize(oldInset);
        }
    }

    public void onSideUiChanged() {
        mRailViewportTransition = false;
        scheduleAppearance();
    }

    /** Installed once by TabbedRootUiCoordinator after its native omnibox is initialized. */
    public void configureCommands(Runnable beginInput, Runnable endInput,
            Runnable focusAddressBar, Runnable openSettings) {
        if (mCommandBar != null || mDestroyed) return;
        mFocusAddressBar = focusAddressBar; mOpenSettings = openSettings;
        mEndAddressInput = endInput;
        View url = mLocationBarHost.findViewById(R.id.url_bar);
        if (!(mFrameRoot instanceof ViewGroup) || !(url instanceof EditText)) return;
        mCommandBar = new ArcCommandBar(mActivity, (ViewGroup) mFrameRoot, mLocationBarHost,
                (EditText) url, mOmniboxPlacement, this::commandViewport,
                beginInput, endInput, this::applyAddressBarPosition, this::commandResults,
                mActivity.getString(R.string.arc_command_placeholder),
                mActivity.getString(R.string.arc_command_actions));
        // Capture the native instance once. Fusebox can temporarily move it outside its holder;
        // a fresh descendant lookup on close would leave its command bridge and input alive.
        View location = mLocationBarHost.findViewById(R.id.location_bar);
        mCommandBar.setBoundsChangedListener(() -> {
            if (location instanceof LocationBarLayout bar) {
                bar.setArcCommandBar(mCommandBar.isShowing() ? mCommandBar.resultsBoundsInWindow() : null,
                        mCommandBar.isActions(), mCommandBar::commitNativeNavigation,
                        () -> mCommandBar.close(false, null));
            }
            // The native suggestion container shares this coordinator root. Keep native results
            // above the temporary command surface, retaining its original security/navigation UI.
            View dropdown = mActivity.findViewById(R.id.omnibox_suggestions_dropdown);
            if (mCommandBar.isShowing() && dropdown != null) {
                View container = dropdown;
                while (container.getParent() instanceof View && container.getParent() != mFrameRoot) {
                    container = (View) container.getParent();
                }
                if (container.getParent() == mFrameRoot) {
                    ViewGroup root = (ViewGroup) mFrameRoot;
                    if (root.indexOfChild(container) != root.getChildCount() - 1) container.bringToFront();
                }
            }
        });
        mPaletteInitialized = false;
        applyAppearance();
    }

    private Rect commandViewport() {
        int[] content = new int[2], root = new int[2];
        mCompositorViewHolder.getLocationInWindow(content); mFrameRoot.getLocationInWindow(root);
        return new Rect(content[0] - root[0] + reservedLeftWidth(), content[1] - root[1],
                content[0] - root[0] + mCompositorViewHolder.getWidth(),
                content[1] - root[1] + mCompositorViewHolder.getHeight());
    }

    private List<ArcCommandBar.Result> commandResults(boolean actions) {
        List<ArcCommandBar.Result> results = new ArrayList<>();
        TabModel model = mCurrentModel.get();
        if (model == null || model.getProfile() == null || model.getProfile().shutdownStarted()) return results;
        if (actions) {
            results.add(new ArcCommandBar.Result(mActivity.getString(R.string.arc_command_settings), "", "",
                    mActivity.getDrawable(android.R.drawable.ic_menu_preferences), mOpenSettings));
            results.add(new ArcCommandBar.Result(mActivity.getString(R.string.arc_command_toggle_sidebar), "", "",
                    mActivity.getDrawable(android.R.drawable.ic_menu_view), () -> mCollapseButton.performClick()));
            ArcCollectionsController collections = mCollections;
            if (collections != null) for (ArcSidebarState.Space space : collections.state().spaces()) {
                results.add(new ArcCommandBar.Result(space.name, mActivity.getString(R.string.arc_command_space), "",
                        mActivity.getDrawable(android.R.drawable.ic_menu_agenda), () -> {
                            if (!mDestroyed && mCurrentModel.get() == model && mCollections == collections) {
                                collections.selectSpace(space.id);
                            }
                        }));
            }
            return results;
        }
        for (int i = 0; i < model.getCount(); i++) {
            Tab tab = model.getTabAt(i);
            if (tab == null || tab.isDestroyed()) continue;
            int id = tab.getId();
            results.add(new ArcCommandBar.Result(tab.getTitle(), tab.getUrl().getSpec(),
                    mActivity.getString(R.string.arc_command_switch_tab),
                    mActivity.getDrawable(android.R.drawable.ic_menu_view), () -> {
                        if (mDestroyed || mCurrentModel.get() != model) return;
                        for (int j = 0; j < model.getCount(); j++) {
                            Tab candidate = model.getTabAt(j);
                            if (candidate != null && !candidate.isDestroyed() && candidate.getId() == id) {
                                model.setIndex(j, TabSelectionType.FROM_USER); return;
                            }
                        }
                    }));
        }
        return results;
    }

    public boolean openCommandBar() {
        if (mDestroyed || !ArcDesktopAppearance.isDesktopWindow(mActivity) || mCommandBar == null) return false;
        // Restore a native Ctrl+L popover before moving its holder to the command header.
        if (!mCommandBar.isShowing()) mEndAddressInput.run();
        mCompactOmnibox.restore(); mCommandBar.open(false); return true;
    }

    public boolean dispatchKeyEvent(KeyEvent event) {
        if (mDestroyed || !ArcDesktopAppearance.isDesktopWindow(mActivity)) return false;
        if ((event.isCtrlPressed() || event.isMetaPressed()) && !event.isAltPressed() && !event.isShiftPressed()) {
            if (event.getKeyCode() == KeyEvent.KEYCODE_T) {
                if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) return openCommandBar();
                return mCommandBar != null;
            }
            if (event.getKeyCode() == KeyEvent.KEYCODE_L && mFocusAddressBar != null) {
                if (event.getAction() == KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0) {
                    if (mCommandBar != null) mCommandBar.close(false, null);
                    if (ArcDesktopAppearance.getAddressBarPosition(mActivity) == ArcDesktopAppearance.ADDRESS_SIDEBAR
                            && !ArcDesktopPolicy.showFullControls(mRail.getWidth(), mRail.getHeight(),
                                    mActivity.getResources().getDisplayMetrics().density)) {
                        mCollapseButton.performClick();
                    }
                    mFocusAddressBar.run();
                }
                return true;
            }
        }
        return mCommandBar != null && mCommandBar.dispatchKeyEvent(event);
    }

    private void applyAddressBarPosition() {
        if (mCommandBar != null && mCommandBar.isShowing()) return;
        boolean desktop = !mDestroyed && ArcDesktopAppearance.isDesktopWindow(mActivity);
        boolean top = desktop && ArcDesktopAppearance.getAddressBarPosition(mActivity) == ArcDesktopAppearance.ADDRESS_TOP;
        View locationBar = mLocationBarHost.findViewById(R.id.location_bar);
        if (locationBar instanceof LocationBarLayout nativeBar) nativeBar.setArcTopBar(top);
        if (!desktop || top) mOmniboxPlacement.restore();
        else mOmniboxPlacement.move(mHeader, 1, arcLocationBarLayoutParams());
        mSetToolbarSuppressed.accept(desktop && !top);
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

    private ImageButton navigationButton(
            int drawableRes, int contentDescriptionRes, Consumer<Tab> action) {
        ImageButton button = new ImageButton(mActivity);
        button.setImageResource(drawableRes);
        button.setContentDescription(mActivity.getString(contentDescriptionRes));
        button.setTooltipText(mActivity.getString(contentDescriptionRes));
        button.setMinimumWidth(0);
        button.setMinimumHeight(0);
        button.setPadding(dp(10), dp(8), dp(10), dp(8));
        button.setOnClickListener(
                v -> {
                    Tab tab = mCurrentTab.get();
                    if (!mDestroyed && tab != null && !tab.isDestroyed()) action.accept(tab);
                });
        button.setLayoutParams(
                new LinearLayout.LayoutParams(
                        dp(ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP),
                        dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        return button;
    }

    private void clearCollections() {
        // Remove the old profile/Space predicate before changing models. This restores the native
        // global presentation and prevents one profile's Arc metadata from filtering another.
        mNativeTabListCoordinator.setTabVisibilityPredicate(null);
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
                    if (!mDestroyed && mSessionModel == model) {
                        mNativeTabListCoordinator.refreshTabPresentation();
                        if (mCollectionsView != null) mCollectionsView.refresh();
                        applyAppearance();
                    }
                });
        mTabSession = session;
        mSessionModel = model;
        // Filter the existing Chromium presentation model. The TabModel itself remains untouched.
        mNativeTabListCoordinator.setTabVisibilityPredicate(session::isTabVisibleForActiveSpace);
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
        // Navigation/address stay at the top; collections follow the Arc header actions.
        mHeader.addView(mCollectionsView);
        mPaletteInitialized = false;
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
        if (mDestroyed || (mColorDialog != null && mColorDialog.isShowing())) return;
        mColorDialog = new ArcColorPicker(mActivity, mPreferences,
                mActivity.getResources().getStringArray(R.array.arc_frame_palette_names),
                mActivity.getResources().getStringArray(R.array.arc_frame_rgb_names), preview -> {
                    ArcDesktopAppearance.setPreviewColor(mActivity, preview);
                    if (!mDestroyed) {
                        refreshNativeRows(mNativeTabs);
                        applyAppearance();
                    }
                }).show();
    }

    private int frameSurface(boolean incognito) {
        return ArcDesktopAppearance.surface(mActivity, incognito);
    }

    private LinearLayout.LayoutParams arcLocationBarLayoutParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                -1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP));
        params.setMarginStart(dp(ArcDesktopPolicy.ARC_LOCATION_BAR_SIDE_MARGIN_DP));
        params.setMarginEnd(dp(ArcDesktopPolicy.ARC_LOCATION_BAR_SIDE_MARGIN_DP));
        return params;
    }

    private void ensureExtensionsToolbar() {
        if (mExtensionsToolbarHost != null) return;
        View host = mActivity.findViewById(R.id.extensions_toolbar_container);
        if (host == null || !(host.getParent() instanceof ViewGroup parent)) return;
        mExtensionsToolbarHost = host;
        mExtensionsToolbarOriginalParent = parent;
        mExtensionsToolbarOriginalIndex = parent.indexOfChild(host);
        mExtensionsToolbarOriginalLayoutParams = host.getLayoutParams();
        mExtensionsToolbarOriginalVisibility = host.getVisibility();
        if (mArcToolbarCompositionActive) {
            parent.removeView(host);
            mFooter.addView(host, 1, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        }
    }

    private void attachToolbarControlsToArc() {
        if (mCollapseButton.getParent() instanceof ViewGroup) {
            ((ViewGroup) mCollapseButton.getParent()).removeView(mCollapseButton);
        }
        mNavigationRow.addView(
                mCollapseButton,
                0,
                new LinearLayout.LayoutParams(
                        dp(ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP),
                        dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));

        if (mLocationBarHost.getParent() instanceof ViewGroup) {
            ((ViewGroup) mLocationBarHost.getParent()).removeView(mLocationBarHost);
        }
        mHeader.addView(mLocationBarHost, 1, arcLocationBarLayoutParams());

        if (mMenuButtonWrapper.getParent() instanceof ViewGroup) {
            ((ViewGroup) mMenuButtonWrapper.getParent()).removeView(mMenuButtonWrapper);
        }
        mFooter.addView(
                mMenuButtonWrapper,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));

        if (mExtensionsToolbarHost != null) {
            if (mExtensionsToolbarHost.getParent() instanceof ViewGroup) {
                ((ViewGroup) mExtensionsToolbarHost.getParent()).removeView(
                        mExtensionsToolbarHost);
            }
            mFooter.addView(
                    mExtensionsToolbarHost,
                    new LinearLayout.LayoutParams(
                            ViewGroup.LayoutParams.WRAP_CONTENT,
                            dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP)));
        }
    }

    private void setArcToolbarCompositionActive(boolean active) {
        if (mArcToolbarCompositionActive == active) return;
        if (active) {
            attachToolbarControlsToArc();
            mSetToolbarSuppressed.accept(true);
            mArcToolbarCompositionActive = true;
            return;
        }

        // Restore Chromium's real controls before making ToolbarTablet visible again. This avoids
        // an intermediate visible toolbar with missing/floating children.
        restoreLocationBar();
        restoreToolbarUtilityControls();
        restoreCollapseButton();
        mSetToolbarSuppressed.accept(false);
        mArcToolbarCompositionActive = false;
    }

    private void applyAppearance() {
        if (mDestroyed) return;
        ensureExtensionsToolbar();
        mNavigationState.refresh();
        boolean desktop = ArcDesktopAppearance.isDesktopWindow(mActivity);
        boolean incognito = mIncognitoStateProvider.isIncognitoSelected();
        setArcToolbarCompositionActive(desktop);
        if (!desktop && mCommandBar != null) mCommandBar.close(false, null);
        applyAddressBarPosition();
        int surface = frameSurface(incognito);
        boolean paletteChanged = !mPaletteInitialized || mPaletteDesktop != desktop
                || mPaletteIncognito != incognito || mPaletteSurface != surface;
        mPaletteInitialized = true;
        mPaletteDesktop = desktop;
        mPaletteIncognito = incognito;
        mPaletteSurface = surface;
        if (paletteChanged) {
            View locationBar = mLocationBarHost.findViewById(R.id.location_bar);
            if (locationBar instanceof LocationBarLayout) {
                ((LocationBarLayout) locationBar).setArcSurfaceColor(
                        desktop ? surface : null);
            }
        }
        if (paletteChanged && mNativeTabs instanceof VerticalTabRailLayout) {
            // This binder restores upstream colors/tints too when ARC is no longer active.
            VerticalTabListViewBinder.refreshArcAppearance(
                    (VerticalTabRailLayout) mNativeTabs, incognito);
        }
        if (!desktop) {
            mCompactOmnibox.restore();
            mNewTabRow.setVisibility(View.GONE);
            mNativeNewTabButton.setVisibility(mNativeNewTabVisibility);
            mHeader.setVisibility(View.GONE);
            mFooter.setVisibility(View.GONE);
            if (mCollectionsView != null) mCollectionsView.setVisibility(View.GONE);
            mColumn.setBackgroundColor(Color.TRANSPARENT);
            clearFrameGeometry();
            return;
        }

        float density = mActivity.getResources().getDisplayMetrics().density;
        int captionHeight = Math.max(mCaptionSpacer.getHeight(),
                Math.max(0, mCaptionSpacer.getLayoutParams().height));
        int collectionBudget = ArcDesktopPolicy.collectionScrollBudgetPx(
                mRail.getHeight(), density, captionHeight);
        boolean expanded =
                ArcDesktopPolicy.showFullControls(
                        mRail.getWidth(),
                        mRail.getHeight(),
                        density);
        // Collection scrolling can run out of height while navigation still fits the wide rail.
        // Budget only the collection area; do not turn a wide sidebar into the compact layout.
        // Keep the real Chromium LocationBar visible even in collapsed mode so keyboard/focus
        // paths never target a GONE omnibox. Secondary Arc controls are restored on expansion.
        mHeader.setVisibility(View.VISIBLE);
        mNavigationRow.setVisibility(View.VISIBLE);
        mNavigationControls.setVisibility(View.VISIBLE);
        mNavigationState.setExpanded(expanded);
        mNavigationRow.setOrientation(expanded ? LinearLayout.HORIZONTAL : LinearLayout.VERTICAL);
        mNavigationRow.setGravity(expanded ? Gravity.START : Gravity.CENTER_HORIZONTAL);
        ViewGroup.LayoutParams navigationLayout = mNavigationRow.getLayoutParams();
        int navigationHeight = dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP) * (expanded ? 1 : 2);
        if (navigationLayout.height != navigationHeight) {
            navigationLayout.height = navigationHeight;
            mNavigationRow.setLayoutParams(navigationLayout);
        }
        mHeaderActions.setVisibility(expanded ? View.VISIBLE : View.GONE);
        boolean commandOpen = mCommandBar != null && mCommandBar.isShowing();
        mCompactOmnibox.setCompact(!expanded && !commandOpen
                && ArcDesktopAppearance.getAddressBarPosition(mActivity) == ArcDesktopAppearance.ADDRESS_SIDEBAR);
        updateNewTabRow(expanded);
        // The native app menu remains reachable while collapsed. Secondary footer actions can
        // disappear so the compact rail does not retain expanded hitboxes.
        mFooter.setVisibility(View.VISIBLE);
        mFooter.setOrientation(expanded ? LinearLayout.HORIZONTAL : LinearLayout.VERTICAL);
        mFooter.setGravity(expanded ? Gravity.START : Gravity.CENTER_HORIZONTAL);
        if (mExtensionsToolbarHost != null) {
            mExtensionsToolbarHost.setVisibility(expanded ? View.VISIBLE : View.GONE);
            View toolbar = mActivity.findViewById(R.id.toolbar);
            if (expanded && toolbar instanceof ToolbarTablet tablet) {
                // The native menu is not guaranteed to be 44dp (theme, padding and font scale).
                // Reserve its measured width, both Arc buttons and rail insets before allocating
                // extension icons. Its layout listener refreshes this budget after first measure.
                tablet.updateArcExtensionsWidth(Math.max(0, mRail.getWidth()
                        - mRail.getPaddingLeft() - mRail.getPaddingRight()
                        - Math.max(dp(ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP),
                                mMenuButtonWrapper.getMeasuredWidth())
                        - 2 * dp(ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP)));
            }
        }
        if (mCollectionsView != null) {
            mCollectionsView.setVisibility(
                    expanded && collectionBudget >= dp(80) ? View.VISIBLE : View.GONE);
        }
        applyFrameGeometry();
        if (expanded && mCollectionsView != null) {
            mCollectionsView.setCollectionHeight(collectionBudget);
        }
        // Palette work is independent of rail width. Avoid rebuilding drawables on every
        // animation frame; Chromium continues animating the reserved width and viewport.
        if (!paletteChanged) return;
        int foreground = ArcDesktopPolicy.foreground(surface);
        if (mCommandBar != null) mCommandBar.setAppearance(surface, foreground, ArcDesktopPolicy.selection(surface));
        mNewTabIcon.setTint(foreground);
        mColumn.setBackgroundColor(surface);
        styleInteraction(mNewTabRow, foreground, ArcDesktopPolicy.selection(surface));
        for (int i = 0; i < mNavigationControls.getChildCount(); i++) {
            View button = mNavigationControls.getChildAt(i);
            styleInteraction(button, foreground, ArcDesktopPolicy.selection(surface));
            if (button instanceof ImageButton) {
                ((ImageButton) button).setImageTintList(new ColorStateList(
                        new int[][] {new int[] {-android.R.attr.state_enabled}, new int[] {}},
                        new int[] {(foreground & 0xffffff) | 0x66000000, foreground}));
            }
        }
        tintHeader(mHeader, foreground, ArcDesktopPolicy.selection(surface));
        tintHeader(mFooter, foreground, ArcDesktopPolicy.selection(surface));
        if (mCollectionsView != null) {
            mCollectionsView.setAppearance(surface, foreground, ArcDesktopPolicy.selection(surface));
        }
    }

    private int reservedLeftWidth() {
        if (mRailViewportTransition) return mRail.getWidth() + mTransitionOtherInset;
        Integer width = mReservedLeftWidth.get();
        return Math.max(0, width == null ? 0 : width);
    }

    private void updateNewTabRow(boolean expanded) {
        mNewTabRow.setVisibility(View.VISIBLE);
        CharSequence label = expanded ? mActivity.getString(R.string.arc_new_tab) : "";
        if (!TextUtils.equals(mNewTabRow.getText(), label)) mNewTabRow.setText(label);
        mNewTabRow.setCompoundDrawablesRelative(mNewTabIcon, null, null, null);
        mNewTabRow.setCompoundDrawablePadding(expanded ? dp(8) : 0);
        int availableWidth = Math.max(0, mRail.getWidth()
                - mRail.getPaddingLeft() - mRail.getPaddingRight());
        int rowWidth = Math.min(mNewTabRow.getWidth(), availableWidth);
        if (rowWidth <= 0) {
            rowWidth = availableWidth;
        }
        int padding = expanded ? dp(12) : Math.max(0, (rowWidth - dp(24)) / 2);
        mNewTabRow.setPadding(padding, 0, padding, 0);
        mNewTabRow.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
        mNewTabRow.setEnabled(mNativeNewTabButton.isEnabled());
        mNativeNewTabButton.setVisibility(View.GONE);
    }

    private int arcClipLeftForView(View view) {
        int reserved = reservedLeftWidth();
        if (view == mCompositorViewHolder) return Math.min(reserved, view.getWidth());
        // The active SurfaceView is normally full-holder width. If Chromium supplies a content-only
        // surface instead, it has already removed the Side UI width and must not be inset twice.
        int holderWidth = mCompositorViewHolder.getWidth();
        if (holderWidth > 0 && Math.abs(view.getWidth() - holderWidth) <= dp(2)) {
            return Math.min(reserved, view.getWidth());
        }
        return 0;
    }

    private boolean isInsideArcContent(float x, float y) {
        return ArcDesktopPolicy.containsArcContentPoint(
                x, y, reservedLeftWidth(), 0, mCompositorViewHolder.getWidth(),
                mCompositorViewHolder.getHeight(), dp(ArcDesktopPolicy.ARC_CONTENT_RADIUS_DP));
    }

    private void restoreClippedSurface() {
        if (mClippedSurface == null) return;
        mClippedSurface.removeOnAttachStateChangeListener(mSurfaceAttachStateListener);
        mClippedSurface.removeOnLayoutChangeListener(mContentLayoutListener);
        mClippedSurface.setOutlineProvider(mClippedSurfaceOriginalOutlineProvider);
        mClippedSurface.setClipToOutline(mClippedSurfaceOriginalClipToOutline);
        mClippedSurface.setClipBounds(mClippedSurfaceOriginalClipBounds);
        mClippedSurface.invalidateOutline();
        mClippedSurface = null;
        mClippedSurfaceOriginalOutlineProvider = null;
        mClippedSurfaceOriginalClipBounds = null;
    }

    private void applyActiveSurfaceClip() {
        View activeSurface = mCompositorViewHolder.getActiveSurfaceView();
        if (activeSurface == mClippedSurface) {
            if (activeSurface != null) {
                activeSurface.setClipBounds(new Rect(arcClipLeftForView(activeSurface), 0,
                        activeSurface.getWidth(), activeSurface.getHeight()));
                activeSurface.invalidateOutline();
            }
            return;
        }
        restoreClippedSurface();
        if (activeSurface == null) return;
        mClippedSurface = activeSurface;
        mClippedSurfaceOriginalOutlineProvider = activeSurface.getOutlineProvider();
        mClippedSurfaceOriginalClipToOutline = activeSurface.getClipToOutline();
        mClippedSurfaceOriginalClipBounds = activeSurface.getClipBounds();
        activeSurface.addOnAttachStateChangeListener(mSurfaceAttachStateListener);
        // The surface can acquire its size after the holder's layout, or resize
        // independently on recreation. Refresh an initially empty/stale crop then.
        activeSurface.addOnLayoutChangeListener(mContentLayoutListener);
        activeSurface.setOutlineProvider(mArcContentOutlineProvider);
        activeSurface.setClipToOutline(true);
        activeSurface.setClipBounds(new Rect(arcClipLeftForView(activeSurface), 0,
                activeSurface.getWidth(), activeSurface.getHeight()));
        activeSurface.invalidateOutline();
    }

    private void applyFrameGeometry() {
        if (mDestroyed || !ArcDesktopAppearance.isDesktopWindow(mActivity)) return;
        mArcFrameActive = true;
        mCompositorViewHolder.setOutlineProvider(mArcContentOutlineProvider);
        mCompositorViewHolder.setClipToOutline(true);
        int outer = dp(ArcDesktopPolicy.ARC_OUTER_PADDING_DP);
        int gap = dp(ArcDesktopPolicy.ARC_FRAME_GAP_DP);
        // Preserve the complete Side UI width, especially the 52dp collapsed contract. The frame
        // gap belongs between Side UI and content, not inside the rail where it would shrink
        // native tab hit targets. Top/bottom padding remains part of the Arc frame.
        mRail.setPadding(
                mOriginalRailPaddingLeft, outer, mOriginalRailPaddingRight, outer);

        ViewGroup.LayoutParams raw = mCompositorViewHolder.getLayoutParams();
        if (raw instanceof ViewGroup.MarginLayoutParams) {
            ViewGroup.MarginLayoutParams margins = (ViewGroup.MarginLayoutParams) raw;
            int contentLeftMargin = mOriginalContentMarginLeft + gap;
            int contentTopMargin = mOriginalContentMarginTop + outer;
            int contentRightMargin = mOriginalContentMarginRight + outer;
            int contentBottomMargin = mOriginalContentMarginBottom + outer;
            if (margins.leftMargin != contentLeftMargin
                    || margins.topMargin != contentTopMargin
                    || margins.rightMargin != contentRightMargin
                    || margins.bottomMargin != contentBottomMargin) {
                // The holder itself moves right by `gap`; Chromium's existing SideUi content
                // offset remains `reservedLeftWidth`, so visual bounds and touch coordinates both
                // begin at reservedLeftWidth + gap without a fake translation.
                margins.leftMargin = contentLeftMargin;
                margins.topMargin = contentTopMargin;
                margins.rightMargin = contentRightMargin;
                margins.bottomMargin = contentBottomMargin;
                mCompositorViewHolder.setLayoutParams(margins);
            }
        }
        if (mRailViewportTransition) {
            mCompositorViewHolder.setArcContentOffsetForRail(reservedLeftWidth());
        }
        // A rectangular bound also constrains SurfaceView's hole punch. Outline-only clipping
        // can leave pixels exposed in the gap when its asymmetric corner path is composed.
        mCompositorViewHolder.setClipBounds(new Rect(
                Math.min(reservedLeftWidth(), mCompositorViewHolder.getWidth()), 0,
                mCompositorViewHolder.getWidth(), mCompositorViewHolder.getHeight()));
        mCompositorViewHolder.invalidateOutline();
        applyActiveSurfaceClip();

        boolean incognito = mIncognitoStateProvider.isIncognitoSelected();
        int surface = frameSurface(incognito);
        // The rail's top/bottom padding is drawn by the rail itself, outside mColumn.
        // Tinting only mColumn left the old white background visible as two strips.
        mRail.setBackgroundTintList(null);
        if (!(mRail.getBackground() instanceof ColorDrawable railColor)
                || railColor.getColor() != surface) mRail.setBackground(new ColorDrawable(surface));
        if (mFrameRoot != null
                && (!(mFrameRoot.getBackground() instanceof ColorDrawable frameColor)
                        || frameColor.getColor() != surface)) {
            mFrameRoot.setBackground(new ColorDrawable(surface));
        }
    }

    private void clearFrameGeometry() {
        mFrameDispatch.cancel();
        if (!mArcFrameActive) return;
        mArcFrameActive = false;
        mRejectingRoundedCornerGesture = false;
        restoreClippedSurface();
        mCompositorViewHolder.setOutlineProvider(mOriginalContentOutlineProvider);
        mCompositorViewHolder.setClipToOutline(mOriginalContentClipToOutline);
        mCompositorViewHolder.setClipBounds(mOriginalContentClipBounds);
        mCompositorViewHolder.invalidateOutline();
        ViewGroup.LayoutParams raw = mCompositorViewHolder.getLayoutParams();
        if (raw instanceof ViewGroup.MarginLayoutParams) {
            ViewGroup.MarginLayoutParams margins = (ViewGroup.MarginLayoutParams) raw;
            margins.leftMargin = mOriginalContentMarginLeft;
            margins.topMargin = mOriginalContentMarginTop;
            margins.rightMargin = mOriginalContentMarginRight;
            margins.bottomMargin = mOriginalContentMarginBottom;
            mCompositorViewHolder.setLayoutParams(margins);
        }
        mRail.setPadding(
                mOriginalRailPaddingLeft, mOriginalRailPaddingTop,
                mOriginalRailPaddingRight, mOriginalRailPaddingBottom);
        mRail.setBackground(mOriginalRailBackground);
        mRail.setBackgroundTintList(mOriginalRailBackgroundTint);
        if (mFrameRoot != null) mFrameRoot.setBackground(mOriginalFrameBackground);
    }

    private void restoreFrameGeometry() {
        clearFrameGeometry();
        mCompositorViewHolder.removeTouchEventObserver(mArcTouchEventObserver);
        mCompositorViewHolder.removeOnLayoutChangeListener(mContentLayoutListener);
    }

    private void restoreToolbarUtilityControls() {
        View toolbar = mActivity.findViewById(R.id.toolbar);
        if (toolbar instanceof ToolbarTablet tablet) tablet.clearArcExtensionsWidth();
        if (mMenuButtonWrapper.getParent() instanceof ViewGroup) {
            ((ViewGroup) mMenuButtonWrapper.getParent()).removeView(mMenuButtonWrapper);
        }
        int menuIndex =
                Math.min(
                        Math.max(0, mMenuButtonOriginalIndex),
                        mMenuButtonOriginalParent.getChildCount());
        mMenuButtonOriginalParent.addView(
                mMenuButtonWrapper, menuIndex, mMenuButtonOriginalLayoutParams);

        if (mExtensionsToolbarHost != null && mExtensionsToolbarOriginalParent != null) {
            if (mExtensionsToolbarHost.getParent() instanceof ViewGroup) {
                ((ViewGroup) mExtensionsToolbarHost.getParent()).removeView(mExtensionsToolbarHost);
            }
            int extensionIndex =
                    Math.min(
                            Math.max(0, mExtensionsToolbarOriginalIndex),
                            mExtensionsToolbarOriginalParent.getChildCount());
            mExtensionsToolbarOriginalParent.addView(
                    mExtensionsToolbarHost,
                    extensionIndex,
                    mExtensionsToolbarOriginalLayoutParams);
            mExtensionsToolbarHost.setVisibility(mExtensionsToolbarOriginalVisibility);
        }
    }

    private void restoreCollapseButton() {
        if (mCollapseButton.getParent() instanceof ViewGroup) {
            ((ViewGroup) mCollapseButton.getParent()).removeView(mCollapseButton);
        }
        int index = Math.min(Math.max(0, mCollapseButtonOriginalIndex),
                mCollapseButtonOriginalParent.getChildCount());
        mCollapseButtonOriginalParent.addView(
                mCollapseButton, index, mCollapseButtonOriginalLayoutParams);
    }

    private void restoreLocationBar() {
        if (mLocationBarHost.getParent() instanceof ViewGroup) {
            ((ViewGroup) mLocationBarHost.getParent()).removeView(mLocationBarHost);
        }
        int index = Math.min(Math.max(0, mLocationBarOriginalIndex),
                mLocationBarOriginalParent.getChildCount());
        mLocationBarOriginalParent.addView(
                mLocationBarHost, index, mLocationBarOriginalLayoutParams);
    }

    private void tintHeader(View view, int foreground, int selection) {
        // Native Chromium controls keep their own ripple, hover, accessibility and icon-tint
        // state. Arc only styles views that it owns.
        if (view == mLocationBarHost
                || view == mNavigationControls
                || view == mCollapseButton
                || view == mMenuButtonWrapper
                || view == mExtensionsToolbarHost
                || view == mCollectionsView) {
            return;
        }
        if (view instanceof TextView) ((TextView) view).setTextColor(foreground);
        if (view instanceof Button || view instanceof ImageButton) {
            styleInteraction(view, foreground, selection);
            if (view instanceof ImageButton && view != mAppearanceButton) {
                ((ImageButton) view).setColorFilter(foreground);
            }
        }
        // Website favicons are intentionally never tinted.
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                tintHeader(group.getChildAt(i), foreground, selection);
            }
        }
    }

    private void styleInteraction(View view, int foreground, int selection) {
        StateListDrawable states = new StateListDrawable();
        for (int state : new int[] {android.R.attr.state_pressed,
                android.R.attr.state_focused, android.R.attr.state_hovered}) {
            GradientDrawable active = new GradientDrawable();
            active.setColor(selection);
            active.setCornerRadius(dp(8));
            states.addState(new int[] {android.R.attr.state_enabled, state}, active);
        }
        GradientDrawable idle = new GradientDrawable();
        idle.setColor("arc-header-tile".equals(view.getTag())
                ? ArcDesktopPolicy.activeTabSurface(mPaletteSurface) : Color.TRANSPARENT);
        idle.setCornerRadius(dp(8));
        states.addState(new int[] {}, idle);
        view.setBackground(states);
        if (view instanceof TextView) ((TextView) view).setTextColor(foreground);
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
        mAppearanceDispatch.destroy();
        mColumn.getViewTreeObserver().removeOnGlobalLayoutListener(mFontLayoutListener);
        if (mCommandBar != null) mCommandBar.destroy();
        mFrameDispatch.destroy();
        mCompactOmnibox.destroy();
        ArcDesktopAppearance.setPreviewColor(mActivity, null);
        mNavigationState.destroy();
        mNativeNewTabButton.setVisibility(mNativeNewTabVisibility);
        mIncognitoStateProvider.removeObserver(mIncognitoObserver);
        ((VerticalTabRailLayout) mNativeTabs).setDesktopWindowSpacerHost(null);
        clearCollections();
        mPreferences.unregisterOnSharedPreferenceChangeListener(mPreferenceListener);
        mRail.removeOnLayoutChangeListener(mLayoutListener);
        mMenuButtonWrapper.removeOnLayoutChangeListener(mLayoutListener);
        mNewTabRow.removeOnLayoutChangeListener(mLayoutListener);
        if (mColorDialog != null) mColorDialog.dismiss();
        if (mAboutDialog != null) mAboutDialog.dismiss();
        View locationBar = mLocationBarHost.findViewById(R.id.location_bar);
        if (locationBar instanceof LocationBarLayout) {
            ((LocationBarLayout) locationBar).setArcTopBar(false);
            ((LocationBarLayout) locationBar).setArcSurfaceColor(null);
        }
        restoreFrameGeometry();
        setArcToolbarCompositionActive(false);
        mIcons.destroy();
        mColumn.removeView(mNativeTabs);
        mRail.removeView(mColumn);
        mRail.addView(mNativeTabs, new ViewGroup.LayoutParams(-1, -1));
    }
}
