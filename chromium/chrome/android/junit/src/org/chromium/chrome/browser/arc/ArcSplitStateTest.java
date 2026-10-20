// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import org.junit.Test;

/** Identity/geometry state only: no claim of two WebContents rendered on Android. */
public class ArcSplitStateTest {
    @Test public void pairStartsEqualWithFirstActive() {
        ArcSplitState state = new ArcSplitState();
        assertFalse(state.isSplit()); assertTrue(state.start(17, 42));
        assertEquals(17, state.leftId()); assertEquals(42, state.rightId());
        assertEquals(17, state.activeId()); assertEquals(.5f, state.ratio(), 0f);
    }
    @Test public void invalidPairDoesNotReplaceExistingState() {
        ArcSplitState state = new ArcSplitState(); state.start(17, 42); state.activate(42);
        assertFalse(state.start(17, 17)); assertFalse(state.start(-1, 42));
        assertFalse(state.start(17, -1)); assertEquals(17, state.leftId());
        assertEquals(42, state.rightId()); assertEquals(42, state.activeId());
    }
    @Test public void repeatedSwapsKeepActiveTabAndPhysicalRatio() {
        ArcSplitState state = new ArcSplitState(); state.start(17, 42); state.activate(42); state.setRatio(.65f);
        state.swap(); assertEquals(42, state.leftId()); assertEquals(17, state.rightId());
        assertEquals(42, state.activeId()); assertEquals(.65f, state.ratio(), 0f);
        state.swap(); assertEquals(17, state.leftId()); assertEquals(42, state.rightId());
        assertFalse(state.activate(99)); assertEquals(42, state.activeId());
    }
    @Test public void closeActiveOrInactiveKeepsSurvivorWithoutCreatingTab() {
        for (int closed : new int[] {17, 42}) {
            ArcSplitState state = new ArcSplitState(); state.start(17, 42); state.activate(closed);
            state.remove(99); assertTrue(state.isSplit()); state.remove(closed);
            int survivor = closed == 17 ? 42 : 17;
            assertFalse(state.isSplit()); assertEquals(survivor, state.activeId());
            assertEquals(survivor, state.leftId()); assertEquals(-1, state.rightId());
            state.remove(closed); assertEquals(survivor, state.activeId());
        }
    }
    @Test public void exitIsIdempotentAndPreservesActiveIdentity() {
        ArcSplitState state = new ArcSplitState(); state.start(17, 42); state.activate(42);
        state.exit(); state.exit(); state.swap(); assertFalse(state.isSplit());
        assertEquals(42, state.activeId()); assertEquals(42, state.leftId());
        state.remove(42); assertEquals(-1, state.activeId());
    }
    @Test public void ratioRejectsNonFiniteAndBoundsFiniteValues() {
        ArcSplitState state = new ArcSplitState(); state.start(17, 42);
        for (float invalid : new float[] {Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY}) {
            try {state.setRatio(invalid); fail("Non-finite ratio accepted");}
            catch (IllegalArgumentException expected) {}
            assertEquals(.5f, state.ratio(), 0f);
        }
        state.setRatio(-10f); assertEquals(.2f, state.ratio(), 0f);
        state.setRatio(10f); assertEquals(.8f, state.ratio(), 0f);
    }
}
