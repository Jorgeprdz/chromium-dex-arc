// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

/** Versioned storage; a null persistence keeps an incognito session entirely in memory. */
public final class ArcSidebarStore {
    public interface Persistence {
        String read();
        void write(String state);
    }
    private final Persistence mPersistence;
    private String mCommitted;

    public ArcSidebarStore(Persistence persistence) { mPersistence = persistence; }

    public ArcSidebarState load() {
        if (mCommitted == null) {
            String encoded = mPersistence == null ? "" : mPersistence.read();
            // Preserve invalid/future state for recovery. Never write a replacement on load.
            ArcSidebarState state = encoded.isEmpty() ? new ArcSidebarState()
                    : ArcSidebarState.deserialize(encoded);
            mCommitted = state.serialize();
        }
        // Callers edit an isolated draft. Only a successful save publishes its changes.
        return ArcSidebarState.deserialize(mCommitted);
    }

    public void save(ArcSidebarState state) {
        String encoded = state.serialize();
        if (mPersistence != null) mPersistence.write(encoded);
        mCommitted = encoded;
    }
}
