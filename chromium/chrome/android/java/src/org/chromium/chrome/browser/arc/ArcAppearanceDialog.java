// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.AlertDialog;
import android.content.Context;

import org.chromium.chrome.R;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

/** Native appearance selector, reachable from settings in both Arc and mobile layouts. */
public final class ArcAppearanceDialog {
    private ArcAppearanceDialog() {}

    public static int labelForMode(int mode) {
        return switch (mode) {
            case ArcDesktopPolicy.MODE_ARC -> R.string.arc_interface_arc;
            case ArcDesktopPolicy.MODE_MOBILE -> R.string.arc_interface_mobile;
            default -> R.string.arc_interface_auto;
        };
    }

    public static AlertDialog create(Context context, Runnable onChanged) {
        CharSequence[] choices = {
            context.getString(R.string.arc_interface_auto),
            context.getString(R.string.arc_interface_arc),
            context.getString(R.string.arc_interface_mobile)
        };
        return new AlertDialog.Builder(context)
                .setTitle(R.string.arc_interface)
                .setSingleChoiceItems(choices, ArcDesktopAppearance.getUiMode(context),
                        (dialog, which) -> {
                            ArcDesktopAppearance.setUiMode(context, which);
                            dialog.dismiss();
                            onChanged.run();
                        })
                .setNegativeButton(android.R.string.cancel, null)
                .create();
    }
}
