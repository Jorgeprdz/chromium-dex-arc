// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.password_manager;

import org.chromium.base.ContextUtils;
import org.chromium.build.annotations.Nullable;
import org.jni_zero.CalledByNative;
import org.jni_zero.JNINamespace;

import java.io.IOException;
import java.security.GeneralSecurityException;

/** Native worker-thread bridge. Failures never return a replacement or fallback key. */
@JNINamespace("password_manager")
final class ArchiumPasswordKeyBridge {
    private ArchiumPasswordKeyBridge() {}

    @CalledByNative
    private static byte @Nullable [] getDataKey() {
        try {
            return ArchiumPasswordKey.getOrCreateDataKey(ContextUtils.getApplicationContext());
        } catch (GeneralSecurityException | IOException | RuntimeException exception) {
            // Native maps this to temporary unavailability and preserves encrypted records.
            return null;
        }
    }
}
