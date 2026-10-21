// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.app.Activity;
import android.app.Dialog;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.content.res.ColorStateList;
import android.view.Gravity;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.List;

/** Native mobile chrome only. The host owns Chromium actions, tabs, snapshots and profile state. */
public final class ArcMobileControls {
    public interface Host {
        boolean visible();
        int tabCount();
        int surface();
        int foreground();
        int accent();
        String pageLabel();
        void home();
        void newTab();
        void tabs();
        void spaces();
        List<Action> actions();
        default View nativeHomeView() { return null; }
        default View buildHome() { return null; }
    }
    public static final class Action {
        public final String label;
        public final Runnable run;
        public Action(String label, Runnable run) { this.label = label; this.run = run; }
    }
    private final Activity mActivity;
    private final Host mHost;
    private final FrameLayout mRoot;
    private final View mBrowser;
    private int mReservedBottom;
    private final LinearLayout mBar;
    private final Button mTabs;
    private final String mTabsLabel;
    private final android.view.ViewTreeObserver.OnGlobalLayoutListener mLayout = this::refresh;
    private Dialog mSheet;
    private View mNativeHome, mHome;
    private FrameLayout mHomeParent;
    private final java.util.Map<View,int[]> mHomeChildren=new java.util.IdentityHashMap<>();
    private boolean mUpdatingHome;
    private TextView mAddress;
    private int mAddressGravity, mAddressAlignment;
    private final android.view.ViewTreeObserver.OnGlobalFocusChangeListener mFocus = (oldFocus,newFocus) -> refreshAddress();
    private boolean mDestroyed;
    private int mInset;
    private int mSurface, mForeground, mAccent;
    private boolean mPaletteSet;

