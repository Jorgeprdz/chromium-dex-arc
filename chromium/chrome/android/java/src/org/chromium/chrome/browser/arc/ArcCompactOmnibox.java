// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Rect;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewTreeObserver;

import org.chromium.chrome.R;

import java.util.IdentityHashMap;
import java.util.Map;

/** Compact presentation of the existing Chromium omnibox, with its native focus/touch path. */
public final class ArcCompactOmnibox {
    private final ViewGroup mLocationBar;
    private final View mStatus;
    private final View mIcon;
    private final View mUrl;
    private final Map<View, ControlVisibility> mHiddenControls = new IdentityHashMap<>();
    private final ViewTreeObserver.OnGlobalLayoutListener mLayoutListener = this::update;
    private final ViewTreeObserver.OnGlobalFocusChangeListener mFocusListener =
            (oldFocus, newFocus) -> update();
    private final View.OnAttachStateChangeListener mAttachListener =
            new View.OnAttachStateChangeListener() {
                @Override public void onViewAttachedToWindow(View view) {
                    observe();
                    update();
                }
                @Override public void onViewDetachedFromWindow(View view) {
                    stopObserving();
                }
            };
    private ViewTreeObserver mObserver;
    private Rect mUrlClip;
    private Rect mNativeUrlBounds;
    private Rect mCompactUrlBounds;
    private Rect mNativeStatusBounds;
    private Rect mCompactStatusBounds;
    private boolean mCompact;
    private boolean mApplied;
    private boolean mUpdating;
    private boolean mDestroyed;

    /** Accepts either the real LocationBar view or its original location_bar_holder. */
    public ArcCompactOmnibox(View host) {
        View locationBar = host.findViewById(R.id.location_bar);
        if (locationBar == null) locationBar = host;
        if (!(locationBar instanceof ViewGroup)) {
            throw new IllegalArgumentException("Compact omnibox requires Chromium's LocationBar");
        }
        mLocationBar = (ViewGroup) locationBar;
        mStatus = mLocationBar.findViewById(R.id.location_bar_status);
        mIcon = mLocationBar.findViewById(R.id.location_bar_status_icon);
        mUrl = mLocationBar.findViewById(R.id.url_bar);
        if (mStatus == null || mIcon == null || mUrl == null) {
            throw new IllegalArgumentException("Compact omnibox requires native status and URL views");
        }
        mLocationBar.addOnAttachStateChangeListener(mAttachListener);
        observe();
    }

    /** Editing always takes precedence over the collapsed sidebar presentation. */
    public void setCompact(boolean compact) {
        if (mDestroyed) return;
        mCompact = compact;
        update();
    }

    /** Restores the native presentation on expansion or when leaving desktop mode. */
    public void restore() {
        setCompact(false);
    }

    /** Restores presentation and releases observers; safe to call more than once. */
    public void destroy() {
        if (mDestroyed) return;
        restore();
        mDestroyed = true;
        stopObserving();
        mLocationBar.removeOnAttachStateChangeListener(mAttachListener);
    }

    private void observe() {
        if (mDestroyed) return;
        ViewTreeObserver observer = mLocationBar.getViewTreeObserver();
        if (observer == mObserver) return;
        stopObserving();
        mObserver = observer;
        mObserver.addOnGlobalLayoutListener(mLayoutListener);
        mObserver.addOnGlobalFocusChangeListener(mFocusListener);
    }

    private void stopObserving() {
        if (mObserver != null && mObserver.isAlive()) {
            mObserver.removeOnGlobalLayoutListener(mLayoutListener);
            mObserver.removeOnGlobalFocusChangeListener(mFocusListener);
        }
        mObserver = null;
    }

