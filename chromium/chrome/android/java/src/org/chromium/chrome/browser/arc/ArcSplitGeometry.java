// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Rect;

/** Shared physical pane geometry for Android input, Blink and native composition. */
public final class ArcSplitGeometry {
    private ArcSplitGeometry() {}
    public static Rect[] panes(Rect viewport, float ratio, int inset, int gutter) {
        if (inset < 0 || gutter < 0 || !Float.isFinite(ratio))
            throw new IllegalArgumentException("Invalid split spacing or ratio");
        int middle = viewport.left + Math.round(viewport.width() * Math.max(.2f, Math.min(.8f, ratio)));
        return new Rect[] {
            new Rect(viewport.left + inset, viewport.top + inset,
                    middle - gutter / 2, viewport.bottom - inset),
            new Rect(middle + (gutter - gutter / 2), viewport.top + inset,
                    viewport.right - inset, viewport.bottom - inset)
        };
    }
}
