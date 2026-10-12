// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.toolbar.top;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.mockito.Mockito.doReturn;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.app.Dialog;
import android.graphics.Rect;
import android.os.Looper;
import android.view.View;
import android.widget.FrameLayout;

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnit;
import org.mockito.junit.MockitoRule;
import org.robolectric.Robolectric;

import org.chromium.base.test.BaseRobolectricTestRunner;
import org.chromium.chrome.R;
import org.chromium.chrome.browser.omnibox.LocationBar;

/** Exercises the real ToolbarLayout and Android view hierarchy after sidebar reparenting. */
@RunWith(BaseRobolectricTestRunner.class)
public class ArcToolbarReparentingTest {
    @Rule public final MockitoRule mMockitoRule = MockitoJUnit.rule();
    @Mock private LocationBar mLocationBar;

    private Activity mActivity;
    private FrameLayout mRoot;
    private TestToolbar mToolbar;
    private View mOmnibox;

    private static class TestToolbar extends ToolbarLayout {
        private final LocationBar mLocationBar;

        TestToolbar(Activity activity, LocationBar locationBar) {
            super(activity, null);
            mLocationBar = locationBar;
        }

        @Override
        protected CaptureReadinessResult isReadyForTextureCapture() {
            return CaptureReadinessResult.readyForced();
        }

        @Override
        public LocationBar getLocationBar() {
            return mLocationBar;
        }

        @Override
        public void requestKeyboardFocus() {}
    }

    @Before
    public void setUp() {
        mActivity = Robolectric.buildActivity(Activity.class).setup().get();
        mActivity.setTheme(R.style.Theme_BrowserUI_DayNight);
        mRoot = new FrameLayout(mActivity);
        mToolbar = new TestToolbar(mActivity, mLocationBar);
        mOmnibox = new View(mActivity);
        mOmnibox.setPadding(2, 3, 1, 2);
        doReturn(mOmnibox).when(mLocationBar).getContainerView();
        mRoot.addView(mToolbar, new FrameLayout.LayoutParams(200, 60));
        mActivity.setContentView(mRoot);
        mRoot.layout(0, 0, 600, 400);
        mToolbar.layout(130, 40, 330, 100);
        assertNotNull(mToolbar.getWindowToken());
    }

    @Test
    public void sidebarSiblingUsesWindowCoordinates() {
        FrameLayout sidebar = new FrameLayout(mActivity);
        mRoot.addView(sidebar, new FrameLayout.LayoutParams(100, 200));
        sidebar.addView(mOmnibox, new FrameLayout.LayoutParams(80, 30));
        sidebar.layout(100, 70, 200, 270);
        mOmnibox.layout(15, 16, 95, 46);
        int[] toolbarPosition = new int[2];
        int[] omniboxPosition = new int[2];
        mToolbar.getLocationInWindow(toolbarPosition);
        mOmnibox.getLocationInWindow(omniboxPosition);
        int x = omniboxPosition[0] - toolbarPosition[0];
        int y = omniboxPosition[1] - toolbarPosition[1];
        Rect rect = new Rect();
        mToolbar.getLocationBarContentRect(rect);
        assertEquals(new Rect(x + 2, y + 3, x + 79, y + 28), rect);
    }

    @Test
    public void nativeDescendantKeepsDrawCoordinates() {
        mToolbar.addView(mOmnibox, new FrameLayout.LayoutParams(80, 30));
        mOmnibox.layout(12, 14, 92, 44);
        mOmnibox.setTranslationX(5);
        Rect rect = new Rect();
        mToolbar.getLocationBarContentRect(rect);
        assertEquals(new Rect(19, 17, 96, 42), rect);
    }

    @Test
    public void detachedOmniboxClearsPreviousRectangle() {
        mOmnibox.layout(0, 0, 80, 30);
        Rect rect = new Rect(1, 2, 3, 4);
        mToolbar.getLocationBarContentRect(rect);
        assertTrue(rect.isEmpty());
    }

    @Test
    public void foreignWindowClearsPreviousRectangle() {
        Dialog dialog = new Dialog(mActivity);
        dialog.setContentView(mOmnibox);
        try {
            dialog.show();
            // Dialog attachment is queued in Chromium's PAUSED Robolectric looper.
            shadowOf(Looper.getMainLooper()).idle();
            assertNotNull(mOmnibox.getWindowToken());
            assertTrue(mOmnibox.getWindowToken() != mToolbar.getWindowToken());
            Rect rect = new Rect(1, 2, 3, 4);
            mToolbar.getLocationBarContentRect(rect);
            assertTrue(rect.isEmpty());
        } finally {
            dialog.dismiss();
            shadowOf(Looper.getMainLooper()).idle();
        }
    }
}
