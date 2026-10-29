// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.tasks.tab_management.vertical_tabs;

import static org.junit.Assert.assertEquals;

import android.app.Activity;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.util.ReflectionHelpers;
import org.robolectric.util.ReflectionHelpers.ClassParameter;

import org.chromium.base.test.BaseRobolectricTestRunner;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

/** Tests the actual Chromium binder's regular active-tab color across frame colors. */
@RunWith(BaseRobolectricTestRunner.class)
public class ArcTabSelectionTest {
    @Test
    public void regularActiveTabUsesPaleChosenHue() {
        Activity activity = Robolectric.buildActivity(Activity.class).setup().get();
        ArcDesktopAppearance.setUiMode(activity, ArcDesktopPolicy.MODE_ARC);
        try {
            assertEquals(0xff7365d8, ArcDesktopAppearance.activeTabSurface(activity, false));
            // Hand-derived pale capsules for the selected orange and blue frame colors.
            for (int[] colors : new int[][] {{0xffee4400, 0xfffce0d5}, {0xff0044ee, 0xffd5e0fc}}) {
                int seed = colors[0];
                ArcDesktopAppearance.preferences(activity).edit()
                        .putInt(ArcDesktopAppearance.COLOR_KEY, seed).commit();
                ColorStateList background = ReflectionHelpers.callStaticMethod(
                        TabVerticalViewBinder.class, "getBackgroundTintList",
                        ClassParameter.from(Context.class, activity),
                        ClassParameter.from(boolean.class, true),
                        ClassParameter.from(boolean.class, false),
                        ClassParameter.from(boolean.class, false));
                int foreground = ReflectionHelpers.callStaticMethod(
                        TabVerticalViewBinder.class, "getTextColor",
                        ClassParameter.from(Context.class, activity),
                        ClassParameter.from(boolean.class, true),
                        ClassParameter.from(boolean.class, false));
                assertEquals(colors[1], background.getDefaultColor());
                assertEquals(Color.BLACK, foreground);
            }
        } finally {
            ArcDesktopAppearance.preferences(activity).edit().clear().commit();
            activity.finish();
        }
    }
}
