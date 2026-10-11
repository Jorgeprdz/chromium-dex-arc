// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.os.Looper;
import android.view.View;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

/** Bookmark/favicon refresh may rebuild controls without losing keyboard focus. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcCollectionsFocusTest {
    @Test
    public void focusedEntrySurvivesRefreshByIdentity() {
        checkFocus(false);
    }

    @Test
    public void focusedFavoriteSurvivesRefreshByIdentity() {
        checkFocus(true);
    }

    private void checkFocus(boolean favorite) {
        Activity activity = Robolectric.buildActivity(Activity.class).setup().get();
        ArcTabActions.NativeTabs tabs = mock(ArcTabActions.NativeTabs.class);
        when(tabs.exists(anyInt())).thenReturn(true);
        ArcSidebarStore store = new ArcSidebarStore(null);
        ArcCollectionsController controller = new ArcCollectionsController(
                store, new ArcTabActions(store, tabs), tabs);
        String id = controller.rememberTab(7, "https://example.test", "Saved", favorite);
        ArcCollectionsView view = new ArcCollectionsView(activity, controller,
                () -> new ArcCollectionsView.CurrentTab(7, "https://example.test", "Saved"),
                (entry, button) -> {});
        activity.setContentView(view);
        shadowOf(Looper.getMainLooper()).idle();
        View before = view.findViewWithTag("arc-entry:" + id);
        assertTrue(before.requestFocus());
        assertTrue(before.hasFocus());
        view.refresh();
        View after = view.findViewWithTag("arc-entry:" + id);
        assertNotSame(before, after);
        assertTrue(after.hasFocus());
        view.destroy();
        controller.destroy();
    }
}
