// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import java.util.function.IntConsumer;
import org.chromium.chrome.R;

/** Window-local draft. Apply saves; Cancel, Back and destruction restore the saved finish. */
public final class ArcDesktopMaterialDialog {
    private final AlertDialog mDialog;
    private final SeekBar mSlider;
    private int mDraft;
    public ArcDesktopMaterialDialog(Activity activity, SharedPreferences prefs, int surface,
            IntConsumer preview) {
        mDraft = ArcDesktopMaterial.savedIntensity(prefs);
        int inset = Math.round(20 * activity.getResources().getDisplayMetrics().density);
        LinearLayout content = new LinearLayout(activity); content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(inset, inset / 2, inset, inset);
        ArcDesktopMaterial sample = new ArcDesktopMaterial(); sample.setAppearance(surface, mDraft);
        TextView sampleLabel = new TextView(activity); sampleLabel.setText(R.string.arc_frame_color_preview);
        sampleLabel.setGravity(Gravity.CENTER); sampleLabel.setTextColor(ArcDesktopMaterial.foreground(surface));
        sampleLabel.setBackground(sample); content.addView(sampleLabel, new LinearLayout.LayoutParams(-1, inset * 4));
        TextView value = new TextView(activity); value.setGravity(Gravity.CENTER); value.setText(mDraft + "%");
        content.addView(value);
        TextView help = new TextView(activity); help.setText(R.string.arc_desktop_material_description);
        content.addView(help);
        mSlider = new SeekBar(activity); mSlider.setId(android.R.id.progress); mSlider.setMax(100);
        mSlider.setContentDescription(activity.getString(R.string.arc_desktop_material));
        mSlider.setProgress(mDraft); content.addView(mSlider, new LinearLayout.LayoutParams(-1, inset * 3));
        mSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar bar, int progress, boolean fromUser) {
                mDraft = progress; value.setText(progress + "%"); sample.setAppearance(surface, progress);
                preview.accept(progress);
            }
            @Override public void onStartTrackingTouch(SeekBar bar) {}
            @Override public void onStopTrackingTouch(SeekBar bar) {}
        });
        mDialog = new AlertDialog.Builder(activity).setTitle(R.string.arc_desktop_material)
                .setView(content).setPositiveButton(android.R.string.ok, (dialog, which) ->
                        prefs.edit().putInt(ArcDesktopMaterial.INTENSITY_KEY, mDraft).apply())
                .setNegativeButton(android.R.string.cancel, null)
                .setNeutralButton(R.string.arc_reset_color, null).create();
        mDialog.setOnShowListener(dialog -> mDialog.getButton(AlertDialog.BUTTON_NEUTRAL)
                .setOnClickListener(view -> mSlider.setProgress(ArcDesktopMaterial.DEFAULT_INTENSITY)));
        mDialog.setOnDismissListener(dialog -> preview.accept(-1));
    }
    public AlertDialog show() { mDialog.show(); return mDialog; }
}
