// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

import android.app.Activity;
import android.widget.ImageButton;
import android.view.View;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabObserver;

import java.util.concurrent.atomic.AtomicReference;

/** Android button state follows the selected native Tab; mocks cover that native boundary. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {30, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcNavigationControlsTest {
    @Test
    public void collapsedBackRemainsVisibleAndDispatchesToSelectedNativeTab() {
        Tab tab = mock(Tab.class);
        ImageButton[] buttons = buttons();
        ArcNavigationControls controls = new ArcNavigationControls(() -> tab, buttons[0], buttons[1], buttons[2]);
        controls.setExpanded(false);
        controls.refresh();
        assertEquals(View.VISIBLE, buttons[0].getVisibility());
        assertFalse(buttons[0].isEnabled());
        assertEquals(View.GONE, buttons[1].getVisibility());
        assertEquals(View.GONE, buttons[2].getVisibility());
        when(tab.canGoBack()).thenReturn(true);
        controls.refresh();
        buttons[0].performClick();
        verify(tab).goBack();
        controls.setExpanded(true);
        for (ImageButton button : buttons) assertEquals(View.VISIBLE, button.getVisibility());
        controls.destroy();
        buttons[0].performClick();
        verify(tab, times(1)).goBack();
    }
    private ImageButton[] buttons() {
        Activity activity = Robolectric.buildActivity(Activity.class).setup().get();
        return new ImageButton[] {new ImageButton(activity), new ImageButton(activity), new ImageButton(activity)};
    }

    @Test
    public void historyEventsUpdateBackAndForwardWithoutResize() {
        Tab tab = mock(Tab.class);
        ImageButton[] buttons = buttons();
        ArcNavigationControls controls = new ArcNavigationControls(() -> tab, buttons[0], buttons[1], buttons[2]);
        controls.refresh();
        ArgumentCaptor<TabObserver> listener = ArgumentCaptor.forClass(TabObserver.class);
        verify(tab).addObserver(listener.capture());
        assertFalse(buttons[0].isEnabled());
        when(tab.canGoBack()).thenReturn(true);
        when(tab.canGoForward()).thenReturn(true);
        listener.getValue().onUrlUpdated(tab);
        assertTrue(buttons[0].isEnabled());
        assertTrue(buttons[1].isEnabled());
        assertTrue(buttons[2].isEnabled());
        controls.destroy();
    }

    @Test
    public void selectionRemovesOldObserverAndIgnoresOldEvents() {
        Tab first = mock(Tab.class);
        Tab second = mock(Tab.class);
        AtomicReference<Tab> current = new AtomicReference<>(first);
        ImageButton[] buttons = buttons();
        ArcNavigationControls controls = new ArcNavigationControls(current::get, buttons[0], buttons[1], buttons[2]);
        controls.refresh();
        ArgumentCaptor<TabObserver> listener = ArgumentCaptor.forClass(TabObserver.class);
        verify(first).addObserver(listener.capture());
        current.set(second);
        when(second.canGoForward()).thenReturn(true);
        controls.refresh();
        verify(first).removeObserver(listener.getValue());
        when(first.canGoBack()).thenReturn(true);
        listener.getValue().onUrlUpdated(first);
        assertFalse(buttons[0].isEnabled());
        assertTrue(buttons[1].isEnabled());
        controls.destroy();
    }

    @Test
    public void destroyedTabAndCoordinatorDisableControls() {
        Tab tab = mock(Tab.class);
        ImageButton[] buttons = buttons();
        ArcNavigationControls controls = new ArcNavigationControls(() -> tab, buttons[0], buttons[1], buttons[2]);
        controls.refresh();
        ArgumentCaptor<TabObserver> listener = ArgumentCaptor.forClass(TabObserver.class);
        verify(tab).addObserver(listener.capture());
        when(tab.isDestroyed()).thenReturn(true);
        listener.getValue().onDestroyed(tab);
        controls.refresh();
        assertFalse(buttons[2].isEnabled());
        controls.destroy();
        controls.refresh();
        for (ImageButton button : buttons) assertFalse(button.isEnabled());
        verify(tab, times(1)).addObserver(listener.getValue());
    }
}
