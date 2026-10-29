// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Outline;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.view.Window;

/** Clips only Archium's existing decor. DeX caption/shadow remain owned by the system. */
public final class ArcDesktopWindowFrame {
    private final View mDecor;
    private final ViewOutlineProvider mOriginalOutline;
    private final boolean mOriginalClip;
    private boolean mApplied;
    private int mRadius;
    private final ViewOutlineProvider mOutline = new ViewOutlineProvider() {
        @Override public void getOutline(View view, Outline outline) {
            int width = view.getWidth(), height = view.getHeight();
            if (width <= 0 || height <= 0) { outline.setEmpty(); return; }
            outline.setRoundRect(0, 0, width, height,
                    Math.min(mRadius, Math.min(width, height) / 2f));
        }
    };
    private final View.OnLayoutChangeListener mLayout = (view,l,t,r,b,ol,ot,or,ob) -> {
        if (r-l != or-ol || b-t != ob-ot) view.invalidateOutline();
    };

    public ArcDesktopWindowFrame(Window window) {
        mDecor = window.getDecorView();
        mOriginalOutline = mDecor.getOutlineProvider();
        mOriginalClip = mDecor.getClipToOutline();
    }

    public void applyRadius(int radius) {
        if (mApplied && mRadius == radius) return;
        mRadius = Math.max(0, radius);
        if (!mApplied) mDecor.addOnLayoutChangeListener(mLayout);
        mApplied = true;
        mDecor.setOutlineProvider(mOutline);
        mDecor.setClipToOutline(true);
        mDecor.invalidateOutline();
    }

    public void clear() {
        if (!mApplied) return;
        mApplied = false;
        mDecor.removeOnLayoutChangeListener(mLayout);
        mDecor.setOutlineProvider(mOriginalOutline);
        mDecor.setClipToOutline(mOriginalClip);
        mDecor.invalidateOutline();
    }
}