    private void update() {
        if (mDestroyed || mUpdating) return;
        mUpdating = true;
        try {
            if (!mCompact || mUrl.hasFocus()) {
                restorePresentation();
                return;
            }
            if (!mApplied) {
                mUrlClip = mUrl.getClipBounds();
                mApplied = true;
            }
            for (int i = 0; i < mLocationBar.getChildCount(); i++) {
                View child = mLocationBar.getChildAt(i);
                if (child == mStatus || child == mUrl || child.getId() == R.id.focus_thief) {
                    continue;
                }
                int visibility = child.getVisibility();
                ControlVisibility saved = mHiddenControls.get(child);
                if (saved == null) {
                    saved = new ControlVisibility(visibility);
                    mHiddenControls.put(child, saved);
                } else if (visibility != saved.appliedVisibility) {
                    // Chromium may change a control while the sidebar is compact. Retain the latest
                    // native value rather than the value observed when the sidebar first collapsed.
                    saved.nativeVisibility = visibility;
                }
                // INVISIBLE retains Chromium's constraints and native LayoutParams.
                if (visibility == View.VISIBLE) child.setVisibility(View.INVISIBLE);
                saved.appliedVisibility = child.getVisibility();
            }
            // Clip drawing only: the real, VISIBLE UrlBar still receives tablet background touches
            // and programmatic requestFocus(). Its normal native focus listener remains installed.
            mUrl.setClipBounds(new Rect(0, 0, 0, mUrl.getHeight()));
            // The UrlBar's original hit rectangle can overlap the centered status icon. Give the
            // unfocused editor zero horizontal bounds so native icon dispatch still wins. Tablet
            // background routing calls the real editor directly, even at zero width, and focusing
            // restores its native bounds synchronously. No invisible duplicate touch target exists.
            Rect urlBounds = bounds(mUrl);
            if (mCompactUrlBounds == null || !urlBounds.equals(mCompactUrlBounds)) {
                mNativeUrlBounds = urlBounds;
            }
            mUrl.layout(mUrl.getLeft(), mUrl.getTop(), mUrl.getLeft(), mUrl.getBottom());
            mCompactUrlBounds = bounds(mUrl);
            if (mLocationBar.getWidth() <= 0 || mIcon.getWidth() <= 0) return;
            Rect statusBounds = bounds(mStatus);
            if (mCompactStatusBounds == null || !statusBounds.equals(mCompactStatusBounds)) {
                mNativeStatusBounds = statusBounds;
            }
            Rect iconBounds = new Rect();
            mIcon.getDrawingRect(iconBounds);
            mLocationBar.offsetDescendantRectToMyCoords(mIcon, iconBounds);
            int shift = Math.round(mLocationBar.getWidth() / 2f - iconBounds.exactCenterX());
            if (shift != 0) {
                mStatus.layout(mStatus.getLeft() + shift, mStatus.getTop(),
                        mStatus.getRight() + shift, mStatus.getBottom());
            }
            mCompactStatusBounds = bounds(mStatus);
        } finally {
            mUpdating = false;
        }
    }

    private void restorePresentation() {
        if (!mApplied) return;
        mUrl.setClipBounds(mUrlClip);
        if (mNativeUrlBounds != null) {
            mUrl.layout(mNativeUrlBounds.left, mNativeUrlBounds.top,
                    mNativeUrlBounds.right, mNativeUrlBounds.bottom);
        }
        mNativeUrlBounds = null;
        mCompactUrlBounds = null;
        for (Map.Entry<View, ControlVisibility> entry : mHiddenControls.entrySet()) {
            View child = entry.getKey();
            ControlVisibility saved = entry.getValue();
            // A native change after the last compact update already has the correct expanded value.
            if (child.getVisibility() == saved.appliedVisibility) {
                child.setVisibility(saved.nativeVisibility);
            }
        }
        mHiddenControls.clear();
        if (mNativeStatusBounds != null) {
            mStatus.layout(mNativeStatusBounds.left, mNativeStatusBounds.top,
                    mNativeStatusBounds.right, mNativeStatusBounds.bottom);
        }
        mNativeStatusBounds = null;
        mCompactStatusBounds = null;
        mUrlClip = null;
        mApplied = false;
        mLocationBar.requestLayout();
    }

    private static final class ControlVisibility {
        int nativeVisibility;
        int appliedVisibility;

        ControlVisibility(int visibility) {
            nativeVisibility = visibility;
            appliedVisibility = visibility;
        }
    }

    private static Rect bounds(View view) {
        return new Rect(view.getLeft(), view.getTop(), view.getRight(), view.getBottom());
    }
}
