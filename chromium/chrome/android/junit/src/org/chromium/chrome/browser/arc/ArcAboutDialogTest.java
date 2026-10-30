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

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

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
    @Test public void showsInstalledVersionAndApplicationIcon() throws Exception {
        Activity activity = Robolectric.buildActivity(Activity.class).setup().get();
        AlertDialog dialog = null;
        Path directory = Files.createTempDirectory("archium-about-assets");
        Path assets = directory.resolve("fixture.apk");
        try {
            // The Chromium runner contains the real CI asset; the standalone
            // runner does not. Overlay a known test-owned asset in both cases.
            try (ZipOutputStream zip = new ZipOutputStream(Files.newOutputStream(assets))) {
                zip.putNextEntry(new ZipEntry("assets/archium-build.json"));
                zip.write("{\"version\":\"0.9.201\",\"build_number\":201}"
                        .getBytes(StandardCharsets.UTF_8));
                zip.closeEntry();
            }
            int cookie = (Integer) android.content.res.AssetManager.class
                    .getMethod("addAssetPath", String.class)
                    .invoke(activity.getAssets(), assets.toString());
            assertTrue("The test asset must be available to the real dialog", cookie > 0);
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
            assertEquals("Archium 0.9.201\nChromium 9.8.7 (987)", version.getText().toString());
            assertNotNull(logo.getDrawable());
            assertTrue(dialog.isShowing());
        } finally {
            if (dialog != null) dialog.dismiss();
            activity.finish();
            Files.deleteIfExists(assets);
            Files.deleteIfExists(directory);
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
