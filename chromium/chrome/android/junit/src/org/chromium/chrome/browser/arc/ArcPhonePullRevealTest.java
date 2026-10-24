// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.drawable.ColorDrawable;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcPhonePullRevealTest {
    private static class Fixture implements AutoCloseable {
        final org.robolectric.android.controller.ActivityController<Activity> activity =
                Robolectric.buildActivity(Activity.class).setup();
        final FrameLayout root = new FrameLayout(activity.get());
        final FrameLayout page = new FrameLayout(activity.get());
        int reveals;
        final ArcPhonePullReveal reveal;
        Fixture() {
            root.addView(page,new FrameLayout.LayoutParams(400,800));
            root.layout(0,0,400,800);page.layout(0,0,400,800);
            reveal=new ArcPhonePullReveal(page,()->reveals++);reveal.setEnabled(true);
        }
        float dp(float value){return value*page.getResources().getDisplayMetrics().density;}
        ColorDrawable fill() throws Exception {
            var f=ArcPhonePullReveal.class.getDeclaredField("mFill");f.setAccessible(true);
            return (ColorDrawable)f.get(reveal);
        }
        @Override public void close(){reveal.destroy();activity.pause().stop().destroy();}
    }

    @Test public void shortPullStaysRevealedWithoutForwardingRefreshOrResizingPage() {
        try(var f=new Fixture()) {
            assertTrue(f.reveal.start());assertEquals(1,f.reveals);
            assertEquals(0,f.reveal.pull(f.dp(80)),0);
            assertEquals(f.dp(40),f.page.getTranslationY(),.01);
            assertFalse(f.reveal.release(true));
            org.robolectric.shadows.ShadowLooper.idleMainLooper(300,java.util.concurrent.TimeUnit.MILLISECONDS);
            assertEquals(f.dp(56),f.page.getTranslationY(),.01);
            assertEquals(400,f.page.getWidth());assertEquals(800,f.page.getHeight());
            assertEquals(0,f.page.getTop());assertEquals(0,f.page.getPaddingTop());
            assertTrue(f.reveal.isRevealed());
        }
    }

    @Test public void longPullForwardsOnlyExcessAndRewindRetractsNativeProgress() {
        try(var f=new Fixture()) {
            assertTrue(f.reveal.start());
            assertEquals(f.dp(28),f.reveal.pull(f.dp(140)),.01);
            assertEquals(f.dp(56),f.page.getTranslationY(),.01);
            assertEquals(-f.dp(28),f.reveal.pull(-f.dp(60)),.01);
            assertFalse(f.reveal.release(true));
            f.reveal.reset(false);assertTrue(f.reveal.start());
            assertEquals(f.dp(88),f.reveal.pull(f.dp(200)),.01);
            assertTrue(f.reveal.release(true)); // Chromium still owns its refresh threshold/reload.
        }
    }

    @Test public void coloredGapFollowsLightDarkAndActualPageOrigin() throws Exception {
        try(var f=new Fixture()) {
            f.page.layout(7,11,407,811);f.reveal.setSurface(0xffe87524);
            assertTrue(f.reveal.start());f.reveal.pull(f.dp(80));
            assertEquals(0xffe87524,f.fill().getColor());
            assertEquals(new Rect(7,11,407,11+Math.round(f.dp(40))),f.fill().getBounds());
            f.reveal.setSurface(0xff202124);assertEquals(0xff202124,f.fill().getColor());
            f.reveal.setSurface(Color.WHITE);assertEquals(Color.WHITE,f.fill().getColor());
            assertEquals(2,f.root.getChildCount());
            View gap=f.root.getChildAt(0);assertSame(f.page,f.root.getChildAt(1));
            assertFalse(gap.isEnabled());assertFalse(gap.isClickable());assertFalse(gap.isFocusable());
            assertEquals(View.IMPORTANT_FOR_ACCESSIBILITY_NO,gap.getImportantForAccessibility());
        }
    }

    @Test public void translatedPageReceivesRealLocalTouchCoordinates() {
        try(var f=new Fixture()) {
            final float[] local={-1};
            f.page.setOnTouchListener((v,e)->{local[0]=e.getY();return true;});
            f.reveal.start();f.reveal.pull(f.dp(80));f.reveal.release(true);
            org.robolectric.shadows.ShadowLooper.idleMainLooper(300,java.util.concurrent.TimeUnit.MILLISECONDS);
            float y=f.page.getTranslationY()+20;
            for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}) {
                var e=MotionEvent.obtain(0,1,action,30,y,0);
                assertTrue(f.root.dispatchTouchEvent(e));e.recycle();
            }
            assertEquals(20,local[0],.01);
        }
    }

    @Test public void cancellationDisableResizeAndDestroyRestoreOwnedTranslation() throws Exception {
        try(var f=new Fixture()) {
            f.page.setTranslationY(9);f.reveal.start();f.reveal.pull(f.dp(80));
            assertFalse(f.reveal.release(false));f.reveal.reset(false);
            assertEquals(9,f.page.getTranslationY(),0);assertFalse(f.reveal.isRevealed());
            f.reveal.start();f.reveal.pull(f.dp(80));f.reveal.setEnabled(false);
            assertEquals(9,f.page.getTranslationY(),0);assertFalse(f.reveal.start());
            f.reveal.setEnabled(true);f.reveal.start();f.reveal.pull(f.dp(80));
            f.page.layout(0,0,800,400);assertEquals(9,f.page.getTranslationY(),0);
            f.reveal.start();f.reveal.pull(f.dp(80));f.reveal.destroy();
            assertEquals(9,f.page.getTranslationY(),0);assertTrue(f.fill().getBounds().isEmpty());
        }
    }

    @Test public void newPullDuringSettleContinuesFromVisibleOffset() {
        try(var f=new Fixture()) {
            f.reveal.start();f.reveal.pull(f.dp(80));f.reveal.release(true);
            float visible=f.page.getTranslationY();
            f.reveal.start();f.reveal.pull(f.dp(4));
            assertEquals(Math.min(f.dp(56),visible+f.dp(2)),f.page.getTranslationY(),.01);
        }
    }

    @Test public void ordinaryScrollCollapsesLatchedGapButDoesNotCancelActivePull() {
        try(var f=new Fixture()) {
            f.reveal.start();f.reveal.pull(f.dp(80));f.reveal.onPageScroll();
            assertEquals(f.dp(40),f.page.getTranslationY(),.01);
            f.reveal.release(true);
            org.robolectric.shadows.ShadowLooper.idleMainLooper(300,java.util.concurrent.TimeUnit.MILLISECONDS);
            f.reveal.onPageScroll();
            org.robolectric.shadows.ShadowLooper.idleMainLooper(300,java.util.concurrent.TimeUnit.MILLISECONDS);
            assertEquals(0,f.page.getTranslationY(),0);assertFalse(f.reveal.isRevealed());
        }
    }

    @Test public void tinyPullDoesNotLatchAndDetachedPageDeclinesGesture() {
        try(var f=new Fixture()) {
            f.reveal.start();f.reveal.pull(f.dp(4));assertFalse(f.reveal.release(true));
            f.reveal.reset(false);assertFalse(f.reveal.isRevealed());
            f.root.removeView(f.page);assertFalse(f.reveal.start());
        }
    }
}
