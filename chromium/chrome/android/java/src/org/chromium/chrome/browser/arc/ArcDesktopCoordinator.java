// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.text.TextUtils;
import android.transition.Transition;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.view.ViewGroup;
import android.view.SurfaceView;
import android.view.SurfaceHolder;
import android.view.ViewTreeObserver;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.PopupMenu;
import android.widget.ScrollView;
import android.widget.TextView;

import org.chromium.chrome.R;
import org.chromium.base.supplier.NullableObservableSupplier;
import org.chromium.chrome.browser.bookmarks.BookmarkManagerOpener;
import org.chromium.chrome.browser.bookmarks.BookmarkOpener;
import org.chromium.chrome.browser.compositor.CompositorViewHolder;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.ui.side_ui.SideUiStateProvider;
import org.chromium.chrome.browser.ui.side_ui.SideUiObserver;
import org.chromium.chrome.browser.ui.side_ui.SideUiCoordinator.SideUiSpecs;
import org.chromium.chrome.browser.ui.side_ui.SideUiCoordinator.AnchorSide;
import org.chromium.chrome.browser.ui.side_ui.SideUiCoordinator.UiUpdateRequest;
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
    private final int mOriginalNativeTabsPaddingLeft, mOriginalNativeTabsPaddingTop;
    private final int mOriginalNativeTabsPaddingRight, mOriginalNativeTabsPaddingBottom;
    private final LinearLayout mColumn;
    private final LinearLayout mHeader;
    private final ScrollView mHeaderScroll;
    private final View mCaptionSpacer;
    private final LinearLayout mNavigationRow;
    private final LinearLayout mNavigationControls;
    private final ArcNavigationState mNavigationState;
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
    private final ViewOutlineProvider mOriginalFrameOutlineProvider;
    private final boolean mOriginalFrameClipToOutline;
    private final ViewOutlineProvider mArcFrameOutlineProvider;
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
    private final SideUiStateProvider mSideUiStateProvider;
    private final SideUiObserver mSideUiObserver = new SideUiObserver() {
        @Override
        public Transition onPreSideUiSpecsChange(SideUiSpecs specs, UiUpdateRequest request) {
            return createArcViewportTransition(specs);
        }

        @Override
        public void onTransitionBegun(SideUiSpecs specs, UiUpdateRequest request) {
            beginArcViewportAnimation(specs);
        }

        @Override
        public void onTransitionEnded(SideUiSpecs specs, UiUpdateRequest request) {
            finishArcViewportAnimation();
            onSidebarGeometryChanged();
        }

        @Override
        public void onSideUiSpecsChanged(SideUiSpecs specs, UiUpdateRequest request) {
            finishArcViewportAnimation();
            onSidebarGeometryChanged();
        }
    };
    private final Consumer<Boolean> mSetToolbarSuppressed;
    private final LargeIconBridge mIcons;
    private final Consumer<String> mNavigate;
    private final IncognitoStateProvider mIncognitoStateProvider;
    private final IncognitoStateObserver mIncognitoObserver;
    private final SharedPreferences mPreferences;
    private final SharedPreferences.OnSharedPreferenceChangeListener mPreferenceListener;
    private final View.OnLayoutChangeListener mLayoutListener;
    private final View.OnLayoutChangeListener mColumnLayoutListener;
    private final View.OnLayoutChangeListener mHeaderLayoutListener;
    private final View.OnLayoutChangeListener mContentLayoutListener;
    private final ViewTreeObserver.OnGlobalLayoutListener mSurfaceLayoutListener;
    private final ViewOutlineProvider mArcContentOutlineProvider;
    private final TouchEventObserver mArcTouchEventObserver;
    private final View.OnAttachStateChangeListener mSurfaceAttachStateListener;
    private final Supplier<TabModel> mCurrentModel;
    private final Supplier<TabCreator> mCurrentCreator;
    private final NullableObservableSupplier<Tab> mCurrentTab;
    private final BookmarkOpener mBookmarkOpener;
    private final Supplier<BookmarkManagerOpener> mBookmarkManagerOpener;
    private final Runnable mUseAutomaticSidebarWidth;
    private final VerticalTabListCoordinator mNativeTabListCoordinator;
    private TabModel mSessionModel;
    private ArcNativeTabSession mTabSession;
    private ArcCollectionsController mCollections;
    private ArcCollectionsView mCollectionsView;
    private ArcNativeBookmarksBridge mNativeBookmarks;
    private boolean mDestroyed;
    private boolean mArcToolbarCompositionActive;
    private boolean mArcFrameActive;
    private boolean mArcViewportAnimationPending;
    private boolean mArcViewportAnimationActive;
    private int mArcVisualReservedLeftWidth = -1;
    private int mArcViewportAnimationGeneration;
    private boolean mRejectingRoundedCornerGesture;
    private View mClippedSurface;
    private ViewOutlineProvider mClippedSurfaceOriginalOutlineProvider;
    private boolean mClippedSurfaceOriginalClipToOutline;
    private Rect mClippedSurfaceOriginalClipBounds;
    private ArcDesktopPolicy.Geometry mFrameGeometry;
    private final Runnable mGeometryUpdate = () -> {
        if (!mDestroyed && mArcFrameActive && mArcToolbarCompositionActive) applyFrameGeometry();
    };
    private final SurfaceHolder.Callback mSurfaceCallback = new SurfaceHolder.Callback() {
        @Override public void surfaceCreated(SurfaceHolder holder) { mGeometryUpdate.run(); }
        @Override public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
            mGeometryUpdate.run();
        }
        @Override public void surfaceDestroyed(SurfaceHolder holder) {
            if (!mDestroyed) mCompositorViewHolder.post(mGeometryUpdate);
        }
    };
    private AlertDialog mColorDialog;
    private PopupMenu mNavigationMenu;
    private int mLastNativeRowHeight = -1;

    public ArcDesktopCoordinator(Activity activity, ViewGroup rail,
            Profile profile, Consumer<String> navigate,
            Runnable openBookmarks, Runnable openPasswordSettings,
            boolean localPasswordsEnabled, IncognitoStateProvider incognitoStateProvider,
            VerticalTabListCoordinator nativeTabListCoordinator,
            CompositorViewHolder compositorViewHolder, SideUiStateProvider sideUiStateProvider,
            Supplier<Integer> reservedLeftWidth,
            Consumer<Boolean> setToolbarSuppressed, Supplier<TabModel> currentModel,
            Supplier<TabCreator> currentCreator, NullableObservableSupplier<Tab> currentTab,
            BookmarkOpener bookmarkOpener, Supplier<BookmarkManagerOpener> bookmarkManagerOpener,
            Runnable useAutomaticSidebarWidth) {
        mActivity = activity;
        mRail = rail;
        mNavigate = navigate;
        mIncognitoStateProvider = incognitoStateProvider;
        mNativeTabListCoordinator = nativeTabListCoordinator;
        mCompositorViewHolder = compositorViewHolder;
        mReservedLeftWidth = reservedLeftWidth;
        mSideUiStateProvider = sideUiStateProvider;
        mSetToolbarSuppressed = setToolbarSuppressed;
        mCurrentModel = currentModel;
        mCurrentCreator = currentCreator;
        mCurrentTab = currentTab;
        mBookmarkOpener = bookmarkOpener;
        mBookmarkManagerOpener = bookmarkManagerOpener;
        mUseAutomaticSidebarWidth = useAutomaticSidebarWidth;
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
        mOriginalFrameOutlineProvider = mFrameRoot == null ? null : mFrameRoot.getOutlineProvider();
        mOriginalFrameClipToOutline = mFrameRoot != null && mFrameRoot.getClipToOutline();
        mArcFrameOutlineProvider = new ViewOutlineProvider() {
            @Override public void getOutline(View view, Outline outline) {
                outline.setRoundRect(0, 0, view.getWidth(), view.getHeight(),
                        currentFrameGeometry().outerRadius);
            }
        };
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
        mOriginalNativeTabsPaddingLeft = nativeTabs.getPaddingLeft();
        mOriginalNativeTabsPaddingTop = nativeTabs.getPaddingTop();
        mOriginalNativeTabsPaddingRight = nativeTabs.getPaddingRight();
        mOriginalNativeTabsPaddingBottom = nativeTabs.getPaddingBottom();
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
        mCaptionSpacer = new View(activity);
        mColumn.addView(mCaptionSpacer, new LinearLayout.LayoutParams(
                -1, nativeSpacer.getLayoutParams().height));
        ((VerticalTabRailLayout) mNativeTabs).setDesktopWindowSpacerHost(mCaptionSpacer);
        mHeader = column();
        mHeaderScroll = new ScrollView(activity);
        mHeaderScroll.setVerticalScrollBarEnabled(false);
        mHeaderScroll.addView(mHeader);
        // Keep native navigation reachable when only the 52dp rail or a narrow allocation fits.
        mCollapseButton.setTooltipText(activity.getString(R.string.arc_navigation_hint));
        mCollapseButton.setOnLongClickListener(view -> { showNavigationMenu(view); return true; });

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
        mNavigationState = new ArcNavigationState(mCurrentTab,
                (ImageButton) mNavigationControls.getChildAt(0),
                (ImageButton) mNavigationControls.getChildAt(1),
                (ImageButton) mNavigationControls.getChildAt(2));
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
        locationBarParams.setMarginStart(currentFrameGeometry().sideInset);
        locationBarParams.setMarginEnd(currentFrameGeometry().sideInset);
        mHeader.addView(mLocationBarHost, locationBarParams);

        mHeaderActions = new LinearLayout(activity);
        Button bookmarksButton = button(activity.getString(R.string.arc_bookmarks), openBookmarks);
        Button googleButton = button("Google", () -> {});
        googleButton.setOnClickListener(v -> showGoogleMenu(v));
        Button appearanceButton = button("●", () -> {});
        appearanceButton.setOnClickListener(this::showAppearanceMenu);
        appearanceButton.setContentDescription(activity.getString(R.string.arc_frame_color));
        for (Button action : new Button[] {bookmarksButton, googleButton, appearanceButton}) {
            mHeaderActions.addView(
                    action,
                    new LinearLayout.LayoutParams(
                            0, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP), 1));
        }
        mHeader.addView(mHeaderActions);
        mColumn.addView(mHeaderScroll);
        mColumn.addView(mNativeTabs, new LinearLayout.LayoutParams(-1, 0, 1));

        // VerticalTabRailLayout already owns Chromium's real new-tab button and handler. Keep it
        // as the single new-tab action instead of adding a second Arc handler here.
        mFooter = new LinearLayout(activity);
        // arc-media does not expose local passwords. Do not substitute an unrelated Autofill
        // settings action; Chromium's real menu and extensions remain available below.
        mPasswordButton = localPasswordsEnabled ? button("Passwords", openPasswordSettings) : null;
        if (mPasswordButton != null) {
            mPasswordButton.setContentDescription("Local passwords");
            mFooter.addView(mPasswordButton, new LinearLayout.LayoutParams(
                    0, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP), 1));
        }
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
                        Rect bounds = arcClipBoundsForView(view);
                        if (bounds.isEmpty()) {
                            outline.setEmpty();
                            return;
                        }
                        outline.setRoundRect(bounds, currentFrameGeometry().viewportRadius);
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
                            view.post(mGeometryUpdate);
                        }
                    }

                    @Override
                    public void onViewDetachedFromWindow(View view) {
                        if (!mDestroyed && mArcFrameActive) {
                            mCompositorViewHolder.post(mGeometryUpdate);
                        }
                    }
                };
        mCompositorViewHolder.addTouchEventObserver(mArcTouchEventObserver);
        mContentLayoutListener =
                (v, l, t, r, b, ol, ot, or, ob) -> {
                    if (mArcFrameActive) applyFrameGeometry();
                };
        mCompositorViewHolder.addOnLayoutChangeListener(mContentLayoutListener);
        // Global layout catches a same-size replacement of the active compositor SurfaceView.
        // This is a layout event, not a frame callback or permanent polling loop.
        mSurfaceLayoutListener = () -> {
            if (!mDestroyed && mArcFrameActive) applyActiveSurfaceClip();
        };
        mCompositorViewHolder.getViewTreeObserver().addOnGlobalLayoutListener(mSurfaceLayoutListener);

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
        mLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> {
            if (r - l != or - ol || b - t != ob - ot) onSidebarGeometryChanged();
        };
        rail.addOnLayoutChangeListener(mLayoutListener);
        // The rail may be laid out before its child. Re-evaluate actual available width.
        mColumnLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> {
            if (r - l != or - ol || b - t != ob - ot) onSidebarGeometryChanged();
        };
        mColumn.addOnLayoutChangeListener(mColumnLayoutListener);
        mHeaderLayoutListener = (v, l, t, r, b, ol, ot, or, ob) -> {
            if (!mDestroyed && mArcToolbarCompositionActive) applySidebarGeometry();
        };
        mHeader.addOnLayoutChangeListener(mHeaderLayoutListener);
        mCaptionSpacer.addOnLayoutChangeListener(mHeaderLayoutListener);
        mIncognitoStateProvider.addIncognitoStateObserverAndTrigger(mIncognitoObserver);
        applyAppearance();
        mSideUiStateProvider.addObserver(mSideUiObserver);
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
        button.setTextSize(ArcDesktopPolicy.ARC_TAB_TEXT_SIZE_SP);
        button.setSingleLine(true);
        button.setEllipsize(TextUtils.TruncateAt.END);
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
        if (mNativeBookmarks != null) mNativeBookmarks.destroy();
        mNativeBookmarks = null;
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
                        if (!mDestroyed && mTabSession == session && mCurrentModel.get() == model) {
                            ArcCollectionsView.applyFavoriteIcon(
                                    button, new org.chromium.url.GURL(entry.url), icon, color);
                        }
                    });
        });
        // Native model loading can invoke the bridge callback synchronously. Attach first so
        // that geometry always sees real LayoutParams, including during private-model switches.
        mHeader.addView(mCollectionsView, 2);
        // BookmarkModel redirects private profiles to the shared original-profile model. The
        // bridge retains this session's profile so native opening still respects incognito.
        mNativeBookmarks = new ArcNativeBookmarksBridge(mActivity, model.getProfile(),
                () -> !mDestroyed && mTabSession == session && mCurrentModel.get() == model,
                mBookmarkOpener, mBookmarkManagerOpener, mCurrentTab, items -> {
                    if (!mDestroyed && mTabSession == session && mCollectionsView != null) {
                        mCollectionsView.refresh();
                        if (mArcToolbarCompositionActive) applySidebarGeometry();
                    }
                });
        mCollectionsView.setNativeBookmarks(mNativeBookmarks, (item, button) -> {
            if (model.getProfile().isOffTheRecord() || item.isFolder()) return;
            mIcons.getLargeIconForUrl(item.getUrl(), dp(24), (icon, color, fallback, type) -> {
                if (!mDestroyed && mTabSession == session && mCurrentModel.get() == model) {
                    ArcCollectionsView.applyFavoriteIcon(button, item.getUrl(), icon, color);
                }
            });
        });
    }

    private void showNavigationMenu(View anchor) {
        if (mDestroyed) return;
        if (mNavigationMenu != null) mNavigationMenu.dismiss();
        mNavigationMenu = new PopupMenu(mActivity, anchor);
        Tab tab = mCurrentTab.get();
        mNavigationMenu.getMenu().add(0, 0, 0, R.string.accessibility_toolbar_btn_back)
                .setEnabled(tab != null && tab.canGoBack());
        mNavigationMenu.getMenu().add(0, 1, 1, R.string.accessibility_toolbar_btn_forward)
                .setEnabled(tab != null && tab.canGoForward());
        mNavigationMenu.getMenu().add(0, 2, 2, tab != null && tab.isLoading()
                ? R.string.accessibility_btn_stop_loading : R.string.accessibility_btn_refresh);
        mNavigationMenu.setOnMenuItemClickListener(item -> {
            Tab current = mCurrentTab.get();
            if (mDestroyed || current == null) return false;
            if (item.getItemId() == 0 && current.canGoBack()) current.goBack();
            else if (item.getItemId() == 1 && current.canGoForward()) current.goForward();
            else if (item.getItemId() == 2) {
                if (current.isLoading()) current.stopLoading();
                else current.reload();
            }
            return true;
        });
        mNavigationMenu.show();
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

    private void showAppearanceMenu(View anchor) {
        if (mDestroyed) return;
        if (mNavigationMenu != null) mNavigationMenu.dismiss();
        mNavigationMenu = new PopupMenu(mActivity, anchor);
        mNavigationMenu.getMenu().add(0, 0, 0, R.string.arc_warm_color);
        mNavigationMenu.getMenu().add(0, 1, 1, R.string.arc_custom_color);
        mNavigationMenu.getMenu().add(0, 2, 2, R.string.arc_reset_color);
        mNavigationMenu.getMenu().add(0, 3, 3, R.string.arc_automatic_sidebar_width);
        mNavigationMenu.setOnMenuItemClickListener(item -> {
            if (mDestroyed) return false;
            if (item.getItemId() == 0) {
                mPreferences.edit().putInt(ArcDesktopAppearance.COLOR_KEY,
                        ArcDesktopAppearance.WARM_COLOR).apply();
            } else if (item.getItemId() == 1) {
                showColorPicker();
            } else if (item.getItemId() == 2) {
                mPreferences.edit().remove(ArcDesktopAppearance.COLOR_KEY).apply();
            } else {
                mUseAutomaticSidebarWidth.run();
            }
            return true;
        });
        mNavigationMenu.show();
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

    private LinearLayout.LayoutParams arcLocationBarLayoutParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                -1, dp(ArcDesktopPolicy.ARC_NAV_ROW_HEIGHT_DP));
        params.setMarginStart(currentFrameGeometry().sideInset);
        params.setMarginEnd(currentFrameGeometry().sideInset);
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
        mCollapseButton.setTooltipText(mActivity.getString(R.string.arc_navigation_hint));
        mCollapseButton.setOnLongClickListener(view -> { showNavigationMenu(view); return true; });
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
        View urlText = mLocationBarHost.findViewById(R.id.url_bar);
        if (urlText instanceof TextView) {
            // The shared 14sp text policy snapshots the original native size and restores it
            // in MOBILE. It changes presentation without changing the UrlBar/editing model.
            ArcDesktopAppearance.applyTabTextSize((TextView) urlText);
        }
        mNavigationState.setActive(desktop);
        if (mNativeTabs instanceof VerticalTabRailLayout) {
            // This binder restores upstream colors/tints too when ARC is no longer active.
            VerticalTabListViewBinder.refreshArcAppearance(
                    (VerticalTabRailLayout) mNativeTabs, incognito);
        }
        if (!desktop) {
            ((VerticalTabRailLayout) mNativeTabs).setArcAvailableTabHeight(0, false);
            mNativeTabs.setPadding(mOriginalNativeTabsPaddingLeft, mOriginalNativeTabsPaddingTop,
                    mOriginalNativeTabsPaddingRight, mOriginalNativeTabsPaddingBottom);
            mHeader.setVisibility(View.GONE);
            mHeaderScroll.setVisibility(View.GONE);
            mFooter.setVisibility(View.GONE);
            if (mCollectionsView != null) mCollectionsView.setVisibility(View.GONE);
            mColumn.setBackgroundColor(Color.TRANSPARENT);
            clearFrameGeometry();
            return;
        }

        updateSidebarControls();
        // Leave native tab selection, incognito and favicon rendering to its binders.
        int foreground = ArcDesktopAppearance.foreground(mActivity, incognito);
        // The native SideUi anchor has an opaque theme background. Paint this full-height column
        // once so its children share a continuous gradient instead of restarting each section.
        ArcDesktopAppearance.applySidebarBackground(mColumn, incognito);
        tintHeader(mHeader, foreground, ArcDesktopAppearance.selection(mActivity, incognito));
        tintHeader(mFooter, foreground, ArcDesktopAppearance.selection(mActivity, incognito));
    }

    /** Keep palette and collection refreshes out of animated width/resize callbacks. */
    private void onSidebarGeometryChanged() {
        if (mDestroyed || !mArcToolbarCompositionActive) return;
        updateSidebarControls();
    }

    private void updateSidebarControls() {
        // mColumn has the actual allocated width after rail padding and split-window resize.
        final int availableWidthPx = mColumn.getWidth();
        final int availableHeightPx = mColumn.getHeight();
        final float density = mActivity.getResources().getDisplayMetrics().density;
        ArcDesktopPolicy.Geometry geometry = currentFrameGeometry();
        boolean navigationVisible = ArcDesktopPolicy.showNavigationControls(
                availableWidthPx - geometry.sideInset * 2, density);
        boolean expanded = ArcDesktopPolicy.showFullControls(
                availableWidthPx, availableHeightPx, density);
        // Keep the real Chromium LocationBar visible even in collapsed mode so keyboard/focus
        // paths never target a GONE omnibox. Secondary Arc controls are restored on expansion.
        mHeader.setVisibility(View.VISIBLE);
        mHeaderScroll.setVisibility(View.VISIBLE);
        mNavigationRow.setVisibility(View.VISIBLE);
        mNavigationControls.setVisibility(navigationVisible ? View.VISIBLE : View.GONE);
        mHeaderActions.setVisibility(expanded ? View.VISIBLE : View.GONE);
        // The native app menu remains reachable while collapsed. Secondary footer actions can
        // disappear so the compact rail does not retain expanded hitboxes.
        mFooter.setVisibility(View.VISIBLE);
        if (mPasswordButton != null) {
            mPasswordButton.setVisibility(expanded ? View.VISIBLE : View.GONE);
        }
        if (mExtensionsToolbarHost != null) {
            mExtensionsToolbarHost.setVisibility(expanded ? mExtensionsToolbarOriginalVisibility : View.GONE);
        }
        if (mCollectionsView != null) {
            mCollectionsView.setVisibility(expanded ? View.VISIBLE : View.GONE);
        }
        applyFrameGeometry();
        if (expanded && mCollectionsView != null) {
            mCollectionsView.setCollectionHeight(
                    Math.max(0, Math.min(dp(112), availableHeightPx / 6)));
        }
        applySidebarGeometry();
    }

    private int reservedLeftWidth() {
        if (mArcViewportAnimationActive) return Math.max(0, mArcVisualReservedLeftWidth);
        Integer width = mReservedLeftWidth.get();
        return Math.max(0, width == null ? 0 : width);
    }

    private Transition createArcViewportTransition(SideUiSpecs specs) {
        if (mDestroyed || !mArcToolbarCompositionActive || !mArcFrameActive
                || mCompositorViewHolder.getFullscreenManager().getPersistentFullscreenMode()) {
            finishArcViewportAnimation();
            return null;
        }
        int start = reservedLeftWidth();
        int end = Math.max(0, specs.getReservedWidth(AnchorSide.LEFT));
        if (start == end) {
            // Hover expands the rail without reserving more page width; stale pending work
            // from an interrupted request must not prepare a second renderer canvas.
            finishArcViewportAnimation();
            return null;
        }
        final int generation = ++mArcViewportAnimationGeneration;
        mArcVisualReservedLeftWidth = start;
        mArcViewportAnimationPending = true;
        return new ArcViewportTransition(mCompositorViewHolder, start, end, width -> {
            if (generation == mArcViewportAnimationGeneration) updateArcAnimatedViewportWidth(width);
        });
    }

    private void beginArcViewportAnimation(SideUiSpecs specs) {
        if (mDestroyed || !mArcToolbarCompositionActive || !mArcViewportAnimationPending) return;
        if (!mArcFrameActive
                || mCompositorViewHolder.getFullscreenManager().getPersistentFullscreenMode()) {
            finishArcViewportAnimation();
            return;
        }
        mArcViewportAnimationPending = false;
        mArcViewportAnimationActive = true;
        // Keep the larger canvas available throughout both directions. Collapse prepares the
        // larger target now; expansion keeps its current canvas until native settlement.
        mCompositorViewHolder.prepareArcSideUiAnimation(
                mArcVisualReservedLeftWidth, specs.getReservedWidth(AnchorSide.LEFT));
    }

    private void finishArcViewportAnimation() {
        mArcViewportAnimationPending = false;
        mArcViewportAnimationActive = false;
        mArcVisualReservedLeftWidth = -1;
        ++mArcViewportAnimationGeneration;
    }

    private void updateArcAnimatedViewportWidth(int width) {
        if (mDestroyed || !mArcToolbarCompositionActive || !mArcViewportAnimationActive) return;
        mArcVisualReservedLeftWidth = Math.max(0, width);
        mCompositorViewHolder.setArcSideUiContentOffsetX(mArcVisualReservedLeftWidth);
        mFrameGeometry = currentFrameGeometry();
        mCompositorViewHolder.invalidateOutline();
        applyActiveSurfaceClip();
    }

    private int captionHeight() {
        if (mCaptionSpacer.getVisibility() != View.VISIBLE) return 0;
        return Math.max(0, mCaptionSpacer.getLayoutParams().height);
    }

    private void applySidebarGeometry() {
        if (mDestroyed || !mArcToolbarCompositionActive) return;
        ArcDesktopPolicy.Geometry g = currentFrameGeometry();
        boolean compact = mColumn.getWidth() <= dp(ArcDesktopPolicy.COLLAPSED_WIDTH_DP);
        int side = compact ? 0 : g.sideInset;
        if (mNativeTabs.getPaddingLeft() != side || mNativeTabs.getPaddingRight() != side) {
            mNativeTabs.setPadding(side, mOriginalNativeTabsPaddingTop,
                    side, mOriginalNativeTabsPaddingBottom);
        }
        if (mLastNativeRowHeight != g.omniboxHeight) {
            mLastNativeRowHeight = g.omniboxHeight;
            refreshNativeRows(mNativeTabs);
        }
        mHeader.setPadding(0, g.headerTopInset, 0, 0);
        mNavigationRow.setPadding(side, 0, side, 0);
        LinearLayout.LayoutParams collapse = (LinearLayout.LayoutParams) mCollapseButton.getLayoutParams();
        if (collapse.width != dp(ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP)
                || collapse.height != g.navigationHeight || collapse.getMarginStart() != 0
                || collapse.bottomMargin != 0) {
            collapse.width = dp(ArcDesktopPolicy.ARC_NAV_BUTTON_WIDTH_DP);
            collapse.height = g.navigationHeight;
            collapse.setMarginStart(0);
            collapse.bottomMargin = 0;
            mCollapseButton.setLayoutParams(collapse);
        }
        updateLocationBarGeometry(g, side);
        if (mCollectionsView != null) {
            LinearLayout.LayoutParams collections = (LinearLayout.LayoutParams) mCollectionsView.getLayoutParams();
            int gap = g.omniboxBottomGap;
            if (collections.getMarginStart() != side || collections.getMarginEnd() != side
                    || collections.topMargin != gap) {
                collections.setMarginStart(side);
                collections.setMarginEnd(side);
                collections.topMargin = gap;
                mCollectionsView.setLayoutParams(collections);
            }
            mCollectionsView.applyGeometry(g, Math.max(0, mColumn.getWidth() - 2 * side));
        }
        mFooter.setPadding(side, 0, side, g.footerBottomInset);
        int caption = captionHeight();
        ArcDesktopPolicy.SidebarBudget budget = ArcDesktopPolicy.sidebarBudget(
                mColumn.getHeight(), caption, mHeader.getMeasuredHeight(),
                mActivity.getResources().getDisplayMetrics().density, g.footerBottomInset);
        ((VerticalTabRailLayout) mNativeTabs).setArcAvailableTabHeight(budget.tabHeight, true);
        LinearLayout.LayoutParams footer = (LinearLayout.LayoutParams) mFooter.getLayoutParams();
        if (footer.height != budget.footerHeight) {
            footer.height = budget.footerHeight;
            mFooter.setLayoutParams(footer);
        }
        LinearLayout.LayoutParams header = (LinearLayout.LayoutParams) mHeaderScroll.getLayoutParams();
        if (header.height != budget.headerHeight) {
            header.height = budget.headerHeight;
            mHeaderScroll.setLayoutParams(header);
        }
        // Keep the app menu inside the scrolling native header if utilities do not fit.
        boolean footerVisible = budget.footerHeight > 0;
        ViewGroup menuParent = footerVisible ? mFooter : mHeader;
        if (mMenuButtonWrapper.getParent() != menuParent) {
            ((ViewGroup) mMenuButtonWrapper.getParent()).removeView(mMenuButtonWrapper);
            menuParent.addView(mMenuButtonWrapper, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT, g.footerHeight));
        }
        mFooter.setVisibility(footerVisible ? View.VISIBLE : View.GONE);
    }

    private void updateLocationBarGeometry(ArcDesktopPolicy.Geometry g, int side) {
        LinearLayout.LayoutParams url = (LinearLayout.LayoutParams) mLocationBarHost.getLayoutParams();
        // Chromium owns this holder while Fusebox expands it. Resetting height/margins from a
        // header layout fights native focus animation; defer baseline changes until native blur.
        if (url.height == ViewGroup.LayoutParams.WRAP_CONTENT) return;
        if (url.height != g.omniboxHeight || url.getMarginStart() != side
                || url.getMarginEnd() != side) {
            url.height = g.omniboxHeight;
            url.setMarginStart(side);
            url.setMarginEnd(side);
            mLocationBarHost.setLayoutParams(url);
        }
    }

    private int arcClipLeftForView(View view) {
        return arcClipBoundsForView(view).left;
    }

    private ArcDesktopPolicy.Geometry currentFrameGeometry() {
        int width = mFrameRoot == null ? 0 : mFrameRoot.getWidth();
        int height = mFrameRoot == null ? 0 : mFrameRoot.getHeight();
        if (width <= 0) width = mCompositorViewHolder.getWidth();
        if (height <= 0) height = mCompositorViewHolder.getHeight();
        return ArcDesktopPolicy.geometry(width, height, reservedLeftWidth(),
                mActivity.getResources().getDisplayMetrics().density, false);
    }

    private int arcCaptionClipTop() {
        int caption = captionHeight();
        if (caption == 0) return 0;
        int[] captionPosition = new int[2];
        int[] holderPosition = new int[2];
        mCaptionSpacer.getLocationInWindow(captionPosition);
        mCompositorViewHolder.getLocationInWindow(holderPosition);
        // Native TopControlsStacker already offsets web/bookmarks for this caption. Protect its
        // window area by clipping, without adding the caption again to compositor layout margins.
        return Math.min(mCompositorViewHolder.getHeight(),
                Math.max(0, captionPosition[1] + caption - holderPosition[1]));
    }

    private Rect arcClipBoundsForView(View view) {
        int left = Math.min(reservedLeftWidth(), mCompositorViewHolder.getWidth());
        Rect bounds = new Rect(left, arcCaptionClipTop(),
                mCompositorViewHolder.getWidth(), mCompositorViewHolder.getHeight());
        if (view != mCompositorViewHolder) {
            int[] holderPosition = new int[2];
            int[] surfacePosition = new int[2];
            mCompositorViewHolder.getLocationInWindow(holderPosition);
            view.getLocationInWindow(surfacePosition);
            int dx = holderPosition[0] - surfacePosition[0];
            int dy = holderPosition[1] - surfacePosition[1];
            bounds.set(Math.max(0, bounds.left + dx), Math.max(0, bounds.top + dy),
                    Math.min(view.getWidth(), bounds.right + dx),
                    Math.min(view.getHeight(), bounds.bottom + dy));
        }
        return bounds;
    }

    private boolean isInsideArcContent(float x, float y) {
        Rect bounds = arcClipBoundsForView(mCompositorViewHolder);
        return ArcDesktopPolicy.containsRoundedRectPoint(
                x, y, bounds.left, bounds.top, bounds.right, bounds.bottom,
                currentFrameGeometry().viewportRadius);
    }

    private void restoreClippedSurface() {
        if (mClippedSurface == null) return;
        mClippedSurface.removeCallbacks(mGeometryUpdate);
        if (mClippedSurface instanceof SurfaceView) {
            ((SurfaceView) mClippedSurface).getHolder().removeCallback(mSurfaceCallback);
        }
        mClippedSurface.removeOnAttachStateChangeListener(mSurfaceAttachStateListener);
        mClippedSurface.setOutlineProvider(mClippedSurfaceOriginalOutlineProvider);
        mClippedSurface.setClipToOutline(mClippedSurfaceOriginalClipToOutline);
        mClippedSurface.setClipBounds(mClippedSurfaceOriginalClipBounds);
        mClippedSurface.invalidateOutline();
        mClippedSurface = null;
        mClippedSurfaceOriginalOutlineProvider = null;
    }

    private void applyActiveSurfaceClip() {
        View activeSurface = mCompositorViewHolder.getActiveSurfaceView();
        if (activeSurface == mClippedSurface) {
            if (activeSurface != null) {
                Rect bounds = arcClipBoundsForView(activeSurface);
                if (!bounds.equals(activeSurface.getClipBounds())) {
                    activeSurface.setClipBounds(bounds);
                    activeSurface.invalidateOutline();
                }
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
        activeSurface.setOutlineProvider(mArcContentOutlineProvider);
        activeSurface.setClipToOutline(true);
        activeSurface.setClipBounds(arcClipBoundsForView(activeSurface));
        if (activeSurface instanceof SurfaceView) {
            ((SurfaceView) activeSurface).getHolder().addCallback(mSurfaceCallback);
        }
        activeSurface.invalidateOutline();
    }

    private void applyFrameGeometry() {
        if (mDestroyed || !mArcToolbarCompositionActive) return;
        if (mCompositorViewHolder.getFullscreenManager().getPersistentFullscreenMode()) {
            clearFrameGeometry();
            return;
        }
        mArcFrameActive = true;
        mFrameGeometry = currentFrameGeometry();
        mCompositorViewHolder.setOutlineProvider(mArcContentOutlineProvider);
        mCompositorViewHolder.setClipToOutline(true);
        // The sidebar reaches the frame edges. SideUiCoordinator already owns its full width.
        mRail.setPadding(
                mOriginalRailPaddingLeft, 0, mOriginalRailPaddingRight, 0);

        ViewGroup.LayoutParams raw = mCompositorViewHolder.getLayoutParams();
        if (raw instanceof ViewGroup.MarginLayoutParams) {
            ViewGroup.MarginLayoutParams margins = (ViewGroup.MarginLayoutParams) raw;
            int contentLeftMargin = mOriginalContentMarginLeft;
            int contentTopMargin = mOriginalContentMarginTop + mFrameGeometry.topInset;
            int contentRightMargin = mOriginalContentMarginRight + mFrameGeometry.endInset;
            int contentBottomMargin = mOriginalContentMarginBottom + mFrameGeometry.bottomInset;
            if (margins.leftMargin != contentLeftMargin
                    || margins.topMargin != contentTopMargin
                    || margins.rightMargin != contentRightMargin
                    || margins.bottomMargin != contentBottomMargin) {
                // Native Side UI offsets determine both page position and input coordinates.
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
        if (mFrameRoot != null) {
            ArcDesktopAppearance.applySidebarBackground(mFrameRoot, incognito);
            mFrameRoot.setOutlineProvider(mArcFrameOutlineProvider);
            mFrameRoot.setClipToOutline(true);
            mFrameRoot.invalidateOutline();
        }
    }

    private void clearFrameGeometry() {
        finishArcViewportAnimation();
        if (!mArcFrameActive) return;
        mArcFrameActive = false;
        mCompositorViewHolder.removeCallbacks(mGeometryUpdate);
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
        if (mFrameRoot != null) {
            mFrameRoot.setBackground(mOriginalFrameBackground);
            mFrameRoot.setOutlineProvider(mOriginalFrameOutlineProvider);
            mFrameRoot.setClipToOutline(mOriginalFrameClipToOutline);
            mFrameRoot.invalidateOutline();
        }
    }

    private void restoreFrameGeometry() {
        clearFrameGeometry();
        ((VerticalTabRailLayout) mNativeTabs).setArcAvailableTabHeight(0, false);
        mNativeTabs.setPadding(mOriginalNativeTabsPaddingLeft, mOriginalNativeTabsPaddingTop,
                mOriginalNativeTabsPaddingRight, mOriginalNativeTabsPaddingBottom);
        mCompositorViewHolder.removeTouchEventObserver(mArcTouchEventObserver);
        mCompositorViewHolder.removeOnLayoutChangeListener(mContentLayoutListener);
        if (mCompositorViewHolder.getViewTreeObserver().isAlive()) {
            mCompositorViewHolder.getViewTreeObserver().removeOnGlobalLayoutListener(mSurfaceLayoutListener);
        }
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
        mCollapseButton.setOnLongClickListener(null);
        mCollapseButton.setTooltipText(null);
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
        // Native Chromium controls retain their own input/state; only owned Arc views are styled.
        if (view == mLocationBarHost
                || view == mCollapseButton
                || view == mMenuButtonWrapper
                || view == mExtensionsToolbarHost) {
            return;
        }
        if (view instanceof ArcCollectionsView) {
            ((ArcCollectionsView) view).applyAppearance(mIncognitoStateProvider.isIncognitoSelected());
            return;
        }
        if (view instanceof TextView) ((TextView) view).setTextColor(foreground);
        if (view instanceof Button || view instanceof ImageButton) {
            view.setBackground(ArcDesktopAppearance.controlBackground(
                    mActivity, mIncognitoStateProvider.isIncognitoSelected(), 8));
            if (view instanceof ImageButton) {
                ImageButton button = (ImageButton) view;
                button.clearColorFilter();
                button.setImageTintList(new ColorStateList(
                        new int[][] {new int[] {-android.R.attr.state_enabled}, new int[] {}},
                        new int[] {(foreground & 0x00ffffff) | 0x61000000, foreground}));
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
        mNavigationState.destroy();
        mSideUiStateProvider.removeObserver(mSideUiObserver);
        mIncognitoStateProvider.removeObserver(mIncognitoObserver);
        ((VerticalTabRailLayout) mNativeTabs).setDesktopWindowSpacerHost(null);
        clearCollections();
        mPreferences.unregisterOnSharedPreferenceChangeListener(mPreferenceListener);
        mRail.removeOnLayoutChangeListener(mLayoutListener);
        mColumn.removeOnLayoutChangeListener(mColumnLayoutListener);
        mHeader.removeOnLayoutChangeListener(mHeaderLayoutListener);
        mCaptionSpacer.removeOnLayoutChangeListener(mHeaderLayoutListener);
        if (mNavigationMenu != null) mNavigationMenu.dismiss();
        if (mColorDialog != null) mColorDialog.dismiss();
        restoreFrameGeometry();
        setArcToolbarCompositionActive(false);
        mIcons.destroy();
        mColumn.removeView(mNativeTabs);
        mRail.removeView(mColumn);
        mRail.addView(mNativeTabs, new ViewGroup.LayoutParams(-1, -1));
    }

    /** Native caption/fullscreen events share the existing resize/layout recomposition path. */
    public void onSystemWindowStateChanged() {
        if (!mDestroyed) applyAppearance();
    }
}
