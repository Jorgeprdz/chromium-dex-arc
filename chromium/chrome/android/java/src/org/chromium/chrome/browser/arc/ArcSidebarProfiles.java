// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import org.chromium.base.ThreadUtils;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.profiles.ProfileKeyedMap;
import org.chromium.components.prefs.PrefService;
import org.chromium.components.user_prefs.UserPrefs;

/** Uses Chromium profile preferences and its native profile-destruction lifecycle. */
public final class ArcSidebarProfiles {
    public static final String PREF = "archium.sidebar.state";
    private static final ProfileKeyedMap<ArcSidebarStore> sStores = new ProfileKeyedMap<>(
            ProfileKeyedMap.ProfileSelection.OWN_INSTANCE,
            ProfileKeyedMap.noRequiredCleanupAction());

    private ArcSidebarProfiles() {}

    public static ArcSidebarStore getForProfile(Profile profile) {
        ThreadUtils.assertOnUiThread();
        return sStores.getForProfile(profile, owner -> {
            // No regular-profile redirection or persistence for any off-the-record profile.
            if (owner.isOffTheRecord()) return new ArcSidebarStore(null);
            PrefService preferences = UserPrefs.get(owner);
            return new ArcSidebarStore(new ArcSidebarStore.Persistence() {
                @Override public String read() { return preferences.getString(PREF); }
                @Override public void write(String state) { preferences.setString(PREF, state); }
            });
        });
    }
}