    public ArcMobileControls(Activity activity, FrameLayout root, View browser, Host host,
            String home, String add, String tabs, String menu) {
        mActivity = activity; mRoot = root; mBrowser = browser; mHost = host; mTabsLabel=tabs;
        mBar = new LinearLayout(activity);
        mBar.setGravity(Gravity.CENTER); mBar.setElevation(dp(3));
        mBar.setTag("archium-mobile-navigation");
        addButton("⌂", home, host::home, false);
        addButton("+", add, host::newTab, true);
        mTabs = addButton("0", tabs, host::tabs, false);
        mTabs.setOnLongClickListener(view -> { if(mDestroyed)return false;host.spaces();return true; });
        addButton("⋮", menu, this::showMenu, false);
        FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(-1, dp(64), Gravity.BOTTOM);
        root.addView(mBar, params);
        mBar.setOnApplyWindowInsetsListener((view, insets) -> {
            int bottom = android.os.Build.VERSION.SDK_INT >= 30
                    ? insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout()).bottom
                    : insets.getSystemWindowInsetBottom();
            if (bottom != mInset) {
                mInset = bottom;
                mBar.setPadding(0,0,0,bottom);
                ViewGroup.LayoutParams size = mBar.getLayoutParams(); size.height = dp(64)+bottom;
                mBar.setLayoutParams(size);
            }
            refresh(); return insets;
        });
        root.getViewTreeObserver().addOnGlobalLayoutListener(mLayout);
        mBar.requestApplyInsets(); refresh();
    }
    private int dp(int value) { return Math.round(value*mActivity.getResources().getDisplayMetrics().density); }
    private Button addButton(String text, String label, Runnable action, boolean primary) {
        Button button = new Button(mActivity);
        button.setText(text); button.setTextSize(primary ? 30 : 22);
        button.setContentDescription(label); button.setTooltipText(label);button.setSingleLine(true);
        button.setMinWidth(0); button.setMinimumWidth(0); button.setPadding(0,0,0,0);
        button.setTag(primary ? "archium-mobile-new-tab" : label);
        button.setOnClickListener(view -> {
            if (mDestroyed) return;
            view.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);
            action.run(); refresh();
        });
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0,dp(48),1);
        params.setMargins(dp(4),dp(8),dp(4),dp(8));
        mBar.addView(button, params);
        return button;
    }
    public void bindAddressBar(TextView address) {
        if (mAddress != null) return;
        mAddress=address;mAddressGravity=address.getGravity();mAddressAlignment=address.getTextAlignment();
        mRoot.getViewTreeObserver().addOnGlobalFocusChangeListener(mFocus);
        refreshAddress();
    }
    private void refreshAddress() {
        if(mDestroyed || mAddress==null)return;
        if(!mHost.visible()) {
            mAddress.setGravity(mAddressGravity);mAddress.setTextAlignment(mAddressAlignment);return;
        }
        // Observe focus without replacing Chromium's touch/focus listeners or moving its editor.
        mAddress.setTextAlignment(View.TEXT_ALIGNMENT_GRAVITY);
        mAddress.setGravity((mAddress.hasFocus()?Gravity.START:Gravity.CENTER_HORIZONTAL)|Gravity.CENTER_VERTICAL);
    }
    public void refresh() {
        if (mDestroyed) return;
        refreshAddress();refreshHome();
        WindowInsets insets = mRoot.getRootWindowInsets();
        boolean ime = insets != null && android.os.Build.VERSION.SDK_INT >= 30
                && insets.isVisible(WindowInsets.Type.ime());
        boolean visible = mHost.visible() && !ime;
        mBar.setVisibility(visible ? View.VISIBLE : View.GONE);
        if (!visible && mSheet != null) mSheet.dismiss();
        if (mBrowser.getLayoutParams() instanceof ViewGroup.MarginLayoutParams params) {
            int reservation=visible?dp(64)+mInset:0;
            int margin = params.bottomMargin-mReservedBottom+reservation;
            mReservedBottom=reservation;
            if (params.bottomMargin != margin) { params.bottomMargin=margin; mBrowser.setLayoutParams(params); }
        }
        String count = Integer.toString(mHost.tabCount());
        if (!count.contentEquals(mTabs.getText())) {
            mTabs.setText(count);mTabs.setContentDescription(mTabsLabel+", "+count);
        }
        int surface = mHost.surface(), foreground = mHost.foreground(), accent = mHost.accent();
        if (mPaletteSet && mSurface == surface && mForeground == foreground && mAccent == accent) return;
        mPaletteSet=true;mSurface=surface;mForeground=foreground;mAccent=accent;
        mBar.setBackgroundColor(surface);
        for (int i=0;i<mBar.getChildCount();i++) {
            Button button=(Button)mBar.getChildAt(i);
            boolean primary=i==1;
            GradientDrawable shape=new GradientDrawable(); shape.setCornerRadius(dp(primary?24:12));
            shape.setColor(primary?accent:Color.TRANSPARENT);
            shape.setStroke(dp(1),foreground);
            button.setTextColor(primary?contrast(accent):foreground);
            button.setBackground(new RippleDrawable(ColorStateList.valueOf((foreground&0xffffff)|0x24000000),shape,null));
        }
    }
    public void invalidateHome() { clearHome();refreshHome(); }
    private void refreshHome() {
        if(mUpdatingHome)return;mUpdatingHome=true;
        try {
            View owner=mHost.visible()?mHost.nativeHomeView():null;
            if(owner!=mNativeHome || (mHome!=null && mHome.getParent()!=mHomeParent)) {
                clearHome();
                // Insert into the actual native NTP, below dialogs and inside native thumbnails.
                // Unsupported native-page containers retain their original Chromium surface.
                if(!(owner instanceof FrameLayout parent))return;
                View home=mHost.buildHome();
                if(home==null || mHost.nativeHomeView()!=owner)return;
                mNativeHome=owner;mHome=home;mHomeParent=parent;
                parent.addView(home,new FrameLayout.LayoutParams(-1,-1));
            }
            if(mHomeParent==null)return;
            for(int i=0;i<mHomeParent.getChildCount();i++) {
                View child=mHomeParent.getChildAt(i);
                if(child==mHome || mHomeChildren.containsKey(child))continue;
                mHomeChildren.put(child,new int[]{child.getVisibility(),child.getImportantForAccessibility()});
                child.setVisibility(View.INVISIBLE);
                child.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
            }
        } finally {mUpdatingHome=false;}
    }
    private void clearHome() {
        if(mHome!=null && mHomeParent!=null)mHomeParent.removeView(mHome);
        for(var item:mHomeChildren.entrySet()) {
            View child=item.getKey();int[] state=item.getValue();
            // Preserve any later visibility/accessibility decision made by Chromium itself.
            if(child.getVisibility()==View.INVISIBLE)child.setVisibility(state[0]);
            if(child.getImportantForAccessibility()==View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS)
                child.setImportantForAccessibility(state[1]);
        }
        mHomeChildren.clear();mHome=null;mNativeHome=null;mHomeParent=null;
    }
    static int contrast(int color) {
        // Used for the solid + surface; the host supplies its established page/theme palette.
        double luminance=0;
        for (int i=0;i<3;i++) {
            double c=((color>>(16-8*i))&255)/255.0;
            c=c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4);
            luminance+=c*(i==0?.2126:i==1?.7152:.0722);
        }
        return luminance>.179?Color.BLACK:Color.WHITE;
    }
    public void showMenu() {
        if (mDestroyed || !mHost.visible()) return;
        if (mSheet != null) mSheet.dismiss();
        Dialog dialog=new Dialog(mActivity); mSheet=dialog;
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout content=new LinearLayout(mActivity);content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(20),dp(12),dp(20),dp(20));
        GradientDrawable background=new GradientDrawable();background.setColor(mHost.surface());
        background.setCornerRadii(new float[]{dp(24),dp(24),dp(24),dp(24),0,0,0,0});
        content.setBackground(background);
        TextView heading=new TextView(mActivity);heading.setText(mHost.pageLabel());
        heading.setTextColor(mHost.foreground());heading.setTextSize(18);heading.setAccessibilityHeading(true);
        heading.setPadding(0,dp(12),0,dp(16));content.addView(heading);
        final float[] down={0};
        heading.setOnTouchListener((view,event)-> {
            if(event.getActionMasked()==MotionEvent.ACTION_DOWN){down[0]=event.getRawY();return true;}
            if(event.getActionMasked()==MotionEvent.ACTION_UP){
                if(event.getRawY()-down[0]>dp(48))dialog.dismiss();else view.performClick();
                return true;
            }
            return event.getActionMasked()==MotionEvent.ACTION_MOVE;
        });
        for(Action action:mHost.actions()) {
            Button button=new Button(mActivity);button.setText(action.label);button.setAllCaps(false);
            button.setTextColor(mHost.foreground());button.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);
            button.setOnClickListener(view->{dialog.dismiss();if(!mDestroyed)action.run.run();});
            content.addView(button,new LinearLayout.LayoutParams(-1,dp(52)));
        }
        ScrollView scroll=new ScrollView(mActivity) {
            @Override protected void onMeasure(int widthSpec,int heightSpec) {
                int cap=Math.min(dp(600),Math.max(dp(200),mRoot.getHeight()*3/4));
                if(MeasureSpec.getMode(heightSpec)!=MeasureSpec.UNSPECIFIED)cap=Math.min(cap,MeasureSpec.getSize(heightSpec));
                super.onMeasure(widthSpec,MeasureSpec.makeMeasureSpec(cap,MeasureSpec.AT_MOST));
            }
        };
        scroll.setFillViewport(false);scroll.addView(content);
        scroll.setOnApplyWindowInsetsListener((view,insets)-> {
            if(android.os.Build.VERSION.SDK_INT >= 30) {
                var safe=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
                view.setPadding(safe.left,0,safe.right,safe.bottom);
            } else view.setPadding(0,0,0,insets.getSystemWindowInsetBottom());
            return insets;
        });
        dialog.setContentView(scroll);dialog.setCanceledOnTouchOutside(true);
        Window window=dialog.getWindow();
        if(window!=null) {
            window.setBackgroundDrawableResource(android.R.color.transparent);
            window.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            window.setDimAmount(.22f);window.setGravity(Gravity.BOTTOM);
            window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        }
        dialog.show();
        if(window!=null)window.setLayout(-1,ViewGroup.LayoutParams.WRAP_CONTENT);
    }
    public void destroy() {
        if(mDestroyed)return; mDestroyed=true;clearHome();
        if(mSheet!=null)mSheet.dismiss();mRoot.getViewTreeObserver().removeOnGlobalLayoutListener(mLayout);
        mBar.setOnApplyWindowInsetsListener(null);mRoot.removeView(mBar);
        mRoot.getViewTreeObserver().removeOnGlobalFocusChangeListener(mFocus);
        if(mAddress!=null){mAddress.setGravity(mAddressGravity);mAddress.setTextAlignment(mAddressAlignment);mAddress=null;}
        if(mBrowser.getLayoutParams() instanceof ViewGroup.MarginLayoutParams params) {
            params.bottomMargin-=mReservedBottom;mReservedBottom=0;mBrowser.setLayoutParams(params);
        }
    }
}
