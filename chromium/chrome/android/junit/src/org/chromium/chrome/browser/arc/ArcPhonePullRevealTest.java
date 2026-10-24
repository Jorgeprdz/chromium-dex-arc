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

    @Test public void contextualIdentityHasFallbackAndClearsOnReplacement() throws Exception {
        try(var f=new Fixture()) {
            var set=ArcPhonePullReveal.class.getMethod("setIdentity",android.graphics.Bitmap.class,String.class,String.class);
            var icon=android.graphics.Bitmap.createBitmap(16,16,android.graphics.Bitmap.Config.ARGB_8888);
            set.invoke(f.reveal,icon,"github.com","chromium-dex-arc");
            for(String field:new String[]{"mFavicon","mSite","mTitle"}) {
                var value=ArcPhonePullReveal.class.getDeclaredField(field);value.setAccessible(true);
                assertEquals(field.equals("mFavicon")?icon:field.equals("mSite")?"github.com":"chromium-dex-arc",value.get(f.reveal));
            }
            set.invoke(f.reveal,null,"example.test","A long title");
            var favicon=ArcPhonePullReveal.class.getDeclaredField("mFavicon");favicon.setAccessible(true);
            assertNull(favicon.get(f.reveal));
            for(int color:new int[]{Color.WHITE,0xff202124,0xffe87524}) {
                f.reveal.setSurface(color);
                var text=ArcPhonePullReveal.class.getDeclaredField("mTextPaint");text.setAccessible(true);
                int fg=((android.graphics.Paint)text.get(f.reveal)).getColor();
                double a=Color.luminance(color),b=Color.luminance(fg);
                assertTrue((Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5);
            }
            f.reveal.start();f.reveal.pull(f.dp(64));f.reveal.reset(false);
            assertTrue(f.fill().getBounds().isEmpty());
            set.invoke(f.reveal,null,"","");assertNull(favicon.get(f.reveal));
        }
    }

    @Test public void drawCommandsRetainFaviconAndBoundedNonClippingCornerMask() throws Exception {
        try(var f=new Fixture()) {
            var icon=android.graphics.Bitmap.createBitmap(16,16,android.graphics.Bitmap.Config.ARGB_8888);icon.eraseColor(Color.RED);
            var set=ArcPhonePullReveal.class.getMethod("setIdentity",android.graphics.Bitmap.class,String.class,String.class);
            set.invoke(f.reveal,icon,"github.com","Long page title that must fit without leaving its reveal area");
            f.reveal.setSurface(Color.BLUE);f.reveal.start();f.reveal.pull(f.dp(64));
            View gap=f.root.getChildAt(0);
            var image=android.graphics.Bitmap.createBitmap(400,800,android.graphics.Bitmap.Config.ARGB_8888);
            gap.draw(new android.graphics.Canvas(image));
            var recorded=org.robolectric.Shadows.shadowOf(new android.graphics.Canvas());
            // The local ARM64 host cannot run Robolectric's x86 native raster. Check actual
            // Android draw commands and mask bounds here; physical pixel acceptance is pending.
            var canvas=new android.graphics.Canvas(image);gap.draw(canvas);
            recorded=org.robolectric.Shadows.shadowOf(canvas);
            assertEquals(2,recorded.getTextHistoryCount());
            assertTrue(recorded.getDescription().contains("Bitmap"));
            var field=ArcPhonePullReveal.class.getDeclaredField("mCorners");field.setAccessible(true);
            var mask=(android.graphics.drawable.Drawable)field.get(f.reveal);
            assertEquals(new Rect(0,0,400,Math.round(f.dp(16))),mask.getBounds());
            var corners=new android.graphics.Canvas(image);mask.draw(corners);
            assertEquals(1,org.robolectric.Shadows.shadowOf(corners).getPathPaintHistoryCount());
            assertEquals(Color.BLUE,org.robolectric.Shadows.shadowOf(corners).getDrawnPathPaint(0).getColor());
            assertFalse(f.page.getClipToOutline());
            f.reveal.reset(false);assertTrue(mask.getBounds().isEmpty());
        }
    }

    @Test public void approvedShortAndLongPullUseActualPinnedNativeRefreshWidget() {
        for(int dragDp:new int[]{64,119,121}) {
            try(var f=new Fixture()) {
                var refresh=new org.chromium.third_party.android.swiperefresh.SwipeRefreshLayout(f.activity.get());
                final int[] refreshRequests={0};refresh.setOnRefreshListener(()->refreshRequests[0]++);
                assertTrue(refresh.start());assertTrue(f.reveal.start());
                // Real incremental touchscreen delivery; Chromium also rejects single-event flings.
                for(int i=0;i<dragDp;i++) {
                    float excess=f.reveal.pull(f.dp(1));
                    if(excess!=0)refresh.pull(excess);
                }
                refresh.release(f.reveal.release(true));
                assertEquals("refresh at finger drag dp="+dragDp,dragDp>120,refresh.isRefreshing());
                if(refresh.isRefreshing()) {
                    // Deliver the platform animation-end event to the real native callback.
                    android.view.animation.Animation.AnimationListener listener=
                            org.robolectric.util.ReflectionHelpers.getField(refresh,"mRefreshListener");
                    listener.onAnimationEnd(null);
                }
                assertEquals(dragDp>120?1:0,refreshRequests[0]);
                if(dragDp==64) {
                    org.robolectric.shadows.ShadowLooper.idleMainLooper(300,java.util.concurrent.TimeUnit.MILLISECONDS);
                    assertEquals(f.dp(64),f.page.getTranslationY(),.01);
                    assertTrue(f.reveal.isRevealed());
                    // Another short gesture must not become a refresh just because the gap exists.
                    assertTrue(refresh.start());assertTrue(f.reveal.start());
                    for(int i=0;i<64;i++) {float excess=f.reveal.pull(f.dp(1));if(excess!=0)refresh.pull(excess);}
                    refresh.release(f.reveal.release(true));assertFalse(refresh.isRefreshing());
                    f.reveal.onPageScroll();
                    org.robolectric.shadows.ShadowLooper.idleMainLooper(300,java.util.concurrent.TimeUnit.MILLISECONDS);
                    assertEquals(0,f.page.getTranslationY(),0);
                }
                refresh.reset();
            }
        }
    }

    @Test public void shortPullStaysRevealedWithoutForwardingRefreshOrResizingPage() {
        try(var f=new Fixture()) {
            assertTrue(f.reveal.start());assertEquals(1,f.reveals);
            assertEquals(0,f.reveal.pull(f.dp(64)),0);
            assertEquals(f.dp(64),f.page.getTranslationY(),.01);
            assertFalse(f.reveal.release(true));
            org.robolectric.shadows.ShadowLooper.idleMainLooper(300,java.util.concurrent.TimeUnit.MILLISECONDS);
            assertEquals(f.dp(64),f.page.getTranslationY(),.01);
            assertEquals(400,f.page.getWidth());assertEquals(800,f.page.getHeight());
            assertEquals(0,f.page.getTop());assertEquals(0,f.page.getPaddingTop());
            assertTrue(f.reveal.isRevealed());
        }
    }

    @Test public void longPullForwardsOnlyExcessAndRewindRetractsNativeProgress() {
        try(var f=new Fixture()) {
            assertTrue(f.reveal.start());
            assertEquals(f.dp(36.57143f),f.reveal.pull(f.dp(80)),.01);
            assertEquals(f.dp(64),f.page.getTranslationY(),.01);
            assertEquals(-f.dp(36.57143f),f.reveal.pull(-f.dp(32)),.01);
            assertFalse(f.reveal.release(true));
            f.reveal.reset(false);assertTrue(f.reveal.start());
            assertEquals(f.dp(130.28571f),f.reveal.pull(f.dp(121)),.01);
            assertTrue(f.reveal.release(true)); // Chromium still owns its refresh threshold/reload.
        }
    }

    @Test public void coloredGapFollowsLightDarkAndActualPageOrigin() throws Exception {
        try(var f=new Fixture()) {
            f.page.layout(7,11,407,811);f.reveal.setSurface(0xffe87524);
            assertTrue(f.reveal.start());f.reveal.pull(f.dp(40));
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
            f.reveal.start();f.reveal.pull(f.dp(40));f.reveal.release(true);
            float visible=f.page.getTranslationY();
            f.reveal.start();f.reveal.pull(f.dp(4));
            assertEquals(Math.min(f.dp(64),visible+f.dp(4)),f.page.getTranslationY(),.01);
        }
    }

    @Test public void ordinaryScrollCollapsesLatchedGapButDoesNotCancelActivePull() {
        try(var f=new Fixture()) {
            f.reveal.start();f.reveal.pull(f.dp(40));f.reveal.onPageScroll();
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
