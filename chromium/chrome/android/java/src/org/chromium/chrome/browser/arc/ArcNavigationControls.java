// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.widget.ImageButton;

import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tab.TabObserver;

import java.util.function.Supplier;

/** Keep Arc navigation state attached to the current Chromium Tab only. */
public final class ArcNavigationControls {
    private final Supplier<Tab> mCurrent;
    private final ImageButton mBack;
    private final ImageButton mForward;
    private final ImageButton mReload;
    private Tab mObserved;
    private boolean mDestroyed;
    private final TabObserver mObserver = new TabObserver() {
        @Override public void onUrlUpdated(Tab tab) { changed(tab); }
        @Override public void onNavigationEntriesDeleted(Tab tab) { changed(tab); }
        @Override public void onLoadStarted(Tab tab, boolean toDifferentDocument) { changed(tab); }
        @Override public void onLoadStopped(Tab tab, boolean toDifferentDocument) { changed(tab); }
        @Override public void onDestroyed(Tab tab) {
            if (tab != mObserved) return;
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
    }

    private void changed(Tab tab) {
        if (!mDestroyed && tab == mObserved) refresh();
    }

    public void refresh() {
        if (mDestroyed) return;
        Tab selected = mCurrent.get();
        if (selected != null && selected.isDestroyed()) selected = null;
        if (selected != mObserved) {
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
        mDestroyed = true;
        detach();
        update(null);
    }
}
