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
import org.chromium.ui.base.WindowAndroid;

/** Coordinates two existing native tabs; one selected Tab remains authoritative for browser UI. */
public final class ArcSplitViewCoordinator {
    private static final int MIN_PANE_DP = 240;
    public static final class Labels {
        final String title, existing, newTab, exit, unsupported, noTabs, swap, blocked;
        public Labels(String title, String existing, String newTab, String exit,
                String unsupported, String noTabs, String swap, String blocked) {
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
    private final ArcSplitDividerView mDivider;
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
            mAnimation.settle();mLastViewport=null;
            mBackground=true; mUpdating=true;
            try {Tab peer=tab==mObservedLeft?mObservedRight:mObservedLeft;
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
        mDivider=new ArcSplitDividerView(activity,this::swap,this::resize,labels.swap);
        mDivider.setVisibility(View.GONE);
        View boundary=activity.findViewById(R.id.tab_modal_dialog_container);
        if(boundary==null)boundary=activity.findViewById(R.id.tab_modal_dialog_container_stub);
        while(boundary!=null && boundary.getParent() instanceof View && boundary.getParent()!=root)
            boundary=(View)boundary.getParent();
        int index=boundary!=null && boundary.getParent()==root?root.indexOfChild(boundary):root.getChildCount();
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
            if(mModel!=null)persist();
            leavePresentation();unwatch();dismissPicker();
            if(mModel!=null)mModel.removeObserver(mModelObserver);
            mState.exit();mModel=model;mRestored=false;mBackground=false;
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
        if(!desktop || mBackground || active.isHidden() || mHolder.getWindowVisibility()!=View.VISIBLE
                || viewport.width()<2*dp(MIN_PANE_DP) || viewport.height()<=0 || !mHolder.canPresentArcSplit()) {
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
        int leftWidth=Math.round(viewport.width()*presentationRatio(viewport));
        mViewportPolicy.update(one,leftWidth/density);
        mViewportPolicy.update(two,(viewport.width()-leftWidth)/density);
    }
    private float presentationRatio(Rect viewport) {
        if(viewport.width()<=0)return .5f;
        float minimum=(float)dp(MIN_PANE_DP)/viewport.width();
        return Math.max(minimum,Math.min(1f-minimum,mState.ratio()));
    }
    private void positionDivider(Rect viewport) {
        int[] holder=new int[2],root=new int[2];mHolder.getLocationInWindow(holder);mRoot.getLocationInWindow(root);
        ViewGroup.LayoutParams raw=mDivider.getLayoutParams();
        int height=mHolder.getHeight();
        if(raw.width!=dp(48) || raw.height!=height){raw.width=dp(48);raw.height=height;mDivider.setLayoutParams(raw);}
        mDivider.setX(holder[0]-root[0]+viewport.left+viewport.width()*presentationRatio(viewport)-dp(24));
        mDivider.setY(holder[1]-root[1]);mDivider.setGeometry(presentationRatio(viewport),viewport.width());
        mDivider.setVisibility(View.VISIBLE);
    }
    private void resize(float ratio) {
        if(!mState.isSplit() || mDestroyed)return;
        mAnimation.settle();mState.setRatio(ratio);refresh(mDesktop);
        mHolder.removeCallbacks(mDeferredSave);mHolder.postDelayed(mDeferredSave,150);
    }
    public void swap() {
        if(mDestroyed || !mState.isSplit() || mLastViewport==null || !mCanChangeLayout.getAsBoolean())return;
        mAnimation.settle();mState.swap();refresh(mDesktop);persist();
        mDivider.setBusy(true);mHolder.setArcSplitInputBlocked(true);
        mAnimation.start(p -> {if(!mDestroyed)mHolder.setArcSplitSwapProgress(p);},()->{
            mHolder.setArcSplitInputBlocked(false);mDivider.setBusy(false);
        });
    }
    public void exit() {
        if(mDestroyed)return;
        mAnimation.settle();leavePresentation();unwatch();mState.exit();persist();dismissPicker();
    }
    private void leavePresentation() {
        mViewportPolicy.clear();
        mHolder.clearArcSplitTabs();mDivider.setVisibility(View.GONE);mLastViewport=null;
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
    void settleForTesting(){mAnimation.settle();}
    public void destroy() {
        if(mDestroyed)return;
        persist();mDestroyed=true;mAnimation.destroy();
        mHolder.removeCallbacks(mReconcile);mHolder.removeFrameRequestObserver(mFrameObserver);
        mHolder.removeCallbacks(mDeferredSave);mHolder.removeOnLayoutChangeListener(mLayoutListener);mRoot.removeOnLayoutChangeListener(mLayoutListener);
        mHolder.setArcSplitActivation(null);leavePresentation();unwatch();dismissPicker();
        if(mModel!=null)mModel.removeObserver(mModelObserver);
        if(mDivider.getParent()==mRoot)mRoot.removeView(mDivider);
    }
}
