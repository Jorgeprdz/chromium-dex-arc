// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import android.app.Activity;
import android.content.Context;
import android.content.ContextWrapper;

import java.util.WeakHashMap;
import android.content.pm.PackageManager;
import android.os.Build;
import android.view.Display;
import android.view.WindowManager;
import android.content.SharedPreferences;
import android.content.res.Configuration;

import org.chromium.chrome.browser.desktop_policy.ArchiumWindowMetrics;

/** Arc styling follows the current usable window; independent of vendor or desktop service. */
public final class ArcDesktopAppearance {
    public static final String UI_FONT_KEY = "ui_font";
    public static final String COLOR_KEY = "frame_color";
    public static final String UI_MODE_KEY = "ui_mode";
    public static final String ADDRESS_BAR_POSITION_KEY = "address_bar_position";
    public static final int ADDRESS_SIDEBAR = 0;
    public static final int ADDRESS_TOP = 1;
    public static final int DEFAULT_COLOR = 0xff53657b;

    // UI-thread only. A draft belongs to its Activity, never another window or saved profile.
    private static final WeakHashMap<Context, Integer> PREVIEW_COLORS = new WeakHashMap<>();

    private ArcDesktopAppearance() {}

    public static int getAddressBarPosition(Context context) {
        return preferences(context).getInt(ADDRESS_BAR_POSITION_KEY, ADDRESS_SIDEBAR) == ADDRESS_TOP
                ? ADDRESS_TOP : ADDRESS_SIDEBAR;
    }

    public static void setAddressBarPosition(Context context, int position) {
        if (position != ADDRESS_SIDEBAR && position != ADDRESS_TOP) {
            throw new IllegalArgumentException("Invalid address bar position");
        }
        preferences(context).edit().putInt(ADDRESS_BAR_POSITION_KEY, position).apply();
    }

    public static int getUiFont(Context context) {
        int font = preferences(context).getInt(UI_FONT_KEY, 0);
        return font >= 0 && font <= 3 ? font : 0;
    }

    public static void setUiFont(Context context, int font) {
        if (font < 0 || font > 3) throw new IllegalArgumentException("Invalid UI font");
        preferences(context).edit().putInt(UI_FONT_KEY, font).apply();
    }

    /** Apply only to browser controls/settings, never a page or compositor subtree. */
    public static void applyUiFont(android.view.View controls) {
        String[] families = {"sans-serif", "sans-serif-medium", "serif", "monospace"};
        applyUiFont(controls, families[getUiFont(controls.getContext())]);
    }

    private static void applyUiFont(android.view.View view, String family) {
        if (view instanceof android.widget.TextView text) {
            android.graphics.Typeface current = text.getTypeface();
            android.graphics.Typeface selected = android.graphics.Typeface.create(
                    family, current == null ? 0 : current.getStyle());
            if (!selected.equals(current)) text.setTypeface(selected);
        }
        if (view instanceof android.view.ViewGroup group) {
            for (int i = 0; i < group.getChildCount(); i++) applyUiFont(group.getChildAt(i), family);
        }
    }

    private static Context visualContext(Context context) {
        while (!(context instanceof Activity) && context instanceof ContextWrapper wrapper) {
            Context base = wrapper.getBaseContext();
            if (base == context) break;
            context = base;
        }
        return context;
    }

    public static void setPreviewColor(Context context, Integer color) {
        Context window = visualContext(context);
        if (color == null) PREVIEW_COLORS.remove(window);
        else PREVIEW_COLORS.put(window, color);
    }

