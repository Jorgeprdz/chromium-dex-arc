// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import static org.junit.Assert.*;
import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.PackageInfo;
import android.widget.ImageView;
import android.widget.TextView;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.robolectric.annotation.SQLiteMode;

@RunWith(RobolectricTestRunner.class)
@Config(manifest = Config.NONE, sdk = {29, 36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcAboutDialogTest {
    @Test public void showsInstalledVersionAndApplicationIcon() {
        Activity activity = Robolectric.buildActivity(Activity.class).setup().get();
        AlertDialog dialog = null;
        try {
            PackageInfo info = new PackageInfo();
            info.packageName = activity.getPackageName();
            info.applicationInfo = activity.getApplicationInfo();
            info.versionName = "9.8.7";
            info.setLongVersionCode(987);
            shadowOf(activity.getPackageManager()).installPackage(info);
            dialog = ArcAboutDialog.show(activity, "Acerca de Archium", "Archium %1$s\nChromium %2$s (%3$d)");
            TextView version = dialog.findViewById(android.R.id.content)
                    .getRootView().findViewWithTag("arc-about-version");
            ImageView logo = dialog.findViewById(android.R.id.content)
                    .getRootView().findViewWithTag("arc-about-logo");
            assertEquals("Archium desarrollo\nChromium 9.8.7 (987)", version.getText().toString());
            assertNotNull(logo.getDrawable());
            assertTrue(dialog.isShowing());
        } finally {
            if (dialog != null) dialog.dismiss();
            activity.finish();
        }
    }

    @Test public void independentBuildVersionIsValidatedWithoutUsingChromiumVersion() {
        assertEquals("0.9.201", ArcAboutDialog.parseArchiumVersion(
                "{\"version\":\"0.9.201\",\"build_number\":201}"));
        assertEquals("desarrollo", ArcAboutDialog.parseArchiumVersion("{}"));
        assertEquals("desarrollo", ArcAboutDialog.parseArchiumVersion("not json"));
        assertEquals("desarrollo", ArcAboutDialog.parseArchiumVersion(
                "{\"version\":\"157.0.8086.0\",\"build_number\":201}"));
    }
}
