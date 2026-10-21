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
import org.chromium.base.test.BaseRobolectricTestRunner;
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
@RunWith(BaseRobolectricTestRunner.class)
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
        Tab one=mock(Tab.class),two=mock(Tab.class),other=mock(Tab.class),four=mock(Tab.class),five=mock(Tab.class);
        AtomicReference<TabModel> suppliedModel=new AtomicReference<>(model);
        AtomicReference<Tab> current=new AtomicReference<>(one);
        java.util.concurrent.atomic.AtomicBoolean allowed=new java.util.concurrent.atomic.AtomicBoolean(true);
        ArcSplitViewCoordinator coordinator;
        android.content.SharedPreferences prefs=a.getSharedPreferences("split-fixture-"+System.nanoTime(),0);
        Fixture() {this(null,false);}
        Fixture(String saved,boolean incognito) {
            a.setContentView(root);root.layout(0,0,1280,800);
            Tab[] tabs={one,two,other,four,five};WindowAndroid window=mock(WindowAndroid.class);
            when(window.getActivity()).thenReturn(new java.lang.ref.WeakReference<>(a));
            when(profile.isOffTheRecord()).thenReturn(incognito);when(model.getProfile()).thenReturn(profile);when(model.isTabModelRestored()).thenReturn(true);when(model.getCount()).thenReturn(5);
            for(int i=0;i<tabs.length;i++) {Tab t=tabs[i];int id=17+i;
                when(t.getId()).thenReturn(id);when(t.isIncognito()).thenReturn(incognito);when(t.getProfile()).thenReturn(profile);when(t.getWindowAndroid()).thenReturn(window);
                when(t.getTitle()).thenReturn("Public fixture "+id);when(model.getTabById(id)).thenReturn(t);when(model.getTabAt(i)).thenReturn(t);
            }
            when(holder.canPresentArcSplit()).thenReturn(true);when(holder.getArcSplitViewport()).thenReturn(new android.graphics.Rect(0,0,1100,800));
            when(holder.getResources()).thenReturn(a.getResources());when(holder.getWindowVisibility()).thenReturn(android.view.View.VISIBLE);
            when(holder.setArcSplitTabs(any(),any(),anyFloat(),anyInt())).thenReturn(true);
            doAnswer(call->{current.set(tabs[(int)call.getArgument(0)]);return null;}).when(model).setIndex(anyInt(),anyInt());
            if(saved!=null)prefs.edit().putString("arc_split_task_"+a.getTaskId(),saved).apply();
            coordinator=new ArcSplitViewCoordinator(a,root,holder,suppliedModel::get,()->creator,current::get,()->{},allowed::get,
                prefs,new ArcSplitViewCoordinator.Labels("Split","Existing","New","Exit","Unsupported","No tabs","Swap","Close dialog first"));
            coordinator.refresh(true);
        }
        void close(){coordinator.destroy();a.finish();}
    }
    @Test public void externalSelectionSuspendsAndRestoresPairWithoutLosingGeometry() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        f.coordinator.stateForTesting().setRatio(.65f);f.coordinator.activate(18);
        f.current.set(f.other);f.coordinator.refresh(true);
        assertSame(f.other,f.current.get());assertFalse(f.coordinator.stateForTesting().isSplit());
        f.current.set(f.two);f.coordinator.refresh(true);
        assertTrue("Returning to a member restores its pair",f.coordinator.stateForTesting().isSplit());
        assertEquals(17,f.coordinator.stateForTesting().leftId());assertEquals(.65f,f.coordinator.stateForTesting().ratio(),.001f);
        assertEquals(18,f.coordinator.stateForTesting().activeId());verifyNoInteractions(f.creator);f.close();
    }
    @Test public void fiveTabsKeepTwoIndependentPairsAndInactiveClosureDoesNotSelectSurvivor() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        f.coordinator.stateForTesting().setRatio(.65f);f.coordinator.activate(18);
        f.current.set(f.four);f.coordinator.refresh(true);assertTrue(f.coordinator.enter(f.four,f.five));
        f.coordinator.stateForTesting().setRatio(.35f);f.coordinator.activate(21);
        f.current.set(f.other);f.coordinator.refresh(true);
        f.current.set(f.two);f.coordinator.refresh(true);
        assertTrue(f.coordinator.stateForTesting().isSplit());assertEquals(.65f,f.coordinator.stateForTesting().ratio(),.001f);
        f.current.set(f.five);f.coordinator.refresh(true);
        assertEquals(20,f.coordinator.stateForTesting().leftId());assertEquals(.35f,f.coordinator.stateForTesting().ratio(),.001f);
        f.current.set(f.other);f.coordinator.refresh(true);
        ArgumentCaptor<TabModelObserver> observer=ArgumentCaptor.forClass(TabModelObserver.class);verify(f.model).addObserver(observer.capture());
        observer.getValue().willCloseTab(f.one,true);assertSame(f.other,f.current.get());
        f.current.set(f.five);f.coordinator.refresh(true);assertTrue(f.coordinator.stateForTesting().isSplit());
        verify(f.one,never()).reload();verify(f.two,never()).reload();verify(f.four,never()).reload();verify(f.five,never()).reload();f.close();
    }
    @Test public void snapshotsAreStableAndPairSelectionRestoresStoredActive() {
        Fixture f=new Fixture();java.util.concurrent.atomic.AtomicInteger changes=new java.util.concurrent.atomic.AtomicInteger();
        f.coordinator.setPairsChangedCallback(changes::incrementAndGet);
        assertTrue(f.coordinator.enter(f.one,f.two));int representative=f.coordinator.getPairSnapshot().get(0)[0];
        f.coordinator.activate(18);assertTrue("Pane activation updates sidebar",changes.get()>=2);
        f.coordinator.swap();f.coordinator.settleForTesting();assertEquals(representative,f.coordinator.getPairSnapshot().get(0)[0]);
        int[] detached=f.coordinator.getPairSnapshot().get(0);detached[1]=999;
        assertEquals(18,f.coordinator.getPairSnapshot().get(0)[1]);
        f.current.set(f.other);f.coordinator.refresh(true);assertTrue(f.coordinator.selectPair(17));assertSame(f.two,f.current.get());
        assertTrue(f.coordinator.isPairMember(17));assertFalse(f.coordinator.enter(f.one,f.four));
        f.coordinator.separatePair(17);assertFalse(f.coordinator.isPairMember(18));assertSame(f.two,f.current.get());f.close();
    }
    @Test public void inactiveMemberAttachmentAndDestructionAreObserved() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        f.current.set(f.four);f.coordinator.refresh(true);assertTrue(f.coordinator.enter(f.four,f.five));
        f.current.set(f.other);f.coordinator.refresh(true);
        ArgumentCaptor<TabObserver> observer=ArgumentCaptor.forClass(TabObserver.class);verify(f.one).addObserver(observer.capture());
        WindowAndroid moved=mock(WindowAndroid.class);Activity elsewhere=Robolectric.buildActivity(Activity.class).setup().get();
        when(moved.getActivity()).thenReturn(new java.lang.ref.WeakReference<>(elsewhere));
        observer.getValue().onActivityAttachmentChanged(f.one,moved);
        assertFalse(f.coordinator.isPairMember(17));assertTrue(f.coordinator.isPairMember(20));assertSame(f.other,f.current.get());
        ArgumentCaptor<TabObserver> otherObserver=ArgumentCaptor.forClass(TabObserver.class);verify(f.five).addObserver(otherObserver.capture());
        otherObserver.getValue().onDestroyed(f.five);assertFalse(f.coordinator.isPairMember(20));assertSame(f.other,f.current.get());
        elsewhere.finish();f.close();
    }
    @Test public void versionedRestoreRejectsEntriesIndependentlyAndDoesNotStealNativeSelection() {
        Fixture f=new Fixture("v2;17,17,18,18,0.65;20,20,21,21,0.35;19,19,20,19,0.5;99,99,100,99,NaN",false);
        assertSame(f.one,f.current.get());assertEquals(2,f.coordinator.getPairSnapshot().size());
        f.current.set(f.other);f.coordinator.refresh(true);assertTrue(f.coordinator.selectPair(20));assertSame(f.five,f.current.get());
        assertEquals(.35f,f.coordinator.stateForTesting().ratio(),.001f);
        assertTrue(f.prefs.getString("arc_split_task_"+f.a.getTaskId(),"").startsWith("v2;"));f.close();
    }
    @Test public void incompatibleSectionSuspendsWithoutLosingPairsRatiosOrNativeSelection() {
        Fixture f=new Fixture();f.coordinator.setPairCompatibility((a,b)->a!=f.one && b!=f.one);
        assertFalse(f.coordinator.enter(f.one,f.two));assertTrue(f.coordinator.enter(f.four,f.five));
        f.coordinator.stateForTesting().setRatio(.35f);f.coordinator.activate(21);
        f.coordinator.setPairCompatibility((a,b)->true);assertTrue(f.coordinator.enter(f.one,f.two));
        f.coordinator.stateForTesting().setRatio(.65f);f.coordinator.activate(18);
        f.current.set(f.other);f.coordinator.refresh(true);clearInvocations(f.model,f.holder);
        f.coordinator.setPairCompatibility((a,b)->a!=f.one && b!=f.one);
        assertTrue("A section move must retain the association",f.coordinator.isPairMember(17));
        assertTrue(f.coordinator.isPairMember(20));assertEquals(2,f.coordinator.getPairSnapshot().size());
        assertSame(f.other,f.current.get());verify(f.model,never()).setIndex(anyInt(),anyInt());
        assertFalse("A suspended row cannot select an incompatible pair",f.coordinator.selectPair(17));
        assertSame(f.other,f.current.get());
        f.current.set(f.two);f.coordinator.refresh(true);clearInvocations(f.holder);
        f.coordinator.refresh(true);verify(f.holder,never()).setArcSplitTabs(any(),any(),anyFloat(),anyInt());
        assertEquals(.65f,f.coordinator.stateForTesting().ratio(),.001f);
        assertFalse(f.coordinator.enter(f.one,f.other));assertEquals(2,f.coordinator.getPairSnapshot().size());
        f.coordinator.setPairCompatibility((a,b)->true);
        verify(f.holder).setArcSplitTabs(f.one,f.two,.65f,18);assertSame(f.two,f.current.get());
        f.current.set(f.other);f.coordinator.refresh(true);assertTrue(f.coordinator.selectPair(20));
        assertSame(f.five,f.current.get());assertEquals(.35f,f.coordinator.stateForTesting().ratio(),.001f);
        assertTrue(f.coordinator.selectPair(17));assertSame(f.two,f.current.get());
        assertEquals(.65f,f.coordinator.stateForTesting().ratio(),.001f);f.close();
    }
    @Test public void incompatibleRestoredPairRemainsStoredAndCanBeExplicitlySeparated() {
        Fixture f=new Fixture("17,18,18,0.65",false);f.coordinator.destroy();
        f.current.set(f.other);
        f.coordinator=new ArcSplitViewCoordinator(f.a,f.root,f.holder,f.suppliedModel::get,()->f.creator,f.current::get,()->{},()->true,f.prefs,
            new ArcSplitViewCoordinator.Labels("Split","Existing","New","Exit","Unsupported","No tabs","Swap","Blocked"));
        f.coordinator.setPairCompatibility((a,b)->false);f.coordinator.refresh(true);
        assertTrue(f.coordinator.isPairMember(17));assertSame(f.other,f.current.get());
        assertTrue(f.prefs.getString("arc_split_task_"+f.a.getTaskId(),"").contains("0.65"));
        f.coordinator.separatePair(17);assertFalse(f.coordinator.isPairMember(18));assertSame(f.other,f.current.get());f.close();
    }
    @Test public void differentProfileWithReusedNativeIdsCannotLoadNormalAssociations() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        String saved=f.prefs.getString("arc_split_task_"+f.a.getTaskId(),null);
        Profile profile=mock(Profile.class);TabModel model=mock(TabModel.class);
        Tab a=mock(Tab.class),b=mock(Tab.class);WindowAndroid window=mock(WindowAndroid.class);
        when(window.getActivity()).thenReturn(new java.lang.ref.WeakReference<>(f.a));
        when(model.getProfile()).thenReturn(profile);when(model.getCount()).thenReturn(2);when(model.isTabModelRestored()).thenReturn(true);
        for(int i=0;i<2;i++) {Tab tab=i==0?a:b;int id=17+i;when(tab.getId()).thenReturn(id);when(tab.getProfile()).thenReturn(profile);
            when(tab.getWindowAndroid()).thenReturn(window);when(model.getTabById(id)).thenReturn(tab);when(model.getTabAt(i)).thenReturn(tab);}
        f.suppliedModel.set(model);f.current.set(a);f.coordinator.refresh(true);
        assertTrue("Persisted associations belong to their original profile",f.coordinator.getPairSnapshot().isEmpty());
        assertTrue(f.coordinator.enter(a,b));f.coordinator.exit();
        assertEquals(saved,f.prefs.getString("arc_split_task_"+f.a.getTaskId(),null));
        f.suppliedModel.set(f.model);f.current.set(f.one);f.coordinator.refresh(true);assertTrue(f.coordinator.isPairMember(18));f.close();
    }
    @Test public void inactiveActivityHiddenDoesNotHideVisiblePair() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        f.current.set(f.four);f.coordinator.refresh(true);assertTrue(f.coordinator.enter(f.four,f.five));
        ArgumentCaptor<TabObserver> observer=ArgumentCaptor.forClass(TabObserver.class);verify(f.one).addObserver(observer.capture());
        clearInvocations(f.four,f.five,f.holder);
        observer.getValue().onHidden(f.one,org.chromium.chrome.browser.tab.TabHidingType.ACTIVITY_HIDDEN);
        verify(f.four,never()).hide(anyInt());verify(f.five,never()).hide(anyInt());
        f.coordinator.refresh(true);verify(f.holder,never()).clearArcSplitTabs();
        assertSame(f.four,f.current.get());f.close();
    }
    @Test public void inactiveSeparationLeavesOtherPairAndSelectionAlone() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));
        f.current.set(f.four);f.coordinator.refresh(true);assertTrue(f.coordinator.enter(f.four,f.five));
        f.coordinator.activate(21);clearInvocations(f.model,f.holder);
        f.coordinator.separatePair(17);
        assertFalse(f.coordinator.isPairMember(18));assertTrue(f.coordinator.isPairMember(21));
        assertSame(f.five,f.current.get());verify(f.model,never()).setIndex(anyInt(),anyInt());
        verify(f.holder,never()).clearArcSplitTabs();f.close();
    }
    @Test public void storeMigrationRejectsMalformedRowsWithoutDroppingOtherPairs() {
        ArcSplitPairStore legacy=ArcSplitPairStore.decode("17,18,18,0.65");
        assertEquals("v2;17,17,18,18,0.65",legacy.encode());
        ArcSplitPairStore store=ArcSplitPairStore.decode("v2;17,17,18,18,0.65;bad;"
                +"20,20,21,20,NaN;20,20,21,20,Infinity;20,20,21,20,0.9;"
                +"20,20,21,999,0.5;20,20,21,20,0.35;19,19,20,19,0.5");
        assertEquals(2,store.pairs().size());assertNull(store.member(19));
        assertSame(store.member(20),store.member(21));
        assertEquals(store.encode(),ArcSplitPairStore.decode(store.encode()).encode());
    }
    @Test public void startupWaitsForNativeModelRestorationWithoutChangingPreferences() {
        Fixture f=new Fixture();f.coordinator.destroy();String key="arc_split_task_"+f.a.getTaskId();
        f.prefs.edit().putString(key,"17,18,18,0.65").apply();when(f.model.isTabModelRestored()).thenReturn(false);
        f.coordinator=new ArcSplitViewCoordinator(f.a,f.root,f.holder,f.suppliedModel::get,()->f.creator,f.current::get,()->{},()->true,f.prefs,
            new ArcSplitViewCoordinator.Labels("Split","Existing","New","Exit","Unsupported","No tabs","Swap","Blocked"));
        f.coordinator.refresh(true);assertTrue(f.coordinator.getPairSnapshot().isEmpty());
        assertFalse(f.coordinator.enter(f.four,f.five));assertEquals("17,18,18,0.65",f.prefs.getString(key,null));
        when(f.model.isTabModelRestored()).thenReturn(true);f.coordinator.refresh(true);
        assertTrue(f.coordinator.isPairMember(18));assertSame(f.one,f.current.get());f.close();
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
    @Test public void balanceAndTemporaryFocusPreservePairAndRatio() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.stateForTesting().setRatio(.7f);
        f.coordinator.activate(18);f.coordinator.toggleFocusedPane();assertTrue(f.coordinator.isFocusedForTesting());
        assertTrue(f.coordinator.stateForTesting().isSplit());assertEquals(.7f,f.coordinator.stateForTesting().ratio(),.001f);
        assertSame(f.two,f.current.get());verify(f.holder,atLeastOnce()).clearArcSplitTabs();
        f.coordinator.toggleFocusedPane();assertFalse(f.coordinator.isFocusedForTesting());
        assertEquals(.7f,f.coordinator.stateForTesting().ratio(),.001f);assertEquals(18,f.coordinator.stateForTesting().activeId());
        f.coordinator.balance();f.coordinator.settleForTesting();assertEquals(.5f,f.coordinator.stateForTesting().ratio(),0f);
        verify(f.one,never()).reload();verify(f.two,never()).reload();f.close();
    }
    @Test public void linkOpeningCreatesNativeTabOrNavigatesNeighborWithOriginalParams() {
        Fixture f=new Fixture();var p=new org.chromium.content_public.browser.LoadUrlParams("https://example.test/item");
        when(f.creator.createNewTab(same(p),anyInt(),eq(f.one))).thenReturn(f.other);
        assertTrue(f.coordinator.openLink(f.one,p));assertEquals(19,f.coordinator.stateForTesting().rightId());assertSame(f.other,f.current.get());
        clearInvocations(f.creator);var next=new org.chromium.content_public.browser.LoadUrlParams("https://example.test/second");
        assertTrue(f.coordinator.openLink(f.other,next));verify(f.one).loadUrl(same(next));verifyNoInteractions(f.creator);
        assertSame(f.one,f.current.get());assertEquals(19,f.coordinator.stateForTesting().rightId());f.close();
    }
    @Test public void staleOrBlockedSourceAndExternalSchemesCannotUseLinkRoute() {
        Fixture f=new Fixture();var url=new org.chromium.url.GURL("https://example.test/item");
        assertTrue(ArcSplitLinkRouter.canOpen(f.one,url));assertFalse(ArcSplitLinkRouter.canOpen(f.one,new org.chromium.url.GURL("mailto:test@example.test")));
        f.allowed.set(false);assertFalse(f.coordinator.openLink(f.one,new org.chromium.content_public.browser.LoadUrlParams(url.getSpec())));
        verifyNoInteractions(f.creator);f.allowed.set(true);f.current.set(f.two);
        assertFalse(ArcSplitLinkRouter.canOpen(f.one,url));f.current.set(f.one);when(f.one.isClosing()).thenReturn(true);
        assertFalse(ArcSplitLinkRouter.canOpen(f.one,url));f.close();assertFalse(ArcSplitLinkRouter.canOpen(f.two,url));
    }
    @Test public void balanceCannotOverwriteNewModelPairAfterModelSwitch() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.stateForTesting().setRatio(.7f);f.coordinator.balance();
        TabModel replacement=mock(TabModel.class);when(replacement.getProfile()).thenReturn(f.profile);
        when(replacement.isTabModelRestored()).thenReturn(true);when(replacement.getCount()).thenReturn(2);
        when(replacement.getTabAt(0)).thenReturn(f.one);when(replacement.getTabAt(1)).thenReturn(f.two);
        when(replacement.getTabById(17)).thenReturn(f.one);when(replacement.getTabById(18)).thenReturn(f.two);
        f.suppliedModel.set(replacement);f.coordinator.refresh(true);assertTrue(f.coordinator.stateForTesting().isSplit());
        f.coordinator.stateForTesting().setRatio(.3f);f.coordinator.settleForTesting();
        assertEquals(.3f,f.coordinator.stateForTesting().ratio(),.001f);f.close();
    }
    @Test public void nativeLinkPreservesHeadersBodyAndRendererFlag() {
        // ResourceRequestBody is final: use its real factory with a scoped JNI boundary.
        var nativeBody=mock(org.chromium.content_public.common.ResourceRequestBody.Natives.class);
        byte[] encoded={1,2,3};
        when(nativeBody.createResourceRequestBodyFromBytes(any())).thenReturn(encoded);
        org.chromium.content_public.common.ResourceRequestBody.setNativesForTesting(nativeBody);
        try {
            Fixture f=new Fixture();var body=org.chromium.content_public.common.ResourceRequestBody.createFromBytes(new byte[]{42});
            assertSame(encoded,body.getEncodedNativeForm());
            when(f.creator.createNewTab(any(),anyInt(),eq(f.one))).thenReturn(f.other);
            assertTrue(ArcSplitLinkRouter.openNative(f.one,new org.chromium.url.GURL("https://example.test/item"),"X-Test: fixture",body,true));
            ArgumentCaptor<org.chromium.content_public.browser.LoadUrlParams> params=ArgumentCaptor.forClass(org.chromium.content_public.browser.LoadUrlParams.class);
            verify(f.creator).createNewTab(params.capture(),anyInt(),eq(f.one));
            assertEquals("X-Test: fixture",params.getValue().getVerbatimHeaders());assertSame(body,params.getValue().getPostData());assertTrue(params.getValue().getIsRendererInitiated());f.close();
        } finally {
            org.chromium.content_public.common.ResourceRequestBody.setNativesForTesting(null);
        }
    }
    @Test public void rendererCreatedContentsKeepNativeIdentityAndPriorNeighborTabAlive() {
        Fixture f=new Fixture();assertTrue(f.coordinator.enter(f.one,f.two));f.coordinator.stateForTesting().setRatio(.7f);
        var contents=mock(org.chromium.content_public.browser.WebContents.class);when(f.other.getWebContents()).thenReturn(contents);
        assertTrue(f.coordinator.adoptLink(f.one,contents,()->{f.current.set(f.other);return true;}));
        assertEquals(17,f.coordinator.stateForTesting().leftId());assertEquals(19,f.coordinator.stateForTesting().rightId());
        assertEquals(.7f,f.coordinator.stateForTesting().ratio(),.001f);assertSame(f.other,f.current.get());verifyNoInteractions(f.creator);
        verify(f.two).hide(org.chromium.chrome.browser.tab.TabHidingType.CHANGED_TABS);verify(f.two,never()).reload();f.close();
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
        clearInvocations(f.holder);
        when(f.holder.setArcSplitTabs(eq(f.four),eq(f.five),anyFloat(),anyInt())).thenReturn(false);
        assertFalse(f.coordinator.enter(f.four,f.five));assertEquals(17,f.coordinator.stateForTesting().leftId());
        assertEquals(18,f.coordinator.stateForTesting().rightId());assertSame(f.two,f.current.get());
        verify(f.five).hide(org.chromium.chrome.browser.tab.TabHidingType.CHANGED_TABS);
        verify(f.holder).setArcSplitTabs(f.one,f.two,.5f,18);f.close();
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
        assertTrue(f.coordinator.stateForTesting().isSplit());assertSame(f.one,f.current.get());
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
        f.current.set(f.one);f.coordinator.refresh(true);assertTrue(f.coordinator.isPairMember(17));assertSame(f.one,f.current.get());
        when(f.holder.canPresentArcSplit()).thenReturn(true);f.coordinator.refresh(true);
        assertTrue(f.coordinator.stateForTesting().isSplit());assertSame(f.one,f.current.get());verifyNoInteractions(f.creator);f.close();
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
        f.coordinator.refresh(true);assertTrue(f.coordinator.isPairMember(17));verify(f.holder,never()).setArcSplitTabs(any(),any(),anyFloat(),anyInt());
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
