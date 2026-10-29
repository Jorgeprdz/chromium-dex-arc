// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.theme;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;

import androidx.annotation.ColorInt;
import androidx.annotation.VisibleForTesting;

import java.util.function.BiFunction;

import org.chromium.build.annotations.NullMarked;
import org.chromium.build.annotations.Nullable;
import org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider;
import org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider.ControlsPosition;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.theme.ThemeColorProvider.ThemeColorObserver;
import org.chromium.chrome.browser.theme.ThemeColorProvider.TintObserver;
import org.chromium.chrome.browser.ui.bottombar.BottomBarConfigUtils;
import org.chromium.chrome.browser.ui.theme.BrandedColorScheme;
import org.chromium.components.browser_ui.styles.ChromeColors;
import org.chromium.ui.util.ColorUtils;

/**
 * Theme color provider for the toolbar. It listens to {@link TopUiThemeColorProvider} by default.
 * If {@link BottomBarConfigUtils#isBottomBarEnabled(Context)} is true, it switches to {@link
 * BottomUiThemeColorProvider} when the controls position is {@link ControlsPosition#BOTTOM}.
 */
@NullMarked
public class ToolbarThemeColorProvider extends ThemeColorProvider
        implements BrowserControlsStateProvider.Observer, ThemeColorObserver, TintObserver {
    private @Nullable Runnable mArcPhonePageColorChangedCallback;
    private int mArcLastPageColor, mArcLastPageFallback;
    private boolean mArcHasPageColor;
    private final ThemeColorObserver mArcPageObserver=(color,animate)->{
        int fallback=getArcPhoneSurfaceColor();
        if(mArcHasPageColor&&mArcLastPageColor==color&&mArcLastPageFallback==fallback)return;
        mArcHasPageColor=true;mArcLastPageColor=color;mArcLastPageFallback=fallback;
        if(mArcPhonePageColorChangedCallback!=null)mArcPhonePageColorChangedCallback.run();
    };

    /** Metadata notification survives the floating toolbar's intentional neutral color clamp. */
    public void setArcPhonePageColorChangedCallback(@Nullable Runnable callback){
        if(mArcPhonePageColorChangedCallback==callback)return;
        if(mArcPhonePageColorChangedCallback!=null)mTopUiThemeColorProvider.removeThemeColorObserver(mArcPageObserver);
        mArcPhonePageColorChangedCallback=callback;mArcHasPageColor=false;
        if(callback!=null)mTopUiThemeColorProvider.addThemeColorObserver(mArcPageObserver);
    }

    private final Context mArcContext;
    private final BiFunction<Context, Boolean, Integer> mArcSurfaceColorResolver;
    private final BiFunction<Context, Integer, ColorStateList> mArcIconTintResolver;
    private boolean mArcPhoneFloatingSurface;
    private final TopUiThemeColorProvider mTopUiThemeColorProvider;
    private final BottomUiThemeColorProvider mBottomUiThemeColorProvider;
    private final BrowserControlsStateProvider mBrowserControlsStateProvider;
    private final boolean mIsBottomBarEnabled;
    private @ControlsPosition int mControlsPosition;
    private @Nullable ThemeColorProvider mActiveProvider;

    /**
     * @param context The {@link Context} to check if bottom bar is enabled.
     * @param topUiThemeColorProvider The default provider.
     * @param bottomUiThemeColorProvider The provider to use when bottom bar is enabled and position
     *     is BOTTOM.
     * @param browserControlsStateProvider Provider of the browser controls state to listen for
     *     position changes.
     */
    public ToolbarThemeColorProvider(
            Context context,
            TopUiThemeColorProvider topUiThemeColorProvider,
            BottomUiThemeColorProvider bottomUiThemeColorProvider,
            BrowserControlsStateProvider browserControlsStateProvider) {
        this(context, topUiThemeColorProvider, bottomUiThemeColorProvider,
                browserControlsStateProvider, BottomBarConfigUtils.isBottomBarEnabled(context),
                ChromeColors::getDefaultThemeColor, ThemeUtils::getThemedToolbarIconTint);
    }

    /** Explicit resource boundaries for tests; production keeps the native resolvers above. */
    @VisibleForTesting
    public ToolbarThemeColorProvider(
            Context context,
            TopUiThemeColorProvider topUiThemeColorProvider,
            BottomUiThemeColorProvider bottomUiThemeColorProvider,
            BrowserControlsStateProvider browserControlsStateProvider,
            boolean bottomBarEnabled,
            BiFunction<Context, Boolean, Integer> surfaceColorResolver,
            BiFunction<Context, Integer, ColorStateList> iconTintResolver) {
        super(context);
        mArcContext = context;
        mArcSurfaceColorResolver = surfaceColorResolver;
        mArcIconTintResolver = iconTintResolver;
        mTopUiThemeColorProvider = topUiThemeColorProvider;
        mBottomUiThemeColorProvider = bottomUiThemeColorProvider;
        mBrowserControlsStateProvider = browserControlsStateProvider;
        mIsBottomBarEnabled = bottomBarEnabled;
        mControlsPosition = browserControlsStateProvider.getControlsPosition();

        mBrowserControlsStateProvider.addObserver(this);
        updateActiveProvider(/* animate= */ false);
    }

    /** Phone-only palette opt-in; use the same native color scheme for surface and icons. */
    public void setArcPhoneFloatingSurfaceEnabled(boolean enabled) {
        if (mArcPhoneFloatingSurface == enabled
                && (!enabled || getThemeColor() == getArcPhoneSurfaceColor())) return;
        mArcPhoneFloatingSurface = enabled;
        if (mActiveProvider == null) return;
        onThemeColorChanged(mActiveProvider.getThemeColor(), /* shouldAnimate= */ false);
        onTintChanged(mActiveProvider.getTint(), mActiveProvider.getActivityFocusTint(),
                mActiveProvider.getBrandedColorScheme());
    }

    private @ColorInt int getArcPhoneSurfaceColor() {
        boolean incognito = mActiveProvider != null
                && mActiveProvider.getBrandedColorScheme() == BrandedColorScheme.INCOGNITO;
        int color = mArcSurfaceColorResolver.apply(mArcContext, incognito);
        return ColorUtils.shouldUseLightForegroundOnBackground(color) ? 0xff202124 : Color.WHITE;
    }

    /**
     * @param tab The {@link Tab} on which the theme color is used.
     * @param fallbackColor The fallback color to use if the default color is used or there is no
     *     current tab.
     * @return Theme color or the given fallback color if the default color is used or there is no
     *     current tab.
     */
    public @ColorInt int getThemeColorOrFallback(@Nullable Tab tab, @ColorInt int fallbackColor) {
        if (mArcPhoneFloatingSurface) return getArcPhoneSurfaceColor();
        if (mActiveProvider == mTopUiThemeColorProvider) {
            return mTopUiThemeColorProvider.getThemeColorOrFallback(tab, fallbackColor);
        }
        return mBottomUiThemeColorProvider.getThemeColor();
    }

    /** Page palette for the revealed web gap, independent of the approved phone pill palette. */
    public @ColorInt int getArcPhonePageColor(@Nullable Tab tab) {
        return mTopUiThemeColorProvider.getThemeColorOrFallback(tab, getArcPhoneSurfaceColor());
    }

    /**
     * @param tab The {@link Tab} on which the toolbar background color is used.
     * @return Returns the toolbar background color.
     */
    public @ColorInt int getToolbarBackgroundColor(Tab tab) {
        if (mArcPhoneFloatingSurface) return getArcPhoneSurfaceColor();
        if (mActiveProvider == mTopUiThemeColorProvider) {
            return mTopUiThemeColorProvider.getToolbarBackgroundColor(tab);
        }
        return mBottomUiThemeColorProvider.getThemeColor();
    }

    @Override
    public void destroy() {
        setArcPhonePageColorChangedCallback(null);
        super.destroy();
        mBrowserControlsStateProvider.removeObserver(this);
        if (mActiveProvider != null) {
            mActiveProvider.removeThemeColorObserver(this);
            mActiveProvider.removeTintObserver(this);
        }
    }

    @Override
    public void onControlsPositionChanged(@ControlsPosition int controlsPosition) {
        if (mControlsPosition == controlsPosition) return;
        mControlsPosition = controlsPosition;
        updateActiveProvider(/* animate= */ true);
    }

    @Override
    public void onThemeColorChanged(int color, boolean shouldAnimate) {
        updatePrimaryColor(mArcPhoneFloatingSurface ? getArcPhoneSurfaceColor() : color, shouldAnimate);
    }

    @Override
    public void onTintChanged(
            @Nullable ColorStateList tint,
            @Nullable ColorStateList activityFocusTint,
            @BrandedColorScheme int brandedColorScheme) {
        if (mArcPhoneFloatingSurface) {
            brandedColorScheme = brandedColorScheme == BrandedColorScheme.INCOGNITO
                    ? BrandedColorScheme.INCOGNITO : BrandedColorScheme.APP_DEFAULT;
            ColorStateList nativeTint = mArcIconTintResolver.apply(mArcContext, brandedColorScheme);
            activityFocusTint = activityFocusTint == null ? null
                    : nativeTint.withAlpha(Color.alpha(activityFocusTint.getDefaultColor()));
            tint = nativeTint;
        }
        updateTint(tint, activityFocusTint, brandedColorScheme);
        if (mArcPhoneFloatingSurface) {
            // Incognito/night changes may notify tint after the primary-color event.
            updatePrimaryColor(getArcPhoneSurfaceColor(), /* shouldAnimate= */ false);
        }
    }

    private void updateActiveProvider(boolean animate) {
        ThemeColorProvider newProvider;
        if (mIsBottomBarEnabled && mControlsPosition == ControlsPosition.BOTTOM) {
            newProvider = mBottomUiThemeColorProvider;
        } else {
            newProvider = mTopUiThemeColorProvider;
        }

        if (newProvider != mActiveProvider) {
            if (mActiveProvider != null) {
                mActiveProvider.removeThemeColorObserver(this);
                mActiveProvider.removeTintObserver(this);
            }
            mActiveProvider = newProvider;
            mActiveProvider.addThemeColorObserver(this);
            mActiveProvider.addTintObserver(this);

            if (mArcPhoneFloatingSurface) {
                onThemeColorChanged(mActiveProvider.getThemeColor(), animate);
                onTintChanged(mActiveProvider.getTint(), mActiveProvider.getActivityFocusTint(),
                        mActiveProvider.getBrandedColorScheme());
            } else {
                updatePrimaryColor(mActiveProvider.getThemeColor(), animate);
                updateTint(mActiveProvider.getTint(), mActiveProvider.getActivityFocusTint(),
                        mActiveProvider.getBrandedColorScheme());
            }
        }
    }
}
