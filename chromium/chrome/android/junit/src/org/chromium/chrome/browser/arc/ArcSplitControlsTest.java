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
    @Test public void capsuleIsWhiteAccessibleAndBusyDoesNotSwapAgain() {
        Activity activity=Robolectric.buildActivity(Activity.class).setup().get();
        AtomicInteger swaps=new AtomicInteger();
        ArcSplitDividerView divider=new ArcSplitDividerView(activity,swaps::incrementAndGet,r -> {},"Intercambiar paneles");
        activity.setContentView(divider);
        assertEquals(Color.WHITE,((GradientDrawable)divider.buttonForTesting().getBackground()).getColor().getDefaultColor());
        assertEquals("Intercambiar paneles",divider.buttonForTesting().getContentDescription());
        divider.buttonForTesting().performClick();assertEquals(1,swaps.get());
        divider.setBusy(true);divider.buttonForTesting().performClick();assertEquals(1,swaps.get());
        divider.setBusy(false);divider.buttonForTesting().performClick();assertEquals(2,swaps.get());activity.finish();
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
