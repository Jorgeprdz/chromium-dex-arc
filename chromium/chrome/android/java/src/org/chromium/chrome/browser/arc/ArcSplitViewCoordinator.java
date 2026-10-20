// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Rect;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.BooleanSupplier;
import java.util.function.Supplier;
import org.chromium.chrome.R;
import org.chromium.chrome.browser.compositor.CompositorViewHolder;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabHidingType;
import org.chromium.chrome.browser.tab.TabLaunchType;
import org.chromium.chrome.browser.tab.TabObserver;
import org.chromium.chrome.browser.tab.TabSelectionType;
import org.chromium.chrome.browser.tabmodel.TabCreator;
import org.chromium.chrome.browser.tabmodel.TabModel;
import org.chromium.chrome.browser.tabmodel.TabModelObserver;
import org.chromium.content_public.browser.LoadUrlParams;
import org.chromium.content_public.browser.WebContents;
import org.chromium.url.GURL;
import org.chromium.ui.base.WindowAndroid;

/** Coordinates two existing native tabs; one selected Tab remains authoritative for browser UI. */
public final class ArcSplitViewCoordinator {
    private static final int MIN_PANE_DP = 240;
    public static final class Labels {
        final String title, existing, newTab, exit, unsupported, noTabs, swap, blocked, controls, focus, restore;
        public Labels(String title, String existing, String newTab, String exit,
                String unsupported, String noTabs, String swap, String blocked) {
            this(title,existing,newTab,exit,unsupported,noTabs,swap,blocked,title);
        }
        public Labels(String title, String existing, String newTab, String exit,
                String unsupported, String noTabs, String swap, String blocked, String controls) {
            this(title,existing,newTab,exit,unsupported,noTabs,swap,blocked,controls,"Ampliar panel","Volver a división");
        }
        public Labels(String title, String existing, String newTab, String exit,
                String unsupported, String noTabs, String swap, String blocked, String controls,
                String focus, String restore) {
            this.focus=focus; this.restore=restore;
            this.controls=controls;
            this.title=title; this.existing=existing; this.newTab=newTab; this.exit=exit;
            this.unsupported=unsupported; this.noTabs=noTabs; this.swap=swap; this.blocked=blocked;
        }
    }
    private final Activity mActivity;
    private final ViewGroup mRoot;
    private final CompositorViewHolder mHolder;
    private final Supplier<TabModel> mModelSupplier;
    private final Supplier<TabCreator> mCreator;
    private final Supplier<Tab> mCurrent;
    private final Runnable mFocusNew;
    private final BooleanSupplier mCanChangeLayout;
    private final SharedPreferences mPrefs;
    private final Labels mLabels;
    private final ArcSplitViewportPolicy mViewportPolicy = new ArcSplitViewportPolicy();
    private final ArcSplitState mState = new ArcSplitState();
    private final ArcSplitSwapAnimator mAnimation = new ArcSplitSwapAnimator();
    private final ArcSplitSwapAnimator mResizeAnimation = new ArcSplitSwapAnimator();
    private boolean mFocusedPane;
    private final ArcSplitDividerView mDivider;
    private final ArcSplitFrameView mFrame;
    private final String mStateKey;
    private final View.OnLayoutChangeListener mLayoutListener;
    private final CompositorViewHolder.FrameRequestObserver mFrameObserver;
    private final Runnable mReconcile = this::reconcile;
    private boolean mPresentationReady;
    private final Runnable mDeferredSave = this::persist;
    private TabModel mModel;
    private Tab mObservedLeft, mObservedRight;
    private AlertDialog mPicker;
    private boolean mDestroyed, mUpdating, mRestored, mDesktop, mIncognito, mBackground;
    private Rect mLastViewport;
    private int mLastLeft=-1, mLastRight=-1, mLastActive=-1;
    private float mLastRatio;

