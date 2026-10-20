// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

/** Center capture/release hysteresis; quarter layouts remain freely adjustable. */
public final class ArcSplitResizePolicy {
    private ArcSplitResizePolicy() {}
    public static float snap(float ratio, boolean captured) {
        if (!Float.isFinite(ratio)) throw new IllegalArgumentException("Non-finite ratio");
        if (Math.abs(ratio-.5f) <= (captured ? .045f : .025f)) return .5f;
        return Math.max(.2f, Math.min(.8f, ratio));
    }
}
