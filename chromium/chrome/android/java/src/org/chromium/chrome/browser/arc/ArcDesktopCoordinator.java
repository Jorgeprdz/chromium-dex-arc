// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.res.Configuration;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.text.Editable;
import android.text.TextWatcher;
import android.graphics.Outline;
import android.graphics.Path;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.text.InputType;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.GridLayout;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;

import org.chromium.chrome.R;
import org.chromium.chrome.browser.compositor.CompositorViewHolder;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
import org.chromium.components.browser_ui.widget.TouchEventObserver;
import org.chromium.components.favicon.LargeIconBridge;

import java.util.Locale;
import java.util.function.Consumer;
import java.util.function.Supplier;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tabmodel.TabCreator;
import org.chromium.chrome.browser.tabmodel.TabModel;
import org.chromium.chrome.browser.tabmodel.IncognitoStateProvider;
import org.chromium.chrome.browser.tabmodel.IncognitoStateProvider.IncognitoStateObserver;

import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinator;
import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListViewBinder;
import org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayout;
import org.chromium.chrome.browser.toolbar.top.ToolbarTablet;

/** Composes profile-owned Arc collections around Chromium's real vertical tab rail. */
public final class ArcDesktopCoordinator {
    private final Activity mActivity;
    private final ViewGroup mRail;
    private final View mNativeTabs;
    private final View mNativeNewTabButton;
    private final int mNativeNewTabOriginalVisibility;
    private final TextView mArcNewTabRow;
    private final LinearLayout mColumn;
    private final LinearLayout mHeader;
    private final LinearLayout mNavigationRow;
    private final LinearLayout mNavigationControls;
    private final View mMenuButtonWrapper;
    private final ViewGroup mMenuButtonOriginalParent;
    private final int mMenuButtonOriginalIndex;
    private final ViewGroup.LayoutParams mMenuButtonOriginalLayoutParams;
    private final View mExtensionsToolbarHost;
    private final ViewGroup mExtensionsToolbarOriginalParent;
    private final int mExtensionsToolbarOriginalIndex;
    private final ViewGroup.LayoutParams mExtensionsToolbarOriginalLayoutParams;
    private final int mExtensionsToolbarOriginalVisibility;
    private final View mCollapseButton;
    private final ViewGroup mCollapseButtonOriginalParent;
    private final int mCollapseButtonOriginalIndex;
    private final ViewGroup.LayoutParams mCollapseButtonOriginalLayoutParams;
    private final LinearLayout mHeaderActions;
    private final LinearLayout mFooter;
    private final Button mPasswordButton;
    private final View mLocationBarHost;
    private final ViewGroup mLocationBarOriginalParent;
    private final int mLocationBarOriginalIndex;
    private final ViewGroup.LayoutParams mLocationBarOriginalLayoutParams;
    private final CompositorViewHolder mCompositorViewHolder;
    private final View mFrameRoot;
    private final Drawable mOriginalFrameBackground;
    private final ViewOutlineProvider mOriginalContentOutlineProvider;
    private final boolean mOriginalContentClipToOutline;
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
    private AlertDialog mColorDialog;
    // Async surface attach/detach may outlive ARC mode transitions. Never apply a stale frame.
    private int mFrameGeometryGeneration;
    private View mPendingFrameGeometryHost;
    private Runnable mPendingFrameGeometry;

