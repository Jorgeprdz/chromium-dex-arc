// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.graphics.Rect;
import android.graphics.drawable.ColorDrawable;
import android.os.Looper;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;

import org.chromium.chrome.R;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.LooperMode;
import org.robolectric.annotation.SQLiteMode;

/** Real Android view layout, clipping, focus and touch dispatch; no Chromium model replacement. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {29, 36})
@LooperMode(LooperMode.Mode.PAUSED)
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcCompactOmniboxTest {
    private Activity mActivity;
    private ActivityController<Activity> mActivityController;
    private FrameLayout mHolder;
    private NativeTouchLocationBar mBar;
    private LinearLayout mStatus;
    private ImageView mIcon;
    private EditText mUrl;
    private View mActions;
    private View mOther;
    private ArcCompactOmnibox mCompact;
    private ColorDrawable mFavicon;
    private ViewGroup.LayoutParams mStatusParams;
    private Rect mExpandedStatus;

    @Before public void setUp() {
        mActivityController = Robolectric.buildActivity(Activity.class).setup();
        mActivity = mActivityController.get();
        mHolder = new FrameLayout(mActivity);
        mBar = new NativeTouchLocationBar(mActivity);
        mBar.setId(R.id.location_bar);
        mBar.setPadding(5, 3, 13, 7);
        mHolder.addView(mBar, new FrameLayout.LayoutParams(240, 60));
        mUrl = new EditText(mActivity);
        mUrl.setId(R.id.url_bar);
        mUrl.setSingleLine(true);
        mUrl.setText("https://example.com/original");
        FrameLayout.LayoutParams urlParams = new FrameLayout.LayoutParams(180, 50);
        urlParams.leftMargin = 52;
        mBar.addView(mUrl, urlParams);
        mStatus = new LinearLayout(mActivity);
        mStatus.setId(R.id.location_bar_status);
        mStatus.setPadding(7, 0, 19, 0);
        mIcon = new ImageView(mActivity);
        mIcon.setId(R.id.location_bar_status_icon);
        mFavicon = new ColorDrawable(0xff4433dd);
        mIcon.setImageDrawable(mFavicon);
        mStatus.addView(mIcon, new LinearLayout.LayoutParams(24, 24));
        mStatusParams = new FrameLayout.LayoutParams(50, 48);
        ((FrameLayout.LayoutParams) mStatusParams).leftMargin = 4;
        mBar.addView(mStatus, 0, mStatusParams);
        mActions = new View(mActivity);
        mActions.setId(R.id.action_buttons_segment);
        mBar.addView(mActions, new FrameLayout.LayoutParams(8, 40));
        mOther = new View(mActivity);
        mOther.setFocusableInTouchMode(true);
        mHolder.addView(mOther, new FrameLayout.LayoutParams(1, 1));
        mActivity.setContentView(mHolder);
        mOther.requestFocus();
        layout(240);
        mExpandedStatus = bounds(mStatus);
        mCompact = new ArcCompactOmnibox(mHolder);
    }

    @After public void tearDown() {
        if (mCompact != null) mCompact.destroy();
        mActivityController.pause().stop().destroy();
    }

    @Test public void compactCentersActualFaviconWithoutChangingNativeViewsOrModel() {
        mCompact.setCompact(true);
        layout(64);
        assertEquals(32, iconCenter(), 1);
        assertNotNull(mUrl.getClipBounds());
        assertEquals(0, mUrl.getClipBounds().width());
        assertEquals(View.VISIBLE, mUrl.getVisibility());
        assertSame(mFavicon, mIcon.getDrawable());
        assertSame(mUrl, mBar.findViewById(R.id.url_bar));
        assertSame(mStatusParams, mStatus.getLayoutParams());
        assertEquals("https://example.com/original", mUrl.getText().toString());
        assertEquals(View.INVISIBLE, mActions.getVisibility());
    }

    @Test public void compactTracksNarrowAndRepeatedNativeResizeInBothDirections() {
        mCompact.setCompact(true);
        for (int direction : new int[] {View.LAYOUT_DIRECTION_LTR, View.LAYOUT_DIRECTION_RTL}) {
            mBar.setLayoutDirection(direction);
            for (int width : new int[] {88, 44, 72, 56, 88}) {
                layout(width);
                assertEquals(width / 2f, iconCenter(), 1);
                assertNotNull(mUrl.getClipBounds());
                assertEquals(0, mUrl.getClipBounds().width());
                assertEquals(0f, mBar.getTranslationX(), 0);
            }
        }
    }

    @Test public void realUrlRequestFocusRestoresDrawingBeforeEditingAndBlurRecompacts() {
        mCompact.setCompact(true);
        layout(64);
        assertTrue(mUrl.requestFocus());
        assertTrue(mUrl.getWidth() > 0);
        assertNull(mUrl.getClipBounds());
        assertEquals(View.VISIBLE, mActions.getVisibility());
        mUrl.setText("https://example.com/new");
        assertEquals("https://example.com/new", mUrl.getText().toString());
        assertTrue(mOther.requestFocus());
        assertNotNull(mUrl.getClipBounds());
        assertEquals(0, mUrl.getClipBounds().width());
        assertEquals(32, iconCenter(), 1);
    }

    @Test public void actualNativeBackgroundTouchReachesUrlAndRevealsEditor() {
        mCompact.setCompact(true);
        layout(64);
        assertNotNull(mUrl.getClipBounds());
        // Native tablet background touches forward to the nearest shown URL/delete target.
        MotionEvent down = MotionEvent.obtain(0, 1, MotionEvent.ACTION_DOWN, 58, 55, 0);
        MotionEvent up = MotionEvent.obtain(0, 2, MotionEvent.ACTION_UP, 58, 55, 0);
        assertTrue(mBar.dispatchTouchEvent(down));
        assertTrue(mBar.dispatchTouchEvent(up));
        down.recycle();
        up.recycle();
        assertTrue(mUrl.hasFocus());
        assertNull(mUrl.getClipBounds());
    }

    @Test public void centeredNativeIconStillReceivesItsExistingClickAction() {
        boolean[] clicked = {false};
        mIcon.setOnClickListener(view -> clicked[0] = true);
        mCompact.setCompact(true);
        layout(128);
        Rect icon = new Rect();
        mIcon.getDrawingRect(icon);
        mBar.offsetDescendantRectToMyCoords(mIcon, icon);
        MotionEvent down = MotionEvent.obtain(0, 1, MotionEvent.ACTION_DOWN,
                icon.exactCenterX(), icon.exactCenterY(), 0);
        MotionEvent up = MotionEvent.obtain(0, 2, MotionEvent.ACTION_UP,
                icon.exactCenterX(), icon.exactCenterY(), 0);
        mBar.dispatchTouchEvent(down);
        mBar.dispatchTouchEvent(up);
        down.recycle();
        up.recycle();
        shadowOf(Looper.getMainLooper()).idle();
        assertTrue("The centered real icon retains its native action", clicked[0]);
        assertFalse(mUrl.hasFocus());
    }

    @Test public void expansionRestoresOriginalBoundsClippingVisibilityAndPadding() {
        Rect clip = new Rect(2, 3, 130, 38);
        mUrl.setClipBounds(clip);
        mActions.setVisibility(View.GONE);
        mCompact.setCompact(true);
        layout(64);
        mCompact.restore();
        layout(240);
        assertEquals(mExpandedStatus, bounds(mStatus));
        assertEquals(180, mUrl.getWidth());
        assertEquals(clip, mUrl.getClipBounds());
        assertEquals(View.GONE, mActions.getVisibility());
        assertSame(mStatusParams, mStatus.getLayoutParams());
        assertEquals(5, mBar.getPaddingLeft());
        assertEquals(13, mBar.getPaddingRight());
        assertEquals(7, mStatus.getPaddingLeft());
        assertEquals(19, mStatus.getPaddingRight());
    }

    @Test public void nativeGoneAfterSuppressionSurvivesGlobalLayoutAndExpansion() {
        mCompact.setCompact(true);
        layout(64);
        mActions.setVisibility(View.GONE);
        layout(64);
        assertEquals(View.GONE, mActions.getVisibility());
        mCompact.restore();
        assertEquals(View.GONE, mActions.getVisibility());
    }

    @Test public void nativeGoneAfterSuppressionSurvivesExpansionBeforeNextLayout() {
        mCompact.setCompact(true);
        layout(64);
        mActions.setVisibility(View.GONE);
        mCompact.restore();
        assertEquals(View.GONE, mActions.getVisibility());
    }

    @Test public void nativeVisibleFromGoneIsSuppressedThenRestoredOnExpansion() {
        mActions.setVisibility(View.GONE);
        mCompact.setCompact(true);
        layout(64);
        mActions.setVisibility(View.VISIBLE);
        layout(64);
        assertEquals(View.INVISIBLE, mActions.getVisibility());
        mCompact.restore();
        assertEquals(View.VISIBLE, mActions.getVisibility());
    }

    @Test public void nativeVisibleFromGoneSurvivesExpansionBeforeNextLayout() {
        mActions.setVisibility(View.GONE);
        mCompact.setCompact(true);
        layout(64);
        mActions.setVisibility(View.VISIBLE);
        mCompact.restore();
        assertEquals(View.VISIBLE, mActions.getVisibility());
    }

    @Test public void nativeGoneBeforeFocusAndFocusedUpdatesKeepNativeVisibility() {
        mCompact.setCompact(true);
        layout(64);
        mActions.setVisibility(View.GONE);
        assertTrue(mUrl.requestFocus());
        assertEquals(View.GONE, mActions.getVisibility());
        mActions.setVisibility(View.VISIBLE);
        layout(64);
        assertEquals(View.VISIBLE, mActions.getVisibility());
        mCompact.restore();
        assertEquals(View.VISIBLE, mActions.getVisibility());
        assertNull(mUrl.getClipBounds());
    }

    @Test public void destroyRestoresAndRemovesFocusAndLayoutObservers() {
        mCompact.setCompact(true);
        layout(64);
        mCompact.destroy();
        layout(240);
        assertEquals(mExpandedStatus, bounds(mStatus));
        assertNull(mUrl.getClipBounds());
        mUrl.requestFocus();
        mOther.requestFocus();
        layout(80);
        assertNull(mUrl.getClipBounds());
        mCompact.setCompact(true);
        assertNull(mUrl.getClipBounds());
    }

    @Test public void alreadyFocusedEditorStaysEditableDuringCollapse() {
        assertTrue(mUrl.requestFocus());
        mCompact.setCompact(true);
        layout(64);
        assertNull(mUrl.getClipBounds());
        assertEquals(View.VISIBLE, mActions.getVisibility());
        mCompact.setCompact(false);
        mOther.requestFocus();
        assertNull(mUrl.getClipBounds());
    }

    @Test public void zeroSizeWaitsForActualLayoutAndRestoreIsIdempotent() {
        layout(0);
        mCompact.setCompact(true);
        layout(0);
        layout(64);
        assertEquals(32, iconCenter(), 1);
        mCompact.restore();
        mCompact.restore();
        layout(240);
        assertEquals(mExpandedStatus, bounds(mStatus));
    }

    private void layout(int width) {
        mBar.getLayoutParams().width = width;
        mHolder.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(60, View.MeasureSpec.EXACTLY));
        mHolder.layout(0, 0, width, 60);
        mHolder.getViewTreeObserver().dispatchOnGlobalLayout();
    }

    private float iconCenter() {
        Rect rect = new Rect();
        mIcon.getDrawingRect(rect);
        mBar.offsetDescendantRectToMyCoords(mIcon, rect);
        return rect.exactCenterX();
    }

    private static Rect bounds(View view) {
        return new Rect(view.getLeft(), view.getTop(), view.getRight(), view.getBottom());
    }

    /** Adapter for pinned tablet's shown-target touch routing; Android EditText stays real. */
    private static class NativeTouchLocationBar extends FrameLayout {
        NativeTouchLocationBar(Activity activity) { super(activity); }
        @Override public boolean onTouchEvent(MotionEvent event) {
            // Pinned LocationBarTablet nearest shown-target routing, including its coordinates.
            View target = findViewById(R.id.url_bar);
            if (!target.isShown()) return false;
            Rect bounds = new Rect(0, 0, target.getWidth(), target.getHeight());
            offsetDescendantRectToMyCoords(target, bounds);
            float x = event.getX();
            float y = event.getY();
            float dx = distanceToRange(bounds.left, bounds.right, x);
            float dy = distanceToRange(bounds.top, bounds.bottom, y);
            event.setLocation(x + dx, y + dy);
            return target.onTouchEvent(event);
        }
        private static float distanceToRange(float min, float max, float value) {
            return value < min ? (min - value) : value > max ? (max - value) : 0;
        }
    }
}
