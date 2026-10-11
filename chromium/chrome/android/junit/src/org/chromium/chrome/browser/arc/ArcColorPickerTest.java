// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Looper;
import android.view.View;
import android.widget.EditText;
import android.widget.SeekBar;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;

/** Actual Android views and preferences, not a string contract. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcColorPickerTest {
    private ActivityController<Activity> mController;
    private SharedPreferences mPreferences;
    private AlertDialog mDialog;
    private Integer mPreview;

    @Before
    public void setUp() {
        mController = Robolectric.buildActivity(Activity.class).setup();
        Activity activity = mController.get();
        mPreferences = activity.getSharedPreferences("picker_test", Context.MODE_PRIVATE);
        mPreferences.edit().clear().putInt(ArcDesktopAppearance.COLOR_KEY, 0xff123456).commit();
        mDialog = new ArcColorPicker(activity, mPreferences,
                new String[] {"Slate", "Lavender", "Sage", "Sand", "Rose", "Graphite", "Ocean", "Coral"},
                new String[] {"Red", "Green", "Blue"}, color -> mPreview = color).show();
        shadowOf(Looper.getMainLooper()).idle();
    }

    @After
    public void tearDown() {
        mDialog.dismiss();
        shadowOf(Looper.getMainLooper()).idle();
        mController.pause().stop().destroy();
    }

    private View tagged(String tag) {
        return mDialog.findViewById(android.R.id.content).findViewWithTag(tag);
    }

    private EditText hex() {
        return (EditText) tagged("arc-color-hex");
    }

    private void clickButton(int which) {
        mDialog.getButton(which).performClick();
        shadowOf(Looper.getMainLooper()).idle();
    }

    @Test
    public void previewAndCancelNeverPersistDraft() {
        hex().setText("#998AC3");
        assertEquals(Integer.valueOf(0xff998ac3), mPreview);
        assertEquals(0xff123456, mPreferences.getInt(ArcDesktopAppearance.COLOR_KEY, 0));
        clickButton(AlertDialog.BUTTON_NEGATIVE);
        assertEquals(0xff123456, mPreferences.getInt(ArcDesktopAppearance.COLOR_KEY, 0));
        assertNull(mPreview);
    }

    @Test
    public void applyPersistsValidHexAndClearsPreview() {
        hex().setText("#998AC3");
        clickButton(AlertDialog.BUTTON_POSITIVE);
        assertEquals(0xff998ac3, mPreferences.getInt(ArcDesktopAppearance.COLOR_KEY, 0));
        assertNull(mPreview);
    }

    @Test
    public void invalidHexBlocksApplyAndClearsPresetSelection() {
        tagged("arc-color-preset:1").performClick();
        assertTrue(tagged("arc-color-preset:1").isSelected());
        hex().setText("#wrong");
        assertFalse(mDialog.getButton(AlertDialog.BUTTON_POSITIVE).isEnabled());
        assertFalse(tagged("arc-color-preset:1").isSelected());
        assertEquals(0xff123456, mPreferences.getInt(ArcDesktopAppearance.COLOR_KEY, 0));
    }

    @Test
    public void eightPresetsRemainKeyboardAccessible() {
        for (int i = 0; i < 8; i++) {
            View swatch = tagged("arc-color-preset:" + i);
            assertNotNull(swatch);
            assertTrue(swatch.isFocusable());
            assertNotNull(swatch.getContentDescription());
        }
        assertNull(tagged("arc-color-preset:8"));
    }

    @Test
    public void resetCanBeCancelledWithoutChangingPreference() {
        clickButton(AlertDialog.BUTTON_NEUTRAL);
        assertEquals(Integer.valueOf(ArcDesktopAppearance.DEFAULT_COLOR), mPreview);
        assertEquals(0xff123456, mPreferences.getInt(ArcDesktopAppearance.COLOR_KEY, 0));
        clickButton(AlertDialog.BUTTON_NEGATIVE);
        assertEquals(0xff123456, mPreferences.getInt(ArcDesktopAppearance.COLOR_KEY, 0));
    }

    @Test
    public void applyingResetRemovesCustomPreference() {
        clickButton(AlertDialog.BUTTON_NEUTRAL);
        clickButton(AlertDialog.BUTTON_POSITIVE);
        assertFalse(mPreferences.contains(ArcDesktopAppearance.COLOR_KEY));
    }

    @Test
    public void presetKeepsRgbAndHexConsistent() {
        tagged("arc-color-preset:1").performClick();
        assertEquals("#998AC3", hex().getText().toString());
        assertEquals(153, ((SeekBar) tagged("arc-color-rgb:0")).getProgress());
        assertEquals(138, ((SeekBar) tagged("arc-color-rgb:1")).getProgress());
        assertEquals(195, ((SeekBar) tagged("arc-color-rgb:2")).getProgress());
    }
}
