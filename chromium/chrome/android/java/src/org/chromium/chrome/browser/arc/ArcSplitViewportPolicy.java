// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import org.chromium.content_public.browser.NavigationController;

/** Responsive sizing belongs to WebContents, without changing the user's site mode. */
public final class ArcSplitViewportPolicy {
    // Compatibility hook for callers/probes. CompositorViewHolder owns physical pane sizing;
    // NavigationController must not be used to implement responsive layout or page-scale repair.
    public void update(NavigationController controller, float widthDp) {}
    public void retain(NavigationController first, NavigationController second) {}
    public void clear() {}
}
