// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Rect;
import android.os.Build;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowInsets;
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
public class ArcPhoneStatusFadeTest {
    @Test public void sampledBackdropSharesBoundsAndDetachesWithoutAddingATouchView() throws Exception {
        var activity=Robolectric.buildActivity(Activity.class).setup();
        var decor=new Decor(activity.get());decor.layout(0,0,400,800);
        var owner=new ArcPhoneStatusFade(decor);owner.update(true,Color.WHITE);
        final int[] draws={0};
        var backdrop=new android.graphics.drawable.ColorDrawable(Color.BLUE) {
            @Override public void draw(android.graphics.Canvas canvas){draws[0]++;super.draw(canvas);}
        };
        owner.setBackdrop(backdrop);
        Rect region=new Rect();owner.getBackdropBounds(region);
        assertEquals(new Rect(0,0,400,30),region);assertEquals(region,backdrop.getBounds());
        assertNotNull(backdrop.getCallback());
        drawable(owner).draw(new android.graphics.Canvas());assertEquals(1,draws[0]);
        assertEquals(0,decor.getChildCount());owner.setBackdrop(null);assertNull(backdrop.getCallback());
        owner.destroy();activity.pause().stop().destroy();
    }

    @Test public void toolbarUsesStableStatusInsetWhileLeavingFullscreen() throws Exception {
        WindowInsets raw = new WindowInsets.Builder()
                .setInsets(WindowInsets.Type.statusBars(), Insets.NONE)
                .setInsetsIgnoringVisibility(WindowInsets.Type.statusBars(), Insets.of(0,30,0,0))
                .build();
        assertEquals(30, ArcPhoneStatusFade.toolbarTopInset(raw));
    }