    private final TabObserver mTabs = new TabObserver() {
        @Override public void onShown(Tab tab, int type) {
            if (!mUpdating && tab == mCurrent.get()) {mBackground=false;refresh(mDesktop);}
        }
        @Override public void onHidden(Tab tab, int type) {
            if (mUpdating || !mState.isSplit() || type != TabHidingType.ACTIVITY_HIDDEN) return;
            mDivider.dismissActions();mLastViewport=null;
            mBackground=true; mUpdating=true;
            try {mResizeAnimation.settle();mAnimation.settle();Tab peer=tab==mObservedLeft?mObservedRight:mObservedLeft;
                if (peer!=null && !peer.isDestroyed()) peer.hide(type);
            } finally {mUpdating=false;}
            persist();
        }
        @Override public void onContentChanged(Tab tab) {
            mLastViewport=null;
            if(!mUpdating)refresh(mDesktop);
        }
        @Override public void onDestroyed(Tab tab) {removed(tab);}
        @Override public void onActivityAttachmentChanged(Tab tab, WindowAndroid window) {
            if (!mUpdating && window!=null && window.getActivity().get()!=mActivity) removed(tab);
        }
    };
    private final TabModelObserver mModelObserver = new TabModelObserver() {
        @Override public void didSelectTab(Tab tab,int type,int lastId) {
            if (mUpdating) return;
            if (!mState.isSplit()) {if(!mRestored)refresh(mDesktop);return;}
            if (!mState.activate(tab.getId())) exit(); else refresh(mDesktop);
        }
        @Override public void willCloseTabs(List<Tab> tabs,boolean all,boolean undo) {beforeClose(tabs);}
        @Override public void willCloseTab(Tab tab,boolean alone) {beforeClose(List.of(tab));}
        @Override public void tabRemoved(Tab tab) {removed(tab);}
        @Override public void restoreCompleted() {refresh(mDesktop);}
        @Override public void onDidActiveStateChange(TabModel model,boolean active) {if(!mUpdating)refresh(mDesktop);}
    };

    public ArcSplitViewCoordinator(Activity activity, ViewGroup root, CompositorViewHolder holder,
            Supplier<TabModel> model, Supplier<TabCreator> creator, Supplier<Tab> current,
            Runnable focusNew, BooleanSupplier canChangeLayout, SharedPreferences prefs, Labels labels) {
        mActivity=activity; mRoot=root; mHolder=holder; mModelSupplier=model;
        mCreator=creator; mCurrent=current; mFocusNew=focusNew; mCanChangeLayout=canChangeLayout;
        mPrefs=prefs; mLabels=labels; mStateKey="arc_split_task_"+activity.getTaskId();
        mFrame=new ArcSplitFrameView(activity); mFrame.setVisibility(View.GONE);
        holder.setArcSplitFrameSpacing(dp(4),dp(8));
        mDivider=new ArcSplitDividerView(activity,this::swap,()->{
            if(mCanChangeLayout.getAsBoolean())exit();
        },this::resize,labels.controls,labels.swap,labels.exit);
        mDivider.setBalanceAction(this::balance);
        mDivider.setFocusAction(this::toggleFocusedPane,labels.focus);
        ArcSplitLinkRouter.register(activity,this);
        mDivider.setVisibility(View.GONE);
        View boundary=activity.findViewById(R.id.tab_modal_dialog_container);
        if(boundary==null)boundary=activity.findViewById(R.id.tab_modal_dialog_container_stub);
        while(boundary!=null && boundary.getParent() instanceof View && boundary.getParent()!=root)
            boundary=(View)boundary.getParent();
        int index=boundary!=null && boundary.getParent()==root?root.indexOfChild(boundary):root.getChildCount();
        root.addView(mFrame,index++,new ViewGroup.MarginLayoutParams(0,0));
        root.addView(mDivider,index,new ViewGroup.MarginLayoutParams(dp(48),0));
        mLayoutListener=(v,l,t,r,b,ol,ot,or,ob)->refresh(mDesktop);
        holder.addOnLayoutChangeListener(mLayoutListener);root.addOnLayoutChangeListener(mLayoutListener);
        holder.setArcSplitActivation(this::activate);
        mFrameObserver=()->{
            boolean ready=holder.canPresentArcSplit();
            if(ready!=mPresentationReady) {
                mPresentationReady=ready;
                holder.removeCallbacks(mReconcile);holder.post(mReconcile);
            }
        };
        holder.addFrameRequestObserver(mFrameObserver);
    }

