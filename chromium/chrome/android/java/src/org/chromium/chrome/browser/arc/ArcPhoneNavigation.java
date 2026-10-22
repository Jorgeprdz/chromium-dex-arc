// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.animation.ValueAnimator;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.view.Gravity;
import android.view.HapticFeedbackConstants;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Switch;

import org.chromium.base.Callback;
import org.chromium.build.annotations.Nullable;
import org.chromium.chrome.R;
import org.chromium.chrome.browser.browser_controls.BottomControlsStacker.LayerScrollBehavior;
import org.chromium.chrome.browser.toolbar.bottom.BottomControlsContentDelegate;
import org.chromium.chrome.browser.ui.bottombar.BottomBar;
import org.chromium.chrome.browser.ui.bottombar.BottomBarHostManager;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.toolbar.bottom.BottomControlsCoordinator.BottomControlsVisibilityController;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetContent;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetController;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetType;

/** One replacement content delegate inside Chromium's existing bottom-controls slot. */
public final class ArcPhoneNavigation implements BottomControlsContentDelegate {
    public static final int HOME=0, NEW_TAB=1, TABS=2, MENU=3, PIN=4, FIND=5,
            SHARE=6, FAVORITE=7, DESKTOP_SITE=8, SITE_INFO=9, DOWNLOADS=10, MORE=11;
    public interface Host {
        @Nullable Object pageToken();
        String domain();
        @Nullable Bitmap favicon();
        int tabCount();
        boolean webPage();
        boolean pinned();
        boolean desktopSite();
        int zoomPercent();
        int surface();
        void action(int action);
        void zoom(int direction);
    }
    public static final int HEIGHT_DP=60;
    private final FrameLayout mSlot;
    private final Context mContext;
    private final BottomSheetController mController;
    private final LinearLayout mBar;
    private final int mHeight;
    private boolean mTabbedHost=true;
    private final View[] mButtons=new View[4];
    private Host mHost;
    private BottomControlsVisibilityController mVisibility;
    private Callback<Object> mCapture;
    private MenuSheet mSheet;
    private boolean mDestroyed;
    private int mSurface, mForeground;
    private String mCount="";

