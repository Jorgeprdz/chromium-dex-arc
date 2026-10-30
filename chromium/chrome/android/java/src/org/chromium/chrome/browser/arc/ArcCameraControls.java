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
    private ArcCameraControls() {}

    public static void show(View anchor, @Nullable WebContents contents) {
        if (contents == null || contents.isDestroyed()) return;
        final int mode = ContentUtils.getArcCameraOrientation(contents);
        PopupMenu popup = new PopupMenu(anchor.getContext(), anchor);
        for (int turns = 1; turns <= 3; turns++) {
            popup.getMenu().add(1, turns, turns - 1,
                    anchor.getContext().getString(R.string.arc_camera_angle, turns * 90))
                    .setCheckable(true).setChecked(mode == turns);
        }
        popup.getMenu().setGroupCheckable(1, true, true);
        popup.setOnMenuItemClickListener(item -> {
            if (contents.isDestroyed()) return false;
            int turns = item.getItemId();
            if (turns < 1 || turns > 3) return false;
            ContentUtils.setArcCameraOrientation(contents, turns);
            return true;
        });
        popup.show();
    }
}
