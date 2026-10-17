// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import android.app.Activity;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.FrameLayout;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcOmniboxPlacementTest {
    @Test public void transfersSameHolderPreservingDirectParentTextAndSelection() {
        Activity a = Robolectric.buildActivity(Activity.class).setup().get();
        FrameLayout root = new FrameLayout(a), top = new FrameLayout(a), side = new FrameLayout(a);
        FrameLayout holder = new FrameLayout(a);
        EditText editor = new EditText(a);
        holder.addView(editor); top.addView(holder); root.addView(top); root.addView(side); a.setContentView(root);
        editor.setText("https://example.com/form"); editor.requestFocus(); editor.setSelection(9);
        ArcOmniboxPlacement placement = new ArcOmniboxPlacement(holder);
        for (int i = 0; i < 8; i++) {
            placement.move(side, new FrameLayout.LayoutParams(-1, 44));
            assertSame(holder, editor.getParent()); assertSame(side, holder.getParent());
            placement.restore();
            assertSame(top, holder.getParent()); assertSame(holder, editor.getParent());
            assertEquals("https://example.com/form", editor.getText().toString());
            assertEquals(9, editor.getSelectionStart());
        }
        assertEquals(1, top.getChildCount()); assertEquals(0, side.getChildCount());
        assertTrue(editor.hasFocus());
        placement.restore(); a.finish();
    }
    @Test public void noOpMoveDoesNotDetachOrReplaceParameters() {
        Activity a = Robolectric.buildActivity(Activity.class).setup().get();
        FrameLayout top = new FrameLayout(a), holder = new FrameLayout(a);
        ViewGroup.LayoutParams original = new FrameLayout.LayoutParams(180, 44);
        top.addView(holder, original);
        ArcOmniboxPlacement placement = new ArcOmniboxPlacement(holder);
        placement.move(top, new FrameLayout.LayoutParams(999, 99));
        assertSame(original, holder.getLayoutParams());
        placement.restore(); assertSame(original, holder.getLayoutParams()); a.finish();
    }
    @Test public void sidebarRestorationKeepsAddressBetweenNavigationAndCollections() {
        Activity a = Robolectric.buildActivity(Activity.class).setup().get();
        FrameLayout top = new FrameLayout(a), sidebar = new FrameLayout(a), holder = new FrameLayout(a);
        top.addView(holder); sidebar.addView(new FrameLayout(a)); sidebar.addView(new FrameLayout(a));
        ArcOmniboxPlacement placement = new ArcOmniboxPlacement(holder);
        placement.move(sidebar, 1, new FrameLayout.LayoutParams(200, 44));
        assertSame(holder, sidebar.getChildAt(1));
        placement.restore(); placement.move(sidebar, 1, new FrameLayout.LayoutParams(200, 44));
        assertSame(holder, sidebar.getChildAt(1)); assertEquals(3, sidebar.getChildCount());
        a.finish();
    }
}
