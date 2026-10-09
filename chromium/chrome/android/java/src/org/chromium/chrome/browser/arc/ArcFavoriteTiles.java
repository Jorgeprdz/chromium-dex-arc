// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.content.Context;
import android.view.View;
import android.widget.LinearLayout;

/** Three logical columns of real favorite controls, sharing LinearLayout's margin parameters. */
public final class ArcFavoriteTiles extends LinearLayout {
    public ArcFavoriteTiles(Context context) {
        super(context);
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        int height = getPaddingTop() + getPaddingBottom();
        int rowHeight = 0;
        int column = 0;
        for (int i = 0; i < getChildCount(); i++) {
            View child = getChildAt(i);
            if (child.getVisibility() == View.GONE) continue;
            measureChildWithMargins(child, widthMeasureSpec, 0,
                    MeasureSpec.makeMeasureSpec(0, MeasureSpec.UNSPECIFIED), 0);
            LayoutParams params = (LayoutParams) child.getLayoutParams();
            rowHeight = Math.max(rowHeight,
                    child.getMeasuredHeight() + params.topMargin + params.bottomMargin);
            if (++column == 3) {
                height += rowHeight;
                rowHeight = 0;
                column = 0;
            }
        }
        height += rowHeight;
        setMeasuredDimension(resolveSizeAndState(Math.max(getSuggestedMinimumWidth(),
                        MeasureSpec.getSize(widthMeasureSpec)), widthMeasureSpec, 0),
                resolveSizeAndState(Math.max(getSuggestedMinimumHeight(), height),
                        heightMeasureSpec, 0));
    }

    @Override
    protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
        boolean rtl = getLayoutDirection() == View.LAYOUT_DIRECTION_RTL;
        int rowStart = rtl ? right - left - getPaddingRight() : getPaddingLeft();
        int x = rowStart;
        int y = getPaddingTop();
        int rowHeight = 0;
        int column = 0;
        for (int i = 0; i < getChildCount(); i++) {
            View child = getChildAt(i);
            if (child.getVisibility() == View.GONE) continue;
            LayoutParams params = (LayoutParams) child.getLayoutParams();
            int width = child.getMeasuredWidth();
            int height = child.getMeasuredHeight();
            int childLeft = rtl ? x - params.getMarginStart() - width
                    : x + params.getMarginStart();
            child.layout(childLeft, y + params.topMargin,
                    childLeft + width, y + params.topMargin + height);
            x += (rtl ? -1 : 1) * (params.getMarginStart() + width + params.getMarginEnd());
            rowHeight = Math.max(rowHeight, height + params.topMargin + params.bottomMargin);
            if (++column == 3) {
                x = rowStart;
                y += rowHeight;
                rowHeight = 0;
                column = 0;
            }
        }
    }
}
