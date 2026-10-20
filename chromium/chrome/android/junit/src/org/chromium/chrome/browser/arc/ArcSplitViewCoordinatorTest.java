// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import static org.mockito.Mockito.*;
import android.app.Activity;
import android.widget.FrameLayout;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.compositor.CompositorViewHolder;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabObserver;
import org.chromium.chrome.browser.tabmodel.TabModel;
import org.chromium.chrome.browser.tabmodel.TabCreator;
import org.chromium.chrome.browser.tabmodel.TabModelObserver;
import org.chromium.ui.base.WindowAndroid;
import org.mockito.ArgumentCaptor;
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcSplitViewCoordinatorTest {
    private static class Fixture {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        FrameLayout root=new FrameLayout(a);
        CompositorViewHolder holder=mock(CompositorViewHolder.class);
        Profile profile=mock(Profile.class);
        TabModel model=mock(TabModel.class);
        TabCreator creator=mock(TabCreator.class);
        Tab one=mock(Tab.class),two=mock(Tab.class),other=mock(Tab.class);
        AtomicReference<Tab> current=new AtomicReference<>(one);
        ArcSplitViewCoordinator coordinator;
        android.content.SharedPreferences prefs=a.getSharedPreferences("split-fixture-"+System.nanoTime(),0);
        Fixture() {this(null,false);}
        Fixture(String saved,boolean incognito) {
            a.setContentView(root);root.layout(0,0,1280,800);
            Tab[] tabs={one,two,other};WindowAndroid window=mock(WindowAndroid.class);
            when(window.getActivity()).thenReturn(new java.lang.ref.WeakReference<>(a));
            when(model.getProfile()).thenReturn(profile);when(model.isTabModelRestored()).thenReturn(true);when(model.getCount()).thenReturn(3);
            for(int i=0;i<tabs.length;i++) {Tab t=tabs[i];int id=17+i;
                when(t.getId()).thenReturn(id);when(t.isIncognito()).thenReturn(incognito);when(t.getProfile()).thenReturn(profile);when(t.getWindowAndroid()).thenReturn(window);
                when(t.getTitle()).thenReturn("Public fixture "+id);when(model.getTabById(id)).thenReturn(t);when(model.getTabAt(i)).thenReturn(t);
            }
            when(holder.canPresentArcSplit()).thenReturn(true);when(holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,1100,800));
            when(holder.getResources()).thenReturn(a.getResources());when(holder.getWindowVisibility()).thenReturn(android.view.View.VISIBLE);
            when(holder.setArcSplitTabs(any(),any(),anyFloat(),anyInt())).thenReturn(true);
            doAnswer(call->{current.set(tabs[(int)call.getArgument(0)]);return null;}).when(model).setIndex(anyInt(),anyInt());
            if(saved!=null)prefs.edit().putString("arc_split_task_"+a.getTaskId(),saved).apply();
            coordinator=new ArcSplitViewCoordinator(a,root,holder,()->model,()->creator,current::get,()->{},()->true,
                prefs,new ArcSplitViewCoordinator.Labels("Split","Existing","New","Exit","Unsupported","No tabs","Swap","Close dialog first"));
            coordinator.refresh(true);
        }
        void close(){coordinator.destroy();a.finish();}
    }
    @Test public void enterAndActivationUseNativeIdentitiesAndExitKeepsTabsAlive() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        assertEquals(17,f.coordinator.stateForTesting().activeId());
        f.coordinator.activate(18);assertSame(f.two,f.current.get());assertEquals(18,f.coordinator.stateForTesting().activeId());
        f.coordinator.exit();assertFalse(f.coordinator.stateForTesting().isSplit());
        verify(f.holder,atLeastOnce()).clearArcSplitTabs();verify(f.one,never()).reload();verify(f.two,never()).reload();f.close();
    }
    @Test public void frameAndActionsStayBelowNativeModalsAndExitPreservesActiveIdentity() {
        Fixture f=new Fixture();f.coordinator.destroy();
        FrameLayout modal=new FrameLayout(f.a);modal.setId(org.chromium.chrome.R.id.tab_modal_dialog_container);f.root.addView(modal);
        f.coordinator=new ArcSplitViewCoordinator(f.a,f.root,f.holder,()->f.model,()->f.creator,f.current::get,()->{},()->true,f.prefs,
            new ArcSplitViewCoordinator.Labels("Split","Existing","New","Exit","Unsupported","No tabs","Swap","Blocked"));
        f.coordinator.refresh(true);assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.activate(18);f.coordinator.setAppearance(0xff654321);
        ArcSplitFrameView frame=null;ArcSplitDividerView divider=null;
        for(int i=0;i<f.root.getChildCount();i++){
            if(f.root.getChildAt(i) instanceof ArcSplitFrameView v)frame=v;
            if(f.root.getChildAt(i) instanceof ArcSplitDividerView v)divider=v;
        }
        assertNotNull(frame);assertNotNull(divider);assertEquals(0xff654321,frame.surfaceForTesting());
        assertTrue(f.root.indexOfChild(frame)<f.root.indexOfChild(divider));assertTrue(f.root.indexOfChild(divider)<f.root.indexOfChild(modal));
        verify(f.holder,atLeastOnce()).setArcSplitFrameSpacing(4,8);
        divider.layout(500,0,548,800);divider.buttonForTesting().performClick();assertTrue(divider.isExpandedForTesting());
        divider.exitForTesting().performClick();assertFalse(f.coordinator.stateForTesting().isSplit());assertSame(f.two,f.current.get());
        assertEquals(android.view.View.GONE,frame.getVisibility());assertEquals(android.view.View.GONE,divider.getVisibility());
        verify(f.one,never()).reload();verify(f.two,never()).reload();verifyNoInteractions(f.creator);
        f.close();assertNull(frame.getParent());assertNull(divider.getParent());assertFalse(divider.isExpandedForTesting());
    }
    @Test public void insufficientSpaceSuspendsTrimAndKeepsSavedPair() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,490,800));clearInvocations(f.holder);f.coordinator.refresh(true);
        verify(f.holder).clearArcSplitTabs();verify(f.holder,never()).setArcSplitTabs(any(),any(),anyFloat(),anyInt());
        assertTrue(f.coordinator.stateForTesting().isSplit());
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,1100,800));f.coordinator.refresh(true);
        verify(f.holder).setArcSplitTabs(f.one,f.two,.5f,17);f.close();
    }
    @Test public void wrongProfileOrNativePageCannotReplaceExistingPair() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        when(f.other.getProfile()).thenReturn(mock(Profile.class));assertFalse(f.coordinator.enter(f.one,f.other));
        assertEquals(18,f.coordinator.stateForTesting().rightId());when(f.other.getProfile()).thenReturn(f.profile);when(f.other.isNativePage()).thenReturn(true);
        assertFalse(f.coordinator.enter(f.one,f.other));assertEquals(18,f.coordinator.stateForTesting().rightId());f.close();
    }
    @Test public void narrowWindowSuspendsThenRestoresSamePairWithoutReload() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,200,800));f.coordinator.refresh(true);
        assertTrue(f.coordinator.stateForTesting().isSplit());verify(f.holder,atLeastOnce()).clearArcSplitTabs();
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,1100,800));f.coordinator.refresh(true);
        verify(f.holder,atLeast(2)).setArcSplitTabs(f.one,f.two,.5f,17);verify(f.one,never()).reload();verify(f.two,never()).reload();f.close();
    }
    @Test public void closingOneChoosesSurvivorAndModelObserversAreReleased() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        ArgumentCaptor<TabModelObserver> observer=ArgumentCaptor.forClass(TabModelObserver.class);verify(f.model).addObserver(observer.capture());
        observer.getValue().willCloseTabs(List.of(f.one),false,true);
        assertSame(f.two,f.current.get());assertFalse(f.coordinator.stateForTesting().isSplit());
        f.close();verify(f.model).removeObserver(observer.getValue());
    }
    @Test public void swapRetainsSelectedTabAndDoesNotNavigate() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.activate(18);f.coordinator.swap();
        assertEquals(18,f.coordinator.stateForTesting().leftId());assertSame(f.two,f.current.get());
        f.coordinator.settleForTesting();verify(f.holder).setArcSplitInputBlocked(true);verify(f.holder,atLeastOnce()).setArcSplitInputBlocked(false);
        verify(f.one,never()).reload();verify(f.two,never()).reload();f.close();
    }
    @Test public void nativeViewportSwitchesEachDesktopControllerWithoutReloadAndRestoresOnExit() {
        Fixture f=new Fixture();
        var first=mock(org.chromium.content_public.browser.NavigationController.class);
        var second=mock(org.chromium.content_public.browser.NavigationController.class);
        var a=mock(org.chromium.content_public.browser.WebContents.class);
        var b=mock(org.chromium.content_public.browser.WebContents.class);
        java.util.concurrent.atomic.AtomicBoolean firstDesktop=new java.util.concurrent.atomic.AtomicBoolean(true);
        java.util.concurrent.atomic.AtomicBoolean secondDesktop=new java.util.concurrent.atomic.AtomicBoolean(true);
        when(first.getUseDesktopUserAgent()).thenAnswer(c->firstDesktop.get());
        when(second.getUseDesktopUserAgent()).thenAnswer(c->secondDesktop.get());
        doAnswer(c->{firstDesktop.set(c.getArgument(0));return null;}).when(first).setUseDesktopUserAgent(anyBoolean(),anyBoolean(),anyBoolean());
        doAnswer(c->{secondDesktop.set(c.getArgument(0));return null;}).when(second).setUseDesktopUserAgent(anyBoolean(),anyBoolean(),anyBoolean());
        when(a.getNavigationController()).thenReturn(first);when(b.getNavigationController()).thenReturn(second);
        when(f.one.getWebContents()).thenReturn(a);when(f.two.getWebContents()).thenReturn(b);
        assertTrue(f.coordinator.enter(f.one,f.two));
        assertFalse(firstDesktop.get());assertFalse(secondDesktop.get());
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,1600,800));f.coordinator.refresh(true);
        assertTrue(firstDesktop.get());assertTrue(secondDesktop.get());
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,1100,800));f.coordinator.refresh(true);
        f.coordinator.exit();assertTrue(firstDesktop.get());assertTrue(secondDesktop.get());
        verify(first,never()).setUseDesktopUserAgent(anyBoolean(),eq(true),anyBoolean());
        verify(second,never()).setUseDesktopUserAgent(anyBoolean(),eq(true),anyBoolean());f.close();
    }
    @Test public void failedPresentationKeepsPreviousPairAndSelection() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.activate(18);
        when(f.holder.setArcSplitTabs(eq(f.one),eq(f.other),anyFloat(),anyInt())).thenReturn(false);
        assertFalse(f.coordinator.enter(f.one,f.other));assertEquals(17,f.coordinator.stateForTesting().leftId());
        assertEquals(18,f.coordinator.stateForTesting().rightId());assertSame(f.two,f.current.get());
        verify(f.other).hide(org.chromium.chrome.browser.tab.TabHidingType.CHANGED_TABS);f.close();
    }
    @Test public void existingPickerAndCancellationNeverCreateTab() {
        Fixture f=new Fixture();f.coordinator.requestSplit(f.one);
        var choice=org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();choice.getListView().performItemClick(null,0,0);
        var existing=org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();existing.getListView().performItemClick(null,0,0);
        assertTrue(f.coordinator.stateForTesting().isSplit());assertEquals(18,f.coordinator.stateForTesting().rightId());
        f.coordinator.requestSplit(f.one);org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog().cancel();
        verifyNoInteractions(f.creator);f.close();
    }
    @Test public void newPickerCreatesExactlyOneNativeTabThenFocusesIt() {
        Fixture f=new Fixture();when(f.creator.createNewTab(any(),anyInt(),eq(f.one))).thenReturn(f.other);
        f.coordinator.requestSplit(f.one);var dialog=org.robolectric.shadows.ShadowAlertDialog.getLatestAlertDialog();
        dialog.getListView().performItemClick(null,1,1);assertEquals(19,f.coordinator.stateForTesting().rightId());
        assertSame(f.other,f.current.get());verify(f.creator).createNewTab(any(),anyInt(),eq(f.one));f.close();
    }
    @Test public void backgroundHidesPeerAndForegroundRestoresPair() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        ArgumentCaptor<TabObserver> observer=ArgumentCaptor.forClass(TabObserver.class);verify(f.one).addObserver(observer.capture());
        observer.getValue().onHidden(f.one,org.chromium.chrome.browser.tab.TabHidingType.ACTIVITY_HIDDEN);
        verify(f.two).hide(org.chromium.chrome.browser.tab.TabHidingType.ACTIVITY_HIDDEN);
        observer.getValue().onShown(f.one,1);assertTrue(f.coordinator.stateForTesting().isSplit());f.close();
    }
    @Test public void nativeRestoredIdsReopenOnlyExistingPairAndKeepRatio() {
        Fixture f=new Fixture("17,18,18,0.65",false);
        assertTrue(f.coordinator.stateForTesting().isSplit());assertSame(f.two,f.current.get());
        assertEquals(.65f,f.coordinator.stateForTesting().ratio(),.001f);verifyNoInteractions(f.creator);f.close();
    }
    @Test public void missingRestoredIdDoesNotResurrectTabs() {
        Fixture f=new Fixture("17,999,17,0.5",false);assertFalse(f.coordinator.stateForTesting().isSplit());
        assertTrue(f.prefs.getAll().isEmpty());verifyNoInteractions(f.creator);f.close();
    }
    @Test public void privatePairNeverOverwritesNormalPairOnDisk() {
        Fixture f=new Fixture("17,18,18,0.65",true);assertFalse(f.coordinator.stateForTesting().isSplit());
        assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.swap();f.coordinator.settleForTesting();f.coordinator.exit();
        assertEquals("17,18,18,0.65",f.prefs.getString("arc_split_task_"+f.a.getTaskId(),null));f.close();
    }
    @Test public void unchangedGeometryStillRebindsInactiveContentAndForeground() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        ArgumentCaptor<TabObserver> one=ArgumentCaptor.forClass(TabObserver.class),two=ArgumentCaptor.forClass(TabObserver.class);
        verify(f.one).addObserver(one.capture());verify(f.two).addObserver(two.capture());clearInvocations(f.holder);
        two.getValue().onContentChanged(f.two);verify(f.holder).setArcSplitTabs(f.one,f.two,.5f,17);
        clearInvocations(f.holder);one.getValue().onHidden(f.one,org.chromium.chrome.browser.tab.TabHidingType.ACTIVITY_HIDDEN);
        one.getValue().onShown(f.one,1);verify(f.holder).setArcSplitTabs(f.one,f.two,.5f,17);f.close();
    }
    @Test public void savedPairSurvivesTransientStartupReadiness() {
        Fixture f=new Fixture();String key="arc_split_task_"+f.a.getTaskId();
        f.coordinator.destroy();f.prefs.edit().putString(key,"17,18,18,0.65").apply();when(f.holder.canPresentArcSplit()).thenReturn(false);
        f.coordinator=new ArcSplitViewCoordinator(f.a,f.root,f.holder,()->f.model,()->f.creator,f.current::get,()->{},()->true,f.prefs,
            new ArcSplitViewCoordinator.Labels("Split","Existing","New","Exit","Unsupported","No tabs","Swap","Blocked"));
        f.current.set(null);f.coordinator.refresh(false);assertEquals("17,18,18,0.65",f.prefs.getString(key,null));
        f.current.set(f.one);f.coordinator.refresh(true);assertEquals("17,18,18,0.65",f.prefs.getString(key,null));
        when(f.holder.canPresentArcSplit()).thenReturn(true);f.coordinator.refresh(true);
        assertTrue(f.coordinator.stateForTesting().isSplit());assertSame(f.two,f.current.get());verifyNoInteractions(f.creator);f.close();
    }
    @Test public void asymmetricRatioKeepsTwoUsablePanesWithoutLosingIntendedRatio() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.stateForTesting().setRatio(.2f);
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,500,800));f.coordinator.refresh(true);
        verify(f.holder).setArcSplitTabs(f.one,f.two,.496f,17);assertEquals(.2f,f.coordinator.stateForTesting().ratio(),.001f);
        when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,2000,800));f.coordinator.refresh(true);
        verify(f.holder).setArcSplitTabs(f.one,f.two,.2f,17);f.close();
    }
    @Test public void sceneReadinessEventRetriesPendingRestoreWithoutLayoutChanges() {
        Fixture f=new Fixture();f.coordinator.destroy();f.prefs.edit().putString("arc_split_task_"+f.a.getTaskId(),"17,18,18,0.65").apply();
        when(f.holder.canPresentArcSplit()).thenReturn(false);clearInvocations(f.holder);
        f.coordinator=new ArcSplitViewCoordinator(f.a,f.root,f.holder,()->f.model,()->f.creator,f.current::get,()->{},()->true,f.prefs,
            new ArcSplitViewCoordinator.Labels("Split","Existing","New","Exit","Unsupported","No tabs","Swap","Blocked"));
        f.coordinator.refresh(true);assertFalse(f.coordinator.stateForTesting().isSplit());
        ArgumentCaptor<CompositorViewHolder.FrameRequestObserver> frame=ArgumentCaptor.forClass(CompositorViewHolder.FrameRequestObserver.class);
        verify(f.holder).addFrameRequestObserver(frame.capture());when(f.holder.canPresentArcSplit()).thenReturn(true);
        frame.getValue().onFrameRequested();ArgumentCaptor<Runnable> posted=ArgumentCaptor.forClass(Runnable.class);verify(f.holder).post(posted.capture());
        posted.getValue().run();assertTrue(f.coordinator.stateForTesting().isSplit());f.close();verify(f.holder).removeFrameRequestObserver(frame.getValue());
    }
    @Test public void minimumPanePixelsRemainUsableAtFractionalDensityAndRtl() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));f.root.setLayoutDirection(android.view.View.LAYOUT_DIRECTION_RTL);
        for(float density:new float[]{1f,1.5f,2.625f}) {
            f.a.getResources().getDisplayMetrics().density=density;f.coordinator.stateForTesting().setRatio(.8f);
            int width=Math.round(500*density),minimum=Math.round(240*density);
            when(f.holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,width,800));clearInvocations(f.holder);f.coordinator.refresh(true);
            ArgumentCaptor<Float> ratio=ArgumentCaptor.forClass(Float.class);verify(f.holder).setArcSplitTabs(eq(f.one),eq(f.two),ratio.capture(),eq(17));
            android.graphics.Rect[] panes=ArcSplitGeometry.panes(new android.graphics.Rect(0,0,width,800),ratio.getValue(),Math.round(4*density),Math.round(8*density));
            assertTrue(panes[0].width()>=minimum);assertTrue(panes[1].width()>=minimum);
            assertEquals(17,f.coordinator.stateForTesting().leftId());assertEquals(.8f,f.coordinator.stateForTesting().ratio(),.001f);
        }
        f.a.getResources().getDisplayMetrics().density=1f;f.close();
    }
    @Test public void failedFirstPresentationRestoresSelectionAndHidesUnattachedPeer() {
        Fixture f=new Fixture();when(f.holder.setArcSplitTabs(any(),any(),anyFloat(),anyInt())).thenReturn(false);
        assertFalse(f.coordinator.enter(f.two,f.other));assertSame(f.one,f.current.get());
        verify(f.other).hide(org.chromium.chrome.browser.tab.TabHidingType.CHANGED_TABS);assertFalse(f.coordinator.stateForTesting().isSplit());f.close();
    }
}
