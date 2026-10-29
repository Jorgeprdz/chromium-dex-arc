// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.ScrollView;
import android.graphics.drawable.RippleDrawable;
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
    private boolean mDarkPalette;
    private org.robolectric.android.controller.ActivityController<Activity> mActivity;
    private FrameLayout mSlot;
    private ArcPhoneNavigation mNavigation;
    private BottomSheetController mController;
    private FakeHost mHost;
    private static class FakeHost implements ArcPhoneNavigation.Host {
        Object token=new Object(); int action=-1,zoom=100,count=8,color=0xfff0f0f6; boolean web=true,pinned,home,favorite; int page=Color.RED; String url="https://example.test/";
        public Object pageToken(){return token;}
        public String domain(){return "example.test";}
        public Bitmap favicon(){return null;}
        public int tabCount(){return count;}
        public boolean webPage(){return web;}
        public boolean pinned(){return pinned;}
        public boolean homePage(){return home;}
        public int pageColor(){return page;}
        public String pageUrl(){return url;}
        public boolean favorite(){return favorite;}
        public boolean desktopSite(){return false;}
        public int zoomPercent(){return zoom;}
        public int surface(){return color;}
        public void action(int id){action=id;}
        public void zoom(int direction){zoom+=direction*10;}
    }
    @Before public void setUp(){
        mDarkPalette=false;
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
    private android.graphics.drawable.Drawable aura(String tag) {
        var button=(LinearLayout)find("arc-phone-"+tag);
        var pill=(FrameLayout)button.getChildAt(0);
        assertNotNull("Existing pill must own its persistent aura drawable",pill.getBackground());
        assertFalse("Aura must be a soft gradient rather than a solid capsule",pill.getBackground() instanceof GradientDrawable);
        return pill.getBackground();
    }
    private float strength(String tag){return org.robolectric.util.ReflectionHelpers.getField(aura(tag),"mStrength");}
    private int auraColor(String tag){return org.robolectric.util.ReflectionHelpers.getField(aura(tag),"mColor");}
    private void idle(long millis){org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(millis));}
    @Test public void contextualAuraTracksPageHueWithoutRelayoutOrFakeSelection(){
        View bar=mNavigation.getGlassTarget();Object geometry=bar.getLayoutParams();
        mHost.home=true;mNavigation.refresh();idle(250);
        int red=auraColor("home");float[] hsv=new float[3];Color.colorToHSV(red,hsv);assertTrue(hsv[0]<8||hsv[0]>352);
        assertEquals(1f,strength("home"),.01f);
        mHost.page=Color.GREEN;mNavigation.refresh();idle(250);
        Color.colorToHSV(auraColor("home"),hsv);assertEquals(120f,hsv[0],3f);
        assertSame(geometry,bar.getLayoutParams());assertEquals(4,((ViewGroup)bar).getChildCount());
        mHost.home=false;mNavigation.refresh();idle(250);
        for(String tag:new String[]{"home","new","tabs","menu"}){assertFalse(find("arc-phone-"+tag).isSelected());assertEquals(0f,strength(tag),.01f);}
        mNavigation.getBottomBar().setParent(1);idle(250);assertTrue(find("arc-phone-tabs").isSelected());
        assertEquals(1f,strength("tabs"),.01f);
        mNavigation.getBottomBar().setParent(0);idle(250);assertFalse(find("arc-phone-tabs").isSelected());
    }
    @Test public void selectedAuraRetainsVisibleShoulderBeyondTheIconWithoutHigherPeakOpacity(){
        mHost.home=true;mNavigation.refresh();idle(250);
        var drawable=aura("home");drawable.setBounds(0,0,44,24);
        android.graphics.Paint paint=org.robolectric.util.ReflectionHelpers.getField(drawable,"mPaint");
        var gradient=(android.graphics.RadialGradient)paint.getShader();
        long[] colors=org.robolectric.util.ReflectionHelpers.getField(gradient,"mColorLongs");
        float[] positions=org.robolectric.util.ReflectionHelpers.getField(gradient,"mPositions");
        assertNotNull(colors);assertNotNull(positions);
        // On the existing 44x24dp pill, the icon hides much of the center.
        // Demand at least 10% tint at 72% of the radius, while keeping the 15% cap.
        float radius=.72f;float alpha=0;
        for(int i=0;i<colors.length;i++){
            int a=Color.alpha(Color.valueOf(colors[i]).toArgb());
            assertTrue("Aura exceeds the approved 15% peak",a<=38);
            if(i>0&&radius>=positions[i-1]&&radius<=positions[i]){
                int previous=Color.alpha(Color.valueOf(colors[i-1]).toArgb());
                float fraction=(radius-positions[i-1])/(positions[i]-positions[i-1]);
                alpha=previous+(a-previous)*fraction;
            }
        }
        assertTrue("Halo disappears outside the icon; shoulder alpha="+alpha,alpha>=25.5f);
        assertEquals("No hard edge at the pill boundary",0,Color.alpha(Color.valueOf(colors[colors.length-1]).toArgb()));
        assertEquals(1f,strength("home"),.01f);
    }

    @Test public void newTabPulseIsBriefAndNeverBecomesSelection(){
        float old=android.animation.ValueAnimator.getDurationScale();
        try{
            android.animation.ValueAnimator.setDurationScale(1);
            aura("new");find("arc-phone-new").performClick();
            assertEquals(ArcPhoneNavigation.NEW_TAB,mHost.action);assertFalse(find("arc-phone-new").isSelected());
            android.animation.ValueAnimator pulse=org.robolectric.util.ReflectionHelpers.getField(aura("new"),"mAnimator");
            assertNotNull(pulse);assertEquals(220,pulse.getDuration());pulse.setCurrentFraction(.45f);
            assertTrue(strength("new")>0);pulse.end();assertEquals(0f,strength("new"),.01f);
        }finally{android.animation.ValueAnimator.setDurationScale(old);}
        var sheet=menu();idle(250);assertTrue(find("arc-phone-menu").isSelected());
        sheet.destroy();idle(250);assertFalse(find("arc-phone-menu").isSelected());assertEquals(0f,strength("menu"),.01f);
    }
    @Test public void disabledAnimationsAndDestroyLeaveNoAuraAnimator(){
        aura("home");float scale=android.animation.ValueAnimator.getDurationScale();
        try{android.animation.ValueAnimator.setDurationScale(0);mHost.home=true;mNavigation.refresh();
            assertEquals(1f,strength("home"),0);assertNull(org.robolectric.util.ReflectionHelpers.getField(aura("home"),"mAnimator"));
            find("arc-phone-new").performClick();assertEquals(0f,strength("new"),0);
        }finally{android.animation.ValueAnimator.setDurationScale(scale);}
        mHost.page=Color.BLUE;mNavigation.refresh();var drawables=new java.util.ArrayList<android.graphics.drawable.Drawable>();
        for(String tag:new String[]{"home","new","tabs","menu"})drawables.add(aura(tag));
        mNavigation.destroy();for(var drawable:drawables)assertNull(org.robolectric.util.ReflectionHelpers.getField(drawable,"mAnimator"));
    }
    @Test public void sheetHasNativeFavoriteStateCenteredZoomAndDistinctMoreGlyph(){
        mHost.favorite=true;var sheet=menu();View content=sheet.getContentView();
        assertTrue(content.findViewWithTag("arc-phone-favorite").isSelected());
        var zoom=(TextView)content.findViewWithTag("arc-phone-zoom-value");
        var group=(ViewGroup)zoom.getParent();assertEquals(3,group.getChildCount());assertSame(zoom,group.getChildAt(1));
        assertSame(content.findViewWithTag("arc-phone-zoom-minus"),group.getChildAt(0));
        assertSame(content.findViewWithTag("arc-phone-zoom-plus"),group.getChildAt(2));
        var zoomRow=(ViewGroup)group.getParent();var zoomTitle=(TextView)zoomRow.getChildAt(0);zoomTitle.setText("Zoom");
        content.measure(View.MeasureSpec.makeMeasureSpec(240,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(600,View.MeasureSpec.EXACTLY));content.layout(0,0,240,600);
        assertTrue("Zoom label must fit even in a narrow sheet",zoomTitle.getMeasuredWidth()>=Math.ceil(zoomTitle.getPaint().measureText("Zoom")));
        assertTrue(zoom.getMeasuredWidth()>=Math.ceil(zoom.getPaint().measureText("100%")));
        var row=(ViewGroup)content.findViewWithTag("arc-phone-more");
        var icon=((android.widget.ImageView)row.getChildAt(0)).getDrawable();icon.setBounds(0,0,24,24);
        final int[] dots={0};icon.draw(new android.graphics.Canvas(){@Override public void drawCircle(float x,float y,float radius,android.graphics.Paint paint){assertTrue(radius<2);dots[0]++;}});
        assertEquals(3,dots[0]);
        content.findViewWithTag("arc-phone-favorite").performClick();assertEquals(ArcPhoneNavigation.FAVORITE,mHost.action);
    }
    @Test public void sameTabNavigatingToAnotherUrlDismissesStaleSheet(){
        var sheet=menu();mHost.url="https://another.test/";mNavigation.refresh();
        verify(mController).hideContent(eq(sheet),anyBoolean());
        sheet.getContentView().findViewWithTag("arc-phone-pin").performClick();assertEquals(-1,mHost.action);
    }
    @Test public void rawPageColorChangesNotifyEvenWhenToolbarStaysNeutral() throws Exception {
        var top=mock(org.chromium.chrome.browser.theme.TopUiThemeColorProvider.class);
        var bottom=mock(org.chromium.chrome.browser.theme.BottomUiThemeColorProvider.class);
        var controls=mock(org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider.class);
        when(controls.getControlsPosition()).thenReturn(0);when(top.getThemeColor()).thenReturn(Color.RED);
        var provider=new org.chromium.chrome.browser.theme.ToolbarThemeColorProvider(mActivity.get(),top,bottom,controls,false,
                (context,incognito)->Color.WHITE,(context,scheme)->android.content.res.ColorStateList.valueOf(Color.BLACK));
        assertTrue("Need a metadata observer independent of the clamped toolbar color",
                java.util.Arrays.stream(provider.getClass().getMethods()).anyMatch(m->m.getName().equals("setArcPhonePageColorChangedCallback")));
        final int[] changes={0};provider.getClass().getMethod("setArcPhonePageColorChangedCallback",Runnable.class).invoke(provider,(Runnable)()->changes[0]++);
        var captured=ArgumentCaptor.forClass(org.chromium.chrome.browser.theme.ThemeColorProvider.ThemeColorObserver.class);
        verify(top,atLeastOnce()).addThemeColorObserver(captured.capture());
        var observer=captured.getValue();observer.onThemeColorChanged(Color.RED,false);observer.onThemeColorChanged(Color.RED,false);assertEquals(1,changes[0]);
        when(top.getThemeColor()).thenReturn(Color.GREEN);observer.onThemeColorChanged(Color.GREEN,false);assertEquals(2,changes[0]);
        provider.destroy();verify(top).removeThemeColorObserver(observer);
    }
    @Test public void oneSlotContainsExactlyFourNavigationTargets(){
        assertEquals(1,mSlot.getChildCount());
        ViewGroup bar=(ViewGroup)mSlot.getChildAt(0);assertEquals(4,bar.getChildCount());
        for(String tag:new String[]{"home","new","tabs","menu"})assertNotNull(find("arc-phone-"+tag));
    }
    @Test public void backgroundTabAnimationFindsNativeBarAndRealTabTarget() {
        // Exact lookup contract from pinned NewBackgroundTabAnimationData. Missing first
        // target caused the installed APK's findViewById NPE when opening a link in a tab.
        View bar=mSlot.findViewById(org.chromium.chrome.browser.ui.bottombar.R.id.bottom_bar_container);
        assertSame(mNavigation.getBottomBar().getView(),bar);
        View tabs=bar.findViewById(org.chromium.chrome.R.id.tab_switcher_button);
        assertSame(find("arc-phone-tabs"),tabs);
        tabs.performClick();assertEquals(ArcPhoneNavigation.TABS,mHost.action);
        // Chromium borrows this same bar in the Hub; IDs must survive native reattachment.
        FrameLayout hub=new FrameLayout(mActivity.get());
        mSlot.removeView(bar);hub.addView(bar);
        assertSame(tabs,hub.findViewById(org.chromium.chrome.browser.ui.bottombar.R.id.bottom_bar_container)
                .findViewById(org.chromium.chrome.R.id.tab_switcher_button));
        hub.removeView(bar);mNavigation.attachBottomBarView(bar);
        mNavigation.setCompact(true);
        assertSame(tabs,mSlot.findViewById(org.chromium.chrome.browser.ui.bottombar.R.id.bottom_bar_container)
                .findViewById(org.chromium.chrome.R.id.tab_switcher_button));
        mNavigation.setCompact(false);
        assertEquals(1,mSlot.getChildCount());
    }
    @Test public void glassReusesOneBarWithTransparentNativeBackingAndRestoresFallback(){
        View bar=mNavigation.getGlassTarget();Object layout=bar.getLayoutParams();
        var glass=new ArcPhoneGlass.Backdrop();mNavigation.setGlassBackdrop(glass,true);
        assertSame(bar,mSlot.getChildAt(0));assertEquals(1,mSlot.getChildCount());assertSame(layout,bar.getLayoutParams());
        assertSame(glass,bar.getBackground());assertEquals(Integer.valueOf(Color.TRANSPARENT),mNavigation.getBackgroundColor());
        assertEquals(Color.TRANSPARENT,mNavigation.getBottomBar().getBackgroundColor());
        mNavigation.setGlassBackdrop(glass,false);assertNotSame(glass,bar.getBackground());assertEquals(Integer.valueOf(Color.TRANSPARENT),mNavigation.getBackgroundColor());
        mNavigation.setGlassBackdrop(glass,true);mNavigation.setPhoneModeActive(false);
        assertNotSame(glass,bar.getBackground());assertNotEquals(Integer.valueOf(Color.TRANSPARENT),mNavigation.getBackgroundColor());
    }
    @Test public void glassUsesDayNightTintAndLegibleLabelsAgainstWorstPageBackground(){
        var glass=new ArcPhoneGlass.Backdrop();mNavigation.setGlassBackdrop(glass,true);
        for(int surface:new int[]{Color.WHITE,0xff202124}){
            mHost.color=surface;mNavigation.refresh();
            int tint=glass.tintColor();assertTrue(Color.alpha(tint)<255);
            int page=Color.luminance(surface)>.45?Color.BLACK:Color.WHITE;
            int alpha=Color.alpha(tint);
            int composed=Color.rgb((Color.red(tint)*alpha+Color.red(page)*(255-alpha))/255,
                (Color.green(tint)*alpha+Color.green(page)*(255-alpha))/255,
                (Color.blue(tint)*alpha+Color.blue(page)*(255-alpha))/255);
            ViewGroup bar=(ViewGroup)mNavigation.getGlassTarget();
            for(int i=0;i<bar.getChildCount();i++){
                int text=((TextView)((ViewGroup)bar.getChildAt(i)).getChildAt(1)).getCurrentTextColor();
                double a=Color.luminance(text),b=Color.luminance(composed);
                assertTrue("Glass text AA",(Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5);
            }
        }
    }
    @Test public void nativeNewTabKeepsFloatingPillWithoutSamplingWebContents(){
        mHost.web=false;mHost.home=true;mNavigation.refresh();
        View bar=mNavigation.getGlassTarget();assertTrue(bar.getBackground() instanceof GradientDrawable);
        var params=(FrameLayout.LayoutParams)bar.getLayoutParams();assertTrue(params.leftMargin>=16);assertTrue(params.rightMargin>=16);
        assertEquals(Color.TRANSPARENT,((android.graphics.drawable.ColorDrawable)mSlot.getBackground()).getColor());
        assertEquals(Integer.valueOf(Color.TRANSPARENT),mNavigation.getBackgroundColor());
        assertEquals(Color.TRANSPARENT,mNavigation.getBottomBar().getBackgroundColor());
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
    @Test public void floatingPillHasSideMarginsAndBreathingRoomInsideNativeSlot(){
        mSlot.measure(View.MeasureSpec.makeMeasureSpec(400,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(80,View.MeasureSpec.EXACTLY));mSlot.layout(0,0,400,80);
        ViewGroup bar=(ViewGroup)mSlot.getChildAt(0);
        assertTrue(bar.getLeft()>=16);assertTrue(bar.getRight()<=384);
        assertTrue(bar.getTop()>=8);assertTrue(bar.getBottom()<=72);
        assertTrue(bar.getElevation()>0);assertTrue(bar.getBackground() instanceof GradientDrawable);
        assertTrue(((GradientDrawable)bar.getBackground()).getCornerRadius()>=bar.getHeight()/2f);
        for(String tag:new String[]{"home","new","tabs","menu"}){View v=find("arc-phone-"+tag);assertTrue(v.getWidth()>=48);assertTrue(v.getHeight()>=48);}
    }
    @Test public void compactControlKeepsIdentityAndRestoresSameFourActions() throws Exception {
        View original=mSlot.getChildAt(0);
        final int[] restored={0};
        mNavigation.setCompactListener(()->restored[0]++);
        mNavigation.setCompact(true);
        assertSame(original,mSlot.getChildAt(0));assertEquals(1,mSlot.getChildCount());
        assertEquals(View.GONE,find("arc-phone-home").getVisibility());
        assertEquals(View.VISIBLE,find("arc-phone-menu").getVisibility());
        assertEquals("Archium",((TextView)((LinearLayout)find("arc-phone-menu")).getChildAt(1)).getText().toString());
        assertTrue(find("arc-phone-menu").performClick());assertEquals(1,restored[0]);
        for(String tag:new String[]{"home","new","tabs","menu"})assertEquals(View.VISIBLE,find("arc-phone-"+tag).getVisibility());
    }

    @Test public void compactWidthSurvivesNativeSlotReattachment() {
        mNavigation.setCompact(true);
        View bar=mNavigation.getGlassTarget();
        int compactWidth=bar.getLayoutParams().width;
        assertTrue(compactWidth>0);
        mSlot.removeView(bar);
        mNavigation.attachBottomBarView(bar);
        assertTrue(mNavigation.isCompact());
        assertEquals(compactWidth,bar.getLayoutParams().width);
    }

    @Test public void draggingCompactControlClearsPressAndDoesNotOpenMenu() {
        mNavigation.setCompact(true);
        mSlot.measure(View.MeasureSpec.makeMeasureSpec(320,View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(80,View.MeasureSpec.EXACTLY));
        mSlot.layout(0,0,320,80);
        View button=find("arc-phone-menu");
        View bar=mSlot.getChildAt(0);
        android.view.MotionEvent down=android.view.MotionEvent.obtain(0,1,0,48,24,0);
        android.view.MotionEvent move=android.view.MotionEvent.obtain(0,2,2,500,24,0);
        android.view.MotionEvent up=android.view.MotionEvent.obtain(0,3,1,500,24,0);
        button.dispatchTouchEvent(down);button.setPressed(true);
        button.dispatchTouchEvent(move);button.dispatchTouchEvent(up);
        down.recycle();move.recycle();up.recycle();
        assertFalse("Drag must release the pressed/ripple state",button.isPressed());
        assertTrue(mNavigation.isCompact());
        assertTrue(bar.getTranslationX()>0);
        assertTrue(bar.getRight()+bar.getTranslationX()<=320-18);
        mSlot.measure(View.MeasureSpec.makeMeasureSpec(240,View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(80,View.MeasureSpec.EXACTLY));
        mSlot.layout(0,0,240,80);
        assertTrue("Resizing must keep compact control reachable",bar.getRight()+bar.getTranslationX()<=240-18);
        verify(mController,never()).requestShowContent(any(),anyBoolean());
    }

    @Test public void homeAndHubSelectionFollowNativeState(){
        mHost.home=true;mNavigation.refresh();assertTrue(find("arc-phone-home").isSelected());
        TextView label=(TextView)((LinearLayout)find("arc-phone-home")).getChildAt(1);
        assertEquals(0xff202124,label.getCurrentTextColor()); // Native contrast; selection belongs to the aura.
        mHost.home=false;mNavigation.getBottomBar().setParent(1);
        assertFalse(find("arc-phone-home").isSelected());assertTrue(find("arc-phone-tabs").isSelected());
    }
    @Test public void menuSelectionClearsWhenNativeSheetCloses(){
        var sheet=menu();assertTrue(find("arc-phone-menu").isSelected());
        sheet.destroy();assertFalse(find("arc-phone-menu").isSelected());
    }
    @Test public void lightPaletteKeepsTransparentBackingOutsideCapsule(){
        mHost.color=0xfff0f0f6;mNavigation.refresh();
        assertEquals(Color.TRANSPARENT,mNavigation.getBackgroundColor().intValue());
    }
    @Test public void liveCounterReflectsCurrentModelCount(){
        mHost.count=12;mNavigation.refresh();assertTrue(find("arc-phone-tabs").getContentDescription().toString().contains("12"));
    }
    @Test public void darkSurfaceAndSheetUseHostPaletteWithoutForcingWebTheme(){
        mHost.color=0xff202124;mNavigation.refresh();assertEquals(Color.TRANSPARENT,mNavigation.getBackgroundColor().intValue());
        assertEquals(0xff202124,menu().getSheetBackgroundColorOverride());
    }
    @Test public void leavingPhoneModeReleasesControlsAndClosesSheetWithoutDuplicatingViews(){
        final boolean[] visible={true};mNavigation.initializeWithNative(v->visible[0]=v,t->{});
        var sheet=menu();View bar=mSlot.getChildAt(0);
        mNavigation.setPhoneModeActive(false);assertFalse(visible[0]);assertFalse(find("arc-phone-home").isEnabled());
        verify(mController).hideContent(eq(sheet),anyBoolean());
        mNavigation.setPhoneModeActive(true);assertTrue(visible[0]);assertSame(bar,mSlot.getChildAt(0));assertEquals(1,mSlot.getChildCount());
    }
    @Test public void destroyDoesNotPublishToReleasedNativeCaptureOrVisibility(){
        final int[] callbacks={0};mNavigation.initializeWithNative(v->callbacks[0]++,t->callbacks[0]++);
        menu();callbacks[0]=0;mNavigation.destroy();assertEquals(0,callbacks[0]);
    }
    @Test public void floatingPillKeepsAllTargetsAtNarrowAndWidePhoneWidths(){
        for(int width:new int[]{240,320,800}){
            mSlot.measure(View.MeasureSpec.makeMeasureSpec(width,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(80,View.MeasureSpec.EXACTLY));mSlot.layout(0,0,width,80);
            ViewGroup bar=(ViewGroup)mSlot.getChildAt(0);assertTrue(bar.getRight()<=width-16);
            for(String tag:new String[]{"home","new","tabs","menu"}){View v=find("arc-phone-"+tag);assertTrue(v.getWidth()>=48);assertTrue(v.getHeight()>=48);}
        }
    }
    @Test public void darkSurfaceIsUsedBeforeNativeHostBinds(){
        var context=new android.view.ContextThemeWrapper(mActivity.get(),android.R.style.Theme_Material_NoActionBar);
        FrameLayout slot=new FrameLayout(context);var navigation=new ArcPhoneNavigation(slot,mController);
        assertTrue(Color.luminance(navigation.getBackgroundColor())<.45);navigation.destroy();
    }
    @Test public void visibleMenuRecolorsWithoutReopeningOrLosingScroll(){
        mSlot.measure(View.MeasureSpec.makeMeasureSpec(320,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(ArcPhoneNavigation.getReservedHeight(mActivity.get()),View.MeasureSpec.EXACTLY));mSlot.layout(0,0,320,ArcPhoneNavigation.getReservedHeight(mActivity.get()));
        View bar=mSlot.getChildAt(0);android.graphics.Rect bounds=new android.graphics.Rect(bar.getLeft(),bar.getTop(),bar.getRight(),bar.getBottom());
        var sheet=menu();var scroll=(ScrollView)sheet.getContentView();var body=(ViewGroup)scroll.getChildAt(0);
        scroll.measure(View.MeasureSpec.makeMeasureSpec(320,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY));scroll.layout(0,0,320,360);scroll.scrollTo(0,80);int offset=scroll.getScrollY();
        for(int color:new int[]{0xff202124,Color.WHITE}){
            mHost.color=color;mNavigation.refresh();
            assertSame(scroll,sheet.getContentView());assertSame(body,scroll.getChildAt(0));assertEquals(offset,scroll.getScrollY());
            assertEquals(color,((GradientDrawable)body.getBackground()).getColor().getDefaultColor());
            TextView domain=body.findViewWithTag("arc-phone-domain");assertEquals(color==Color.WHITE?0xff202124:0xfff1f3f4,domain.getCurrentTextColor());
            assertEquals(bounds,new android.graphics.Rect(bar.getLeft(),bar.getTop(),bar.getRight(),bar.getBottom()));
        }
        verify(mController,times(1)).requestShowContent(eq(sheet),anyBoolean());verify(mController,never()).hideContent(any(),anyBoolean());
        verify(mController,times(2)).onSheetBackgroundColorOverrideChanged();
    }
    @Test public void disabledZoomButtonsHaveMatchingDisabledPresentation(){
        mHost.web=false;var content=menu().getContentView();
        for(String tag:new String[]{"minus","plus"}){View step=content.findViewWithTag("arc-phone-zoom-"+tag);assertFalse(step.isEnabled());assertTrue(step.getAlpha()<=.4f);}
    }
    private double contrast(int a,int b){double x=Color.luminance(a),y=Color.luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
    private int composite(int color,int backing){float alpha=Color.alpha(color)/255f;return Color.rgb(Math.round(Color.red(color)*alpha+Color.red(backing)*(1-alpha)),Math.round(Color.green(color)*alpha+Color.green(backing)*(1-alpha)),Math.round(Color.blue(color)*alpha+Color.blue(backing)*(1-alpha)));}
    @Test public void enabledNavigationLabelsMeetAAInLightDarkAndPressedColors(){
        for(int surface:new int[]{Color.WHITE,0xff202124}){
            mHost.color=surface;mHost.home=true;mNavigation.refresh();
            for(String tag:new String[]{"home","new","tabs","menu"}){
                LinearLayout button=(LinearLayout)find("arc-phone-"+tag);TextView label=(TextView)button.getChildAt(1);
                assertTrue(contrast(label.getCurrentTextColor(),surface)>=4.5);
                RippleDrawable ripple=(RippleDrawable)button.getBackground();android.content.res.ColorStateList rippleColor=org.robolectric.util.ReflectionHelpers.getField(ripple.getConstantState(),"mColor");int pressed=composite(rippleColor.getDefaultColor(),surface);
                assertTrue(contrast(label.getCurrentTextColor(),pressed)>=4.5);
                FrameLayout iconHost=(FrameLayout)button.getChildAt(0);android.widget.ImageView icon=(android.widget.ImageView)iconHost.getChildAt(0);
                int iconColor=org.robolectric.util.ReflectionHelpers.getField(icon.getDrawable(),"mColor");
                int iconBacking=iconHost.getBackground() instanceof GradientDrawable bg?bg.getColor().getDefaultColor():surface;
                assertTrue(contrast(iconColor,iconBacking)>=3.0);
                System.out.println("WCAG_NAV surface="+Integer.toHexString(surface)+" action="+tag+" text="+contrast(label.getCurrentTextColor(),surface)+" pressed="+contrast(label.getCurrentTextColor(),pressed)+" icon="+contrast(iconColor,iconBacking));
                assertTrue(button.isFocusable());assertTrue(button.getBackground().isStateful());
            }
        }
    }
    @Test public void phonePaletteKeepsNativeDefaultsUntilExplicitOptIn(){ verifyNativePalette(false); }
    @Test public void phonePalettePreservesDarkAndIncognitoContrast(){ verifyNativePalette(true); }
    @Test public void nativeThemeEventsAutomaticallyNotifyLightDarkLightSurfaceAndIconObservers(){
        var top=mock(org.chromium.chrome.browser.theme.TopUiThemeColorProvider.class);
        var bottom=mock(org.chromium.chrome.browser.theme.BottomUiThemeColorProvider.class);
        var controls=mock(org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider.class);
        when(controls.getControlsPosition()).thenReturn(org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider.ControlsPosition.TOP);
        int scheme=org.chromium.chrome.browser.ui.theme.BrandedColorScheme.APP_DEFAULT;
        when(top.getThemeColor()).thenReturn(Color.RED);when(top.getBrandedColorScheme()).thenReturn(scheme);
        var provider=new org.chromium.chrome.browser.theme.ToolbarThemeColorProvider(
            mActivity.get(),top,bottom,controls,false,
            (context,incognito)->mDarkPalette||incognito?0xff202124:Color.WHITE,
            (context,colorScheme)->android.content.res.ColorStateList.valueOf(mDarkPalette?Color.WHITE:Color.BLACK));
        provider.setArcPhoneFloatingSurfaceEnabled(true);
        var colors=new java.util.ArrayList<Integer>();var icons=new java.util.ArrayList<Integer>();
        provider.addThemeColorObserver((color,animate)->colors.add(color));
        provider.addTintObserver((tint,focus,brand)->icons.add(tint.getDefaultColor()));
        var siteTint=android.content.res.ColorStateList.valueOf(Color.MAGENTA);
        for(boolean night:new boolean[]{true,false,true,false}){
            mDarkPalette=night;
            // Native theme notifications can arrive in either order. No re-opt-in or view rebuild.
            if(night){provider.onTintChanged(siteTint,siteTint,scheme);provider.onThemeColorChanged(Color.BLUE,false);}
            else {provider.onThemeColorChanged(Color.BLUE,false);provider.onTintChanged(siteTint,siteTint,scheme);}
            assertEquals(night?0xff202124:Color.WHITE,provider.getThemeColor());
            assertEquals(night?Color.WHITE:Color.BLACK,provider.getTint().getDefaultColor());
            assertEquals(provider.getThemeColor(),colors.get(colors.size()-1).intValue());
            assertEquals(provider.getTint().getDefaultColor(),icons.get(icons.size()-1).intValue());
        }
        assertEquals(4,colors.size());provider.destroy();
    }
    @Test public void menuUsesSharedFrostedSourceAndRestoresNativeBackdrop() {
        var sampler=new ArcPhoneGlass(mNavigation.getGlassTarget(),new ArcPhoneGlass.Capture(){
            public boolean available(){return false;}
            public void copy(android.graphics.Rect r,android.graphics.Bitmap b,java.util.function.Consumer<Boolean> c){c.accept(false);}
            public void close(){}
        });
        mNavigation.setGlassSampler(sampler);
        var glass=new ArcPhoneGlass.Backdrop();mNavigation.setGlassBackdrop(glass,true);
        var sheet=menu();assertFalse(sheet.hasSolidBackgroundColor());
        assertEquals(android.graphics.Color.TRANSPARENT,sheet.getSheetBackgroundColorOverride());
        assertTrue(sheet.getContentView().getBackground() instanceof ArcPhoneGlass.Backdrop);
        Object token=mHost.token;mHost.color=0xff202124;mNavigation.refresh();
        assertSame(token,mHost.token);assertFalse(sheet.hasSolidBackgroundColor());
        mNavigation.setGlassBackdrop(glass,false);assertTrue(sheet.hasSolidBackgroundColor());
        assertEquals(0xff202124,sheet.getSheetBackgroundColorOverride());
        mNavigation.dismissMenu();sampler.destroy();
    }
    @Test public void glassMenuAndPressedControlsKeepContrastAcrossRepeatedThemeChanges(){
        var glass=new ArcPhoneGlass.Backdrop();mNavigation.setGlassBackdrop(glass,true);
        var sheet=menu();View content=sheet.getContentView();View bar=mNavigation.getGlassTarget();Object geometry=bar.getLayoutParams();
        for(int surface:new int[]{0xff202124,Color.WHITE,0xff202124,Color.WHITE}){
            mHost.color=surface;mNavigation.refresh();
            assertSame(bar,mNavigation.getGlassTarget());assertSame(geometry,bar.getLayoutParams());
            assertSame(glass,bar.getBackground());assertEquals(surface,sheet.getSheetBackgroundColorOverride());
            assertSame(content,sheet.getContentView());
            int behind=surface==Color.WHITE?Color.BLACK:Color.WHITE;
            int backing=composite(glass.tintColor(),behind);
            for(String tag:new String[]{"home","new","tabs","menu"}){
                LinearLayout button=(LinearLayout)find("arc-phone-"+tag);
                var label=(TextView)button.getChildAt(1);
                var ripple=(RippleDrawable)button.getBackground();
                android.content.res.ColorStateList pressed=org.robolectric.util.ReflectionHelpers.getField(ripple.getConstantState(),"mColor");
                assertTrue(contrast(label.getCurrentTextColor(),backing)>=4.5);
                assertTrue(contrast(label.getCurrentTextColor(),composite(pressed.getDefaultColor(),backing))>=4.5);
                var iconHost=(FrameLayout)button.getChildAt(0);
                int icon=org.robolectric.util.ReflectionHelpers.getField(((android.widget.ImageView)iconHost.getChildAt(0)).getDrawable(),"mColor");
                int iconBacking=iconHost.getBackground() instanceof GradientDrawable selected?selected.getColor().getDefaultColor():backing;
                assertTrue(contrast(icon,iconBacking)>=3.0);
            }
            TextView domain=sheet.getContentView().findViewWithTag("arc-phone-domain");
            assertTrue(contrast(domain.getCurrentTextColor(),surface)>=4.5);
        }
        verify(mController,times(1)).requestShowContent(eq(sheet),anyBoolean());
        verify(mController,never()).hideContent(any(),anyBoolean());
    }
    private void verifyNativePalette(boolean dark) {
        mDarkPalette=dark;
        {
            var top=mock(org.chromium.chrome.browser.theme.TopUiThemeColorProvider.class);
            var bottom=mock(org.chromium.chrome.browser.theme.BottomUiThemeColorProvider.class);
            var controls=mock(org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider.class);
            when(controls.getControlsPosition()).thenReturn(org.chromium.chrome.browser.browser_controls.BrowserControlsStateProvider.ControlsPosition.TOP);
            int scheme=dark?org.chromium.chrome.browser.ui.theme.BrandedColorScheme.INCOGNITO:org.chromium.chrome.browser.ui.theme.BrandedColorScheme.APP_DEFAULT;
            var siteTint=android.content.res.ColorStateList.valueOf(0xffffffff);
            var paletteContext=mock(android.content.Context.class);
            var paletteResources=mock(android.content.res.Resources.class);
            when(paletteContext.getResources()).thenReturn(paletteResources);
            when(paletteResources.getColorStateList(anyInt(),any())).thenReturn(siteTint);
            when(top.getThemeColor()).thenReturn(Color.RED);when(top.getTint()).thenReturn(siteTint);
            when(top.getActivityFocusTint()).thenReturn(siteTint);when(top.getBrandedColorScheme()).thenReturn(scheme);
            var provider=new org.chromium.chrome.browser.theme.ToolbarThemeColorProvider(
                    paletteContext,top,bottom,controls,false,
                    (context,incognito)->mDarkPalette||incognito?0xff202124:Color.WHITE,
                    (context,colorScheme)->android.content.res.ColorStateList.valueOf(
                            mDarkPalette||colorScheme==org.chromium.chrome.browser.ui.theme.BrandedColorScheme.INCOGNITO
                                    ?Color.WHITE:Color.BLACK));
            assertEquals(Color.RED,provider.getThemeColor());assertSame(siteTint,provider.getTint());
            provider.setArcPhoneFloatingSurfaceEnabled(true);
            assertEquals(dark?0xff202124:Color.WHITE,provider.getThemeColor());
            assertEquals(dark?Color.WHITE:Color.BLACK,provider.getTint().getDefaultColor());
            provider.onThemeColorChanged(Color.BLUE,false);
            provider.onTintChanged(siteTint,siteTint.withAlpha(128),scheme);
            assertEquals(dark?0xff202124:Color.WHITE,provider.getThemeColor());
            assertEquals(128,Color.alpha(provider.getActivityFocusTint().getDefaultColor()));
            if(!dark){
                when(top.getBrandedColorScheme()).thenReturn(org.chromium.chrome.browser.ui.theme.BrandedColorScheme.DARK_BRANDED_THEME);
                provider.onTintChanged(siteTint,siteTint,org.chromium.chrome.browser.ui.theme.BrandedColorScheme.DARK_BRANDED_THEME);
                assertEquals(Color.WHITE,provider.getThemeColor());assertEquals(Color.BLACK,provider.getTint().getDefaultColor());
                assertEquals(org.chromium.chrome.browser.ui.theme.BrandedColorScheme.APP_DEFAULT,provider.getBrandedColorScheme());
                when(top.getBrandedColorScheme()).thenReturn(org.chromium.chrome.browser.ui.theme.BrandedColorScheme.INCOGNITO);
                provider.onTintChanged(siteTint,siteTint,org.chromium.chrome.browser.ui.theme.BrandedColorScheme.INCOGNITO);
                assertEquals(0xff202124,provider.getThemeColor());
                when(top.getBrandedColorScheme()).thenReturn(scheme);
                provider.onTintChanged(siteTint,siteTint,scheme);assertEquals(Color.WHITE,provider.getThemeColor());
                mDarkPalette=true;provider.setArcPhoneFloatingSurfaceEnabled(true);assertEquals(0xff202124,provider.getThemeColor());
                mDarkPalette=false;provider.setArcPhoneFloatingSurfaceEnabled(true);assertEquals(Color.WHITE,provider.getThemeColor());
            }
            provider.setArcPhoneFloatingSurfaceEnabled(false);
            assertEquals(Color.RED,provider.getThemeColor());assertSame(siteTint,provider.getTint());
            provider.destroy();verify(controls).removeObserver(provider);
        }
    }

}
