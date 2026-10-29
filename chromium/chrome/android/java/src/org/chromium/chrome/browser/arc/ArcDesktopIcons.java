// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.drawable.Drawable;

/** Small shared vector glyphs. Geometry is in a 24-unit optical box, independent of density. */
public final class ArcDesktopIcons extends Drawable {
    public enum Kind { PIN, FAVORITE, FAVORITE_FILLED, CAMERA_ORIENTATION, INFO }
    private final Kind mKind;
    private final Paint mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path mPath = new Path();

    public ArcDesktopIcons(Kind kind, int color) {
        mKind = kind; mPaint.setColor(color); mPaint.setStrokeWidth(1.7f);
        mPaint.setStrokeCap(Paint.Cap.ROUND); mPaint.setStrokeJoin(Paint.Join.ROUND);
        if (kind == Kind.PIN) {
            mPath.moveTo(8, 3); mPath.lineTo(16, 3); mPath.lineTo(15, 9);
            mPath.lineTo(18, 13); mPath.lineTo(6, 13); mPath.lineTo(9, 9); mPath.close();
            mPath.moveTo(12, 13); mPath.lineTo(12, 21);
        } else if (kind == Kind.FAVORITE || kind == Kind.FAVORITE_FILLED) {
            for (int i = 0; i < 10; i++) {
                double angle = Math.PI * i / 5 - Math.PI / 2;
                float radius = i % 2 == 0 ? 9 : 4.2f;
                float x = 12 + (float) Math.cos(angle) * radius;
                float y = 12 + (float) Math.sin(angle) * radius;
                if (i == 0) mPath.moveTo(x, y); else mPath.lineTo(x, y);
            }
            mPath.close();
        } else if (kind == Kind.CAMERA_ORIENTATION) {
            mPath.addRoundRect(4, 8, 16, 18, 2, 2, Path.Direction.CW);
            mPath.moveTo(16, 11); mPath.lineTo(21, 8); mPath.lineTo(21, 18); mPath.lineTo(16, 15);
            mPath.moveTo(5, 5); mPath.cubicTo(8, 1, 14, 1, 17, 5);
            mPath.moveTo(17, 2); mPath.lineTo(17, 5); mPath.lineTo(14, 5);
        } else {
            mPath.addCircle(12, 12, 9, Path.Direction.CW);
            mPath.moveTo(12, 11); mPath.lineTo(12, 17);
            mPath.moveTo(12, 7); mPath.lineTo(12, 7.1f);
        }
    }

    @Override public void draw(Canvas canvas) {
        var bounds = getBounds(); if (bounds.isEmpty()) return;
        int saved = canvas.save();
        float scale = Math.min(bounds.width(), bounds.height()) / 24f;
        canvas.translate(bounds.exactCenterX() - 12 * scale, bounds.exactCenterY() - 12 * scale);
        canvas.scale(scale, scale);
        mPaint.setStyle(mKind == Kind.FAVORITE_FILLED ? Paint.Style.FILL : Paint.Style.STROKE);
        canvas.drawPath(mPath, mPaint); canvas.restoreToCount(saved);
    }
    @Override public int getIntrinsicWidth() { return 24; }
    @Override public int getIntrinsicHeight() { return 24; }
    @Override public void setAlpha(int alpha) { mPaint.setAlpha(alpha); invalidateSelf(); }
    @Override public void setColorFilter(ColorFilter filter) { mPaint.setColorFilter(filter); invalidateSelf(); }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
}