    // OS inset delivery is explicit; overlay, layout, input and drawable are actual Android views.
    private static class Decor extends FrameLayout {
        WindowInsets raw;
        Decor(Activity activity) { super(activity); raw = insets(30, 24, 0); }
        @Override public WindowInsets getRootWindowInsets() { return raw; }
    }
    private static WindowInsets insets(int top, int bottom, int ime) {
        WindowInsets.Builder builder = new WindowInsets.Builder()
                .setSystemWindowInsets(Insets.of(0,top,0,bottom));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            builder.setInsets(WindowInsets.Type.statusBars(), Insets.of(0,top,0,0))
                    .setInsets(WindowInsets.Type.navigationBars(), Insets.of(0,0,0,bottom))
                    .setInsets(WindowInsets.Type.ime(), Insets.of(0,0,0,ime));
        }
        return builder.build();
    }
    private static ArcPhoneStatusFade.Fade drawable(ArcPhoneStatusFade owner) throws Exception {
        var field=ArcPhoneStatusFade.class.getDeclaredField("mFade");field.setAccessible(true);
        return (ArcPhoneStatusFade.Fade) field.get(owner);
    }
    @Test public void gradientIsTranslucentAndEndsWithoutAnOpaqueStripe() {
        for(int c:new int[]{Color.WHITE,0xff202124}) {
            int[] stops=ArcPhoneStatusFade.Fade.colors(c);
            assertTrue(Color.alpha(stops[0]) <= 180);assertTrue(Color.alpha(stops[1]) <= 180);
            assertEquals(0,Color.alpha(stops[2]));
            for(int s:stops)assertEquals(c&0x00ffffff,s&0x00ffffff);
        }
    }
    @Test public void clockBackingMeetsAaEvenOverOppositePageColor() {
        // The plateau under indicators remains translucent; use worst-case black/white web backing.
        for(int surface:new int[]{Color.WHITE,0xff202124}) {
            int stop=ArcPhoneStatusFade.Fade.colors(surface)[1];
            int page=surface==Color.WHITE?Color.BLACK:Color.WHITE;
            double a=Color.alpha(stop)/255.;
            int mixed=Color.rgb((int)(Color.red(stop)*a+Color.red(page)*(1-a)),
                    (int)(Color.green(stop)*a+Color.green(page)*(1-a)),
                    (int)(Color.blue(stop)*a+Color.blue(page)*(1-a)));
            double l=Color.luminance(mixed);
            assertTrue(surface==Color.WHITE?(l+.05)/.05>=4.5:1.05/(l+.05)>=4.5);
        }
    }
    @Test public void liveThemeChangeUpdatesShaderWithoutReplacingOverlayOrContent() throws Exception {
        var activity=Robolectric.buildActivity(Activity.class).setup();var decor=new Decor(activity.get());decor.layout(0,0,400,800);
        var page=new View(activity.get());decor.addView(page);var owner=new ArcPhoneStatusFade(decor);
        owner.update(true,Color.WHITE);var fade=drawable(owner);
        var field=ArcPhoneStatusFade.Fade.class.getDeclaredField("mPaint");field.setAccessible(true);
        var paint=(android.graphics.Paint)field.get(fade);var light=paint.getShader();assertNotNull(light);
        owner.update(true,Color.WHITE);assertSame(light,paint.getShader());
        owner.update(true,0xff202124);assertNotSame(light,paint.getShader());
        assertSame(fade,drawable(owner));assertSame(page,decor.getChildAt(0));assertNotNull(fade.getCallback());
        owner.destroy();activity.pause().stop().destroy();
    }
    @Test public void metadataHysteresisDoesNotFlipOnNeutralChanges() {
        int light=ArcPhoneStatusFade.selectSurface(Color.WHITE,0);
        int dark=ArcPhoneStatusFade.selectSurface(Color.BLACK,light);
        assertEquals(Color.WHITE,light);assertEquals(0xff202124,dark);
        int neutral=0xff808080;
        assertEquals(light,ArcPhoneStatusFade.selectSurface(neutral,light));
        assertEquals(dark,ArcPhoneStatusFade.selectSurface(neutral,dark));
        assertEquals(light,ArcPhoneStatusFade.selectSurface(Color.WHITE,dark));
    }
    @Test @Config(sdk={29,30,36}) public void repeatedInsetsNeverPadOrMoveWebContentAndImeDoesNotExpandFade() throws Exception {
        var activity=Robolectric.buildActivity(Activity.class).setup();var decor=new Decor(activity.get());
        decor.setPadding(3,7,5,9);decor.layout(0,0,400,800);
        var owner=new ArcPhoneStatusFade(decor);owner.update(true,Color.WHITE);
        var fade=drawable(owner);assertEquals(new Rect(0,0,400,30),fade.getBounds());
        for(int i=0;i<3;i++) {decor.raw=insets(30,24,300);owner.update(true,Color.WHITE);}
        assertEquals(new Rect(0,0,400,30),fade.getBounds());
        assertEquals(7,decor.getPaddingTop());assertEquals(9,decor.getPaddingBottom());
        decor.raw=insets(24,0,0);decor.layout(0,0,800,400);
        assertEquals(new Rect(0,0,800,24),fade.getBounds());
        owner.destroy();activity.pause().stop().destroy();
    }
    @Test public void fullscreenHiddenIndicatorsAndResumeRestoreBounds() throws Exception {
        var activity=Robolectric.buildActivity(Activity.class).setup();var decor=new Decor(activity.get());decor.layout(0,0,400,800);
        var owner=new ArcPhoneStatusFade(decor);owner.update(true,Color.WHITE);
        decor.raw=insets(0,0,0);owner.update(true,Color.WHITE);assertTrue(drawable(owner).getBounds().isEmpty());
        owner.update(false,Color.WHITE);decor.raw=insets(30,24,0);owner.update(true,0xff202124);
        assertEquals(new Rect(0,0,400,30),drawable(owner).getBounds());
        owner.destroy();activity.pause().stop().destroy();
    }
    @Test public void visualOverlayDoesNotInterceptPageTouchesOrAccessibility() {
        var activity=Robolectric.buildActivity(Activity.class).setup();var decor=new Decor(activity.get());
        var content=new View(activity.get());final int[] touches={0};content.setOnTouchListener((v,event)->{touches[0]++;return true;});
        decor.addView(content,new FrameLayout.LayoutParams(400,800));decor.layout(0,0,400,800);content.layout(0,0,400,800);
        var owner=new ArcPhoneStatusFade(decor);owner.update(true,Color.WHITE);
        for(int action:new int[]{MotionEvent.ACTION_DOWN,MotionEvent.ACTION_UP}) {
            MotionEvent event=MotionEvent.obtain(1,2,action,20,10,0);assertTrue(decor.dispatchTouchEvent(event));event.recycle();
        }
        assertEquals(2,touches[0]);assertEquals(1,decor.getChildCount());
        owner.destroy();activity.pause().stop().destroy();
    }
    @Test public void disablingDesktopAndDestroyRemoveDrawableAndLayoutListener() throws Exception {
        var activity=Robolectric.buildActivity(Activity.class).setup();var decor=new Decor(activity.get());decor.layout(0,0,400,800);
        var owner=new ArcPhoneStatusFade(decor);owner.update(true,Color.WHITE);var fade=drawable(owner);
        assertNotNull(fade.getCallback());owner.update(false,Color.WHITE);assertNull(fade.getCallback());
        Rect previous=new Rect(fade.getBounds());decor.raw=insets(90,24,0);decor.layout(0,0,410,800);assertEquals(previous,fade.getBounds());
        owner.update(true,0xff202124);owner.destroy();assertNull(fade.getCallback());
        activity.pause().stop().destroy();
    }
    @Test public void activityRecreationUsesFreshInsetsAndNoSavedOverlay() throws Exception {
        for(int top:new int[]{30,24}) {
            var activity=Robolectric.buildActivity(Activity.class).setup();var decor=new Decor(activity.get());
            decor.raw=insets(top,24,0);decor.layout(0,0,400,800);var owner=new ArcPhoneStatusFade(decor);
            owner.update(true,Color.WHITE);assertEquals(top,drawable(owner).getBounds().height());owner.destroy();
            activity.pause().stop().destroy();
        }
    }
}
