// Copyright 2017 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.content;

import org.jni_zero.CalledByNative;
import org.jni_zero.JniType;
import org.jni_zero.NativeMethods;

import org.chromium.build.annotations.NullMarked;
import org.chromium.content_public.browser.WebContents;
import org.chromium.chrome.browser.desktop_site.DesktopSiteUtils;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.ui.base.WindowAndroid;
import org.chromium.url.GURL;

/** A utility class to expose content functionality. */
@NullMarked
public class ContentUtils {
    /**
     * @return The user agent string of Chrome.
     */
    public static String getBrowserUserAgent() {
        return ContentUtilsJni.get().getBrowserUserAgent();
    }

    /**
     * Set the user agent used for override. Currently, the only use case we have for overriding a
     * user agent involves spoofing a desktop Linux user agent for "Request desktop site". Set it
     * for WebContents so that it is available when a NavigationEntry requires the user agent to be
     * overridden.
     */
    public static void setUserAgentOverride(WebContents webContents, boolean overrideInNewTabs) {
        ContentUtilsJni.get().setUserAgentOverride(webContents, overrideInNewTabs);
    }

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

    @NativeMethods
    interface Natives {
        @JniType("std::string")
        String getBrowserUserAgent();

        void setUserAgentOverride(WebContents webContents, boolean overrideInNewTabs);
    }
}