    private boolean compatible(Tab first,Tab second) {
        TabModel model=mModelSupplier.get();
        if(model==null || first==null || second==null || first==second
                || first.isDestroyed() || second.isDestroyed() || first.isClosing() || second.isClosing()
                || first.getId()==second.getId() || first.isNativePage() || second.isNativePage()
                || first.isIncognito()!=second.isIncognito() || first.getProfile()==null
                || !Objects.equals(first.getProfile(),second.getProfile())
                || !Objects.equals(first.getProfile(),model.getProfile())
                || model.getTabById(first.getId())!=first || model.getTabById(second.getId())!=second) return false;
        WindowAndroid one=first.getWindowAndroid(),two=second.getWindowAndroid();
        if(one==null || two==null || one.getActivity().get()!=mActivity || two.getActivity().get()!=mActivity) return false;
        return (first.getView()==null || first.getView()==first.getContentView())
                && (second.getView()==null || second.getView()==second.getContentView());
    }

    public void requestSplit(Tab first) {
        if(mDestroyed || !mDesktop || !mCanChangeLayout.getAsBoolean()) {message(mLabels.blocked);return;}
        dismissPicker();
        List<String> choices=new ArrayList<>(List.of(mLabels.existing,mLabels.newTab));
        if(mState.isSplit())choices.add(mLabels.exit);
        mPicker=new AlertDialog.Builder(mActivity).setTitle(mLabels.title)
                .setItems(choices.toArray(new String[0]),(dialog,which)->{
                    if(which==0)chooseExisting(first);
                    else if(which==1)createAndSplit(first);
                    else exit();
                }).create();
        mPicker.show();
    }
    private void chooseExisting(Tab first) {
        TabModel model=mModelSupplier.get(); if(model==null)return;
        List<Tab> candidates=new ArrayList<>();List<String> titles=new ArrayList<>();
        for(int i=0;i<model.getCount();i++) {
            Tab tab=model.getTabAt(i);
            if(compatible(first,tab)) {candidates.add(tab);String title=tab.getTitle();
                titles.add(title==null || title.isEmpty()?tab.getUrl().getSpec():title);}
        }
        if(candidates.isEmpty()){message(mLabels.noTabs);return;}
        dismissPicker();
        mPicker=new AlertDialog.Builder(mActivity).setTitle(mLabels.existing)
                .setItems(titles.toArray(new String[0]),(dialog,which)->{
                    if(!enter(first,candidates.get(which)))message(mLabels.unsupported);
                }).create();mPicker.show();
    }
    private void createAndSplit(Tab first) {
        TabModel model=mModelSupplier.get();TabCreator creator=mCreator.get();
        if(mDestroyed || creator==null || model==null || model.getTabById(first.getId())!=first
                || first.isDestroyed() || first.isClosing()) return;
        Tab second=creator.createNewTab(new LoadUrlParams("about:blank"),TabLaunchType.FROM_CHROME_UI,first);
        if(second!=null && enter(first,second)) {activate(second.getId());mFocusNew.run();}
        else message(mLabels.unsupported);
    }

    public boolean enter(Tab first,Tab second) {
        if(mDestroyed || !mDesktop || !mCanChangeLayout.getAsBoolean() || !compatible(first,second)
                || !mHolder.canPresentArcSplit()) return false;
        Tab previousSelection=mCurrent.get();
        int oldLeft=mState.leftId(),oldRight=mState.rightId(),oldActive=mState.activeId();float oldRatio=mState.ratio();
        mAnimation.settle();mUpdating=true;
        try {
            unwatch(); mIncognito=first.isIncognito(); mState.start(first.getId(),second.getId());
            select(first);
            if(!mHolder.setArcSplitTabs(first,second,mState.ratio(),mState.activeId())) {
                mState.exit();mHolder.clearArcSplitTabs();
                Tab oldA=mModel.getTabById(oldLeft),oldB=mModel.getTabById(oldRight);
                if(compatible(oldA,oldB)) {
                    mState.start(oldLeft,oldRight);mState.setRatio(oldRatio);mState.activate(oldActive);
                    select(oldActive==oldLeft?oldA:oldB);mIncognito=oldA.isIncognito();
                    mHolder.setArcSplitTabs(oldA,oldB,presentationRatio(mHolder.getArcSplitViewport()),oldActive);watch(oldA,oldB);
                } else {
                    select(previousSelection);
                }
                if(second!=mCurrent.get() && second!=oldA && second!=oldB && !second.isDestroyed()
                        && !second.isHidden())second.hide(TabHidingType.CHANGED_TABS);
                return false;
            }
            watch(first,second);mLastViewport=null;persist();
        } finally {mUpdating=false;}
        refresh(mDesktop);return true;
    }

