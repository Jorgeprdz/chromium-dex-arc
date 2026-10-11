// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.drawable.GradientDrawable;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;

import org.chromium.chrome.R;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;

import java.util.function.Consumer;

/** A color edit is a draft until Apply. Dismissal always clears transient preview. */
public final class ArcColorPicker {
    private final Activity mActivity;
    private final SharedPreferences mPreferences;
    private final Consumer<Integer> mPreview;
    private final ArcColorDraft mDraft;
    private final AlertDialog mDialog;
    private final EditText mHex;
    private final View[] mSwatches = new View[ArcColorDraft.presetCount()];
    private final SeekBar[] mChannels = new SeekBar[3];
    private final TextView[] mChannelLabels = new TextView[3];
    private final String[] mChannelNames;
    private boolean mUpdating;

    public ArcColorPicker(Activity activity, SharedPreferences preferences, String[] presetNames,
            String[] channelNames, Consumer<Integer> preview) {
        if (presetNames.length != mSwatches.length || channelNames.length != 3) {
            throw new IllegalArgumentException("Incomplete color labels");
        }
        mActivity = activity;
        mPreferences = preferences;
        mPreview = preview;
        mChannelNames = channelNames.clone();
        mDraft = new ArcColorDraft(preferences.getInt(ArcDesktopAppearance.COLOR_KEY,
                ArcDesktopAppearance.DEFAULT_COLOR), ArcDesktopAppearance.DEFAULT_COLOR);
        LinearLayout content = new LinearLayout(activity);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(20), dp(8), dp(20), dp(12));
        TextView title = new TextView(activity);
        title.setText(R.string.arc_frame_color_presets);
        content.addView(title);
        GridLayout palette = new GridLayout(activity);
        palette.setColumnCount(4);
        for (int i = 0; i < mSwatches.length; i++) {
            final int index = i;
            View swatch = new View(activity);
            swatch.setTag("arc-color-preset:" + i);
            swatch.setFocusable(true);
            swatch.setClickable(true);
            swatch.setContentDescription(presetNames[i]);
            swatch.setOnClickListener(v -> {
                int color = ArcColorDraft.presetAt(index);
                mDraft.setRgb((color >> 16) & 255, (color >> 8) & 255, color & 255);
                refresh();
            });
            GridLayout.LayoutParams cell = new GridLayout.LayoutParams();
            cell.width = dp(48);
            cell.height = dp(48);
            cell.setMargins(dp(4), dp(4), dp(4), dp(4));
            palette.addView(swatch, cell);
            mSwatches[i] = swatch;
        }
        content.addView(palette);
        mHex = new EditText(activity);
        mHex.setTag("arc-color-hex");
        mHex.setSingleLine(true);
        mHex.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        mHex.setSelectAllOnFocus(true);
        mHex.setContentDescription(activity.getString(R.string.arc_frame_color_custom));
        content.addView(mHex);
        TextView rgbTitle = new TextView(activity);
        rgbTitle.setText(R.string.arc_frame_color_rgb);
        content.addView(rgbTitle);
        for (int i = 0; i < 3; i++) {
            mChannelLabels[i] = new TextView(activity);
            content.addView(mChannelLabels[i]);
            SeekBar channel = new SeekBar(activity);
            channel.setMax(255);
            channel.setTag("arc-color-rgb:" + i);
            channel.setContentDescription(channelNames[i]);
            mChannels[i] = channel;
            content.addView(channel);
        }
        ScrollView scroll = new ScrollView(activity);
        scroll.addView(content);
        mDialog = new AlertDialog.Builder(activity).setTitle(R.string.arc_frame_color)
                .setView(scroll).setPositiveButton(android.R.string.ok, null)
                .setNegativeButton(android.R.string.cancel, null)
                .setNeutralButton(R.string.arc_reset_color, null).create();
        mDialog.setOnDismissListener(dialog -> mPreview.accept(null));
        mDialog.setOnShowListener(dialog -> {
            mDialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> apply());
            mDialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v -> {
                mDraft.reset();
                refresh();
            });
            refresh();
        });
        mHex.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
            @Override public void afterTextChanged(Editable text) {
                if (mUpdating) return;
                if (mDraft.setHex(text.toString())) {
                    refresh();
                } else {
                    mHex.setError(activity.getString(R.string.arc_color_format));
                    refreshSelection();
                    mDialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                }
            }
        });
        for (SeekBar channel : mChannels) {
            channel.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                @Override public void onProgressChanged(SeekBar bar, int progress, boolean fromUser) {
                    if (mUpdating || !fromUser) return;
                    mDraft.setRgb(mChannels[0].getProgress(), mChannels[1].getProgress(),
                            mChannels[2].getProgress());
                    refresh();
                }
                @Override public void onStartTrackingTouch(SeekBar bar) {}
                @Override public void onStopTrackingTouch(SeekBar bar) {}
            });
        }
    }

    public AlertDialog show() {
        mDialog.show();
        return mDialog;
    }

    private int dp(int size) {
        return Math.round(size * mActivity.getResources().getDisplayMetrics().density);
    }

    private void refreshSelection() {
        int selected = mDraft.selectedPreset();
        for (int i = 0; i < mSwatches.length; i++) {
            int color = ArcColorDraft.presetAt(i);
            GradientDrawable background = new GradientDrawable();
            background.setColor(color);
            background.setCornerRadius(dp(12));
            background.setStroke(dp(i == selected ? 3 : 1),
                    i == selected ? ArcDesktopPolicy.foreground(color) : 0x44000000);
            mSwatches[i].setBackground(background);
            mSwatches[i].setSelected(i == selected);
        }
    }

    private void refresh() {
        mUpdating = true;
        try {
            mHex.setError(null);
            mHex.setText(mDraft.hex());
            for (int i = 0; i < 3; i++) {
                int channel = (mDraft.color() >> (16 - i * 8)) & 255;
                mChannels[i].setProgress(channel);
                mChannelLabels[i].setText(mChannelNames[i] + ": " + channel);
            }
            refreshSelection();
            mDialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(mDraft.isValid());
        } finally {
            mUpdating = false;
        }
        mPreview.accept(mDraft.color());
    }

    private void apply() {
        if (!mDraft.isValid()) return;
        SharedPreferences.Editor edit = mPreferences.edit();
        if (mDraft.shouldClearPreference()) {
            edit.remove(ArcDesktopAppearance.COLOR_KEY);
        } else {
            edit.putInt(ArcDesktopAppearance.COLOR_KEY, mDraft.color());
        }
        edit.apply();
        mDialog.dismiss();
    }
}