    public ArcDesktopCoordinator(Activity activity, ViewGroup rail,
            Profile profile, Consumer<String> navigate,
            Runnable openBookmarks, Runnable openPasswordSettings,
            boolean localPasswordsEnabled, IncognitoStateProvider incognitoStateProvider,
            VerticalTabListCoordinator nativeTabListCoordinator,
            CompositorViewHolder compositorViewHolder, Supplier<Integer> reservedLeftWidth,
            Consumer<Boolean> setToolbarSuppressed, Supplier<TabModel> currentModel,
            Supplier<TabCreator> currentCreator, Supplier<Tab> currentTab) {
        mActivity = activity;
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
        mIncognitoObserver = incognito -> { if (!mDestroyed) { rebindCollections(); applyAppearance(); } };
        mIcons = new LargeIconBridge(profile);
        mPreferences = ArcDesktopAppearance.preferences(activity);
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
        View nativeNewTabButton = nativeTabs.findViewById(R.id.new_tab_button);
        if (nativeNewTabButton == null) {
            throw new IllegalStateException("Arc requires Chromium's real new-tab button");
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
        mNativeNewTabButton = nativeNewTabButton;
        mNativeNewTabOriginalVisibility = nativeNewTabButton.getVisibility();
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
        mLocationBarOriginalParent = (ViewGroup) mLocationBarHost.getParent();
        mLocationBarOriginalIndex = mLocationBarOriginalParent.indexOfChild(mLocationBarHost);
        mLocationBarOriginalLayoutParams = mLocationBarHost.getLayoutParams();

        rail.removeView(mNativeTabs);
        mColumn = column();
        View captionSpacer = new View(activity);
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
        mNavigationControls.addView(
                navigationButton(
                        R.drawable.btn_back,
                        R.string.accessibility_toolbar_btn_back,
                        tab -> {
                            if (tab.canGoBack()) tab.goBack();
                        }));
        mNavigationControls.addView(
                navigationButton(
                        R.drawable.btn_forward,
                        R.string.accessibility_toolbar_btn_forward,
                        tab -> {
                            if (tab.canGoForward()) tab.goForward();
                        }));
        mNavigationControls.addView(
                navigationButton(
                        R.drawable.btn_reload_stop,
                        R.string.accessibility_btn_refresh,
                        Tab::reload));
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
        mHeaderActions.setGravity(Gravity.CENTER_VERTICAL);
        Button bookmarksButton = button(activity.getString(R.string.arc_bookmarks), openBookmarks);
        Button googleButton = button("Google", () -> {});
        googleButton.setOnClickListener(v -> showGoogleMenu(v));
        Button appearanceButton = button("●", this::showColorPicker);
        appearanceButton.setContentDescription(activity.getString(R.string.arc_frame_color));
        for (Button action : new Button[] {bookmarksButton, googleButton, appearanceButton}) {
            mHeaderActions.addView(
                    action,
                    new LinearLayout.LayoutParams(
                            0, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP), 1));
        }
        mHeader.addView(mHeaderActions);
        mColumn.addView(mHeader);
        // This visual row delegates to Chromium's one native tab-opening action.
        mArcNewTabRow = new TextView(activity);
        mArcNewTabRow.setText("+  " + activity.getString(R.string.arc_new_tab));
        mArcNewTabRow.setContentDescription(activity.getString(R.string.arc_new_tab));
        mArcNewTabRow.setTooltipText(activity.getString(R.string.arc_new_tab));
        mArcNewTabRow.setTextSize(13);
        mArcNewTabRow.setSingleLine(true);
        mArcNewTabRow.setEllipsize(TextUtils.TruncateAt.END);
        mArcNewTabRow.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        mArcNewTabRow.setPadding(dp(16), 0, dp(12), 0);
        mArcNewTabRow.setFocusable(true);
        mArcNewTabRow.setClickable(true);
        mArcNewTabRow.setOnClickListener(v -> mNativeNewTabButton.performClick());
        mColumn.addView(mArcNewTabRow, new LinearLayout.LayoutParams(-1, dp(44)));
        mColumn.addView(mNativeTabs, new LinearLayout.LayoutParams(-1, 0, 1));

        mFooter = new LinearLayout(activity);
        mFooter.setGravity(Gravity.CENTER_VERTICAL);
        mPasswordButton = button(localPasswordsEnabled ? "Passwords" : "Autofill",
                openPasswordSettings);
        mPasswordButton.setContentDescription(
                localPasswordsEnabled ? "Local passwords" : "Autofill settings");
        // VerticalTabRailLayout already owns Chromium's real new-tab button and handler. Keep it
        // as the single new-tab action instead of adding a second Arc handler here.
        mFooter.addView(
                mPasswordButton,
                new LinearLayout.LayoutParams(
                        0, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP), 1));
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
                        // On API 33+ clip the internal lower-left seam square. Older Android
                        // compositor outlines do not reliably clip asymmetric paths, so retain
                        // a supported round-rect instead of risking unmasked website content.
                        float radius = Math.min(dp(ArcDesktopPolicy.ARC_CONTENT_RADIUS_DP),
                                Math.min((view.getWidth() - left) / 2f, view.getHeight() / 2f));
                        if (android.os.Build.VERSION.SDK_INT >= 33) {
                            Path path = new Path();
                            path.addRoundRect(left, 0, view.getWidth(), view.getHeight(),
                                    new float[] {radius, radius, radius, radius,
                                            radius, radius, 0f, 0f}, Path.Direction.CW);
                            outline.setPath(path);
                        } else {
                            outline.setRoundRect(left, 0, view.getWidth(), view.getHeight(), radius);
                        }
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
                            postCurrentFrameGeometry(view);
                        }
                    }

                    @Override
                    public void onViewDetachedFromWindow(View view) {
                        if (!mDestroyed && mArcFrameActive) {
                            postCurrentFrameGeometry(mCompositorViewHolder);
                        }
                    }
                };
        mCompositorViewHolder.addTouchEventObserver(mArcTouchEventObserver);
        mContentLayoutListener =
                (v, l, t, r, b, ol, ot, or, ob) -> {
                    if (mArcFrameActive) applyFrameGeometry();
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
            } else if (ArcDesktopAppearance.UI_MODE_KEY.equals(key)) {
                // AUTO/ARC/MOBILE can change while this coordinator still exists. Re-evaluate the
                // shell synchronously so ToolbarTablet is never left suppressed in MOBILE.
                refreshNativeRows(mNativeTabs);
                applyAppearance();
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

    private ImageButton navigationButton(
            int drawableRes, int contentDescriptionRes, Consumer<Tab> action) {
        ImageButton button = new ImageButton(mActivity);
        button.setImageResource(drawableRes);
        button.setContentDescription(mActivity.getString(contentDescriptionRes));
        button.setMinimumWidth(0);
        button.setMinimumHeight(0);
        button.setPadding(dp(10), dp(8), dp(10), dp(8));
        button.setOnClickListener(
                v -> {
                    Tab tab = mCurrentTab.get();
                    if (tab != null) action.accept(tab);
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

    /** Opaque window-color fallback until native desktop backdrop blur is verified on DeX. */
    private void showColorPicker() {
        if (mDestroyed || (mColorDialog != null && mColorDialog.isShowing())) return;

        int selected = mPreferences.getInt(
                ArcDesktopAppearance.COLOR_KEY, ArcDesktopAppearance.DEFAULT_COLOR);
        LinearLayout content = new LinearLayout(mActivity);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(20), dp(8), dp(20), dp(12));

        TextView presetTitle = new TextView(mActivity);
        presetTitle.setText(R.string.arc_frame_color_presets);
        content.addView(presetTitle);

        EditText input = new EditText(mActivity);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        input.setSingleLine(true);
        input.setText(String.format(Locale.ROOT, "#%06X", selected & 0xffffff));
        input.setSelectAllOnFocus(true);
        input.setContentDescription(mActivity.getString(R.string.arc_frame_color_custom));

        GridLayout palette = new GridLayout(mActivity);
        palette.setColumnCount(4);
        int[] presetColors = ArcDesktopAppearance.FRAME_COLOR_PRESETS;
        View[] swatches = new View[presetColors.length];
        GradientDrawable[] swatchBackgrounds = new GradientDrawable[presetColors.length];
        String[] presetNames = mActivity.getResources().getStringArray(
                R.array.arc_frame_palette_names);
        for (int i = 0; i < presetColors.length; i++) {
            final int color = presetColors[i];
            View swatch = new View(mActivity);
            swatch.setFocusable(true);
            swatch.setClickable(true);
            swatch.setContentDescription(presetNames[i]);
            GradientDrawable circle = new GradientDrawable();
            circle.setShape(GradientDrawable.OVAL);
            circle.setColor(color);
            circle.setStroke(dp(2), 0xff808080);
            swatch.setBackground(circle);
            swatches[i] = swatch;
            swatchBackgrounds[i] = circle;
            swatch.setOnClickListener(v -> {
                input.setText(String.format(Locale.ROOT, "#%06X", color & 0xffffff));
                input.setSelection(input.length());
            });
            GridLayout.LayoutParams tile = new GridLayout.LayoutParams();
            tile.width = dp(44);
            tile.height = dp(44);
            tile.setMargins(dp(4), dp(4), dp(4), dp(4));
            palette.addView(swatch, tile);
        }
        content.addView(palette);

        TextView customLabel = new TextView(mActivity);
        customLabel.setText(R.string.arc_frame_color_custom);
        LinearLayout.LayoutParams labelParams = new LinearLayout.LayoutParams(-1, -2);
        labelParams.topMargin = dp(12);
        content.addView(customLabel, labelParams);
        content.addView(input, new LinearLayout.LayoutParams(-1, dp(48)));

        TextView preview = new TextView(mActivity);
        preview.setText(R.string.arc_frame_color_preview);
        preview.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams previewParams = new LinearLayout.LayoutParams(-1, dp(42));
        previewParams.topMargin = dp(8);
        content.addView(preview, previewParams);

        TextView rgbLabel = new TextView(mActivity);
        rgbLabel.setText(R.string.arc_frame_color_rgb);
        LinearLayout.LayoutParams rgbLabelParams = new LinearLayout.LayoutParams(-1, -2);
        rgbLabelParams.topMargin = dp(12);
        content.addView(rgbLabel, rgbLabelParams);
        SeekBar[] channels = new SeekBar[3];
        String[] channelNames = mActivity.getResources().getStringArray(
                R.array.arc_frame_rgb_names);
        int[] shifts = {16, 8, 0};
        for (int i = 0; i < channels.length; i++) {
            LinearLayout row = new LinearLayout(mActivity);
            row.setGravity(Gravity.CENTER_VERTICAL);
            TextView title = new TextView(mActivity);
            title.setText(channelNames[i]);
            row.addView(title, new LinearLayout.LayoutParams(dp(44), -2));
            SeekBar slider = new SeekBar(mActivity);
            slider.setMax(255);
            slider.setProgress((selected >>> shifts[i]) & 255);
            slider.setContentDescription(channelNames[i]);
            channels[i] = slider;
            row.addView(slider, new LinearLayout.LayoutParams(0, dp(42), 1f));
            content.addView(row);
        }

        for (SeekBar slider : channels) {
            slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                @Override
                public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                    if (!fromUser) return;
                    int chosen = Color.rgb(channels[0].getProgress(),
                            channels[1].getProgress(), channels[2].getProgress());
                    input.setText(String.format(Locale.ROOT, "#%06X", chosen & 0xffffff));
                    input.setSelection(input.length());
                }
                @Override public void onStartTrackingTouch(SeekBar seekBar) {}
                @Override public void onStopTrackingTouch(SeekBar seekBar) {}
            });
        }
        input.addTextChangedListener(new TextWatcher() {
            @Override
            public void afterTextChanged(Editable value) {
                String hex = value.toString().trim();
                if (!hex.matches("#[0-9a-fA-F]{6}")) {
                    updatePresetSelection(swatches, swatchBackgrounds, presetColors, -1);
                    preview.setText(R.string.arc_color_format);
                    preview.setBackgroundColor(Color.TRANSPARENT);
                    return;
                }
                int chosen = Color.parseColor(hex);
                updatePresetSelection(swatches, swatchBackgrounds, presetColors, chosen);
                for (int i = 0; i < channels.length; i++) {
                    channels[i].setProgress((chosen >>> shifts[i]) & 255);
                }
                updateFrameColorPreview(preview, chosen);
            }
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
        });
        updatePresetSelection(swatches, swatchBackgrounds, presetColors, selected);
        updateFrameColorPreview(preview, selected);

        ScrollView scroll = new ScrollView(mActivity);
        scroll.setFillViewport(false);
        scroll.addView(content);

        AlertDialog dialog = new AlertDialog.Builder(mActivity)
                .setTitle(R.string.arc_frame_color)
                .setView(scroll)
                .setPositiveButton(android.R.string.ok, null)
                .setNegativeButton(android.R.string.cancel, null)
                .setNeutralButton(R.string.arc_reset_color, (d, which) ->
                        mPreferences.edit().remove(ArcDesktopAppearance.COLOR_KEY).apply())
                .create();
        mColorDialog = dialog;
        dialog.setOnDismissListener(d -> {
            if (mColorDialog == dialog) mColorDialog = null;
        });
        dialog.setOnShowListener(d -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(v -> {
                    String hex = input.getText().toString().trim();
                    if (!hex.matches("#[0-9a-fA-F]{6}")) {
                        input.setError(mActivity.getString(R.string.arc_color_format));
                        return;
                    }
                    // Cancel does not mutate the persisted window color.
                    mPreferences.edit().putInt(ArcDesktopAppearance.COLOR_KEY,
                            Color.parseColor(hex)).apply();
                    dialog.dismiss();
                }));
        dialog.show();
    }

    /** A selected swatch has a visible high-contrast ring and Android's selected state. */
    private void updatePresetSelection(View[] swatches, GradientDrawable[] backgrounds,
            int[] presets, int chosen) {
        for (int i = 0; i < presets.length; i++) {
            boolean selected = chosen == presets[i];
            swatches[i].setSelected(selected);
            backgrounds[i].setStroke(dp(selected ? 3 : 2),
                    selected ? ArcDesktopPolicy.foreground(presets[i]) : 0xff808080);
            swatches[i].invalidate();
        }
    }

    /** Preview the actual opaque frame surface instead of the raw seed color. */
    private void updateFrameColorPreview(TextView preview, int seed) {
        boolean dark = mIncognitoStateProvider.isIncognitoSelected()
                || (mActivity.getResources().getConfiguration().uiMode
                        & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
        int surface = ArcDesktopPolicy.surface(seed, dark);
        GradientDrawable background = new GradientDrawable();
        background.setColor(surface);
        background.setCornerRadius(dp(10));
        preview.setBackground(background);
        preview.setTextColor(ArcDesktopPolicy.foreground(surface));
        preview.setText(R.string.arc_frame_color_preview);
    }

    private LinearLayout.LayoutParams arcLocationBarLayoutParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                -1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP));
        params.setMarginStart(dp(ArcDesktopPolicy.ARC_LOCATION_BAR_SIDE_MARGIN_DP));
        params.setMarginEnd(dp(ArcDesktopPolicy.ARC_LOCATION_BAR_SIDE_MARGIN_DP));
        return params;
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
        boolean desktop = ArcDesktopAppearance.isDesktopWindow(mActivity);
        boolean incognito = mIncognitoStateProvider.isIncognitoSelected();
        setArcToolbarCompositionActive(desktop);
        if (mNativeTabs instanceof VerticalTabRailLayout) {
            // This binder restores upstream colors/tints too when ARC is no longer active.
            VerticalTabListViewBinder.refreshArcAppearance(
                    (VerticalTabRailLayout) mNativeTabs, incognito);
        }
        if (!desktop) {
            mHeader.setVisibility(View.GONE);
            mArcNewTabRow.setVisibility(View.GONE);
            mNativeNewTabButton.setVisibility(mNativeNewTabOriginalVisibility);
            mFooter.setVisibility(View.GONE);
            if (mCollectionsView != null) mCollectionsView.setVisibility(View.GONE);
            mColumn.setBackgroundColor(Color.TRANSPARENT);
            clearFrameGeometry();
            return;
        }

        float density = mActivity.getResources().getDisplayMetrics().density;
        // Caption height is supplied by the native desktop rail. Reserve native-tab space
        // before showing secondary collection controls; never resize the rail width.
        View captionSpacer = mColumn.getChildAt(0);
        int captionHeight = captionSpacer == null || captionSpacer.getLayoutParams() == null
                ? 0 : Math.max(0, captionSpacer.getLayoutParams().height);
        int collectionBudget = ArcDesktopPolicy.collectionScrollBudgetPx(
                mRail.getHeight(), density, captionHeight);
        boolean expanded = ArcDesktopPolicy.showFullControls(
                mRail.getWidth(), mRail.getHeight(), density)
                && collectionBudget >= dp(ArcDesktopPolicy.ARC_MIN_COLLECTION_SCROLL_DP);
        // Keep the real Chromium LocationBar visible even in collapsed mode so keyboard/focus
        // paths never target a GONE omnibox. Secondary Arc controls are restored on expansion.
        mHeader.setVisibility(View.VISIBLE);
        mNativeNewTabButton.setVisibility(View.GONE);
        mArcNewTabRow.setVisibility(View.VISIBLE);
        mArcNewTabRow.setText(expanded
                ? "+  " + mActivity.getString(R.string.arc_new_tab) : "+");
        mArcNewTabRow.setGravity((expanded ? Gravity.START : Gravity.CENTER_HORIZONTAL)
                | Gravity.CENTER_VERTICAL);
        mNavigationRow.setVisibility(View.VISIBLE);
        mNavigationControls.setVisibility(expanded ? View.VISIBLE : View.GONE);
        mHeaderActions.setVisibility(expanded ? View.VISIBLE : View.GONE);
        // The native app menu remains reachable while collapsed. Secondary footer actions can
        // disappear so the compact rail does not retain expanded hitboxes.
        mFooter.setVisibility(View.VISIBLE);
        mPasswordButton.setVisibility(expanded ? View.VISIBLE : View.GONE);
        if (mExtensionsToolbarHost != null) {
            mExtensionsToolbarHost.setVisibility(expanded ? mExtensionsToolbarOriginalVisibility : View.GONE);
        }
        if (mCollectionsView != null) {
            mCollectionsView.setVisibility(expanded ? View.VISIBLE : View.GONE);
        }
        applyFrameGeometry();
        if (expanded && mCollectionsView != null) {
            mCollectionsView.setCollectionHeight(collectionBudget);
        }
        // Leave native tab selection, incognito and favicon rendering to its binders.
        int surface = ArcDesktopAppearance.surface(mActivity, incognito);
        int foreground = ArcDesktopPolicy.foreground(surface);
        mColumn.setBackgroundColor(surface);
        mArcNewTabRow.setTextColor(foreground);
        mArcNewTabRow.setBackground(arcButtonStates(
                ArcDesktopPolicy.selection(surface), foreground));
        tintHeader(mHeader, foreground, ArcDesktopPolicy.selection(surface));
        tintHeader(mFooter, foreground, ArcDesktopPolicy.selection(surface));
    }

    private int reservedLeftWidth() {
        Integer width = mReservedLeftWidth.get();
        return Math.max(0, width == null ? 0 : width);
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
        int left = reservedLeftWidth();
        int right = mCompositorViewHolder.getWidth();
        int bottom = mCompositorViewHolder.getHeight();
        float radius = dp(ArcDesktopPolicy.ARC_CONTENT_RADIUS_DP);
        if (android.os.Build.VERSION.SDK_INT < 33) {
            return ArcDesktopPolicy.containsRoundedRectPoint(
                    x, y, left, 0, right, bottom, radius);
        }
        return ArcDesktopPolicy.containsArcViewportPoint(x, y, left, 0, right, bottom, radius);
    }

    private void restoreClippedSurface() {
        if (mClippedSurface == null) return;
        mClippedSurface.removeOnAttachStateChangeListener(mSurfaceAttachStateListener);
        mClippedSurface.setOutlineProvider(mClippedSurfaceOriginalOutlineProvider);
        mClippedSurface.setClipToOutline(mClippedSurfaceOriginalClipToOutline);
        mClippedSurface.invalidateOutline();
        mClippedSurface = null;
        mClippedSurfaceOriginalOutlineProvider = null;
    }

    private void applyActiveSurfaceClip() {
        View activeSurface = mCompositorViewHolder.getActiveSurfaceView();
        if (activeSurface == mClippedSurface) {
            if (activeSurface != null) activeSurface.invalidateOutline();
            return;
        }
        restoreClippedSurface();
        if (activeSurface == null) return;
        mClippedSurface = activeSurface;
        mClippedSurfaceOriginalOutlineProvider = activeSurface.getOutlineProvider();
        mClippedSurfaceOriginalClipToOutline = activeSurface.getClipToOutline();
        activeSurface.addOnAttachStateChangeListener(mSurfaceAttachStateListener);
        activeSurface.setOutlineProvider(mArcContentOutlineProvider);
        activeSurface.setClipToOutline(true);
        activeSurface.invalidateOutline();
    }

    private void invalidatePendingFrameGeometry() {
        mFrameGeometryGeneration++;
        if (mPendingFrameGeometryHost != null && mPendingFrameGeometry != null) {
            mPendingFrameGeometryHost.removeCallbacks(mPendingFrameGeometry);
        }
        mPendingFrameGeometryHost = null;
        mPendingFrameGeometry = null;
    }

    private void postCurrentFrameGeometry(View host) {
        if (mDestroyed || !mArcFrameActive
                || !ArcDesktopAppearance.isDesktopWindow(mActivity)) return;
        // This invalidates and cancels any previously queued host callback.
        invalidatePendingFrameGeometry();
        final int generation = mFrameGeometryGeneration;
        Runnable apply = () -> {
            if (generation != mFrameGeometryGeneration || mDestroyed || !mArcFrameActive
                    || !ArcDesktopAppearance.isDesktopWindow(mActivity)) return;
            mPendingFrameGeometryHost = null;
            mPendingFrameGeometry = null;
            applyFrameGeometry();
        };
        mPendingFrameGeometryHost = host;
        mPendingFrameGeometry = apply;
        host.post(apply);
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
        mCompositorViewHolder.invalidateOutline();
        applyActiveSurfaceClip();

        boolean incognito = mIncognitoStateProvider.isIncognitoSelected();
        int surface = ArcDesktopAppearance.surface(mActivity, incognito);
        if (mFrameRoot != null) mFrameRoot.setBackgroundColor(surface);
    }

    private void clearFrameGeometry() {
        // Cancels queued geometry even if ARC already left this coordinator inactive.
        invalidatePendingFrameGeometry();
        if (!mArcFrameActive) return;
        mArcFrameActive = false;
        mRejectingRoundedCornerGesture = false;
        restoreClippedSurface();
        mCompositorViewHolder.setOutlineProvider(mOriginalContentOutlineProvider);
        mCompositorViewHolder.setClipToOutline(mOriginalContentClipToOutline);
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
        if (mFrameRoot != null) mFrameRoot.setBackground(mOriginalFrameBackground);
    }

    private void restoreFrameGeometry() {
        clearFrameGeometry();
        mCompositorViewHolder.removeTouchEventObserver(mArcTouchEventObserver);
        mCompositorViewHolder.removeOnLayoutChangeListener(mContentLayoutListener);
    }

    private void restoreToolbarUtilityControls() {
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

    private GradientDrawable arcButtonShape(int fill, int foreground, boolean focusRing) {
        GradientDrawable background = new GradientDrawable();
        background.setColor(fill);
        background.setCornerRadius(dp(8));
        if (focusRing) background.setStroke(dp(2), foreground);
        return background;
    }

    /** State list instead of constant selection fill: keyboard/mouse/touch remain perceivable. */
    private StateListDrawable arcButtonStates(int selected, int foreground) {
        StateListDrawable states = new StateListDrawable();
        states.addState(new int[] {android.R.attr.state_pressed},
                arcButtonShape(selected, foreground, false));
        states.addState(new int[] {android.R.attr.state_focused},
                arcButtonShape(selected, foreground, true));
        states.addState(new int[] {android.R.attr.state_hovered},
                arcButtonShape(selected, foreground, false));
        states.addState(new int[] {},
                arcButtonShape(Color.TRANSPARENT, foreground, false));
        return states;
    }

    private void tintHeader(View view, int foreground, int selection) {
        // Native Chromium controls keep their own ripple, hover, accessibility and icon-tint
        // state. Arc only styles views that it owns.
        if (view == mLocationBarHost
                || view == mNavigationControls
                || view == mCollapseButton
                || view == mMenuButtonWrapper
                || view == mExtensionsToolbarHost) {
            return;
        }
        if (view instanceof TextView) ((TextView) view).setTextColor(foreground);
        if (view instanceof Button || view instanceof ImageButton) {
            view.setBackground(arcButtonStates(selection, foreground));
            // Favicons are content, not monochrome glyphs: retain each website's own colors.
            Object tag = view.getTag();
            boolean isEntry = tag instanceof String
                    && ((String) tag).startsWith("arc-entry:");
            if (view instanceof ImageButton && !isEntry) {
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
        restoreFrameGeometry();
        setArcToolbarCompositionActive(false);
        mIcons.destroy();
        mNativeNewTabButton.setVisibility(mNativeNewTabOriginalVisibility);
        mColumn.removeView(mNativeTabs);
        mRail.removeView(mColumn);
        mRail.addView(mNativeTabs, new ViewGroup.LayoutParams(-1, -1));
    }
}
