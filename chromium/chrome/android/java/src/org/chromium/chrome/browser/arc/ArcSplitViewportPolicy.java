// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import java.util.IdentityHashMap;
import java.util.Map;
import org.chromium.content_public.browser.NavigationController;

/** Temporary per-pane UA overrides; responsive layout uses the actual WebContents viewport.
 * Never reloads a document or changes the profile/site preference. Server-specific mobile
 * variants may require a later user-initiated navigation. */
public final class ArcSplitViewportPolicy {
    private static final float MOBILE_DP = 600, DESKTOP_DP = 640;
    // true: we own a desktop -> mobile override; false: user explicitly restored desktop.
    private final Map<NavigationController, Boolean> mOverrides = new IdentityHashMap<>();

    public void update(NavigationController controller, float widthDp) {
        if (controller == null || !Float.isFinite(widthDp) || widthDp <= 0) return;
        if (widthDp >= DESKTOP_DP) { release(controller); return; }
        Boolean owned = mOverrides.get(controller);
        if (owned != null) {
            if (owned && controller.getUseDesktopUserAgent()) mOverrides.put(controller, false);
            return;
        }
        if (widthDp < MOBILE_DP && controller.getUseDesktopUserAgent()) {
            mOverrides.put(controller, true);
            controller.setUseDesktopUserAgent(false, false, false);
        }
    }
    public void retain(NavigationController first, NavigationController second) {
        for (NavigationController controller : new java.util.ArrayList<>(mOverrides.keySet()))
            if (controller != first && controller != second) release(controller);
    }
    private void release(NavigationController controller) {
        Boolean owned = mOverrides.remove(controller);
        if (Boolean.TRUE.equals(owned) && !controller.getUseDesktopUserAgent())
            controller.setUseDesktopUserAgent(true, false, false);
    }
    public void clear() { retain(null, null); }
}
