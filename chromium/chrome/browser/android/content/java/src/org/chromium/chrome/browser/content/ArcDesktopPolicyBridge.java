// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.content;

import org.jni_zero.CalledByNative;
import org.jni_zero.JniType;

import org.chromium.build.annotations.NullMarked;
import org.chromium.chrome.browser.desktop_site.DesktopSiteUtils;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.content_public.browser.WebContents;
import org.chromium.ui.base.WindowAndroid;
import org.chromium.url.GURL;

/** Java policy queries shared with native navigation; owns no Java-to-native bindings. */
@NullMarked
final class ArcDesktopPolicyBridge {
    private ArcDesktopPolicyBridge() {}

    /** Same per-window policy for renderer navigations as TabImpl uses for browser loads. */
    @CalledByNative
    private static int getArchiumUserAgentMode(WebContents webContents, @JniType("GURL") GURL url) {
        WindowAndroid window = webContents.getTopLevelNativeWindow();
        if (window == null) return -1;
        android.content.Context context = window.getContext().get();
        if (context == null) return -1;
        Profile profile = Profile.fromWebContents(webContents);
        if (profile == null) return -1;
        return DesktopSiteUtils.shouldOverrideDesktopSite(profile, url, context) ? 1 : 0;
    }

    @CalledByNative
    private static boolean isArchiumDocumentPipEnabled(WebContents webContents) {
        WindowAndroid window = webContents.getTopLevelNativeWindow();
        if (window == null) return false;
        android.content.Context context = window.getContext().get();
        return context != null && DesktopSiteUtils.isArchiumDocumentPipEnabled(context);
    }

}
