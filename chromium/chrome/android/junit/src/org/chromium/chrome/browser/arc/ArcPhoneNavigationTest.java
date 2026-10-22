// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import android.app.Activity;
import android.graphics.Bitmap;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.FrameLayout;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetContent;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetController;

/** Real Android views and delivered sheet; Chromium controller/action boundaries are mocks. */
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36},qualifiers="mdpi")
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcPhoneNavigationTest {
    private org.robolectric.android.controller.ActivityController<Activity> mActivity;
    private FrameLayout mSlot;
    private ArcPhoneNavigation mNavigation;
    private BottomSheetController mController;
    private FakeHost mHost;
    private static class FakeHost implements ArcPhoneNavigation.Host {
        Object token=new Object(); int action=-1,zoom=100,count=8,color=0xfff0f0f6; boolean web=true,pinned;
        public Object pageToken(){return token;}
        public String domain(){return "example.test";}
        public Bitmap favicon(){return null;}
        public int tabCount(){return count;}
        public boolean webPage(){return web;}
        public boolean pinned(){return pinned;}
        public boolean desktopSite(){return false;}
        public int zoomPercent(){return zoom;}
        public int surface(){return color;}
        public void action(int id){action=id;}
        public void zoom(int direction){zoom+=direction*10;}
    }
    @Before public void setUp(){
        mActivity=Robolectric.buildActivity(Activity.class).setup();
        mSlot=new FrameLayout(mActivity.get());mActivity.get().setContentView(mSlot);
        mController=mock(BottomSheetController.class);
        when(mController.requestShowContent(any(),anyBoolean())).thenReturn(true);
        mNavigation=new ArcPhoneNavigation(mSlot,mController);mHost=new FakeHost();mNavigation.bind(mHost);
        mNavigation.initializeWithNative(visible->{},token->{});
    }
    @After public void close(){mNavigation.destroy();mActivity.pause().stop().destroy();}
    private View find(String tag){return mSlot.findViewWithTag(tag);}
    private BottomSheetContent menu(){
        find("arc-phone-menu").performClick();
        ArgumentCaptor<BottomSheetContent> c=ArgumentCaptor.forClass(BottomSheetContent.class);
        verify(mController).requestShowContent(c.capture(),anyBoolean());return c.getValue();
    }
    private int editors(View v){int n=v instanceof EditText?1:0;if(v instanceof ViewGroup g)for(int i=0;i<g.getChildCount();i++)n+=editors(g.getChildAt(i));return n;}
    @Test public void oneSlotContainsExactlyFourNavigationTargets(){
        assertEquals(1,mSlot.getChildCount());
        ViewGroup bar=(ViewGroup)mSlot.getChildAt(0);assertEquals(4,bar.getChildCount());
        for(String tag:new String[]{"home","new","tabs","menu"})assertNotNull(find("arc-phone-"+tag));
    }
    @Test public void navigationCallsActualHostActions(){
        find("arc-phone-home").performClick();assertEquals(ArcPhoneNavigation.HOME,mHost.action);
        find("arc-phone-new").performClick();assertEquals(ArcPhoneNavigation.NEW_TAB,mHost.action);
        find("arc-phone-tabs").performClick();assertEquals(ArcPhoneNavigation.TABS,mHost.action);
    }
    @Test public void sheetHasStaticDomainAndNoEditorOrNativeOmniboxFallback(){
        var c=menu();assertEquals(0,editors(c.getContentView()));assertNotNull(c.getToolbarView());
        assertEquals(0,c.getToolbarView().getLayoutParams().height);
        assertTrue(c.coversBottomControls());assertTrue(c.swipeToDismissEnabled());
        assertEquals(BottomSheetContent.HeightMode.DISABLED,c.getHalfHeightRatio(),0);
        assertNotNull(c.getContentView().findViewWithTag("arc-phone-domain"));
    }
    @Test public void repeatedMenuClickDoesNotCreateAnotherSheet(){menu();find("arc-phone-menu").performClick();verify(mController,times(1)).requestShowContent(any(),anyBoolean());}
    @Test public void pageActionsDispatchAndDismiss(){
        var c=menu();c.getContentView().findViewWithTag("arc-phone-find").performClick();
        assertEquals(ArcPhoneNavigation.FIND,mHost.action);verify(mController).hideContent(eq(c),anyBoolean());
    }
    @Test public void staleSheetCannotActOnDifferentTab(){
        var c=menu();mHost.token=new Object();mNavigation.refresh();
        c.getContentView().findViewWithTag("arc-phone-favorite").performClick();assertEquals(-1,mHost.action);
    }
    @Test public void zoomUsesHostAndKeepsSheetOpen(){
        var c=menu();c.getContentView().findViewWithTag("arc-phone-zoom-plus").performClick();assertEquals(110,mHost.zoom);
        verify(mController,never()).hideContent(any(),anyBoolean());
    }
    @Test public void nonWebPagesDisableContextActionsButKeepDownloads(){
        mHost.web=false;var c=menu();assertFalse(c.getContentView().findViewWithTag("arc-phone-find").isEnabled());
        assertTrue(c.getContentView().findViewWithTag("arc-phone-downloads").isEnabled());
    }
    @Test public void sheetRejectionDoesNotLeaveDuplicateState(){
        when(mController.requestShowContent(any(),anyBoolean())).thenReturn(false);
        find("arc-phone-menu").performClick();find("arc-phone-menu").performClick();verify(mController,times(2)).requestShowContent(any(),anyBoolean());
    }
    @Test public void destroyReleasesOnlyOwnedChildAndDisablesActions(){
        var c=menu();View old=find("arc-phone-new");mNavigation.destroy();assertEquals(0,mSlot.getChildCount());
        old.performClick();assertEquals(-1,mHost.action);verify(mController).hideContent(eq(c),anyBoolean());
    }

    @Test public void tabSwitcherBorrowsSameBarWithoutReservingAnotherAppBar(){
        boolean[] visible={true};mNavigation.initializeWithNative(v->visible[0]=v,token->{});
        var bridge=mNavigation.getBottomBar();View original=bridge.getView();
        FrameLayout hub=new FrameLayout(mActivity.get());mSlot.removeView(original);hub.addView(original);
        bridge.setParent(org.chromium.chrome.browser.ui.bottombar.BottomBarHostManager.Host.HUB);
        assertFalse(visible[0]);assertEquals(0,mSlot.getChildCount());assertSame(original,hub.getChildAt(0));
        hub.removeView(original);mNavigation.attachBottomBarView(original);
        bridge.setParent(org.chromium.chrome.browser.ui.bottombar.BottomBarHostManager.Host.TABBED);
        assertTrue(visible[0]);assertEquals(1,mSlot.getChildCount());assertSame(original,mSlot.getChildAt(0));
    }
    @Test public void destroyAlsoDetachesBorrowedTabSwitcherBar(){
        var bridge=mNavigation.getBottomBar();View view=bridge.getView();mSlot.removeView(view);
        FrameLayout hub=new FrameLayout(mActivity.get());hub.addView(view);bridge.setParent(1);
        mNavigation.destroy();assertEquals(0,hub.getChildCount());
    }
    @Test public void minimumNativeHeightKeepsFourTouchTargets(){
        mNavigation.destroy();mNavigation=new ArcPhoneNavigation(mSlot,mController,48);mNavigation.bind(mHost);
        mSlot.measure(View.MeasureSpec.makeMeasureSpec(320,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(48,View.MeasureSpec.EXACTLY));mSlot.layout(0,0,320,48);
        for(String tag:new String[]{"home","new","tabs","menu"}){View v=find("arc-phone-"+tag);assertTrue(v.getWidth()>=48);assertEquals(48,v.getHeight());}
    }
    @Test public void liveCounterReflectsCurrentModelCount(){
        mHost.count=12;mNavigation.refresh();assertTrue(find("arc-phone-tabs").getContentDescription().toString().contains("12"));
    }
    @Test public void darkSurfaceAndSheetUseHostPaletteWithoutForcingWebTheme(){
        mHost.color=0xff202124;mNavigation.refresh();assertEquals(0xff202124,mNavigation.getBackgroundColor().intValue());
        assertEquals(0xff202124,menu().getSheetBackgroundColorOverride());
    }
}
