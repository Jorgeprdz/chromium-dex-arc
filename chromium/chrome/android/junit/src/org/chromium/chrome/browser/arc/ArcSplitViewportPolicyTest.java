// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import static org.mockito.Mockito.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import org.chromium.content_public.browser.NavigationController;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcSplitViewportPolicyTest {
    private NavigationController desktop() {
        NavigationController n=mock(NavigationController.class);
        java.util.concurrent.atomic.AtomicBoolean value=new java.util.concurrent.atomic.AtomicBoolean(true);
        when(n.getUseDesktopUserAgent()).thenAnswer(c->value.get());
        doAnswer(c->{value.set(c.getArgument(0));return null;}).when(n).setUseDesktopUserAgent(anyBoolean(),anyBoolean(),anyBoolean());
        return n;
    }
    @Test public void eachPaneChoosesMobileIndependentlyWithoutReload() {
        ArcSplitViewportPolicy p=new ArcSplitViewportPolicy();NavigationController a=desktop(),b=desktop();
        p.update(a,420);p.update(b,800);
        assertFalse(a.getUseDesktopUserAgent());assertTrue(b.getUseDesktopUserAgent());
        verify(a).setUseDesktopUserAgent(false,false,false);verify(b,never()).setUseDesktopUserAgent(anyBoolean(),anyBoolean(),anyBoolean());
        p.clear();assertTrue(a.getUseDesktopUserAgent());verify(a).setUseDesktopUserAgent(true,false,false);
    }
    @Test public void hysteresisPreventsResizeFlappingAndRestoresOriginalMode() {
        ArcSplitViewportPolicy p=new ArcSplitViewportPolicy();NavigationController a=desktop();
        p.update(a,599);p.update(a,610);p.update(a,639);assertFalse(a.getUseDesktopUserAgent());
        p.update(a,640);assertTrue(a.getUseDesktopUserAgent());
        verify(a,times(2)).setUseDesktopUserAgent(anyBoolean(),eq(false),eq(false));
    }
    @Test public void mobilePreferenceIsNeverUpgradedToDesktop() {
        ArcSplitViewportPolicy p=new ArcSplitViewportPolicy();NavigationController a=mock(NavigationController.class);
        p.update(a,400);p.update(a,1000);p.clear();verify(a,never()).setUseDesktopUserAgent(anyBoolean(),anyBoolean(),anyBoolean());
    }
    @Test public void explicitDesktopOverrideWinsUntilPaneWidens() {
        ArcSplitViewportPolicy p=new ArcSplitViewportPolicy();NavigationController a=desktop();
        p.update(a,400);a.setUseDesktopUserAgent(true,false,false);p.update(a,400);p.update(a,500);
        assertTrue(a.getUseDesktopUserAgent());p.clear();
        verify(a,times(1)).setUseDesktopUserAgent(false,false,false);
    }
    @Test public void invalidWidthsAndNullControllersDoNothing() {
        ArcSplitViewportPolicy p=new ArcSplitViewportPolicy();NavigationController a=desktop();
        p.update(a,Float.NaN);p.update(a,-1);p.update(null,400);p.update(a,Float.POSITIVE_INFINITY);
        verify(a,never()).setUseDesktopUserAgent(anyBoolean(),anyBoolean(),anyBoolean());
    }
    @Test public void replacementReleasesOnlyTheRetiredController() {
        ArcSplitViewportPolicy p=new ArcSplitViewportPolicy();NavigationController a=desktop(),b=desktop();
        p.update(a,400);p.update(b,400);p.retain(b,null);
        assertTrue(a.getUseDesktopUserAgent());assertFalse(b.getUseDesktopUserAgent());p.clear();assertTrue(b.getUseDesktopUserAgent());
    }
}
