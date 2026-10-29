// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import android.app.Activity;
import android.animation.ValueAnimator;
import android.graphics.Rect;
import android.view.KeyEvent;
import android.widget.EditText;
import android.widget.FrameLayout;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcCommandBarTest {
    private static class Fixture {
        Activity activity = Robolectric.buildActivity(Activity.class).setup().get();
        FrameLayout root = new FrameLayout(activity), original = new FrameLayout(activity);
        FrameLayout holder = new FrameLayout(activity);
        EditText editor = new EditText(activity);
        AtomicInteger commits = new AtomicInteger(), sessions = new AtomicInteger();
        ArcOmniboxPlacement placement;
        ArcCommandBar bar;
        Fixture() {
            root.addView(original); original.addView(holder); holder.addView(editor);
            activity.setContentView(root); root.layout(0, 0, 1000, 800); holder.layout(10, 10, 220, 54);
            placement = new ArcOmniboxPlacement(holder);
            bar = new ArcCommandBar(activity, root, holder, editor, placement,
                    () -> new Rect(260, 0, 1000, 800),
                    () -> {sessions.incrementAndGet(); editor.requestFocus(); editor.setText("");},
                    () -> {editor.clearFocus(); sessions.decrementAndGet();}, placement::restore,
                    actions -> List.of(new ArcCommandBar.Result("Tab title", "https://example.com/", "Switch", null, commits::incrementAndGet)),
                    "Search or enter URL…", "Actions  Tab");
            bar.setAppearance(0xffeeeeee, 0xff111111, 0xffbbccdd);
        }
        void finish() {bar.destroy(); activity.finish();}
    }
    @Test public void secondOriginClickKeepsEditorAndLaterOutsideClickCloses() {
        Fixture f = new Fixture();
        f.bar.open(false); f.bar.finishAnimationForTesting();
        android.view.View overlay = (android.view.View) f.bar.panelForTesting().getParent();
        overlay.measure(android.view.View.MeasureSpec.makeMeasureSpec(1000, 1073741824),
                android.view.View.MeasureSpec.makeMeasureSpec(800, 1073741824));
        overlay.layout(0, 0, 1000, 800);
        long now = android.os.SystemClock.uptimeMillis();
        for (int action : new int[] {0, 1}) {
            var event = android.view.MotionEvent.obtain(now, now, action, 100, 24, 0);
            overlay.dispatchTouchEvent(event); event.recycle();
        }
        org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        f.bar.finishAnimationForTesting();
        assertTrue("Second click at moved origin must not dismiss the editor", f.bar.isShowing());
        assertEquals(1, f.sessions.get()); assertTrue(f.editor.hasFocus());
        org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(
                java.time.Duration.ofMillis(android.view.ViewConfiguration.getDoubleTapTimeout() + 1));
        overlay.measure(android.view.View.MeasureSpec.makeMeasureSpec(1000, 1073741824),
                android.view.View.MeasureSpec.makeMeasureSpec(800, 1073741824));
        overlay.layout(0, 0, 1000, 800);
        now = android.os.SystemClock.uptimeMillis();
        for (int action : new int[] {0, 1}) {
            var event = android.view.MotionEvent.obtain(now, now, action, 4, 780, 0);
            overlay.dispatchTouchEvent(event); event.recycle();
        }
        org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        f.bar.finishAnimationForTesting(); assertFalse(f.bar.isShowing());
        assertEquals(0, f.sessions.get()); f.finish();
    }
    @Test public void milkyCommandPanelRetainsGeometryAndUniqueNativeEditor() {
        Fixture f = new Fixture();
        var panel=f.bar.panelForTesting();int padding=panel.getPaddingLeft();float elevation=panel.getElevation();
        var glass=new ArcPhoneGlass(f.root,new ArcPhoneGlass.Capture(){
            public boolean available(){return false;}
            public void copy(Rect r,android.graphics.Bitmap b,java.util.function.Consumer<Boolean> result){result.accept(false);}
            public void close(){}
        });
        f.bar.setGlassSampler(glass);var background=panel.getBackground();assertTrue(background instanceof ArcPhoneGlass.Backdrop);
        f.bar.setAppearance(0xff202124,0xffffffff,0xff404148);assertSame(background,panel.getBackground());
        f.bar.open(false);f.bar.finishAnimationForTesting();assertSame(f.holder,f.editor.getParent());assertEquals(1,f.sessions.get());
        assertEquals(padding,panel.getPaddingLeft());assertEquals(elevation,panel.getElevation(),0f);
        f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_ESCAPE));f.bar.finishAnimationForTesting();
        assertSame(f.original,f.holder.getParent());assertEquals(0,f.sessions.get());
        f.bar.setGlassSampler(null);assertTrue(panel.getBackground() instanceof android.graphics.drawable.GradientDrawable);
        f.finish();glass.destroy();
    }
    @Test public void openingAndEscapeCreateNoTabAndRestoreUniqueEditor() {
        Fixture f = new Fixture();
        f.bar.open(false); assertTrue(f.bar.isShowing()); assertEquals(0, f.commits.get());
        assertSame(f.holder, f.editor.getParent());
        assertEquals(3, f.bar.panelForTesting().getChildCount());
        f.bar.open(false); assertEquals(1, f.sessions.get());
        assertTrue(f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ESCAPE)));
        f.bar.finishAnimationForTesting(); assertFalse(f.bar.isShowing());
        assertSame(f.original, f.holder.getParent()); assertEquals(0, f.commits.get());
        assertEquals(0, f.sessions.get()); f.finish();
    }
    @Test public void addressPopupSelectsNativeUrlAndCtrlTStillStartsEmpty() {
        Fixture f = new Fixture();
        String url = "https://example.test/path?q=1#fragment";
        Runnable focusAddress = () -> {
            f.sessions.incrementAndGet();
            f.editor.requestFocus();
            f.editor.setText(url);
            f.editor.selectAll();
        };
        f.bar.openAddress(focusAddress);
        f.bar.finishAnimationForTesting();
        assertTrue(f.bar.isEditingAddress());
        assertEquals(url, f.editor.getText().toString());
        assertEquals(0, f.editor.getSelectionStart());
        assertEquals(url.length(), f.editor.getSelectionEnd());
        f.editor.setText("edited query");
        f.bar.openAddress(focusAddress);
        assertEquals("edited query", f.editor.getText().toString());
        assertEquals(1, f.sessions.get());
        f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ESCAPE));
        f.bar.finishAnimationForTesting();
        assertSame(f.original, f.holder.getParent());
        assertFalse(f.bar.isEditingAddress());
        assertEquals(0, f.sessions.get());
        f.bar.open(false);
        f.bar.finishAnimationForTesting();
        assertFalse(f.bar.isEditingAddress());
        assertEquals("", f.editor.getText().toString());
        assertEquals(0, f.commits.get());
        f.finish();
    }
    @Test public void tabActionsAndEnterCommitExactlyOnce() {
        Fixture f = new Fixture(); f.bar.open(false); f.bar.finishAnimationForTesting();
        f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_TAB));
        assertTrue(f.bar.actionsForTesting());
        f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER));
        f.bar.finishAnimationForTesting(); assertEquals(1, f.commits.get());
        assertFalse(f.bar.isShowing()); assertEquals(0, f.sessions.get()); f.finish();
    }
    @Test public void typedEnterAndArrowsFallThroughToNativeAutocomplete() {
        Fixture f = new Fixture(); f.bar.open(false); f.bar.finishAnimationForTesting();
        f.editor.setText("example");
        assertFalse(f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER)));
        assertFalse(f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_DPAD_DOWN)));
        assertFalse(f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER)));
        f.bar.commitNativeNavigation(); assertEquals(0, f.commits.get()); f.finish();
    }
    @Test public void resizeDuringOpeningAndDestroyReleaseHolderAndCallbacks() {
        Fixture f = new Fixture(); f.bar.open(false);
        f.root.layout(0, 0, 650, 480); f.bar.resize();
        f.bar.destroy(); assertSame(f.original, f.holder.getParent());
        assertFalse(f.bar.isShowing()); assertEquals(0, f.sessions.get());
        f.bar.destroy(); assertEquals(0, f.sessions.get()); f.activity.finish();
    }
    @Test public void unmatchedActionCannotFallThroughHardwareOrImeIntoWebNavigation() {
        Fixture f = new Fixture(); f.bar.open(true); f.bar.finishAnimationForTesting();
        f.editor.setText("does not match a command");
        assertTrue(f.bar.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER)));
        f.bar.commitNativeNavigation(); assertTrue(f.bar.isShowing()); assertEquals(0, f.commits.get());
        f.finish();
    }
    @Test public void nativeConfirmationInterruptsClosingAndRestoresBeforeNavigation() {
        Fixture f = new Fixture(); f.bar.open(false); f.bar.finishAnimationForTesting();
        f.bar.close(true, null); f.bar.commitNativeNavigation();
        assertFalse(f.bar.isShowing()); assertSame(f.original, f.holder.getParent());
        assertFalse(f.bar.isEditingAddress());
        assertEquals(0, f.sessions.get()); f.finish();
    }
    @Test public void rtlPanelAndSuggestionsUseTheSamePhysicalWindowCoordinates() {
        Fixture f = new Fixture();
        f.activity.getApplicationInfo().flags |= android.content.pm.ApplicationInfo.FLAG_SUPPORTS_RTL;
        f.activity.getApplicationInfo().targetSdkVersion = 36;
        f.root.setLayoutDirection(android.view.View.LAYOUT_DIRECTION_RTL);
        f.bar.open(false); f.bar.finishAnimationForTesting();
        f.root.measure(android.view.View.MeasureSpec.makeMeasureSpec(1000, android.view.View.MeasureSpec.EXACTLY),
                android.view.View.MeasureSpec.makeMeasureSpec(800, android.view.View.MeasureSpec.EXACTLY));
        f.root.layout(0, 0, 1000, 800);
        assertEquals(android.view.View.LAYOUT_DIRECTION_RTL,
                ((android.view.View) f.bar.panelForTesting().getParent()).getLayoutDirection());
        int[] panel = new int[2]; f.bar.panelForTesting().getLocationInWindow(panel);
        assertEquals(panel[0], f.bar.resultsBoundsInWindow().left);
        f.finish();
    }
    @Test public void unchangedViewportDoesNotRequestAnotherPanelLayout() {
        Fixture f = new Fixture(); f.bar.open(false); f.bar.finishAnimationForTesting();
        android.view.View panel = f.bar.panelForTesting();
        panel.measure(android.view.View.MeasureSpec.makeMeasureSpec(700, android.view.View.MeasureSpec.EXACTLY),
                android.view.View.MeasureSpec.makeMeasureSpec(360, android.view.View.MeasureSpec.EXACTLY));
        panel.layout(300, 48, 1000, 408);
        assertFalse(panel.isLayoutRequested());
        f.bar.resize();
        assertFalse("Stable insets/viewport must not schedule perpetual layout", panel.isLayoutRequested());
        f.finish();
    }
}
