// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.hardware.display.DisplayManager;
import android.os.Build;
import android.view.Display;
import android.view.WindowManager;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import org.robolectric.shadows.ShadowDisplay;
import org.robolectric.shadows.ShadowDisplayManager;

/** Real Android shadows; registered in chrome_junit_tests, not a host stub fixture. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36}, qualifiers = "sw411dp-w1100dp-h700dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcDesktopAppearanceTest {
    private Activity windowActivity(Activity activity) {
        Activity window = spy(activity);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            // Bare Robolectric Activity wraps Application context. Model the
            // real window-scoped Chrome Activity for width eligibility.
            doReturn(true).when(window).isUiContext();
        }
        return window;
    }
    private Display externalDisplay() {
        ShadowDisplayManager.addDisplay("w1100dp-h700dp-mdpi");
        int id = ShadowDisplayManager.addDisplay("w1100dp-h700dp-mdpi");
        DisplayManager manager = RuntimeEnvironment.getApplication().getSystemService(DisplayManager.class);
        Display display = manager.getDisplay(id);
        ShadowDisplay shadow = shadowOf(display);
        shadow.setWidth(1100);
        assertNotEquals(Display.DEFAULT_DISPLAY, display.getDisplayId());
        return display;
    }

    @Test
    public void externalDisplayBeforeAndAfterAttach() {
        ActivityController<Activity> controller = Robolectric.buildActivity(Activity.class).create();
        Activity activity = windowActivity(controller.get());
        Display external = externalDisplay();
        doReturn(external).when(activity).getDisplay();
        assertFalse(activity.getWindow().getDecorView().isAttachedToWindow());
        assertSame(external, ArcDesktopAppearance.activityDisplay(activity));
        assertTrue(ArcDesktopAppearance.isDesktopWindow(activity));
        controller.start().resume().visible();
        assertTrue(activity.getWindow().getDecorView().isAttachedToWindow());
        assertSame(external, ArcDesktopAppearance.activityDisplay(activity));
        assertTrue(ArcDesktopAppearance.isDesktopWindow(activity));
        controller.pause().stop().destroy();
    }

    @Test
    public void defaultDisplayBeforeAndAfterAttachIsMobile() {
        ActivityController<Activity> controller = Robolectric.buildActivity(Activity.class).create();
        Activity activity = windowActivity(controller.get());
        Display display = ShadowDisplay.getDefaultDisplay();
        doReturn(display).when(activity).getDisplay();
        assertEquals(0, ArcDesktopAppearance.activityDisplay(activity).getDisplayId());
        assertFalse(ArcDesktopAppearance.isDesktopWindow(activity));
        controller.start().resume().visible();
        assertFalse(ArcDesktopAppearance.isDesktopWindow(activity));
        controller.pause().stop().destroy();
    }

    @Test
    public void unsupportedDisplayUsesActivityWindowManager() {
        Activity activity = windowActivity(Robolectric.buildActivity(Activity.class).create().get());
        WindowManager manager = mock(WindowManager.class);
        Display display = externalDisplay();
        doThrow(new UnsupportedOperationException("nonvisual context")).when(activity).getDisplay();
        doReturn(manager).when(activity).getWindowManager();
        when(manager.getDefaultDisplay()).thenReturn(display);
        assertSame(display, ArcDesktopAppearance.activityDisplay(activity));
        assertTrue(ArcDesktopAppearance.isDesktopWindow(activity));
    }

    @Test
    public void nullDisplayAndManagerAreSafeAndMultiwindowStillWorks() {
        Activity activity = windowActivity(Robolectric.buildActivity(Activity.class).create().get());
        doReturn(null).when(activity).getDisplay();
        doReturn(null).when(activity).getWindowManager();
        assertNull(ArcDesktopAppearance.activityDisplay(activity));
        assertFalse(ArcDesktopAppearance.isDesktopWindow(activity));
        doReturn(true).when(activity).isInMultiWindowMode();
        assertTrue(ArcDesktopAppearance.isDesktopWindow(activity));
        ArcDesktopAppearance.setUiMode(activity, ArcDesktopPolicy.MODE_MOBILE);
        assertFalse(ArcDesktopAppearance.isDesktopWindow(activity));
    }

    @Test
    @Config(sdk = 29)
    public void api29UsesWindowManagerWithoutCallingGetDisplay() {
        Activity activity = spy(Robolectric.buildActivity(Activity.class).create().get());
        WindowManager manager = mock(WindowManager.class);
        doReturn(manager).when(activity).getWindowManager();
        when(manager.getDefaultDisplay()).thenReturn(externalDisplay());
        assertNotEquals(0, ArcDesktopAppearance.activityDisplay(activity).getDisplayId());
    }
}
