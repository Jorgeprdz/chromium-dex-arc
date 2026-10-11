// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.assertEquals;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.os.Looper;
import android.view.View;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Lifecycle and window-mode changes must invalidate already queued geometry. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcFrameDispatchTest {
    private View host() {
        Activity activity = Robolectric.buildActivity(Activity.class).setup().get();
        View host = new View(activity);
        activity.setContentView(host);
        shadowOf(Looper.getMainLooper()).idle();
        return host;
    }

    @Test
    public void mobileTransitionBlocksQueuedDesktopGeometry() {
        AtomicBoolean desktop = new AtomicBoolean(true);
        AtomicInteger runs = new AtomicInteger();
        ArcFrameDispatch dispatch = new ArcFrameDispatch(desktop::get);
        dispatch.schedule(host(), runs::incrementAndGet);
        desktop.set(false);
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(0, runs.get());
    }

    @Test
    public void replacementAppliesOnlyLatestFrame() {
        AtomicInteger runs = new AtomicInteger();
        ArcFrameDispatch dispatch = new ArcFrameDispatch(() -> true);
        View host = host();
        dispatch.schedule(host, () -> runs.addAndGet(1));
        dispatch.schedule(host, () -> runs.addAndGet(10));
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(10, runs.get());
    }

    @Test
    public void destroyedCoordinatorCannotPostAnotherFrame() {
        AtomicInteger runs = new AtomicInteger();
        ArcFrameDispatch dispatch = new ArcFrameDispatch(() -> true);
        View host = host();
        dispatch.schedule(host, runs::incrementAndGet);
        dispatch.destroy();
        dispatch.schedule(host, runs::incrementAndGet);
        shadowOf(Looper.getMainLooper()).idle();
        assertEquals(0, runs.get());
    }
}
