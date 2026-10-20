// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import android.app.Activity;
import android.animation.ValueAnimator;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.widget.FrameLayout;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import org.robolectric.util.ReflectionHelpers;
import org.robolectric.util.ReflectionHelpers.ClassParameter;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcSplitControlsTest {
    @Test public void capsuleExpandsWithoutSwappingAndActionsCloseBeforeCallback() {
        Activity activity=Robolectric.buildActivity(Activity.class).setup().get();
        AtomicInteger swaps=new AtomicInteger(),exits=new AtomicInteger();
        ArcSplitDividerView divider=new ArcSplitDividerView(activity,swaps::incrementAndGet,
                exits::incrementAndGet,r -> {},"Redimensionar y opciones","Intercambiar paneles","Salir de vista dividida");
        FrameLayout root=new FrameLayout(activity);root.addView(divider,new FrameLayout.LayoutParams(48,600));activity.setContentView(root);
        root.layout(0,0,1000,600);divider.layout(450,0,498,600);
        assertEquals(Color.WHITE,((GradientDrawable)divider.buttonForTesting().getBackground()).getColor().getDefaultColor());
        divider.buttonForTesting().performClick();assertEquals(0,swaps.get());assertTrue(divider.isExpandedForTesting());
        divider.swapForTesting().performClick();assertEquals(1,swaps.get());assertFalse(divider.isExpandedForTesting());
        divider.buttonForTesting().performClick();divider.exitForTesting().performClick();
        assertEquals(1,exits.get());assertFalse(divider.isExpandedForTesting());
        divider.buttonForTesting().performClick();divider.setBusy(true);assertFalse(divider.isExpandedForTesting());
        divider.buttonForTesting().performClick();assertFalse(divider.isExpandedForTesting());activity.finish();
    }
    @Test public void escapeOutsideAndHiddenWindowDismissWithoutAction() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();AtomicInteger actions=new AtomicInteger();
        ArcSplitDividerView d=new ArcSplitDividerView(a,actions::incrementAndGet,actions::incrementAndGet,r->{},"Opciones","Intercambiar","Salir");
        a.setContentView(d);d.layout(0,0,48,600);d.buttonForTesting().performClick();
        assertTrue(d.dispatchKeyEvent(new android.view.KeyEvent(android.view.KeyEvent.ACTION_DOWN,android.view.KeyEvent.KEYCODE_ESCAPE)));
        assertFalse(d.isExpandedForTesting());assertEquals(0,actions.get());
        d.buttonForTesting().performClick();d.dismissActions();assertFalse(d.isExpandedForTesting());
        d.buttonForTesting().performClick();d.setVisibility(android.view.View.GONE);assertFalse(d.isExpandedForTesting());
        d.destroy();a.finish();
    }
    @Test public void gripDragResizesWithoutOpeningActionsAndCancelDoesNotClick() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();List<Float> ratios=new ArrayList<>();
        ArcSplitDividerView d=new ArcSplitDividerView(a,()->fail("swap on drag"),()->fail("exit on drag"),ratios::add,"Opciones","Intercambiar","Salir");
        FrameLayout root=new FrameLayout(a);root.addView(d,new FrameLayout.LayoutParams(48,600));a.setContentView(root);root.layout(0,0,1000,600);d.layout(0,0,48,600);d.setGeometry(.5f,1000);
        long now=android.os.SystemClock.uptimeMillis();
        for(int i=0;i<3;i++){android.view.MotionEvent e=android.view.MotionEvent.obtain(now,now+i*20,i==0?0:i==1?2:1,i==0?24:124,300,0);d.dispatchTouchEvent(e);e.recycle();}
        assertFalse(ratios.isEmpty());assertEquals(.6f,ratios.get(0),.01f);assertFalse(d.isExpandedForTesting());d.destroy();a.finish();
    }
    @Test public void outsideTouchDetachAndReducedMotionLeaveNoPopupWindow() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        FrameLayout root=new FrameLayout(a);a.setContentView(root);
        ArcSplitDividerView d=new ArcSplitDividerView(a,()->fail("outside swap"),()->fail("outside exit"),r->{},"Options","Swap","Exit");
        root.addView(d,new FrameLayout.LayoutParams(48,600));root.layout(0,0,1000,600);d.layout(450,0,498,600);
        ReflectionHelpers.callStaticMethod(ValueAnimator.class,"setDurationScale",ClassParameter.from(float.class,0f));
        try {
            d.buttonForTesting().performClick();assertTrue(d.isExpandedForTesting());
            android.view.View actions=(android.view.View)d.swapForTesting().getParent();assertEquals(1f,actions.getScaleX(),0f);assertEquals(1f,actions.getAlpha(),0f);
            android.view.MotionEvent e=android.view.MotionEvent.obtain(0,0,android.view.MotionEvent.ACTION_OUTSIDE,-1,-1,0);
            actions.getRootView().dispatchTouchEvent(e);e.recycle();assertFalse(d.isExpandedForTesting());
            d.buttonForTesting().performClick();root.removeView(d);assertFalse(d.isExpandedForTesting());d.destroy();
        } finally {ReflectionHelpers.callStaticMethod(ValueAnimator.class,"setDurationScale",ClassParameter.from(float.class,1f));controller.pause().stop().destroy();}
    }
    @Test public void escapeDismissesWhenAnActionHasKeyboardFocus() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        ArcSplitDividerView d=new ArcSplitDividerView(a,()->fail("swap"),()->fail("exit"),r->{},"Options","Swap","Exit");
        a.setContentView(d);d.layout(0,0,48,600);d.buttonForTesting().performClick();
        org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        d.swapForTesting().setFocusableInTouchMode(true);assertTrue(d.swapForTesting().requestFocus());
        // Exercise our popup content boundary; native WindowManager key tracking is separate.
        android.view.View content=(android.view.View)d.swapForTesting().getParent();
        assertTrue(content.dispatchKeyEvent(new android.view.KeyEvent(android.view.KeyEvent.ACTION_DOWN,android.view.KeyEvent.KEYCODE_ESCAPE)));
        assertFalse(d.isExpandedForTesting());d.destroy();controller.pause().stop().destroy();
    }
    @Test public void expandedGripCanStillResizeWithoutTriggeringAnAction() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();List<Float> ratios=new ArrayList<>();
        ArcSplitDividerView d=new ArcSplitDividerView(a,()->fail("swap"),()->fail("exit"),ratios::add,"Options","Swap","Exit");
        a.setContentView(d);d.layout(0,0,48,600);d.setGeometry(.5f,1000);d.buttonForTesting().performClick();
        android.view.View grip=((android.view.ViewGroup)d.swapForTesting().getParent()).getChildAt(1);
        long now=android.os.SystemClock.uptimeMillis();
        for(int i=0;i<3;i++){android.view.MotionEvent e=android.view.MotionEvent.obtain(now,now+i*20,i==0?0:i==1?2:1,i==0?16:116,24,0);grip.dispatchTouchEvent(e);e.recycle();}
        assertFalse(ratios.isEmpty());assertEquals(.6f,ratios.get(0),.01f);assertFalse(d.isExpandedForTesting());
        d.destroy();controller.pause().stop().destroy();
    }
    @Test public void seamPassesPageTouchesAndDestroyDisablesReopening() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        ArcSplitDividerView d=new ArcSplitDividerView(a,()->{},()->{},r->{},"Options","Swap","Exit");
        a.setContentView(d);d.layout(0,0,48,600);d.setGeometry(.5f,1000);
        android.view.MotionEvent e=android.view.MotionEvent.obtain(0,0,android.view.MotionEvent.ACTION_DOWN,2,100,0);
        assertFalse(d.dispatchTouchEvent(e));e.recycle();
        d.buttonForTesting().performClick();assertTrue(d.isExpandedForTesting());d.destroy();
        d.buttonForTesting().performClick();assertFalse(d.isExpandedForTesting());controller.pause().stop().destroy();
    }
    @Test public void frameUsesThemeAndSharedGeometryWithoutInterceptingPageTouches() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();ArcSplitFrameView frame=new ArcSplitFrameView(a);
        frame.setAppearance(0xff789abc);frame.setGeometry(new android.graphics.Rect(216,0,1216,600),.5f,true);
        assertEquals(0xff789abc,frame.surfaceForTesting());assertFalse(frame.isClickable());assertFalse(frame.isFocusable());
        android.graphics.Rect[] panes=ArcSplitGeometry.panes(new android.graphics.Rect(216,0,1216,600),.5f,4,8);
        assertEquals(new android.graphics.Rect(220,4,712,596),panes[0]);assertEquals(new android.graphics.Rect(720,4,1212,596),panes[1]);
        frame.setGeometry(new android.graphics.Rect(216,0,1216,600),.8f,false);
        assertEquals(ArcSplitGeometry.panes(new android.graphics.Rect(216,0,1216,600),.8f,4,8)[1],frame.activeBoundsForTesting());a.finish();
    }
    @Test public void swapAnimatesProgressAndSettlesExactlyOnce() {
        ArcSplitSwapAnimator animation=new ArcSplitSwapAnimator();List<Float> frames=new ArrayList<>();AtomicInteger done=new AtomicInteger();
        animation.start(frames::add,done::incrementAndGet);
        assertTrue(animation.isRunning());assertEquals(180,animation.animatorForTesting().getDuration());
        animation.animatorForTesting().setCurrentFraction(.5f);
        float middle=frames.get(frames.size()-1);assertTrue(middle>0 && middle<1);
        animation.settle();animation.settle();
        assertFalse(animation.isRunning());assertEquals(1f,frames.get(frames.size()-1),0f);assertEquals(1,done.get());
    }
    @Test public void reducedMotionSkipsMovementAndDestroyDisablesFutureAnimation() {
        ReflectionHelpers.callStaticMethod(ValueAnimator.class,"setDurationScale",ClassParameter.from(float.class,0f));
        try {
            ArcSplitSwapAnimator animation=new ArcSplitSwapAnimator();List<Float> frames=new ArrayList<>();AtomicInteger done=new AtomicInteger();
            animation.start(frames::add,done::incrementAndGet);
            assertFalse(animation.isRunning());assertEquals(List.of(1f),frames);assertEquals(1,done.get());
            animation.destroy();animation.start(frames::add,done::incrementAndGet);assertEquals(1,done.get());
        } finally {ReflectionHelpers.callStaticMethod(ValueAnimator.class,"setDurationScale",ClassParameter.from(float.class,1f));}
    }
    @Test public void repeatedSwapFinishesOldBeforeStartingNewAndDestroySettles() {
        ArcSplitSwapAnimator animation=new ArcSplitSwapAnimator();AtomicInteger done=new AtomicInteger();List<Float> first=new ArrayList<>(),second=new ArrayList<>();
        animation.start(first::add,done::incrementAndGet);animation.start(second::add,done::incrementAndGet);
        assertEquals(1,done.get());assertEquals(1f,first.get(first.size()-1),0f);
        animation.destroy();assertEquals(2,done.get());assertEquals(1f,second.get(second.size()-1),0f);assertFalse(animation.isRunning());
    }
}
