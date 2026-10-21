// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import android.app.Activity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.Button;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;
import java.util.List;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcMobileControlsTest {
    static class Host implements ArcMobileControls.Host {
        boolean visible=true;int home,add,tabs,find,spaces;int count=3;FrameLayout nativeHome;
        public View nativeHomeView(){return nativeHome;}
        public View buildHome(){return nativeHome==null?null:new View(nativeHome.getContext());}
        public boolean visible(){return visible;}public int tabCount(){return count;}
        public int surface(){return 0xffeeeeee;}public int foreground(){return 0xff111111;}public int accent(){return 0xff345678;}
        public String pageLabel(){return "example.test";}
        public void home(){home++;}public void newTab(){add++;}public void tabs(){tabs++;}public void spaces(){spaces++;}
        public List<ArcMobileControls.Action> actions(){return List.of(new ArcMobileControls.Action("Find",()->find++));}
    }
    @Test public void fourActionsRouteToHostAndRestoreContentMargin() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        FrameLayout root=new FrameLayout(a);View browser=new View(a);
        FrameLayout.LayoutParams params=new FrameLayout.LayoutParams(-1,-1);params.bottomMargin=7;
        root.addView(browser,params);a.setContentView(root);
        Host host=new Host();ArcMobileControls controls=new ArcMobileControls(a,root,browser,host,"Home","New","Tabs","Menu");
        LinearLayout bar=root.findViewWithTag("archium-mobile-navigation");
        assertEquals(4,bar.getChildCount());
        for(int i=0;i<3;i++)assertTrue(bar.getChildAt(i).performClick());
        assertEquals(1,host.home);assertEquals(1,host.add);assertEquals(1,host.tabs);
        assertTrue(bar.getChildAt(2).performLongClick());assertEquals(1,host.spaces);
        host.count=8;controls.refresh();assertEquals("8",((Button)bar.getChildAt(2)).getText().toString());
        assertTrue(((ViewGroup.MarginLayoutParams)browser.getLayoutParams()).bottomMargin>7);
        host.visible=false;controls.refresh();assertEquals(View.GONE,bar.getVisibility());
        assertEquals(7,((ViewGroup.MarginLayoutParams)browser.getLayoutParams()).bottomMargin);
        controls.destroy();assertEquals(1,root.getChildCount());
        controller.pause().stop().destroy();
    }
    @Test public void menuContainsOnlyRealHostActionsAndDismissesOnExecution() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        FrameLayout root=new FrameLayout(a);View browser=new View(a);root.addView(browser,new FrameLayout.LayoutParams(-1,-1));a.setContentView(root);
        root.layout(0,0,400,900);Host host=new Host();
        ArcMobileControls controls=new ArcMobileControls(a,root,browser,host,"Home","New","Tabs","Menu");
        controls.showMenu();android.app.Dialog dialog=org.robolectric.shadows.ShadowDialog.getLatestDialog();
        assertTrue(dialog.isShowing());
        android.widget.ScrollView scroll=(android.widget.ScrollView)((ViewGroup)dialog.findViewById(android.R.id.content)).getChildAt(0);
        LinearLayout content=(LinearLayout)scroll.getChildAt(0);assertEquals(2,content.getChildCount());
        assertTrue(content.getChildAt(1).performClick());assertEquals(1,host.find);assertFalse(dialog.isShowing());
        controls.destroy();controller.pause().stop().destroy();
    }
    @Test public void releasingNavigationKeepsOtherBrowserMarginChanges() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        FrameLayout root=new FrameLayout(a);View browser=new View(a);
        root.addView(browser,new FrameLayout.LayoutParams(-1,-1));a.setContentView(root);
        Host host=new Host();ArcMobileControls controls=new ArcMobileControls(a,root,browser,host,"Home","New","Tabs","Menu");
        var params=(ViewGroup.MarginLayoutParams)browser.getLayoutParams();params.bottomMargin+=13;
        browser.setLayoutParams(params);controls.refresh();
        host.visible=false;controls.refresh();
        assertEquals(13,((ViewGroup.MarginLayoutParams)browser.getLayoutParams()).bottomMargin);
        host.visible=true;controls.refresh();controls.destroy();
        assertEquals(13,((ViewGroup.MarginLayoutParams)browser.getLayoutParams()).bottomMargin);
        controller.pause().stop().destroy();
    }
    @Test public void addressFocusKeepsNativeListenerAndRestoresAlignment() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        FrameLayout root=new FrameLayout(a);View browser=new View(a);root.addView(browser,new FrameLayout.LayoutParams(-1,-1));
        android.widget.EditText address=new android.widget.EditText(a);root.addView(address);a.setContentView(root);
        address.setGravity(android.view.Gravity.END);int originalGravity=address.getGravity();int[] focus={0};
        address.setOnFocusChangeListener((view,focused)->focus[0]++);
        Host host=new Host();ArcMobileControls controls=new ArcMobileControls(a,root,browser,host,"Home","New","Tabs","Menu");
        controls.bindAddressBar(address);address.requestFocus();controls.refresh();
        assertEquals(android.view.Gravity.START|android.view.Gravity.CENTER_VERTICAL,address.getGravity());
        assertNotNull(address.getOnFocusChangeListener());
        controls.destroy();assertEquals(originalGravity,address.getGravity());
        controller.pause().stop().destroy();
    }
    @Test public void sheetHeaderSwipeClosesWithoutInvokingAnAction() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        FrameLayout root=new FrameLayout(a);View browser=new View(a);root.addView(browser,new FrameLayout.LayoutParams(-1,-1));a.setContentView(root);
        root.layout(0,0,400,900);Host host=new Host();ArcMobileControls controls=new ArcMobileControls(a,root,browser,host,"Home","New","Tabs","Menu");
        controls.showMenu();android.app.Dialog dialog=org.robolectric.shadows.ShadowDialog.getLatestDialog();
        android.widget.ScrollView scroll=(android.widget.ScrollView)((ViewGroup)dialog.findViewById(android.R.id.content)).getChildAt(0);
        View header=((LinearLayout)scroll.getChildAt(0)).getChildAt(0);
        float distance=100*a.getResources().getDisplayMetrics().density;
        android.view.MotionEvent down=android.view.MotionEvent.obtain(0,0,0,0,0,0);
        android.view.MotionEvent up=android.view.MotionEvent.obtain(0,10,1,0,distance,0);
        header.dispatchTouchEvent(down);header.dispatchTouchEvent(up);down.recycle();up.recycle();
        assertFalse(dialog.isShowing());assertEquals(0,host.find);
        controls.destroy();controller.pause().stop().destroy();
    }
    @Test public void homeUsesNativePageContainerAndRestoresOriginalChildren() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        FrameLayout root=new FrameLayout(a),browser=new FrameLayout(a),nativePage=new FrameLayout(a);
        root.addView(browser,new FrameLayout.LayoutParams(-1,-1));browser.addView(nativePage,new FrameLayout.LayoutParams(-1,-1));
        View original=new View(a);nativePage.addView(original);a.setContentView(root);
        Host host=new Host();host.nativeHome=nativePage;
        ArcMobileControls controls=new ArcMobileControls(a,root,browser,host,"Home","New","Tabs","Menu");
        assertEquals(2,nativePage.getChildCount());assertEquals(View.INVISIBLE,original.getVisibility());
        // A transition to a real page/Hub releases the native NTP; nothing overlays the window.
        host.nativeHome=null;controls.refresh();assertEquals(1,nativePage.getChildCount());assertEquals(View.VISIBLE,original.getVisibility());
        controls.destroy();controller.pause().stop().destroy();
    }
    @Test public void homeSearchFavoritesAndSettingsUseActualViewCallbacks() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();int[] count={0};
        ArcMobileHomeView home=new ArcMobileHomeView(a,"Archium","Personal","Search","Favorites","Recent","Settings",
                0xffeeeeee,0xff111111,0xffdddddd,List.of(new ArcMobileControls.Action("Favorite",()->count[0]++)),
                List.of(new ArcMobileControls.Action("Recent page",()->count[0]++)),()->count[0]++,()->count[0]++,()->count[0]++);
        a.setContentView(home);LinearLayout content=(LinearLayout)home.getChildAt(0);
        for(int i=0;i<content.getChildCount();i++)if(content.getChildAt(i) instanceof Button button)assertTrue(button.performClick());
        assertEquals(5,count[0]);controller.pause().stop().destroy();
    }
    @Test public void plusContrastFollowsLuminance() {
        assertEquals(android.graphics.Color.WHITE,ArcMobileControls.contrast(0xff000000));
        assertEquals(android.graphics.Color.BLACK,ArcMobileControls.contrast(0xffffffff));
    }
    @Test public void homeActionsRemainReadableOnDarkAccentInLightTheme() {
        var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
        ArcMobileHomeView home=new ArcMobileHomeView(a,"Archium","Personal","Search","Favorites","Recent","Settings",
                0xffffffff,0xff111111,0xff000000,List.of(),List.of(),()->{},()->{},()->{});
        LinearLayout content=(LinearLayout)home.getChildAt(0);
        Button space=(Button)content.getChildAt(2);
        assertEquals(android.graphics.Color.WHITE,space.getCurrentTextColor());
        controller.pause().stop().destroy();
    }
}
