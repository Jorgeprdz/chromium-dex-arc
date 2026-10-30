// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.view.Gravity;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Displays the installed application's approved icon and actual package version. */
public final class ArcAboutDialog {
    private ArcAboutDialog() {}

    static String parseArchiumVersion(String metadata) {
        try {
            JSONObject identity = new JSONObject(metadata);
            String version = identity.getString("version");
            int number = identity.getInt("build_number");
            return number > 0 && version.equals("0.9." + number) ? version : "desarrollo";
        } catch (Exception unavailable) {
            return "desarrollo";
        }
    }

    private static String archiumVersion(Activity activity) {
        try (InputStream input = activity.getAssets().open("archium-build.json")) {
            byte[] metadata = new byte[4097];
            int length = 0;
            while (length < metadata.length) {
                int read = input.read(metadata, length, metadata.length - length);
                if (read < 0) break;
                length += read;
            }
            return length > 4096 ? "desarrollo"
                    : parseArchiumVersion(new String(metadata, 0, length, StandardCharsets.UTF_8));
        } catch (Exception unavailable) {
            return "desarrollo";
        }
    }

    public static AlertDialog show(Activity activity, String title, String versionFormat) {
        int padding = Math.round(24 * activity.getResources().getDisplayMetrics().density);
        LinearLayout content = new LinearLayout(activity);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setGravity(Gravity.CENTER_HORIZONTAL);
        content.setPadding(padding, padding, padding, padding);
        ImageView logo = new ImageView(activity);
        logo.setTag("arc-about-logo");
        logo.setContentDescription("Archium");
        logo.setImageDrawable(activity.getPackageManager().getApplicationIcon(
                activity.getApplicationInfo()));
        logo.setScaleType(ImageView.ScaleType.FIT_CENTER);
        content.addView(logo, new LinearLayout.LayoutParams(padding * 3, padding * 3));
        TextView version = new TextView(activity);
        version.setTag("arc-about-version");
        version.setGravity(Gravity.CENTER);
        version.setPadding(0, padding, 0, 0);
        try {
            PackageInfo info = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0);
            String name = info.versionName == null ? Long.toString(info.getLongVersionCode()) : info.versionName;
            version.setText(String.format(Locale.getDefault(), versionFormat,
                    archiumVersion(activity), name, info.getLongVersionCode()));
        } catch (PackageManager.NameNotFoundException unavailable) {
            // Own package metadata should exist; an unavailable package manager must not crash UI.
            version.setText("Versión no disponible");
        }
        content.addView(version);
        AlertDialog dialog = new AlertDialog.Builder(activity).setTitle(title).setView(content)
                .setPositiveButton(android.R.string.ok, null).create();
        dialog.show();
        return dialog;
    }
}