    public boolean canOpenLink(Tab source) {
        TabModel model=mModelSupplier.get();
        if(mDestroyed || mUpdating || !mDesktop || mBackground || !mCanChangeLayout.getAsBoolean()
                || source==null || source!=mCurrent.get() || source.isDestroyed() || source.isClosing()
                || source.isNativePage() || model==null || model!=mModel || model.getTabById(source.getId())!=source
                || source.getProfile()==null || !Objects.equals(source.getProfile(),model.getProfile())
                || !mHolder.canPresentArcSplit() || mHolder.getWindowVisibility()!=View.VISIBLE) return false;
        WindowAndroid window=source.getWindowAndroid();
        return window!=null && window.getActivity().get()==mActivity;
    }
    public boolean openLink(Tab source,LoadUrlParams params) {
        if(params==null || !ArcSplitLinkRouter.isWebLink(new GURL(params.getUrl())) || !canOpenLink(source))return false;
        mResizeAnimation.settle(); mAnimation.settle();
        if(mState.isSplit() && (source.getId()==mState.leftId() || source.getId()==mState.rightId())) {
            int targetId=source.getId()==mState.leftId()?mState.rightId():mState.leftId();
            Tab target=mModel.getTabById(targetId);
            if(!compatible(source,target))return false;
            mFocusedPane=false;activate(targetId);
            if(target.isDestroyed() || target.isClosing() || mModel.getTabById(targetId)!=target)return false;
            // Standard Tab navigation owns beforeunload, downloads and external redirects.
            target.loadUrl(params);return true;
        }
        TabCreator creator=mCreator.get();if(creator==null)return false;
        Tab target;
        mUpdating=true;
        try { target=creator.createNewTab(params,TabLaunchType.FROM_LONGPRESS_FOREGROUND,source); }
        finally { mUpdating=false; }
        if(target==null)return false;
        if(enter(source,target))activate(target.getId());
        // A native tab was created even if presentation became unavailable; never load it twice.
        return true;
    }
    public boolean adoptLink(Tab source,WebContents contents,BooleanSupplier create) {
        if(!canOpenLink(source))return create.getAsBoolean();
        boolean wasSplit=mState.isSplit();float ratio=mState.ratio();
        boolean sourceOnRight=wasSplit && source.getId()==mState.rightId();
        Tab priorPeer=wasSplit?mModel.getTabById(sourceOnRight?mState.leftId():mState.rightId()):null;
        boolean created;
        mUpdating=true;
        try { created=create.getAsBoolean(); } finally { mUpdating=false; }
        if(!created){refresh(mDesktop);return false;}
        Tab target=null;
        for(int i=0;i<mModel.getCount();i++) {
            Tab candidate=mModel.getTabAt(i);
            if(candidate!=null && !candidate.isDestroyed() && candidate.getWebContents()==contents){target=candidate;break;}
        }
        if(target!=null && enter(sourceOnRight?target:source,sourceOnRight?source:target)) {
            if(wasSplit)mState.setRatio(ratio);
            mFocusedPane=false;activate(target.getId());
            if(priorPeer!=null && priorPeer!=source && priorPeer!=target && !priorPeer.isDestroyed() && !priorPeer.isHidden())
                priorPeer.hide(TabHidingType.CHANGED_TABS);
        } else { exit(); }
        return true;
    }

    private void select(Tab tab) {
        if(mModel==null || tab==null || tab.isDestroyed())return;
        for(int i=0;i<mModel.getCount();i++) {
            if(mModel.getTabAt(i)==tab) {mModel.setIndex(i,TabSelectionType.FROM_USER);return;}
        }
    }
    public void activate(int id) {
        if(mDestroyed || mUpdating || !mState.isSplit() || !mState.activate(id))return;
        mAnimation.settle();mUpdating=true;
        try {Tab tab=mModel.getTabById(id);if(tab==null || tab.isDestroyed()){exit();return;}
            select(tab);mHolder.onContentChanged();
        } finally {mUpdating=false;}
        refresh(mDesktop);persist();
    }

    private void reconcile() {refresh(mDesktop);}

