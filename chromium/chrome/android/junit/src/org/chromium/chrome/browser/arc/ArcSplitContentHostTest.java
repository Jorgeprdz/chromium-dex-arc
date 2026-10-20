// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import static org.mockito.Mockito.*;
import android.app.Activity;
import android.graphics.Rect;
import android.view.View;
import android.widget.FrameLayout;
import java.util.ArrayList;
import java.util.List;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.components.embedder_support.view.ContentView;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcSplitContentHostTest {
    private Tab tab(Activity a,int id) {
        Tab tab=mock(Tab.class);ContentView view=ContentView.createContentView(a,null);
        when(tab.getId()).thenReturn(id);when(tab.getContentView()).thenReturn(view);when(tab.getView()).thenReturn(view);return tab;
    }
    @Test public void twoContentViewsHaveIndependentBoundsAndOriginalParamsReturn() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();FrameLayout parent=new FrameLayout(a);a.setContentView(parent);
        Tab left=tab(a,17),right=tab(a,42);View original=left.getView();FrameLayout.LayoutParams params=new FrameLayout.LayoutParams(-1,-1);parent.addView(original,params);
        ArcSplitContentHost host=new ArcSplitContentHost(parent);
        assertTrue(host.show(left,right,new Rect(216,0,1216,800),.5f));
        assertSame(parent,left.getView().getParent());assertSame(parent,right.getView().getParent());
        assertEquals(500,left.getView().getLayoutParams().width);assertEquals(500,right.getView().getLayoutParams().width);
        assertEquals(216,((FrameLayout.LayoutParams)left.getView().getLayoutParams()).leftMargin);
        assertEquals(716,((FrameLayout.LayoutParams)right.getView().getLayoutParams()).leftMargin);
        assertSame(left,host.tabAt(300,100));assertSame(right,host.tabAt(900,100));assertNull(host.tabAt(100,100));
        host.clear();assertSame(params,left.getView().getLayoutParams());assertNull(right.getView().getParent());a.finish();
    }
    @Test public void swapKeepsSameViewsAndRejectsInvalidGeometryWithoutLosingPair() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();FrameLayout parent=new FrameLayout(a);a.setContentView(parent);Tab one=tab(a,17),two=tab(a,42);
        ArcSplitContentHost host=new ArcSplitContentHost(parent);assertTrue(host.show(one,two,new Rect(0,0,1000,600),.65f));
        assertFalse(host.show(one,one,new Rect(0,0,1000,600),.5f));assertSame(one,host.tabAt(10,10));
        assertFalse(host.show(one,two,new Rect(0,0,1000,600),Float.NaN));
        assertTrue(host.show(two,one,new Rect(0,0,1000,600),.65f));assertSame(two,host.tabAt(10,10));assertSame(one,host.tabAt(900,10));
        assertEquals(2,parent.getChildCount());host.clear();host.clear();assertEquals(0,parent.getChildCount());a.finish();
    }
    @Test public void destroyedContentViewDuringSurfaceSuspensionDoesNotReattachStaleViews() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();FrameLayout parent=new FrameLayout(a);a.setContentView(parent);
        Tab one=tab(a,17),two=tab(a,42);ArcSplitContentHost host=new ArcSplitContentHost(parent);
        assertTrue(host.show(one,two,new Rect(0,0,1000,600),.5f));host.setAttached(false);
        when(two.getContentView()).thenReturn(null);when(two.getView()).thenReturn(null);
        host.setAttached(true);assertEquals(0,parent.getChildCount());host.clear();a.finish();
    }
    @Test public void selectionTransfersFocusButNeverStealsFromOmniboxOrModal() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();FrameLayout parent=new FrameLayout(a);a.setContentView(parent);
        Tab one=tab(a,17),two=tab(a,42);ArcSplitContentHost host=new ArcSplitContentHost(parent);
        one.getContentView().setFocusableInTouchMode(true);two.getContentView().setFocusableInTouchMode(true);
        assertTrue(host.show(one,two,new Rect(0,0,1000,600),.5f));one.getContentView().requestFocus();
        assertTrue(host.focus(two,null,false));assertTrue(two.getContentView().hasFocus());assertFalse(one.getContentView().hasFocus());
        assertFalse(host.focus(one,null,true));assertTrue(two.getContentView().hasFocus());
        android.widget.EditText address=new android.widget.EditText(a);parent.addView(address);address.requestFocus();
        assertFalse(host.focus(one,address,false));assertTrue(address.hasFocus());
        host.clear();a.finish();
    }
    @Test public void frameReservesRealInsetsAndGutterAndRestoresOriginalLayout() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();FrameLayout parent=new FrameLayout(a);a.setContentView(parent);
        Tab one=tab(a,17),two=tab(a,42);FrameLayout.LayoutParams original=new FrameLayout.LayoutParams(-1,-1);parent.addView(one.getView(),original);
        ArcSplitContentHost host=new ArcSplitContentHost(parent);host.setFrameSpacing(4,8);
        assertTrue(host.show(one,two,new Rect(216,0,1216,600),.5f));
        assertEquals(new android.graphics.RectF(220,4,712,596),host.bounds(one));
        assertEquals(new android.graphics.RectF(720,4,1212,596),host.bounds(two));
        FrameLayout.LayoutParams params=(FrameLayout.LayoutParams)one.getView().getLayoutParams();
        assertEquals(4,params.topMargin);assertEquals(592,params.height);assertEquals(492,params.width);
        assertNull(host.tabAt(716,100));assertNull(host.tabAt(217,100));assertSame(one,host.tabAt(221,5));
        assertFalse(host.show(one,two,new Rect(0,0,8,8),.5f));assertEquals(492,one.getView().getLayoutParams().width);
        host.clear();assertSame(original,one.getView().getLayoutParams());a.finish();
    }

}
