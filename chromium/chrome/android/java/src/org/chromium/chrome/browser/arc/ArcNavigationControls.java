// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.widget.ImageButton;
import android.view.View;

import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabObserver;

import java.util.function.Supplier;
import java.util.function.BiPredicate;

/** Keep Arc navigation state attached to the current Chromium Tab only. */
public final class ArcNavigationControls {
    private final Supplier<Tab> mCurrent;
    private final ImageButton mBack;
    private final ImageButton mForward;
    private final ImageButton mReload;
    private Tab mObserved;
    private boolean mDestroyed;
    private BiPredicate<View, Boolean> mOpenHistory;
    private Runnable mDismissHistory = () -> {};
    private final TabObserver mObserver = new TabObserver() {
        @Override public void onUrlUpdated(Tab tab) { changed(tab); }
        @Override public void onNavigationEntriesDeleted(Tab tab) { changed(tab); }
        @Override public void onLoadStarted(Tab tab, boolean toDifferentDocument) { changed(tab); }
        @Override public void onLoadStopped(Tab tab, boolean toDifferentDocument) { changed(tab); }
        @Override public void onHidden(Tab tab, int type) {
            if (tab == mObserved) mDismissHistory.run();
        }
        @Override public void onDestroyed(Tab tab) {
            if (tab != mObserved) return;
            mDismissHistory.run();
            detach();
            update(null);
        }
    };

    public ArcNavigationControls(Supplier<Tab> current, ImageButton back,
            ImageButton forward, ImageButton reload) {
        mCurrent = current;
        mBack = back;
        mForward = forward;
        mReload = reload;
        mBack.setOnClickListener(v -> {
            Tab tab = selected();
            if (tab != null && tab.canGoBack()) tab.goBack();
        });
        mForward.setOnClickListener(v -> {
            Tab tab = selected();
            if (tab != null && tab.canGoForward()) tab.goForward();
        });
        mReload.setOnClickListener(v -> {
            Tab tab = selected();
            if (tab != null) tab.reload();
        });
    }

    /** Native history presentation remains owned by Chromium; this class guards its lifecycle. */
    public void setHistoryActions(BiPredicate<View, Boolean> open, Runnable dismiss) {
        if (mDestroyed) return;
        mDismissHistory.run();
        mOpenHistory = open;
        mDismissHistory = dismiss;
        mBack.setOnLongClickListener(v -> openHistory(v, false));
        mForward.setOnLongClickListener(v -> openHistory(v, true));
    }

    private boolean openHistory(View anchor, boolean forward) {
        Tab tab = selected();
        if (tab == null || mOpenHistory == null
                || !(forward ? tab.canGoForward() : tab.canGoBack())) return false;
        refresh();
        return mOpenHistory.test(anchor, forward);
    }

    private Tab selected() {
        if (mDestroyed) return null;
        Tab tab = mCurrent.get();
        return tab == null || tab.isDestroyed() ? null : tab;
    }

    /** A disabled Back still occupies a reachable, labelled compact navigation row. */
    public void setExpanded(boolean expanded) {
        mBack.setVisibility(View.VISIBLE);
        mForward.setVisibility(expanded ? View.VISIBLE : View.GONE);
        mReload.setVisibility(expanded ? View.VISIBLE : View.GONE);
    }

    private void changed(Tab tab) {
        if (!mDestroyed && tab == mObserved) {
            mDismissHistory.run();
            refresh();
        }
    }

    public void refresh() {
        if (mDestroyed) return;
        Tab selected = mCurrent.get();
        if (selected != null && selected.isDestroyed()) selected = null;
        if (selected != mObserved) {
            mDismissHistory.run();
            detach();
            mObserved = selected;
            if (selected != null) selected.addObserver(mObserver);
        }
        update(selected);
    }

    private void update(Tab tab) {
        mBack.setEnabled(tab != null && tab.canGoBack());
        mForward.setEnabled(tab != null && tab.canGoForward());
        mReload.setEnabled(tab != null);
    }

    private void detach() {
        if (mObserved != null) {
            mObserved.removeObserver(mObserver);
            mObserved = null;
        }
    }

    public void destroy() {
        if (mDestroyed) return;
        mDestroyed = true;
        mDismissHistory.run();
        mDismissHistory = () -> {};
        mOpenHistory = null;
        mBack.setOnLongClickListener(null);
        mForward.setOnLongClickListener(null);
        detach();
        update(null);
    }
}
