// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.view.View;

/** Noninteractive trim; pane geometry reserves the border instead of covering page edges. */
public final class ArcSplitFrameView extends View {
    private final Paint mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path mTrim = new Path();
    private final Rect mViewport = new Rect(), mActive = new Rect();
    private Rect[] mPanes = {new Rect(), new Rect()};
    private int mSurface;
    public ArcSplitFrameView(Context context) {
        super(context);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
    }
    public void setAppearance(int surface) { mSurface = surface; invalidate(); }
    public void setGeometry(Rect viewport, float ratio, boolean leftActive) {
        mViewport.set(viewport);
        mPanes = ArcSplitGeometry.panes(viewport, ratio, dp(4), dp(8));
        mActive.set(mPanes[leftActive ? 0 : 1]);
        invalidate();
    }
    @Override protected void onDraw(Canvas canvas) {
        if (mViewport.isEmpty()) return;
        mTrim.reset();
        mTrim.setFillType(Path.FillType.EVEN_ODD);
        mTrim.addRect(new RectF(mViewport), Path.Direction.CW);
        for (Rect pane : mPanes)
            mTrim.addRoundRect(new RectF(pane), dp(10), dp(10), Path.Direction.CW);
        mPaint.setStyle(Paint.Style.FILL); mPaint.setColor(mSurface);
        canvas.drawPath(mTrim, mPaint);
        // Low contrast outline follows the active page without recoloring its content.
        mPaint.setStyle(Paint.Style.STROKE); mPaint.setStrokeWidth(dp(1));
        double luminance = .2126 * android.graphics.Color.red(mSurface)
                + .7152 * android.graphics.Color.green(mSurface) + .0722 * android.graphics.Color.blue(mSurface);
        mPaint.setColor(luminance > 140 ? 0x26000000 : 0x40ffffff);
        RectF outline = new RectF(mActive); outline.inset(-dp(1) / 2f, -dp(1) / 2f);
        canvas.drawRoundRect(outline, dp(10), dp(10), mPaint);
    }
    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }
    int surfaceForTesting() { return mSurface; }
    Rect activeBoundsForTesting() { return new Rect(mActive); }
}
