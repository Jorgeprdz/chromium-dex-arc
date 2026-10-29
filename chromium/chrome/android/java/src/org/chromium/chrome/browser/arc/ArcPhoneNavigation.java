// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import android.animation.ValueAnimator;
import android.content.Context;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.util.TypedValue;
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
import android.view.MotionEvent;
import android.view.ViewConfiguration;
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
        default boolean homePage(){return false;}
        default int pageColor(){return Color.TRANSPARENT;}
        default String pageUrl(){return domain();}
        default boolean favorite(){return false;}
        boolean desktopSite();
        int zoomPercent();
        int surface();
        void action(int action);
        void zoom(int direction);
    }
    public static final int HEIGHT_DP=76;
    private final FrameLayout mSlot;
    private final Context mContext;
    private final BottomSheetController mController;
    private final LinearLayout mBar;
    private final int mHeight;
    private final int mBarHeight;
    private boolean mTabbedHost=true;
    private boolean mPhoneModeActive=true;
    private final View[] mButtons=new View[4];
    private final Aura[] mAuras=new Aura[4];
    private boolean mHubActive;
    private int mPageColor=Color.TRANSPARENT, mAccentColor=ArcPhonePalette.FALLBACK;
    private boolean mAuraDark;
    private Host mHost;
    private BottomControlsVisibilityController mVisibility;
    private Callback<Object> mCapture;
    private MenuSheet mSheet;
    private boolean mDestroyed;
    private int mSurface, mForeground;
    private ArcPhoneGlass.Backdrop mGlass;
    private ArcPhoneGlass mGlassSampler;
    private boolean mGlassEnabled;
    private String mCount="";
    private boolean mCompact;
    private Runnable mCompactListener;
    private float mCompactDownX, mCompactStartX;
    private boolean mCompactDragged;
    private final View.OnLayoutChangeListener mCompactLayoutListener=(v,l,t,r,b,ol,ot,or,ob)->clampCompactPosition();

    public ArcPhoneNavigation(FrameLayout slot, BottomSheetController controller) {
        this(slot,controller,Math.round(HEIGHT_DP*slot.getResources().getDisplayMetrics().density));
    }
    public ArcPhoneNavigation(FrameLayout slot, BottomSheetController controller,int height) {
        mHeight=height;
        mSlot=slot;mContext=slot.getContext();mController=controller;
        mSurface=themeSurface();
        mForeground=Color.luminance(mSurface)>.45?0xff202124:0xfff1f3f4;
        mBarHeight=Math.min(mHeight,Math.max(dp(48),mHeight-dp(20)));
        mBar=new LinearLayout(mContext);mBar.setGravity(Gravity.CENTER);
        mBar.setTag("arc-phone-navigation");
        // Native background-tab animations locate the replacement bar and its actual target.
        mBar.setId(org.chromium.chrome.browser.ui.bottombar.R.id.bottom_bar_container);
        mBar.setElevation(dp(4));
        mBar.setOutlineAmbientShadowColor(0x180d244b);
        mBar.setOutlineSpotShadowColor(0x180d244b);
        int[] labels={R.string.arc_phone_home,R.string.arc_phone_new,R.string.arc_phone_tabs,R.string.arc_phone_menu};
        String[] tags={"home","new","tabs","menu"};
        for(int i=0;i<4;i++) {
            final int action=i;
            LinearLayout button=new LinearLayout(mContext);button.setOrientation(LinearLayout.VERTICAL);
            button.setGravity(Gravity.CENTER);button.setPadding(0,dp(3),0,dp(3));
            if(i==TABS)button.setId(R.id.tab_switcher_button);
            ImageView icon=new ImageView(mContext);icon.setImageDrawable(new Icon(i,mForeground,""));
            FrameLayout pill=new FrameLayout(mContext);pill.addView(icon,new FrameLayout.LayoutParams(Math.min(dp(26),mBarHeight-dp(26)),Math.min(dp(26),mBarHeight-dp(26)),Gravity.CENTER));
            mAuras[i]=new Aura();pill.setBackground(mAuras[i]);
            button.addView(pill,new LinearLayout.LayoutParams(dp(i==NEW_TAB?60:44),Math.max(dp(24),mBarHeight-dp(24))));
            TextView text=text(mContext.getString(labels[i]),12);text.setGravity(Gravity.CENTER);
            button.addView(text,new LinearLayout.LayoutParams(-1,dp(18)));
            accessible(button,mContext.getString(labels[i]),"arc-phone-"+tags[i]);
            button.setOnClickListener(v->{if(mDestroyed||mHost==null)return;haptic(v);if(mCompact){setCompact(false);if(mCompactListener!=null)mCompactListener.run();}
                else if(action==MENU)showMenu();else {if(action==NEW_TAB)mAuras[NEW_TAB].pulse(mAccentColor);mHost.action(action);}});
            if(i==MENU) {
                button.setOnLongClickListener(v->{
                    if(mCompact)showMenu();
                    else {setCompact(true);if(mCompactListener!=null)mCompactListener.run();}
                    return true;
                });
                button.setOnTouchListener((v,event)->{
                    if(!mCompact)return false;
                    switch(event.getActionMasked()) {
                        case MotionEvent.ACTION_DOWN:
                            mCompactDownX=event.getRawX();mCompactStartX=mBar.getTranslationX();mCompactDragged=false;break;
                        case MotionEvent.ACTION_MOVE:
                            float delta=event.getRawX()-mCompactDownX;
                            if(Math.abs(delta)>ViewConfiguration.get(mContext).getScaledTouchSlop())mCompactDragged=true;
                            if(mCompactDragged){
                                v.cancelLongPress();v.setPressed(false);
                                float limit=Math.max(0,(mSlot.getWidth()-mBar.getWidth())/2f-dp(18));
                                mBar.setTranslationX(Math.max(-limit,Math.min(limit,mCompactStartX+delta)));
                                v.getParent().requestDisallowInterceptTouchEvent(true);
                                return true;
                            }break;
                        case MotionEvent.ACTION_UP:
                        case MotionEvent.ACTION_CANCEL:
                            if(mCompactDragged){v.setPressed(false);v.getParent().requestDisallowInterceptTouchEvent(false);return true;}break;
                    }
                    return false;
                });
            }
            mBar.addView(button,new LinearLayout.LayoutParams(0,mBarHeight,1));mButtons[i]=button;
        }
        // Native BottomControlsCoordinator owns size, insets, fullscreen, keyboard and raster capture.
        slot.addView(mBar,floatingLayout());
        slot.addOnLayoutChangeListener(mCompactLayoutListener);
        refresh();
    }
    /** Let Chromium's tab switcher borrow the same view, never a duplicate bar. */
    public BottomBar getBottomBar() {
        return new BottomBar() {
            public View getView(){return mBar;}
            public int getBackgroundColor(){return isFloatingSurface()?Color.TRANSPARENT:mSurface;}
            public void setParent(int host){mTabbedHost=host==BottomBarHostManager.Host.TABBED;mHubActive=host==BottomBarHostManager.Host.HUB;if(!mTabbedHost)setCompact(false);dismissMenu();refresh();}
            public boolean maybeShowPromoDialog(Profile profile){return false;}
            public void onStartupPromoFlowFinished(boolean promoShown){}
        };
    }
    public void attachBottomBarView(View view) {
        if(mDestroyed)return;
        mSlot.addView(view,floatingLayout());refresh();
    }
    private FrameLayout.LayoutParams floatingLayout() {
        FrameLayout.LayoutParams params=new FrameLayout.LayoutParams(-1,mBarHeight,Gravity.CENTER);
        if(mCompact)params.width=dp(96);
        int vertical=(mHeight-mBarHeight)/2;
        params.setMargins(dp(18),vertical,dp(18),vertical);
        return params;
    }
    public static int getReservedHeight(Context context) {
        return Math.round(HEIGHT_DP*context.getResources().getDisplayMetrics().density);
    }
    public void setPhoneModeActive(boolean active) {
        if(mPhoneModeActive==active)return;
        mPhoneModeActive=active;
        if(!active){setCompact(false);dismissMenu();}
        refresh();
    }
    public void setCompactListener(Runnable listener){mCompactListener=listener;}
    public boolean isCompact(){return mCompact;}
    public void setCompact(boolean compact){
        if(mDestroyed||mCompact==compact)return;
        if(compact&&(!mPhoneModeActive||!mTabbedHost||mHost==null||!mHost.webPage()))return;
        mCompact=compact;
        mBar.setTranslationX(0);
        FrameLayout.LayoutParams params=floatingLayout();
        if(compact)params.width=dp(96);
        mBar.setLayoutParams(params);
        refresh();
    }
    private void clampCompactPosition(){
        if(!mCompact)return;
        float limit=Math.max(0,(mSlot.getWidth()-mBar.getWidth())/2f-dp(18));
        mBar.setTranslationX(Math.max(-limit,Math.min(limit,mBar.getTranslationX())));
    }
    public View getGlassTarget(){return mBar;}
    public void setGlassSampler(ArcPhoneGlass sampler){mGlassSampler=sampler;}
    public void setGlassBackdrop(ArcPhoneGlass.Backdrop glass,boolean enabled){mGlass=glass;if(glass!=null)glass.setFloatingMaterial(mContext.getResources().getDisplayMetrics().density);mGlassEnabled=enabled;refresh();}
    private boolean isFloatingSurface(){return mPhoneModeActive;}
    private boolean usesGlass(){return mGlassEnabled && mPhoneModeActive && mTabbedHost && mGlass!=null;}
    public void bind(Host host){if(mDestroyed)return;mHost=host;refresh();}
    public void refresh() {
        if(mDestroyed)return;
        if(mSheet!=null && (mHost==null || mSheet.mToken!=mHost.pageToken()
                || !mSheet.mPageUrl.equals(mHost.pageUrl())))dismissMenu();
        int nativeSurface=mHost==null?themeSurface():mHost.surface();
        mSurface=Color.luminance(nativeSurface)>.45?Color.WHITE:nativeSurface;
        mForeground=Color.luminance(mSurface)>.45?0xff202124:0xfff1f3f4;
        if(mGlass!=null)mGlass.setSurface(mSurface);
        mSlot.setBackgroundColor(isFloatingSurface()?Color.TRANSPARENT:mSurface);
        mBar.setBackground(usesGlass()?mGlass:shape((mSurface&0xffffff)|0xf9000000,100));
        boolean dark=Color.luminance(mSurface)<=.45;
        int page=mHost==null?Color.TRANSPARENT:mHost.pageColor();
        if(page!=mPageColor || dark!=mAuraDark){mPageColor=page;mAuraDark=dark;mAccentColor=ArcPhonePalette.accent(page,dark);}
        int active=!mPhoneModeActive?-1:mSheet!=null?MENU:mHubActive?TABS:mHost!=null&&mHost.homePage()?HOME:-1;
        String count=mHost==null?"0":Integer.toString(Math.max(0,mHost.tabCount()));
        for(int i=0;i<4;i++) {
            LinearLayout button=(LinearLayout)mButtons[i];
            button.setVisibility(mCompact&&i!=MENU?View.GONE:View.VISIBLE);
            TextView label=(TextView)button.getChildAt(1);
            if(i==MENU)label.setText(mCompact?"Archium":mContext.getString(R.string.arc_phone_menu));
            if(i==MENU){
                String hint=mContext.getString(mCompact?R.string.arc_phone_expand_controls:R.string.arc_phone_compact_controls);
                button.setContentDescription(hint);button.setTooltipText(hint);
            }
            button.setEnabled(mHost!=null && mPhoneModeActive);
            button.setBackground(ripple(Color.TRANSPARENT,24));
            boolean selected=i==active;button.setSelected(selected);
            int foreground=mForeground;
            FrameLayout pill=(FrameLayout)button.getChildAt(0);
            if(mPhoneModeActive){mAuras[i].setAmbientEnabled(mHost!=null);mAuras[i].update(selected,mAccentColor,true);}
            else mAuras[i].clear();
            ((ImageView)pill.getChildAt(0)).setImageDrawable(new Icon(i,foreground,i==TABS?count:""));
            ((TextView)button.getChildAt(1)).setTextColor(usesGlass()?mForeground:foreground);
        }
        mButtons[TABS].setContentDescription(mContext.getString(R.string.arc_phone_tabs)+", "+count);
        boolean countChanged=!mCount.equals(count);mCount=count;
        if(mVisibility!=null)mVisibility.setBottomControlsVisible(mHost!=null && mTabbedHost && mPhoneModeActive);
        if(mSheet!=null && mSheet.applyPalette())mController.onSheetBackgroundColorOverrideChanged();
        if(mCapture!=null)mCapture.onResult(countChanged?count:new Object());
    }
    @Override public void initializeWithNative(BottomControlsVisibilityController visibility,Callback<Object> capture){mVisibility=visibility;mCapture=capture;refresh();}
    @Override public int getScrollBehavior(){return LayerScrollBehavior.DEFAULT_SCROLL_OFF;}
    @Override public Integer getBackgroundColor(){return isFloatingSurface()?Color.TRANSPARENT:mSurface;}
    private void showMenu() {
        if(mDestroyed||mHost==null||!mPhoneModeActive||mSheet!=null)return;
        MenuSheet sheet=new MenuSheet(mHost);mSheet=sheet;
        if(!mController.requestShowContent(sheet,ValueAnimator.areAnimatorsEnabled()))sheet.destroy();
        refresh();
    }
    public void dismissMenu(){MenuSheet sheet=mSheet;if(sheet==null)return;mSheet=null;mController.hideContent(sheet,ValueAnimator.areAnimatorsEnabled());sheet.destroy();}
    @Override public void destroy(){if(mDestroyed)return;mDestroyed=true;for(Aura aura:mAuras)aura.clear();mSlot.removeOnLayoutChangeListener(mCompactLayoutListener);dismissMenu();mCompactListener=null;mHost=null;mCapture=null;mVisibility=null;if(mBar.getParent() instanceof ViewGroup parent)parent.removeView(mBar);}
    private boolean valid(MenuSheet sheet){return !mDestroyed && mPhoneModeActive && !sheet.mClosed && mHost!=null && sheet.mToken==mHost.pageToken() && sheet.mPageUrl.equals(mHost.pageUrl());}
    private void act(MenuSheet sheet,int action){if(!valid(sheet))return;Host host=mHost;dismissMenu();host.action(action);refresh();}
    private void haptic(View view){view.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);}
    private int themeSurface() {
        TypedValue color=new TypedValue();
        if(mContext.getTheme().resolveAttribute(android.R.attr.colorBackground,color,true)) {
            if(color.type>=TypedValue.TYPE_FIRST_COLOR_INT && color.type<=TypedValue.TYPE_LAST_COLOR_INT)return color.data;
            if(color.resourceId!=0)return mContext.getColor(color.resourceId);
        }
        return (mContext.getResources().getConfiguration().uiMode&Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES?0xff202124:Color.WHITE;
    }
    private int dp(int value){return Math.round(value*mContext.getResources().getDisplayMetrics().density);}
    private TextView text(String value,int sp){TextView t=new TextView(mContext);t.setText(value);t.setTextSize(sp);t.setTextColor(mForeground);return t;}
    private GradientDrawable shape(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
    private Drawable ripple(int background,int radius){return new RippleDrawable(ColorStateList.valueOf((mForeground&0xffffff)|0x10000000),shape(background,radius),null);}
    private void accessible(View view,String label,String tag){view.setTag(tag);view.setContentDescription(label);view.setTooltipText(label);view.setFocusable(true);view.setClickable(true);view.setMinimumHeight(dp(48));}

    private final class MenuSheet implements BottomSheetContent {
        final Object mToken;
        final String mPageUrl;
        final ScrollView mScroll;
        final LinearLayout mBody;
        final View mEmptyToolbar;
        boolean mClosed;
        final GradientDrawable mOpaqueBackground;
        final ArcPhoneGlass.Backdrop mBackdrop;
        int mPaintedSurface;
        boolean mPaintedGlass;
        MenuSheet(Host host) {
            mToken=host.pageToken();mPageUrl=host.pageUrl();mScroll=new ScrollView(mContext);mScroll.setFillViewport(false);
            mBody=new LinearLayout(mContext);mBody.setOrientation(LinearLayout.VERTICAL);mBody.setPadding(dp(16),dp(10),dp(16),dp(12));
            mOpaqueBackground=shape(mSurface,28);mOpaqueBackground.setCornerRadii(new float[]{dp(28),dp(28),dp(28),dp(28),0,0,0,0});mBody.setBackground(mOpaqueBackground);
            mBackdrop=mGlassSampler==null?null:mGlassSampler.add(mScroll,r->r.set(0,0,mScroll.getWidth(),mScroll.getHeight()));
            if(mBackdrop!=null){mBackdrop.setFloatingMaterial(mContext.getResources().getDisplayMetrics().density);mBackdrop.setTopCorners(dp(28));}
            mScroll.addView(mBody,new ScrollView.LayoutParams(-1,-2));
            // A non-null, zero-height toolbar prevents the native sheet's omnibox fallback.
            mEmptyToolbar=new View(mContext);mEmptyToolbar.setLayoutParams(new FrameLayout.LayoutParams(-1,0));
            View grip=new View(mContext);grip.setTag("arc-phone-menu-grip");grip.setBackground(shape((mForeground&0xffffff)|0x50000000,3));
            LinearLayout.LayoutParams gripSize=new LinearLayout.LayoutParams(dp(32),dp(4));gripSize.gravity=Gravity.CENTER_HORIZONTAL;gripSize.bottomMargin=dp(12);mBody.addView(grip,gripSize);
            LinearLayout header=new LinearLayout(mContext);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(dp(8),dp(4),dp(8),dp(12));
            ImageView favicon=new ImageView(mContext);favicon.setScaleType(ImageView.ScaleType.FIT_CENTER);Bitmap bitmap=host.favicon();
            if(bitmap!=null)favicon.setImageBitmap(bitmap);else favicon.setImageDrawable(new Icon(SITE_INFO,mForeground,""));
            header.addView(favicon,new LinearLayout.LayoutParams(dp(32),dp(32)));
            LinearLayout title=new LinearLayout(mContext);title.setOrientation(LinearLayout.VERTICAL);title.setPadding(dp(16),0,0,0);
            TextView domain=text(host.domain(),18);domain.setTag("arc-phone-domain");domain.setSingleLine(true);domain.setEllipsize(android.text.TextUtils.TruncateAt.END);domain.setTooltipText(host.domain());title.addView(domain);
            TextView subtitle=text(mContext.getString(R.string.arc_phone_site_info),13);subtitle.setTag("arc-phone-domain-subtitle");title.addView(subtitle);header.addView(title,new LinearLayout.LayoutParams(0,-2,1));
            accessible(header,mContext.getString(R.string.arc_phone_site_info),"arc-phone-site-info");header.setEnabled(host.webPage());header.setOnClickListener(v->act(this,SITE_INFO));mBody.addView(header);
            LinearLayout quick=new LinearLayout(mContext);quick.setGravity(Gravity.CENTER);
            int[] actions={PIN,FIND,SHARE};int[] labels={host.pinned()?R.string.arc_phone_unpin:R.string.arc_phone_pin,R.string.arc_phone_find,R.string.arc_phone_share};String[] tags={"pin","find","share"};
            for(int i=0;i<3;i++) {
                final int action=actions[i];LinearLayout tile=new LinearLayout(mContext);tile.setOrientation(LinearLayout.VERTICAL);tile.setGravity(Gravity.CENTER);
                ImageView icon=new ImageView(mContext);icon.setImageDrawable(new Icon(action,mForeground,""));tile.addView(icon,new LinearLayout.LayoutParams(dp(24),dp(24)));
                TextView label=text(mContext.getString(labels[i]),13);label.setGravity(Gravity.CENTER);tile.addView(label);
                accessible(tile,mContext.getString(labels[i]),"arc-phone-"+tags[i]);tile.setEnabled(host.webPage());tile.setAlpha(host.webPage()?1f:.4f);tile.setBackground(ripple(Color.luminance(mSurface)>.45?0x66ffffff:0x24363840,16));
                tile.setOnClickListener(v->{haptic(v);act(this,action);});
                LinearLayout.LayoutParams size=new LinearLayout.LayoutParams(0,dp(88),1);size.setMargins(dp(3),dp(4),dp(3),dp(12));quick.addView(tile,size);
            }
            mBody.addView(quick);separator();
            row(FAVORITE,R.string.arc_phone_favorite,"favorite",host.webPage(),null);
            LinearLayout zoomRow=new LinearLayout(mContext);zoomRow.setGravity(Gravity.CENTER_VERTICAL);zoomRow.setPadding(dp(12),0,dp(4),0);
            TextView zoom=text("",16);zoom.setText(host.zoomPercent()+"%");zoom.setTag("arc-phone-zoom-value");
            TextView zoomTitle=text(mContext.getString(R.string.arc_phone_zoom),17);zoomRow.addView(zoomTitle,new LinearLayout.LayoutParams(0,dp(64),1));zoomTitle.setGravity(Gravity.CENTER_VERTICAL);
            LinearLayout zoomControls=new LinearLayout(mContext);zoomControls.setGravity(Gravity.CENTER_VERTICAL);
            zoom.setGravity(Gravity.CENTER);zoom.setMinWidth(dp(56));
            for(int direction:new int[]{-1,1}) {
                TextView step=text(direction<0?"−":"+",26);step.setGravity(Gravity.CENTER);step.setBackground(ripple(Color.TRANSPARENT,24));
                accessible(step,mContext.getString(direction<0?R.string.arc_phone_zoom_out:R.string.arc_phone_zoom_in),"arc-phone-zoom-"+(direction<0?"minus":"plus"));step.setEnabled(host.webPage());step.setAlpha(host.webPage()?1f:.4f);
                step.setOnClickListener(v->{if(!valid(this))return;haptic(v);mHost.zoom(direction);zoom.setText(mHost.zoomPercent()+"%");});zoomControls.addView(step,new LinearLayout.LayoutParams(dp(48),dp(48)));
                if(direction<0)zoomControls.addView(zoom,new LinearLayout.LayoutParams(dp(56),dp(48)));
            }
            zoomRow.addView(zoomControls);mBody.addView(zoomRow);separator();
            row(DESKTOP_SITE,R.string.arc_phone_desktop,"desktop",host.webPage(),host.desktopSite()?"✓":"○");
            row(SITE_INFO,R.string.arc_phone_site_settings,"site-settings",host.webPage(),"›");
            row(DOWNLOADS,R.string.arc_phone_downloads,"downloads",true,"›");
            row(MORE,R.string.arc_phone_more,"more",true,"›");
            applyPalette();
        }
        private void row(int action,int label,String tag,boolean enabled,String end) {
            LinearLayout row=new LinearLayout(mContext);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(12),0,dp(12),0);
            ImageView icon=new ImageView(mContext);icon.setImageDrawable(new Icon(action,mForeground,action==FAVORITE&&mHost.favorite()?"filled":""));row.addView(icon,new LinearLayout.LayoutParams(dp(24),dp(24)));
            TextView title=text(mContext.getString(action==FAVORITE&&mHost.favorite()?R.string.arc_phone_favorite_saved:label),17);title.setPadding(dp(16),dp(12),dp(8),dp(12));row.addView(title,new LinearLayout.LayoutParams(0,-2,1));
            if(action==DESKTOP_SITE) {
                Switch toggle=new Switch(mContext);toggle.setChecked(mHost.desktopSite());
                toggle.setClickable(false);toggle.setFocusable(false);toggle.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);row.addView(toggle);
            } else if(end!=null)row.addView(text(end,22));
            accessible(row,mContext.getString(label),"arc-phone-"+tag);row.setEnabled(enabled);row.setAlpha(enabled?1f:.4f);row.setBackground(ripple(Color.TRANSPARENT,12));
            if(action==FAVORITE){row.setSelected(mHost.favorite());if(mHost.favorite())row.setContentDescription(mContext.getString(R.string.arc_phone_favorite_saved));}
            if(action==DESKTOP_SITE){row.setSelected(mHost.desktopSite());row.setContentDescription(mContext.getString(label)+", "+mContext.getString(mHost.desktopSite()?R.string.arc_phone_on:R.string.arc_phone_off));}
            row.setOnClickListener(v->{haptic(v);act(this,action);});mBody.addView(row,new LinearLayout.LayoutParams(-1,-2));
        }
        private void separator(){View line=new View(mContext);line.setTag("arc-phone-menu-divider");line.setBackgroundColor((mForeground&0xffffff)|0x0d000000);mBody.addView(line,new LinearLayout.LayoutParams(-1,dp(1)));}
        private boolean applyPalette() {
            boolean glass=mBackdrop!=null&&usesGlass();
            if(mPaintedSurface==mSurface&&mPaintedGlass==glass)return false;
            mPaintedSurface=mSurface;mPaintedGlass=glass;
            mOpaqueBackground.setColor(mSurface);
            if(mBackdrop!=null)mBackdrop.setSurface(mSurface);
            mScroll.setBackground(glass?mBackdrop:null);
            mBody.setBackground(glass?null:mOpaqueBackground);
            recolor(mBody);
            return true;
        }
        private void recolor(View view) {
            if(view instanceof TextView label)label.setTextColor("arc-phone-domain-subtitle".equals(view.getTag())?(mForeground&0xffffff)|0xb3000000:mForeground);
            if(view instanceof ImageView icon && icon.getDrawable() instanceof Icon vector)vector.setColor(mForeground);
            Object tag=view.getTag();
            if("arc-phone-menu-grip".equals(tag))((GradientDrawable)view.getBackground()).setColor((mForeground&0xffffff)|0x50000000);
            if("arc-phone-menu-divider".equals(tag))view.setBackgroundColor((mForeground&0xffffff)|0x0d000000);
            if(view.getBackground() instanceof RippleDrawable ripple) {
                ripple.setColor(ColorStateList.valueOf((mForeground&0xffffff)|0x10000000));
                if(("arc-phone-pin".equals(tag)||"arc-phone-find".equals(tag)||"arc-phone-share".equals(tag))
                        && ripple.getDrawable(0) instanceof GradientDrawable tile) {
                    tile.setColor(Color.luminance(mSurface)>.45?0x66ffffff:0x24363840);
                }
            }
            if(view instanceof ViewGroup group)for(int i=0;i<group.getChildCount();i++)recolor(group.getChildAt(i));
        }
        @Override public View getContentView(){return mScroll;}
        @Override public View getToolbarView(){return mEmptyToolbar;}
        @Override public int getVerticalScrollOffset(){return mScroll.getScrollY();}
        @Override public int getPriority(){return ContentPriority.HIGH;}
        @Override public boolean swipeToDismissEnabled(){return true;}
        @Override public boolean coversBottomControls(){return true;}
        @Override public float getHalfHeightRatio(){return HeightMode.DISABLED;}
        @Override public float getFullHeightRatio(){return HeightMode.WRAP_CONTENT;}
        @Override public BottomSheetType getSheetType(){return new BottomSheetType.Builder().setUserInitiated(true).setModal(true).build();}
        @Override public boolean hasSolidBackgroundColor(){return mBackdrop==null||!usesGlass();}
        @Override public int getSheetBackgroundColorOverride(){return hasSolidBackgroundColor()?mSurface:Color.TRANSPARENT;}
        @Override public int getSheetHalfHeightAccessibilityStringId(){return R.string.arc_phone_menu;}
        @Override public int getSheetFullHeightAccessibilityStringId(){return R.string.arc_phone_menu;}
        @Override public int getSheetClosedAccessibilityStringId(){return R.string.arc_phone_menu_closed;}
        @Override public void destroy(){if(mClosed)return;mClosed=true;if(mGlassSampler!=null&&mBackdrop!=null)mGlassSampler.remove(mBackdrop);if(mSheet==this)mSheet=null;refresh();}
    }
    /** Paint-only aura on the existing icon pill; never participates in layout or input. */
    private static final class Aura extends Drawable {
        private final Paint mPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        private static final android.animation.ArgbEvaluator COLORS=new android.animation.ArgbEvaluator();
        private int mColor=ArcPhonePalette.FALLBACK,mTargetColor=mColor,mAlpha=255;
        private float mStrength,mTarget,mAmbientStrength;
        private boolean mPulsing;
        private ValueAnimator mAnimator;
        void setAmbientEnabled(boolean enabled){
            float strength=enabled?.70f:0f;
            if(mAmbientStrength==strength)return;mAmbientStrength=strength;invalidateSelf();
        }
        void update(boolean selected,int color,boolean animate){
            if(mPulsing&&!selected){mTargetColor=color;setColor(color);return;}
            float target=selected?1f:0f;
            if(mTarget==target&&mTargetColor==color)return;
            cancel();mTarget=target;mTargetColor=color;
            if(!animate||!ValueAnimator.areAnimatorsEnabled()||(mStrength==0&&target==0&&mAmbientStrength==0)){mStrength=target;setColor(color);invalidateSelf();return;}
            run(false,color);
        }
        void pulse(int color){
            cancel();mTarget=0;mTargetColor=color;
            if(!ValueAnimator.areAnimatorsEnabled()){mStrength=0;invalidateSelf();return;}
            mPulsing=true;setColor(color);run(true,color);
        }
        private void run(boolean pulse,int color){
            final float start=mStrength;final int startColor=mColor;
            mAnimator=ValueAnimator.ofFloat(0f,1f);mAnimator.setDuration(220);
            mAnimator.addUpdateListener(animation->{
                float value=(float)animation.getAnimatedValue();
                mStrength=pulse?(value<.5f?value*2:(1-value)*2):start+(mTarget-start)*value;
                setColor(pulse?mTargetColor:(int)COLORS.evaluate(value,startColor,color));invalidateSelf();
            });
            mAnimator.addListener(new android.animation.AnimatorListenerAdapter(){@Override public void onAnimationEnd(android.animation.Animator animation){mAnimator=null;mPulsing=false;mStrength=mTarget;invalidateSelf();}});
            mAnimator.start();
        }
        private void setColor(int color){if(mColor==color&&mPaint.getShader()!=null)return;mColor=color;updateShader();invalidateSelf();}
        private void updateShader(){var b=getBounds();if(b.isEmpty())return;int rgb=mColor&0xffffff;
            // Keep the approved 14% peak, but carry tint beyond the icon's optical box.
            // The old early falloff left only ~5% alpha at 72% radius on a 44x24dp pill.
            var gradient=new android.graphics.RadialGradient(0,0,1,
                    new int[]{0x24000000|rgb,0x24000000|rgb,0x1c000000|rgb,rgb},
                    new float[]{0f,.55f,.80f,1f},android.graphics.Shader.TileMode.CLAMP);
            var matrix=new android.graphics.Matrix();matrix.setScale(b.width()/2f,b.height()/2f);matrix.postTranslate(b.exactCenterX(),b.exactCenterY());
            gradient.setLocalMatrix(matrix);mPaint.setShader(gradient);}
        @Override protected void onBoundsChange(android.graphics.Rect bounds){updateShader();}
        @Override public void draw(Canvas canvas){float strength=mAmbientStrength+(1-mAmbientStrength)*mStrength;if(strength<=0)return;var b=getBounds();mPaint.setAlpha(Math.round(mAlpha*strength));canvas.drawRoundRect(new RectF(b),b.height()/2f,b.height()/2f,mPaint);}
        private void cancel(){if(mAnimator!=null){mAnimator.removeAllListeners();mAnimator.removeAllUpdateListeners();mAnimator.cancel();mAnimator=null;}mPulsing=false;}
        void clear(){cancel();mTarget=0;mStrength=0;mAmbientStrength=0;invalidateSelf();}
        @Override public void setAlpha(int alpha){mAlpha=alpha;invalidateSelf();}
        @Override public void setColorFilter(ColorFilter filter){mPaint.setColorFilter(filter);invalidateSelf();}
        @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }

    /** Small vectors drawn without bitmap allocation; no website content or snapshots are touched. */
    private static final class Icon extends Drawable {
        private final int mKind;private int mColor;private final String mCount;private final Paint mPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
        Icon(int kind,int color,String count){mKind=kind;mColor=color;mCount=count;}
        void setColor(int color){mColor=color;invalidateSelf();}
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
            else if(mKind==FAVORITE){if("filled".equals(mCount))mPaint.setStyle(Paint.Style.FILL);Path p=new Path();for(int i=0;i<10;i++){double a=-Math.PI/2+i*Math.PI/5;float r=i%2==0?10:4.5f;float x=12+(float)Math.cos(a)*r,y=12+(float)Math.sin(a)*r;if(i==0)p.moveTo(x,y);else p.lineTo(x,y);}p.close();canvas.drawPath(p,mPaint);}
            else if(mKind==DESKTOP_SITE){canvas.drawRoundRect(new RectF(2,3,22,17),2,2,mPaint);canvas.drawLine(12,17,12,22,mPaint);canvas.drawLine(8,22,16,22,mPaint);}
            else if(mKind==DOWNLOADS){canvas.drawLine(12,2,12,16,mPaint);canvas.drawLine(7,11,12,16,mPaint);canvas.drawLine(12,16,17,11,mPaint);canvas.drawLine(3,17,3,22,mPaint);canvas.drawLine(3,22,21,22,mPaint);canvas.drawLine(21,22,21,17,mPaint);}
            else if(mKind==MORE){mPaint.setStyle(Paint.Style.FILL);for(int x:new int[]{5,12,19})canvas.drawCircle(x,12,1.7f,mPaint);}
            else {canvas.drawCircle(12,12,9,mPaint);canvas.drawLine(12,11,12,17,mPaint);canvas.drawPoint(12,7,mPaint);}
            canvas.restoreToCount(save);
        }
        @Override public void setAlpha(int alpha){mPaint.setAlpha(alpha);}
        @Override public void setColorFilter(ColorFilter filter){mPaint.setColorFilter(filter);}
        @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    }
}
