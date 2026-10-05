// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.autofill;

/** This unbranded fork has no internal Google backend; it may use the selected Android service. */
public final class ArchiumAutofillPolicy {
    private ArchiumAutofillPolicy() {}

    public static boolean mustUseInternalGoogleProvider(String browserPackage, boolean googleService) {
        return googleService && !"app.archium.android".equals(browserPackage);
    }
}