    public ArcPhoneNavigation(FrameLayout slot, BottomSheetController controller) {
        this(slot,controller,Math.round(HEIGHT_DP*slot.getResources().getDisplayMetrics().density));
    }
    public ArcPhoneNavigation(FrameLayout slot, BottomSheetController controller,int height) {
        mHeight=height;
        mSlot=slot;mContext=slot.getContext();mController=controller;
        mBar=new LinearLayout(mContext);mBar.setGravity(Gravity.CENTER);
        mBar.setTag("arc-phone-navigation");
        int[] labels={R.string.arc_phone_home,R.string.arc_phone_new,R.string.arc_phone_tabs,R.string.arc_phone_menu};
        String[] tags={"home","new","tabs","menu"};
        for(int i=0;i<4;i++) {
            final int action=i;
            LinearLayout button=new LinearLayout(mContext);button.setOrientation(LinearLayout.VERTICAL);
            button.setGravity(Gravity.CENTER);button.setPadding(0,dp(3),0,dp(3));
            ImageView icon=new ImageView(mContext);icon.setImageDrawable(new Icon(i,Color.BLACK,""));
            FrameLayout pill=new FrameLayout(mContext);pill.addView(icon,new FrameLayout.LayoutParams(Math.min(dp(26),mHeight-dp(26)),Math.min(dp(26),mHeight-dp(26)),Gravity.CENTER));
            button.addView(pill,new LinearLayout.LayoutParams(dp(i==NEW_TAB?60:44),Math.max(dp(24),mHeight-dp(24))));
            TextView text=text(mContext.getString(labels[i]),12);text.setGravity(Gravity.CENTER);
            button.addView(text,new LinearLayout.LayoutParams(-1,dp(18)));
            accessible(button,mContext.getString(labels[i]),"arc-phone-"+tags[i]);
            button.setOnClickListener(v->{if(mDestroyed||mHost==null)return;haptic(v);if(action==MENU)showMenu();else mHost.action(action);});
            mBar.addView(button,new LinearLayout.LayoutParams(0,mHeight,1));mButtons[i]=button;
        }
        // Native BottomControlsCoordinator owns size, insets, fullscreen, keyboard and raster capture.
        slot.addView(mBar,new FrameLayout.LayoutParams(-1,mHeight));
        refresh();
    }
    /** Let Chromium's tab switcher borrow the same view, never a duplicate bar. */
    public BottomBar getBottomBar() {
        return new BottomBar() {
            public View getView(){return mBar;}
            public int getBackgroundColor(){return mSurface;}
            public void setParent(int host){mTabbedHost=host==BottomBarHostManager.Host.TABBED;dismissMenu();refresh();}
            public boolean maybeShowPromoDialog(Profile profile){return false;}
            public void onStartupPromoFlowFinished(boolean promoShown){}
        };
    }
    public void attachBottomBarView(View view) {
        if(mDestroyed)return;
        mSlot.addView(view,new FrameLayout.LayoutParams(-1,mHeight));refresh();
    }
    public void bind(Host host){if(mDestroyed)return;mHost=host;refresh();}
    public void refresh() {
        if(mDestroyed)return;
        if(mSheet!=null && (mHost==null || mSheet.mToken!=mHost.pageToken()))dismissMenu();
        mSurface=mHost==null?Color.WHITE:mHost.surface();
        mForeground=Color.luminance(mSurface)>.45?0xff202124:0xfff1f3f4;
        mBar.setBackgroundColor(mSurface);
        String count=mHost==null?"0":Integer.toString(Math.max(0,mHost.tabCount()));
        for(int i=0;i<4;i++) {
            LinearLayout button=(LinearLayout)mButtons[i];button.setEnabled(mHost!=null);
            button.setBackground(ripple(Color.TRANSPARENT,12));
            FrameLayout pill=(FrameLayout)button.getChildAt(0);
            pill.setBackground(i==NEW_TAB?shape(Color.luminance(mSurface)>.45?Color.WHITE:0xff44464f,24):null);
            ((ImageView)pill.getChildAt(0)).setImageDrawable(new Icon(i,mForeground,i==TABS?count:""));
            ((TextView)button.getChildAt(1)).setTextColor(mForeground);
        }
        mButtons[TABS].setContentDescription(mContext.getString(R.string.arc_phone_tabs)+", "+count);
        boolean countChanged=!mCount.equals(count);mCount=count;
        if(mVisibility!=null)mVisibility.setBottomControlsVisible(mHost!=null && mTabbedHost);
        if(mCapture!=null)mCapture.onResult(countChanged?count:new Object());
    }
    @Override public void initializeWithNative(BottomControlsVisibilityController visibility,Callback<Object> capture){mVisibility=visibility;mCapture=capture;refresh();}
    @Override public int getScrollBehavior(){return LayerScrollBehavior.DEFAULT_SCROLL_OFF;}
    @Override public Integer getBackgroundColor(){return mSurface;}
    private void showMenu() {
        if(mDestroyed||mHost==null||mSheet!=null)return;
        MenuSheet sheet=new MenuSheet(mHost);mSheet=sheet;
        if(!mController.requestShowContent(sheet,ValueAnimator.areAnimatorsEnabled()))sheet.destroy();
    }
    public void dismissMenu(){MenuSheet sheet=mSheet;if(sheet==null)return;mSheet=null;mController.hideContent(sheet,ValueAnimator.areAnimatorsEnabled());sheet.destroy();}
    @Override public void destroy(){if(mDestroyed)return;dismissMenu();mDestroyed=true;mHost=null;mCapture=null;mVisibility=null;if(mBar.getParent() instanceof ViewGroup parent)parent.removeView(mBar);}
    private boolean valid(MenuSheet sheet){return !mDestroyed && !sheet.mClosed && mHost!=null && sheet.mToken==mHost.pageToken();}
    private void act(MenuSheet sheet,int action){if(!valid(sheet))return;Host host=mHost;dismissMenu();host.action(action);refresh();}
    private void haptic(View view){view.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);}
    private int dp(int value){return Math.round(value*mContext.getResources().getDisplayMetrics().density);}
    private TextView text(String value,int sp){TextView t=new TextView(mContext);t.setText(value);t.setTextSize(sp);t.setTextColor(mForeground);return t;}
    private GradientDrawable shape(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
    private Drawable ripple(int background,int radius){return new RippleDrawable(ColorStateList.valueOf((mForeground&0xffffff)|0x1e000000),shape(background,radius),null);}
    private void accessible(View view,String label,String tag){view.setTag(tag);view.setContentDescription(label);view.setTooltipText(label);view.setFocusable(true);view.setClickable(true);view.setMinimumHeight(dp(48));}

    private final class MenuSheet implements BottomSheetContent {
        final Object mToken;
        final ScrollView mScroll;
        final LinearLayout mBody;
        final View mEmptyToolbar;
        boolean mClosed;
        MenuSheet(Host host) {
            mToken=host.pageToken();mScroll=new ScrollView(mContext);mScroll.setFillViewport(false);
            mBody=new LinearLayout(mContext);mBody.setOrientation(LinearLayout.VERTICAL);mBody.setPadding(dp(16),dp(10),dp(16),dp(12));
            GradientDrawable background=shape(mSurface,28);background.setCornerRadii(new float[]{dp(28),dp(28),dp(28),dp(28),0,0,0,0});mBody.setBackground(background);
            mScroll.addView(mBody,new ScrollView.LayoutParams(-1,-2));
            // A non-null, zero-height toolbar prevents the native sheet's omnibox fallback.
            mEmptyToolbar=new View(mContext);mEmptyToolbar.setLayoutParams(new FrameLayout.LayoutParams(-1,0));
            View grip=new View(mContext);grip.setBackground(shape((mForeground&0xffffff)|0x50000000,3));
            LinearLayout.LayoutParams gripSize=new LinearLayout.LayoutParams(dp(32),dp(4));gripSize.gravity=Gravity.CENTER_HORIZONTAL;gripSize.bottomMargin=dp(12);mBody.addView(grip,gripSize);
            LinearLayout header=new LinearLayout(mContext);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(dp(8),dp(4),dp(8),dp(12));
            ImageView favicon=new ImageView(mContext);Bitmap bitmap=host.favicon();
            if(bitmap!=null)favicon.setImageBitmap(bitmap);else favicon.setImageDrawable(new Icon(SITE_INFO,mForeground,""));
            header.addView(favicon,new LinearLayout.LayoutParams(dp(32),dp(32)));
            LinearLayout title=new LinearLayout(mContext);title.setOrientation(LinearLayout.VERTICAL);title.setPadding(dp(16),0,0,0);
            TextView domain=text(host.domain(),20);domain.setTag("arc-phone-domain");title.addView(domain);
            title.addView(text(mContext.getString(R.string.arc_phone_site_info),13));header.addView(title,new LinearLayout.LayoutParams(0,-2,1));
            accessible(header,mContext.getString(R.string.arc_phone_site_info),"arc-phone-site-info");header.setEnabled(host.webPage());header.setOnClickListener(v->act(this,SITE_INFO));mBody.addView(header);
            LinearLayout quick=new LinearLayout(mContext);quick.setGravity(Gravity.CENTER);
            int[] actions={PIN,FIND,SHARE};int[] labels={host.pinned()?R.string.arc_phone_unpin:R.string.arc_phone_pin,R.string.arc_phone_find,R.string.arc_phone_share};String[] tags={"pin","find","share"};
            for(int i=0;i<3;i++) {
                final int action=actions[i];LinearLayout tile=new LinearLayout(mContext);tile.setOrientation(LinearLayout.VERTICAL);tile.setGravity(Gravity.CENTER);
                ImageView icon=new ImageView(mContext);icon.setImageDrawable(new Icon(action,mForeground,""));tile.addView(icon,new LinearLayout.LayoutParams(dp(26),dp(26)));
                TextView label=text(mContext.getString(labels[i]),14);label.setGravity(Gravity.CENTER);tile.addView(label);
                accessible(tile,mContext.getString(labels[i]),"arc-phone-"+tags[i]);tile.setEnabled(host.webPage());tile.setAlpha(host.webPage()?1f:.4f);tile.setBackground(ripple(Color.luminance(mSurface)>.45?Color.WHITE:0xff363840,20));
                tile.setOnClickListener(v->{haptic(v);act(this,action);});
                LinearLayout.LayoutParams size=new LinearLayout.LayoutParams(0,dp(88),1);size.setMargins(dp(3),dp(4),dp(3),dp(12));quick.addView(tile,size);
            }
            mBody.addView(quick);separator();
            row(FAVORITE,R.string.arc_phone_favorite,"favorite",host.webPage(),null);
            LinearLayout zoomRow=new LinearLayout(mContext);zoomRow.setGravity(Gravity.CENTER_VERTICAL);zoomRow.setPadding(dp(12),0,dp(4),0);
            TextView zoom=text("",16);zoom.setText(host.zoomPercent()+"%");zoom.setTag("arc-phone-zoom-value");
            TextView zoomTitle=text(mContext.getString(R.string.arc_phone_zoom),17);zoomRow.addView(zoomTitle,new LinearLayout.LayoutParams(0,dp(64),1));zoomTitle.setGravity(Gravity.CENTER_VERTICAL);zoomRow.addView(zoom);
            for(int direction:new int[]{-1,1}) {
                TextView step=text(direction<0?"−":"+",26);step.setGravity(Gravity.CENTER);step.setBackground(ripple(Color.TRANSPARENT,24));
                accessible(step,mContext.getString(direction<0?R.string.arc_phone_zoom_out:R.string.arc_phone_zoom_in),"arc-phone-zoom-"+(direction<0?"minus":"plus"));step.setEnabled(host.webPage());
                step.setOnClickListener(v->{if(!valid(this))return;haptic(v);mHost.zoom(direction);zoom.setText(mHost.zoomPercent()+"%");});zoomRow.addView(step,new LinearLayout.LayoutParams(dp(48),dp(48)));
            }
            mBody.addView(zoomRow);separator();
            row(DESKTOP_SITE,R.string.arc_phone_desktop,"desktop",host.webPage(),host.desktopSite()?"✓":"○");
            row(SITE_INFO,R.string.arc_phone_site_settings,"site-settings",host.webPage(),"›");
            row(DOWNLOADS,R.string.arc_phone_downloads,"downloads",true,"›");
            row(MORE,R.string.arc_phone_more,"more",true,"›");
        }
        private void row(int action,int label,String tag,boolean enabled,String end) {
            LinearLayout row=new LinearLayout(mContext);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(12),0,dp(12),0);
            ImageView icon=new ImageView(mContext);icon.setImageDrawable(new Icon(action,mForeground,""));row.addView(icon,new LinearLayout.LayoutParams(dp(24),dp(24)));
            TextView title=text(mContext.getString(label),17);title.setPadding(dp(16),dp(12),dp(8),dp(12));row.addView(title,new LinearLayout.LayoutParams(0,-2,1));
            if(action==DESKTOP_SITE) {
                Switch toggle=new Switch(mContext);toggle.setChecked(mHost.desktopSite());
                toggle.setClickable(false);toggle.setFocusable(false);toggle.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);row.addView(toggle);
            } else if(end!=null)row.addView(text(end,22));
            accessible(row,mContext.getString(label),"arc-phone-"+tag);row.setEnabled(enabled);row.setAlpha(enabled?1f:.4f);row.setBackground(ripple(Color.TRANSPARENT,12));
            if(action==DESKTOP_SITE){row.setSelected(mHost.desktopSite());row.setContentDescription(mContext.getString(label)+", "+mContext.getString(mHost.desktopSite()?R.string.arc_phone_on:R.string.arc_phone_off));}
            row.setOnClickListener(v->{haptic(v);act(this,action);});mBody.addView(row,new LinearLayout.LayoutParams(-1,-2));
        }
        private void separator(){View line=new View(mContext);line.setBackgroundColor((mForeground&0xffffff)|0x0d000000);mBody.addView(line,new LinearLayout.LayoutParams(-1,dp(1)));}
        @Override public View getContentView(){return mScroll;}
        @Override public View getToolbarView(){return mEmptyToolbar;}
        @Override public int getVerticalScrollOffset(){return mScroll.getScrollY();}
        @Override public int getPriority(){return ContentPriority.HIGH;}
        @Override public boolean swipeToDismissEnabled(){return true;}
        @Override public boolean coversBottomControls(){return true;}
        @Override public float getHalfHeightRatio(){return HeightMode.DISABLED;}
        @Override public float getFullHeightRatio(){return HeightMode.WRAP_CONTENT;}
        @Override public BottomSheetType getSheetType(){return new BottomSheetType.Builder().setUserInitiated(true).setModal(true).build();}
        @Override public int getSheetBackgroundColorOverride(){return mSurface;}
        @Override public int getSheetHalfHeightAccessibilityStringId(){return R.string.arc_phone_menu;}
        @Override public int getSheetFullHeightAccessibilityStringId(){return R.string.arc_phone_menu;}
        @Override public int getSheetClosedAccessibilityStringId(){return R.string.arc_phone_menu_closed;}
        @Override public void destroy(){mClosed=true;if(mSheet==this)mSheet=null;}
    }
    /** Small vectors drawn without bitmap allocation; no website content or snapshots are touched. */
    private static final class Icon extends Drawable {
        private final int mKind,mColor;private final String mCount;private final Paint mPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        Icon(int kind,int color,String count){mKind=kind;mColor=color;mCount=count;}
        @Override public void draw(Canvas canvas){
            int save=canvas.save();canvas.translate(getBounds().left,getBounds().top);canvas.scale(getBounds().width()/24f,getBounds().height()/24f);
            mPaint.setColor(mColor);mPaint.setStyle(Paint.Style.STROKE);mPaint.setStrokeWidth(1.8f);mPaint.setStrokeCap(Paint.Cap.ROUND);mPaint.setStrokeJoin(Paint.Join.ROUND);
            if(mKind==HOME){Path p=new Path();p.moveTo(3,10);p.lineTo(12,3);p.lineTo(21,10);p.lineTo(21,21);p.lineTo(15,21);p.lineTo(15,14);p.lineTo(9,14);p.lineTo(9,21);p.lineTo(3,21);p.close();canvas.drawPath(p,mPaint);}
            else if(mKind==NEW_TAB){canvas.drawLine(12,4,12,20,mPaint);canvas.drawLine(4,12,20,12,mPaint);}
            else if(mKind==TABS){canvas.drawRoundRect(new RectF(4,3,20,22),4,4,mPaint);mPaint.setStyle(Paint.Style.FILL);mPaint.setTextSize(mCount.length()>2?7:11);mPaint.setTextAlign(Paint.Align.CENTER);canvas.drawText(mCount,12,16,mPaint);}
            else if(mKind==MENU){canvas.drawLine(6,15,12,9,mPaint);canvas.drawLine(12,9,18,15,mPaint);}
            else if(mKind==FIND){canvas.drawCircle(10,10,7,mPaint);canvas.drawLine(15,15,22,22,mPaint);}
            else if(mKind==SHARE){canvas.drawCircle(5,12,3,mPaint);canvas.drawCircle(19,5,3,mPaint);canvas.drawCircle(19,19,3,mPaint);canvas.drawLine(8,10,16,6,mPaint);canvas.drawLine(8,14,16,18,mPaint);}
            else if(mKind==PIN){Path p=new Path();p.moveTo(8,3);p.lineTo(16,3);p.lineTo(15,10);p.lineTo(19,15);p.lineTo(5,15);p.lineTo(9,10);p.close();canvas.drawPath(p,mPaint);canvas.drawLine(12,15,12,22,mPaint);}
            else if(mKind==FAVORITE){Path p=new Path();for(int i=0;i<10;i++){double a=-Math.PI/2+i*Math.PI/5;float r=i%2==0?10:4.5f;float x=12+(float)Math.cos(a)*r,y=12+(float)Math.sin(a)*r;if(i==0)p.moveTo(x,y);else p.lineTo(x,y);}p.close();canvas.drawPath(p,mPaint);}
            else if(mKind==DESKTOP_SITE){canvas.drawRoundRect(new RectF(2,3,22,17),2,2,mPaint);canvas.drawLine(12,17,12,22,mPaint);canvas.drawLine(8,22,16,22,mPaint);}
            else if(mKind==DOWNLOADS){canvas.drawLine(12,2,12,16,mPaint);canvas.drawLine(7,11,12,16,mPaint);canvas.drawLine(12,16,17,11,mPaint);canvas.drawLine(3,17,3,22,mPaint);canvas.drawLine(3,22,21,22,mPaint);canvas.drawLine(21,22,21,17,mPaint);}
            else {canvas.drawCircle(12,12,9,mPaint);canvas.drawLine(12,11,12,17,mPaint);canvas.drawPoint(12,7,mPaint);}
            canvas.restoreToCount(save);
        }
        @Override public void setAlpha(int alpha){mPaint.setAlpha(alpha);}
        @Override public void setColorFilter(ColorFilter filter){mPaint.setColorFilter(filter);}
        @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
}