    public void refresh(boolean desktop) {
        if(mDestroyed || mUpdating)return;
        mDesktop=desktop;
        TabModel model=mModelSupplier.get();
        if(model!=mModel) {
            // Finish callbacks against the old model; refresh from the final frame must not reenter.
            mUpdating=true;
            try {mResizeAnimation.settle();mAnimation.settle();} finally {mUpdating=false;}
            if(mModel!=null)persist();
            leavePresentation();unwatch();dismissPicker();
            if(mModel!=null)mModel.removeObserver(mModelObserver);
            mState.exit();mFocusedPane=false;mModel=model;mRestored=false;mBackground=false;
            if(model!=null)model.addObserver(mModelObserver);
        }
        if(model==null)return;
        if(!mRestored && model.isTabModelRestored()) {
            mRestored=restore();
            if(!mRestored)return;
        }
        if(!mState.isSplit())return;
        Tab left=model.getTabById(mState.leftId()),right=model.getTabById(mState.rightId()),active=mCurrent.get();
        if(!compatible(left,right) || active==null || !mState.activate(active.getId())) {exit();return;}
        Rect viewport=mHolder.getArcSplitViewport();
        if(mFocusedPane && desktop && !mBackground && !active.isHidden()
                && mHolder.getWindowVisibility()==View.VISIBLE && mHolder.canPresentArcSplit()) {
            leavePresentation();mDivider.setFocusedMode(true,mLabels.restore);
            int[] at=new int[2],rootAt=new int[2];mHolder.getLocationInWindow(at);mRoot.getLocationInWindow(rootAt);
            ViewGroup.LayoutParams raw=mDivider.getLayoutParams();
            raw.width=dp(48);raw.height=mHolder.getHeight();mDivider.setLayoutParams(raw);
            mDivider.setX(at[0]-rootAt[0]+viewport.right-dp(48));mDivider.setY(at[1]-rootAt[1]);
            mDivider.setVisibility(View.VISIBLE);watch(left,right);return;
        }
        mDivider.setFocusedMode(false,mLabels.restore);
        if(!desktop || mBackground || active.isHidden() || mHolder.getWindowVisibility()!=View.VISIBLE
                || viewport.width()<2*dp(MIN_PANE_DP)+2*dp(4)+dp(8) || viewport.height()<=2*dp(4) || !mHolder.canPresentArcSplit()) {
            mAnimation.settle();leavePresentation();return;
        }
        float ratio=presentationRatio(viewport);
        boolean changed=mLastViewport==null || !mLastViewport.equals(viewport)
                || mLastLeft!=mState.leftId() || mLastRight!=mState.rightId()
                || mLastRatio!=ratio || mLastActive!=mState.activeId();
        if(mAnimation.isRunning() && !changed)return;
        if(changed) {
            mAnimation.settle();mUpdating=true;
            try {if(!mHolder.setArcSplitTabs(left,right,ratio,mState.activeId())) {leavePresentation();return;}}
            finally {mUpdating=false;}
            mLastViewport=new Rect(viewport);mLastLeft=mState.leftId();mLastRight=mState.rightId();
            mLastRatio=ratio;mLastActive=mState.activeId();
        }
        updateMobileViewports(left,right,viewport);
        positionDivider(viewport);watch(left,right);
    }
    private org.chromium.content_public.browser.NavigationController navigation(Tab tab) {
        if(tab==null || tab.isDestroyed())return null;
        var contents=tab.getWebContents();
        return contents==null || contents.isDestroyed()?null:contents.getNavigationController();
    }
    private void updateMobileViewports(Tab left,Tab right,Rect viewport) {
        var one=navigation(left);var two=navigation(right);
        mViewportPolicy.retain(one,two);
        float density=mActivity.getResources().getDisplayMetrics().density;
        Rect[] panes=ArcSplitGeometry.panes(viewport,presentationRatio(viewport),dp(4),dp(8));
        mViewportPolicy.update(one,panes[0].width()/density);
        mViewportPolicy.update(two,panes[1].width()/density);
    }
    private float presentationRatio(Rect viewport) {
        if(viewport.width()<=0)return .5f;
        float minimum=(float)(dp(MIN_PANE_DP)+dp(4)+(dp(8)-dp(8)/2))/viewport.width();
        return Math.max(minimum,Math.min(1f-minimum,mState.ratio()));
    }
    public void setAppearance(int surface) { mFrame.setAppearance(surface); }
    private void positionDivider(Rect viewport) {
        int[] holder=new int[2],root=new int[2];mHolder.getLocationInWindow(holder);mRoot.getLocationInWindow(root);
        ViewGroup.LayoutParams raw=mDivider.getLayoutParams();
        int height=mHolder.getHeight();
        if(raw.width!=dp(48) || raw.height!=height){raw.width=dp(48);raw.height=height;mDivider.setLayoutParams(raw);}
        mDivider.setX(holder[0]-root[0]+viewport.left+viewport.width()*presentationRatio(viewport)-dp(24));
        mDivider.setY(holder[1]-root[1]);mDivider.setGeometry(presentationRatio(viewport),viewport.width());
        mDivider.setVisibility(View.VISIBLE);
        ViewGroup.LayoutParams frameParams=mFrame.getLayoutParams();
        if(frameParams.width!=mHolder.getWidth() || frameParams.height!=height) {
            frameParams.width=mHolder.getWidth();frameParams.height=height;mFrame.setLayoutParams(frameParams);
        }
        mFrame.setX(holder[0]-root[0]);mFrame.setY(holder[1]-root[1]);
        mFrame.setGeometry(viewport,presentationRatio(viewport),mState.activeId()==mState.leftId());
        mFrame.setVisibility(View.VISIBLE);
    }
    public void balance() {
        if(mDestroyed || mFocusedPane || !mState.isSplit() || mLastViewport==null || !mCanChangeLayout.getAsBoolean())return;
        mResizeAnimation.settle();mAnimation.settle();float start=mState.ratio();
        mResizeAnimation.start(p->{if(!mDestroyed){mState.setRatio(start+(.5f-start)*p);refresh(mDesktop);}},this::persist);
    }
    public void toggleFocusedPane() {
        if(mDestroyed || !mState.isSplit() || !mCanChangeLayout.getAsBoolean())return;
        mResizeAnimation.settle();mAnimation.settle();mFocusedPane=!mFocusedPane;refresh(mDesktop);
    }
    boolean isFocusedForTesting() { return mFocusedPane; }
    private void resize(float ratio) {
        if(!mState.isSplit() || mDestroyed || mFocusedPane || !mCanChangeLayout.getAsBoolean())return;
        mResizeAnimation.settle();
        mAnimation.settle();mState.setRatio(ratio);refresh(mDesktop);
        mHolder.removeCallbacks(mDeferredSave);mHolder.postDelayed(mDeferredSave,150);
    }
    public void swap() {
        if(mDestroyed || !mState.isSplit() || mLastViewport==null || !mCanChangeLayout.getAsBoolean())return;
        mResizeAnimation.settle();mAnimation.settle();mState.swap();refresh(mDesktop);persist();
        mDivider.setBusy(true);mHolder.setArcSplitInputBlocked(true);
        mAnimation.start(p -> {if(!mDestroyed)mHolder.setArcSplitSwapProgress(p);},()->{
            mHolder.setArcSplitInputBlocked(false);mDivider.setBusy(false);
        });
    }
    public void exit() {
        if(mDestroyed)return;
        mResizeAnimation.settle();mAnimation.settle();mFocusedPane=false;leavePresentation();unwatch();mState.exit();persist();dismissPicker();
    }
    private void leavePresentation() {
        mViewportPolicy.clear();
        mHolder.clearArcSplitTabs();mDivider.setVisibility(View.GONE);mFrame.setVisibility(View.GONE);mLastViewport=null;
        Tab active=mCurrent.get();
        for(Tab tab:new Tab[]{mObservedLeft,mObservedRight})
            if(tab!=null && tab!=active && !tab.isDestroyed() && !tab.isHidden())tab.hide(TabHidingType.CHANGED_TABS);
    }
    private void beforeClose(List<Tab> closing) {
        if(mUpdating || !mState.isSplit() || mModel==null)return;
        boolean left=closing.stream().anyMatch(t->t.getId()==mState.leftId());
        boolean right=closing.stream().anyMatch(t->t.getId()==mState.rightId());
        if(!left && !right)return;
        Tab survivor=left&&!right?mModel.getTabById(mState.rightId()):right&&!left?mModel.getTabById(mState.leftId()):null;
        mUpdating=true;
        try {if(survivor!=null && !survivor.isDestroyed() && !survivor.isClosing())select(survivor);exit();}
        finally {mUpdating=false;}
    }
    private void removed(Tab tab) {
        if(mDestroyed || mUpdating || !mState.isSplit()
                || (tab.getId()!=mState.leftId() && tab.getId()!=mState.rightId()))return;
        beforeClose(List.of(tab));
    }
    private void watch(Tab left,Tab right) {
        if(mObservedLeft==left && mObservedRight==right)return;
        unwatch();mObservedLeft=left;mObservedRight=right;left.addObserver(mTabs);right.addObserver(mTabs);
    }
    private void unwatch() {
        if(mObservedLeft!=null)mObservedLeft.removeObserver(mTabs);
        if(mObservedRight!=null)mObservedRight.removeObserver(mTabs);
        mObservedLeft=null;mObservedRight=null;
    }
    private void persist() {
        if(mIncognito || mPrefs==null)return;
        String value=mState.isSplit()?mState.leftId()+","+mState.rightId()+","+mState.activeId()+","+mState.ratio():null;
        if(!Objects.equals(value,mPrefs.getString(mStateKey,null))) {
            SharedPreferences.Editor edit=mPrefs.edit();if(value==null)edit.remove(mStateKey);else edit.putString(mStateKey,value);edit.apply();
        }
    }
    /** false means a transient prerequisite is missing; do not consume saved state. */
    private boolean restore() {
        Tab current=mCurrent.get();
        if(current==null)return false;
        if(current.isIncognito())return true;
        String saved=mPrefs.getString(mStateKey,null);
        if(saved==null)return true;
        try {
            String[] parts=saved.split(",");
            if(parts.length!=4)throw new IllegalArgumentException();
            int left=Integer.parseInt(parts[0]),right=Integer.parseInt(parts[1]);
            int active=Integer.parseInt(parts[2]);float ratio=Float.parseFloat(parts[3]);
            if(!Float.isFinite(ratio) || (active!=left && active!=right))throw new IllegalArgumentException();
            Tab a=mModel.getTabById(left),b=mModel.getTabById(right);
            if(a==null || b==null || a==b || a.isDestroyed() || b.isDestroyed()
                    || a.isClosing() || b.isClosing() || a.isIncognito() || b.isIncognito()
                    || !Objects.equals(a.getProfile(),b.getProfile())
                    || !Objects.equals(a.getProfile(),mModel.getProfile()))throw new IllegalArgumentException();
            if(a.getWindowAndroid()==null || b.getWindowAndroid()==null)return false;
            if(!compatible(a,b))throw new IllegalArgumentException();
            if(!mDesktop || !mHolder.canPresentArcSplit() || !mCanChangeLayout.getAsBoolean()
                    || mHolder.getArcSplitViewport().width()<2*dp(MIN_PANE_DP))return false;
            // enter/activate can synchronously call refresh; suppress recursive restoration.
            mRestored=true;
            if(!enter(a,b)) {mRestored=false;return false;}
            mState.setRatio(ratio);activate(active);persist();return true;
        } catch(IllegalArgumentException error) {
            mPrefs.edit().remove(mStateKey).apply();return true;
        }
    }
    private void dismissPicker(){if(mPicker!=null){mPicker.dismiss();mPicker=null;}}
    private void message(String text){if(!mDestroyed && !mActivity.isFinishing())Toast.makeText(mActivity,text,Toast.LENGTH_SHORT).show();}
    private int dp(int value){return Math.round(value*mActivity.getResources().getDisplayMetrics().density);}
    ArcSplitState stateForTesting(){return mState;}
    void settleForTesting(){mAnimation.settle();mResizeAnimation.settle();}
    public void destroy() {
        if(mDestroyed)return;
        mResizeAnimation.settle();persist();mDestroyed=true;mAnimation.destroy();mResizeAnimation.destroy();
        ArcSplitLinkRouter.unregister(mActivity,this);
        mHolder.removeCallbacks(mReconcile);mHolder.removeFrameRequestObserver(mFrameObserver);
        mHolder.removeCallbacks(mDeferredSave);mHolder.removeOnLayoutChangeListener(mLayoutListener);mRoot.removeOnLayoutChangeListener(mLayoutListener);
        mHolder.setArcSplitActivation(null);leavePresentation();unwatch();dismissPicker();
        if(mModel!=null)mModel.removeObserver(mModelObserver);
        mDivider.destroy();
        if(mFrame.getParent()==mRoot)mRoot.removeView(mFrame);
        if(mDivider.getParent()==mRoot)mRoot.removeView(mDivider);
    }
}
