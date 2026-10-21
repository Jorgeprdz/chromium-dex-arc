// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;
import android.app.Activity;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.List;

/** A native Archium home surface; the host attaches it only to its native NTP container. */
public final class ArcMobileHomeView extends ScrollView {
    public ArcMobileHomeView(Activity activity,String brand,String space,String search,
            String favoritesLabel,String recentLabel,String settings,int surface,int foreground,int accent,
            List<ArcMobileControls.Action> favorites,List<ArcMobileControls.Action> recent,
            Runnable focusSearch,Runnable spaces,Runnable customize) {
        super(activity);
        setTag("archium-mobile-home");setFillViewport(true);setBackgroundColor(surface);
        LinearLayout content=new LinearLayout(activity);content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(24),dp(32),dp(24),dp(24));addView(content);
        ImageView logo=new ImageView(activity);
        logo.setImageDrawable(activity.getApplicationInfo().loadIcon(activity.getPackageManager()));
        logo.setScaleType(ImageView.ScaleType.FIT_CENTER);logo.setContentDescription(brand);
        LinearLayout.LayoutParams icon=new LinearLayout.LayoutParams(dp(56),dp(56));icon.bottomMargin=dp(16);content.addView(logo,icon);
        TextView title=new TextView(activity);title.setText(brand);title.setTextSize(28);title.setTextColor(foreground);
        title.setAccessibilityHeading(true);content.addView(title);
        addAction(content,new ArcMobileControls.Action(space,spaces),foreground,accent);
        addAction(content,new ArcMobileControls.Action(search,focusSearch),foreground,accent);
        addSection(content,favoritesLabel,favorites,foreground,accent);
        addSection(content,recentLabel,recent,foreground,accent);
        addAction(content,new ArcMobileControls.Action(settings,customize),foreground,surface);
    }
    private int dp(int value){return Math.round(value*getResources().getDisplayMetrics().density);}
    private void addSection(LinearLayout content,String label,List<ArcMobileControls.Action> actions,int foreground,int accent) {
        if(actions.isEmpty())return;
        TextView heading=new TextView(getContext());heading.setText(label);heading.setTextColor(foreground);
        heading.setTextSize(16);heading.setAccessibilityHeading(true);heading.setPadding(0,dp(24),0,dp(8));content.addView(heading);
        for(ArcMobileControls.Action action:actions)addAction(content,action,foreground,accent);
    }
    private void addAction(LinearLayout content,ArcMobileControls.Action action,int foreground,int surface) {
        int textColor=ArcMobileControls.contrast(surface);
        Button button=new Button(getContext());button.setAllCaps(false);button.setText(action.label);
        button.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);button.setTextColor(textColor);
        button.setPadding(dp(16),0,dp(16),0);button.setMaxLines(2);
        GradientDrawable background=new GradientDrawable();background.setCornerRadius(dp(16));background.setColor(surface);
        button.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf((textColor&0xffffff)|0x24000000),background,null));
        button.setOnClickListener(view->action.run.run());
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,dp(56));params.topMargin=dp(8);content.addView(button,params);
    }
}
