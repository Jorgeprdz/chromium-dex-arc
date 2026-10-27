// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.view.View;
import android.widget.PopupMenu;
import org.chromium.build.annotations.NullMarked;
import org.chromium.build.annotations.Nullable;
import org.chromium.chrome.R;
import org.chromium.chrome.browser.content.ContentUtils;
import org.chromium.content_public.browser.WebContents;

/** Native Desktop action beside extensions; calibration is owned by the chosen tab. */
@NullMarked
public final class ArcCameraControls {
    private static final int AUTO = 1, MANUAL = 2, ROTATE = 3, RESET = 4;
    private ArcCameraControls() {}

    public static void show(View anchor, @Nullable WebContents contents) {
        if (contents == null || contents.isDestroyed()) return;
        final int mode = ContentUtils.getArcCameraOrientation(contents);
        PopupMenu popup = new PopupMenu(anchor.getContext(), anchor);
        popup.getMenu().add(1, AUTO, 0, R.string.arc_camera_auto).setCheckable(true).setChecked(mode < 0);
        popup.getMenu().add(1, MANUAL, 1, anchor.getContext().getString(
                R.string.arc_camera_manual, Math.max(0, mode) * 90))
                .setCheckable(true).setChecked(mode >= 0);
        popup.getMenu().setGroupCheckable(1, true, true);
        popup.getMenu().add(0, ROTATE, 2, R.string.arc_camera_rotate).setEnabled(mode >= 0);
        popup.getMenu().add(0, RESET, 3, R.string.arc_camera_reset).setEnabled(mode >= 0);
        popup.setOnMenuItemClickListener(item -> {
            if (contents.isDestroyed()) return false;
            int next;
            switch (item.getItemId()) {
                case AUTO: case RESET: next = -1; break;
                case MANUAL: next = Math.max(0, mode); break;
                case ROTATE: next = (Math.max(0, mode) + 1) % 4; break;
                default: return false;
            }
            ContentUtils.setArcCameraOrientation(contents, next);
            return true;
        });
        popup.show();
    }
}
