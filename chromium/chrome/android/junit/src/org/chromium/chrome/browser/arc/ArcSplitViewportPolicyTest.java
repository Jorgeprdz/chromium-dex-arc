// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import static org.mockito.Mockito.*;
import org.junit.Test;
import org.chromium.content_public.browser.NavigationController;
@org.junit.runner.RunWith(org.robolectric.RobolectricTestRunner.class)
@org.robolectric.annotation.Config(manifest=org.robolectric.annotation.Config.NONE,sdk={30,36})
@org.robolectric.annotation.GraphicsMode(org.robolectric.annotation.GraphicsMode.Mode.LEGACY)
@org.robolectric.annotation.SQLiteMode(org.robolectric.annotation.SQLiteMode.Mode.LEGACY)
public class ArcSplitViewportPolicyTest {
    @Test public void repeatedResizeNeverOverridesSiteModeOrReloads() {
        ArcSplitViewportPolicy policy = new ArcSplitViewportPolicy();
        NavigationController controller = mock(NavigationController.class);
        for (int i = 0; i < 10; i++) {
            policy.update(controller, 800); policy.update(controller, 400);
            policy.update(controller, 800);
        }
        policy.retain(null, null); policy.clear();
        verifyNoInteractions(controller);
    }
    @Test public void invalidWidthsNeverReachNavigation() {
        ArcSplitViewportPolicy policy = new ArcSplitViewportPolicy();
        NavigationController controller = mock(NavigationController.class);
        policy.update(controller, Float.NaN); policy.update(controller, -1);
        policy.update(null, 400); policy.update(controller, Float.POSITIVE_INFINITY);
        policy.clear(); verifyNoInteractions(controller);
    }
}