    public static boolean isDesktopWindow(Context context) {
        context = visualContext(context);
        int mode = getUiMode(context);
        if (mode == ArcDesktopPolicy.MODE_ARC) return true;
        if (mode == ArcDesktopPolicy.MODE_MOBILE) return false;
        Configuration config = context.getResources().getConfiguration();
        if ((config.uiMode & Configuration.UI_MODE_TYPE_MASK) == Configuration.UI_MODE_TYPE_DESK
                || context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_PC)) return true;
        boolean desktop = config.smallestScreenWidthDp >= 600;
        if (context instanceof Activity activity) {
            Display display = activityDisplay(activity);
            if (display != null && display.getDisplayId() != Display.DEFAULT_DISPLAY) return true;
            desktop |= activity.isInMultiWindowMode();
        }
        return desktop && ArcDesktopPolicy.isArcWindow(mode,
                ArchiumWindowMetrics.currentWidthDp(context));
    }

    @SuppressWarnings("deprecation")
    static Display activityDisplay(Activity activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Display display = activity.getDisplay();
                if (display != null) return display;
            } catch (UnsupportedOperationException unavailableVisualContext) {
                // The Activity's WindowManager is the API 29/nonvisual fallback.
            }
        }
        WindowManager manager = activity.getWindowManager();
        return manager == null ? null : manager.getDefaultDisplay();
    }

    public static int getUiMode(Context context) {
        int preference = preferences(context).getInt(UI_MODE_KEY, ArcDesktopPolicy.MODE_AUTO);
        if (preference != ArcDesktopPolicy.MODE_ARC
                && preference != ArcDesktopPolicy.MODE_MOBILE) {
            return ArcDesktopPolicy.MODE_AUTO;
        }
        return preference;
    }

    public static void setUiMode(Context context, int preference) {
        if (preference != ArcDesktopPolicy.MODE_AUTO && preference != ArcDesktopPolicy.MODE_ARC
                && preference != ArcDesktopPolicy.MODE_MOBILE) {
            throw new IllegalArgumentException("Invalid Arc appearance mode");
        }
        preferences(context).edit().putInt(UI_MODE_KEY, preference).apply();
    }

    @SuppressWarnings("UseSharedPreferencesManagerFromChromeCheck")
    public static SharedPreferences preferences(Context context) {
        return context.getApplicationContext().getSharedPreferences("arc_appearance", Context.MODE_PRIVATE);
    }

    public static int surface(Context context, boolean incognito) {
        boolean dark = incognito || (context.getResources().getConfiguration().uiMode
                & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
        Integer preview = PREVIEW_COLORS.get(visualContext(context));
        if (preview != null) return ArcDesktopPolicy.surface(preview, dark);
        SharedPreferences saved = preferences(context);
        if (!saved.contains(COLOR_KEY)) return ArcDesktopPolicy.defaultSurface(dark);
        return ArcDesktopPolicy.surface(saved.getInt(COLOR_KEY, DEFAULT_COLOR), dark);
    }

    public static int activeTabSurface(Context context, boolean incognito) {
        if (incognito) return selection(context, true);
        boolean custom = PREVIEW_COLORS.containsKey(visualContext(context))
                || preferences(context).contains(COLOR_KEY);
        return custom ? ArcDesktopPolicy.activeTabSurface(surface(context, false)) : 0xff7365d8;
    }

    public static int foreground(Context context, boolean incognito) {
        return ArcDesktopPolicy.foreground(surface(context, incognito));
    }

    public static int selection(Context context, boolean incognito) {
        return ArcDesktopPolicy.selection(surface(context, incognito));
    }

    private static final WeakHashMap<android.widget.TextView, Float> SIDEBAR_TEXT_SP = new WeakHashMap<>();
    private static final WeakHashMap<android.widget.ImageView, int[]> SIDEBAR_ICON_SIZE = new WeakHashMap<>();
    private static final WeakHashMap<android.view.View, int[]> SIDEBAR_ICON_CONTAINER_SIZE = new WeakHashMap<>();

    /** Retain the existing +2sp (pinned native TextMedium is 14sp); never stack an increase. */
    public static void styleSidebarTitle(android.widget.TextView text) {
        if (isDesktopWindow(text.getContext())) {
            Float original = SIDEBAR_TEXT_SP.get(text);
            if (original == null) {
                android.util.DisplayMetrics metrics = text.getResources().getDisplayMetrics();
                // Android 14+ scales fonts nonlinearly: scaledDensity is not the inverse of sp.
                original = Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE
                        ? android.util.TypedValue.deriveDimension(android.util.TypedValue.COMPLEX_UNIT_SP,
                                text.getTextSize(), metrics)
                        : text.getTextSize() / metrics.scaledDensity;
                SIDEBAR_TEXT_SP.put(text, original);
            }
            text.setTextSize(original + 2f);
        } else {
            Float original = SIDEBAR_TEXT_SP.remove(text);
            if (original != null) text.setTextSize(original);
        }
    }

    /** Size the native owning slot; its image fills the slot without overflowing a clipping parent. */
    public static void sizeSidebarFavicon(android.widget.ImageView icon, boolean pair, boolean compact) {
        if (!(icon.getParent() instanceof android.widget.FrameLayout owner)) return;
        android.view.ViewGroup.LayoutParams params = icon.getLayoutParams();
        android.view.ViewGroup.LayoutParams ownerParams = owner.getLayoutParams();
        if (params == null || ownerParams == null) return;
        if (!SIDEBAR_ICON_SIZE.containsKey(icon)) {
            SIDEBAR_ICON_SIZE.put(icon, new int[] {params.width, params.height});
        }
        if (!SIDEBAR_ICON_CONTAINER_SIZE.containsKey(owner)) {
            SIDEBAR_ICON_CONTAINER_SIZE.put(owner, new int[] {ownerParams.width, ownerParams.height});
        }
        float density = icon.getResources().getDisplayMetrics().density;
        int height = Math.round(22 * density);
        int width = Math.round((pair ? (compact ? 32 : 45) : 22) * density);
        if (ownerParams.width != width || ownerParams.height != height) {
            ownerParams.width = width;
            ownerParams.height = height;
            owner.setLayoutParams(ownerParams);
        }
        // Native row constraints and title spacing follow the owning container, never the image.
        if (params.width != android.view.ViewGroup.LayoutParams.MATCH_PARENT
                || params.height != android.view.ViewGroup.LayoutParams.MATCH_PARENT) {
            params.width = android.view.ViewGroup.LayoutParams.MATCH_PARENT;
            params.height = android.view.ViewGroup.LayoutParams.MATCH_PARENT;
            icon.setLayoutParams(params);
        }
    }

    public static void restoreSidebarFaviconSize(android.widget.ImageView icon) {
        int[] original = SIDEBAR_ICON_SIZE.remove(icon);
        android.view.ViewGroup.LayoutParams params = icon.getLayoutParams();
        if (original != null && params != null
                && (params.width != original[0] || params.height != original[1])) {
            params.width = original[0];
            params.height = original[1];
            icon.setLayoutParams(params);
        }
        if (icon.getParent() instanceof android.widget.FrameLayout owner) {
            int[] ownerOriginal = SIDEBAR_ICON_CONTAINER_SIZE.remove(owner);
            android.view.ViewGroup.LayoutParams ownerParams = owner.getLayoutParams();
            if (ownerOriginal != null && ownerParams != null
                    && (ownerParams.width != ownerOriginal[0] || ownerParams.height != ownerOriginal[1])) {
                ownerParams.width = ownerOriginal[0];
                ownerParams.height = ownerOriginal[1];
                owner.setLayoutParams(ownerParams);
            }
        }
    }

    /** Retains native favicon/fallback artwork and its existing box, including asynchronous results. */
    public static void normalizeSidebarFavicon(android.widget.ImageView favicon) {
        favicon.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);
        favicon.setImageTintList(null);
    }

    /** UI-only feedback; selection comes from the native row model, never another selection store. */
    public static void applySidebarRowState(android.view.View row, boolean active,
            boolean multiSelected, boolean incognito, boolean hoveredOrFocused) {
        int fill = active ? activeTabSurface(row.getContext(), incognito)
                : multiSelected || hoveredOrFocused ? selection(row.getContext(), incognito)
                : android.graphics.Color.TRANSPARENT;
        int disabledFill = (fill & 0x00ffffff)
                | (Math.round(android.graphics.Color.alpha(fill) * .4f) << 24);
        SidebarRowOutline outline;
        if (row.getForeground() instanceof SidebarRowOutline existing) {
            outline = existing;
        } else {
            outline = new SidebarRowOutline(row);
            row.setForeground(outline);
        }
        row.setBackgroundTintList(new android.content.res.ColorStateList(
                new int[][] {{-android.R.attr.state_enabled}, {}},
                new int[] {disabledFill, fill}));
        outline.update(active, foreground(row.getContext(), incognito));
    }

    /** Removes only our decoration when a window switches back to the native mobile layout. */
    public static void clearSidebarRowState(android.view.View row) {
        if (row.getForeground() instanceof SidebarRowOutline outline) {
            outline.dispose();
            row.setForeground(outline.originalForeground);
        }
    }

    /** One physical pixel inside the native capsule; a modest radius is restored on release. */
    private static final class SidebarRowOutline extends android.graphics.drawable.Drawable
            implements android.view.View.OnAttachStateChangeListener {
        final android.view.View row;
        final android.graphics.Paint paint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        final android.graphics.RectF bounds = new android.graphics.RectF();
        android.graphics.drawable.GradientDrawable roundedShape;
        final android.graphics.drawable.Drawable originalForeground;
        final android.content.res.ColorStateList originalTint;
        final float originalElevation;
        final int originalAmbientShadowColor;
        final int originalSpotShadowColor;
        float originalRadius;
        boolean active;
        boolean initialized;
        int color;
        int alpha;
        android.animation.ValueAnimator animator;

        SidebarRowOutline(android.view.View row) {
            this.row = row;
            originalForeground = row.getForeground();
            originalTint = row.getBackgroundTintList();
            originalElevation = row.getElevation();
            originalAmbientShadowColor = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                    ? row.getOutlineAmbientShadowColor() : 0;
            originalSpotShadowColor = Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                    ? row.getOutlineSpotShadowColor() : 0;
            paint.setStyle(android.graphics.Paint.Style.STROKE);
            paint.setStrokeWidth(1f);
            row.addOnAttachStateChangeListener(this);
            android.graphics.drawable.Drawable shape = row.getBackground();
            while (shape != null) {
                var current = shape.getCurrent();
                if (current != shape) { shape = current; continue; }
                if (shape instanceof android.graphics.drawable.InsetDrawable inset) {
                    shape = inset.getDrawable();
                } else break;
            }
            if (shape instanceof android.graphics.drawable.GradientDrawable gradient) {
                float radius = gradient.getCornerRadius();
                float wanted = Math.max(radius, 12 * row.getResources().getDisplayMetrics().density);
                if (wanted != radius) {
                    roundedShape = (android.graphics.drawable.GradientDrawable) gradient.mutate();
                    originalRadius = radius;
                    roundedShape.setCornerRadius(wanted);
                }
            }
        }

        void update(boolean active, int color) {
            this.color = color;
            int target = active ? 64 : 0;
            boolean changed = this.active != active;
            this.active = active;
            updateShadow();
            if (!initialized || !row.isAttachedToWindow()
                    || !android.animation.ValueAnimator.areAnimatorsEnabled()) {
                cancelAnimation();
                alpha = target;
                initialized = true;
            } else if (changed) {
                cancelAnimation();
                if (alpha != target) {
                    animator = android.animation.ValueAnimator.ofInt(alpha, target);
                    animator.setDuration(100);
                    animator.addUpdateListener(value -> {
                        alpha = (int) value.getAnimatedValue();
                        invalidateSelf();
                    });
                    animator.start();
                }
            }
            invalidateSelf();
        }

        void updateShadow() {
            boolean selected = active && row.isEnabled();
            row.setElevation(selected ? row.getResources().getDisplayMetrics().density
                    : originalElevation);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                row.setOutlineAmbientShadowColor(selected ? 0x18000000 : originalAmbientShadowColor);
                row.setOutlineSpotShadowColor(selected ? 0x24000000 : originalSpotShadowColor);
            }
        }

        void cancelAnimation() {
            if (animator == null) return;
            animator.cancel();
            animator.removeAllUpdateListeners();
            animator = null;
        }

        void dispose() {
            cancelAnimation();
            if (roundedShape != null) roundedShape.setCornerRadius(originalRadius);
            row.setElevation(originalElevation);
            row.setBackgroundTintList(originalTint);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                row.setOutlineAmbientShadowColor(originalAmbientShadowColor);
                row.setOutlineSpotShadowColor(originalSpotShadowColor);
            }
            row.removeOnAttachStateChangeListener(this);
        }

        @Override public void onViewAttachedToWindow(android.view.View view) {}
        @Override public void onViewDetachedFromWindow(android.view.View view) {
            cancelAnimation();
            alpha = active ? 64 : 0;
            invalidateSelf();
        }

        @Override public boolean isStateful() { return true; }
        @Override protected boolean onStateChange(int[] state) {
            updateShadow();
            invalidateSelf();
            return true;
        }
        @Override public void draw(android.graphics.Canvas canvas) {
            boolean focused = row.hasFocus();
            for (int state : getState()) focused |= state == android.R.attr.state_focused;
            int opacity = row.isEnabled() ? focused ? 192 : alpha : Math.round(alpha * .4f);
            if (opacity == 0) return;
            android.graphics.drawable.Drawable background = row.getBackground();
            // Follow the innermost native shape, including its existing vertical insets.
            while (background != null) {
                android.graphics.drawable.Drawable current = background.getCurrent();
                if (current != background) { background = current; continue; }
                if (background instanceof android.graphics.drawable.InsetDrawable inset) {
                    background = inset.getDrawable();
                } else break;
            }
            android.graphics.Rect nativeBounds = background == null ? getBounds() : background.getBounds();
            bounds.set(nativeBounds.isEmpty() ? getBounds() : nativeBounds);
            bounds.inset(.5f, .5f);
            float radius = background instanceof android.graphics.drawable.GradientDrawable gradient
                    ? Math.max(0f, gradient.getCornerRadius() - .5f) : 0f;
            paint.setColor(color);
            paint.setAlpha(opacity);
            canvas.drawRoundRect(bounds, radius, radius, paint);
        }
        @Override public void setAlpha(int alpha) { /* State supplies the outline opacity. */ }
        @Override public void setColorFilter(android.graphics.ColorFilter filter) { paint.setColorFilter(filter); }
        @Override public int getOpacity() { return android.graphics.PixelFormat.TRANSLUCENT; }
    }

}
