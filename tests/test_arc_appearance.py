"""Execute pure appearance policy and shipped binder/view helpers with bounded services.

Checks colors, restored native values and sizing contracts. These doubles do not
establish rendered visual fidelity or Android frame performance.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body, window_core_jar

POLICY = ROOT/'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java'
APPEARANCE = POLICY.with_name('ArcDesktopAppearance.java')
NATIVE = ROOT/'.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs'

JAVA = r'''
import java.util.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class AppearanceProbe {
    static class Metrics {float density=1,scaledDensity=1.5f;}
    static class Resources {Metrics m=new Metrics();Metrics getDisplayMetrics(){return m;}}
    static class Context {final Resources res=new Resources();Resources getResources(){return res;}int getColor(int id){return id;}ColorStateList getColorStateList(int id){return ColorStateList.valueOf(id);}}
    static class Drawable {Drawable mutate(){return this;}}
    static class LayerDrawable extends Drawable {final Drawable[] layers;LayerDrawable(Drawable[] d){layers=d;}}
    static class StateListDrawable extends Drawable {java.util.List<int[]> states=new java.util.ArrayList<>();java.util.List<Drawable> drawables=new java.util.ArrayList<>();void addState(int[] s,Drawable d){states.add(s);drawables.add(d);}}
    static class RippleDrawable extends Drawable {final ColorStateList ripple;final Drawable content,mask;RippleDrawable(ColorStateList c,Drawable d,Drawable m){ripple=c;content=d;mask=m;}}
    static class GradientDrawable extends Drawable {
        enum Orientation {TOP_BOTTOM} int start,end,updates,color;float radius;
        GradientDrawable(){}GradientDrawable(Orientation o,int[] colors){setColors(colors);}
        void setColor(int c){color=c;}void setOrientation(Orientation o){}void setColors(int[] c){start=c[0];end=c[1];updates++;}float getCornerRadius(){return radius;}void setCornerRadius(float r){radius=r;}
    }
    static class InsetDrawable extends Drawable {final Drawable d;InsetDrawable(Drawable a){d=a;}Drawable getDrawable(){return d;}}
    static class ViewGroup extends View {static class LayoutParams {static final int MATCH_PARENT=-1;int width,height;}}
    static class LinearLayout {
        static final int VERTICAL=1,HORIZONTAL=0;static class LayoutParams extends ViewGroup.LayoutParams {float weight;int bottomMargin;void setMarginEnd(int n){}void setMarginStart(int n){}}
        void setOrientation(int n){}void setGravity(int n){}
    }
    static class View {
        static final int VISIBLE=0,GONE=8;final Context context=new Context();Drawable background=new Drawable();
        ColorStateList tint,imageTint;void invalidate(){}LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams();int left,top,right,bottom,minWidth,minHeight,visibility,width=1382;
        Context getContext(){return context;}Resources getResources(){return context.res;}Drawable getBackground(){return background;}void setBackground(Drawable d){background=d;}
        View getRootView(){return this;}int getWidth(){return width;}void setBackgroundColor(int color){background=new Drawable();}
        int getPaddingLeft(){return left;}int getPaddingTop(){return top;}int getPaddingRight(){return right;}int getPaddingBottom(){return bottom;}
        void setPadding(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}int getMinimumWidth(){return minWidth;}int getMinimumHeight(){return minHeight;}
        void setMinimumWidth(int n){minWidth=n;}void setMinimumHeight(int n){minHeight=n;}int getVisibility(){return visibility;}
        LinearLayout.LayoutParams getLayoutParams(){return lp;}void setLayoutParams(LinearLayout.LayoutParams p){lp=p;}
    }
    static class TextView extends View {float size=16;int color;ColorStateList getTextColors(){return ColorStateList.valueOf(color);}float getTextSize(){return size;}void setTextSize(int unit,float n){size=unit==TypedValue.COMPLEX_UNIT_SP?n*context.res.m.scaledDensity:n;}void setTextColor(int c){color=c;}void setTextColor(ColorStateList c){color=c.color;}}
    static class TypedValue {static final int COMPLEX_UNIT_SP=2,COMPLEX_UNIT_PX=0;static float applyDimension(int unit,float value,Metrics m){return unit==COMPLEX_UNIT_SP?value*m.scaledDensity:value;}}
    static class ImageView extends View {enum ScaleType {CENTER_INSIDE,FIT_CENTER} ScaleType scale=ScaleType.FIT_CENTER;int imageAlpha=255;ScaleType getScaleType(){return scale;}void setScaleType(ScaleType s){scale=s;}int getImageAlpha(){return imageAlpha;}void setImageAlpha(int a){imageAlpha=a;}}
    static class ImageButton extends ImageView {}
    static class Color {static final int TRANSPARENT=0,WHITE=0xffffffff;}
    static class android {static class R {static class attr {static final int state_pressed=1,state_hovered=2,state_focused=3;}}}
    static class ColorStateList {final int color;int interaction;ColorStateList(int[][] states,int[] colors){color=colors[colors.length-1];interaction=colors[0];}int getDefaultColor(){return color;}ColorStateList(int c){color=c;}static ColorStateList valueOf(int c){return new ColorStateList(c);}}
    static class ArcDesktopAppearance {
        static boolean desktop=true;static boolean isDesktopWindow(Context c){return desktop;}
        static int gradientStart(Context c,boolean incognito){return token("gradientStart",0xffedae9f,incognito,ArcDesktopPolicy.surface(0xffedae9f,incognito));}
        static int gradientEnd(Context c,boolean incognito){return token("gradientEnd",0xffedae9f,incognito,ArcDesktopPolicy.surface(0xffedae9f,incognito));}
        static int surface(Context c,boolean incognito){return ArcDesktopPolicy.surface(0xffedae9f,incognito);}
        static int selection(Context c,boolean incognito){return ArcDesktopPolicy.selection(surface(c,incognito));}
        static int foreground(Context c,boolean incognito){return ArcDesktopPolicy.foreground(surface(c,incognito));}
        static ColorStateList sNewTabBackgroundTint;static int sNewTabBackgroundColor;
        static int interaction(Context c,boolean i){return token("interaction",0xffedae9f,i,0);}
        static final WeakHashMap<View,SidebarBackground> sSidebarBackgrounds=new WeakHashMap<>();
        static final WeakHashMap<TextView,Float> sOriginalTextSizes=new WeakHashMap<>();
        static final WeakHashMap<GradientDrawable,Float> sOriginalCornerRadii=new WeakHashMap<>();
        static final class SidebarBackground SIDEBAR_STATE
        APPEARANCE_HELPERS
    }
    static class PropertyModel {boolean selected,multi,incognito;boolean get(int key){return key==TabProperties.IS_SELECTED?selected:key==TabProperties.IS_INCOGNITO?incognito:multi;}}
    static class TabProperties {static final int IS_SELECTED=1,IS_MULTI_SELECTED=2,IS_INCOGNITO=3;}
    static class VerticalTabItemLayout extends ViewGroup {TextView title=new TextView();ImageView action=new ImageView();TextView getTitleView(){return title;}ImageView getActionButton(){return action;}}
    static class ImageViewCompat {static ColorStateList getImageTintList(View v){return v.imageTint;}static void setImageTintList(View v,ColorStateList c){v.imageTint=c;}}
    static class ViewCompat {static ColorStateList getBackgroundTintList(View v){return v.tint;}static void setBackgroundTintList(View v,ColorStateList c){v.tint=c;}}
    static class IncognitoUtils {static boolean window;static boolean shouldOpenIncognitoAsWindow(){return window;}}
    static class TabUiThemeUtil {static int getTabStripMultiSelectedTabColor(Context c,boolean i){return 27;}static int getHoveredTabContainerColor(Context c,boolean i){return 18;}static int getTabStripMultiSelectedHoveredTabColor(Context c,boolean i){return 19;}static int getTabStripBackgroundColor(Context c,boolean i){return i?12:13;}}
    static class SemanticColorUtils {static int getDefaultIconColor(Context c){return 14;}static int getDefaultTextColor(Context c){return 15;}static int getColorSurface(Context c){return 28;}static int getColorOnSurface(Context c){return 29;}static int getDefaultTextColorSecondary(Context c){return 30;}}
    static class R {static class color {static final int default_bg_color_dark=31,default_text_color_light=32,incognito_tab_title_color=33,incognito_tab_action_button_color=16,incognito_vertical_tabs_button_background_color=17;}}
    static class Gravity {static final int CENTER_HORIZONTAL=1,CENTER_VERTICAL=2;}
    static class RailCollapseState {static final int COLLAPSED=0,EXPANDED=2;}
    static class VerticalTabRailLayout extends View {
        boolean mArcTransparentBackground,mArcNewTabAppearance;Drawable mArcOriginalBackground;
        int mArcNewTabOriginalLeft,mArcNewTabOriginalTop,mArcNewTabOriginalRight,mArcNewTabOriginalBottom,mArcNewTabOriginalMinWidth,mArcNewTabOriginalMinHeight,mArcNewTabOriginalImageAlpha;
        ImageView.ScaleType mArcNewTabOriginalScaleType;
        final ImageButton mNewTabButton=new ImageButton(),mIncognitoButton=new ImageButton();final TextView label=new TextView();final View search=new View(),collapse=new View(),icon=new View();
        final LinearLayout mFooterContainer=new LinearLayout();int mCollapseState=2,mIncognitoChipSizePx=40,mFooterButtonCollapsedWidthPx=40,mFooterButtonCollapsedHeightPx=40,mFooterButtonGapPx=8;
        ImageButton getNewTabButton(){return mNewTabButton;}ImageButton getIncognitoButton(){return mIncognitoButton;}View getCollapseButton(){return collapse;}
        View getSearchIcon(){return icon;}TextView getSearchLabel(){return label;}View getSearchButton(){return search;}
        RAIL_HELPERS
    }

    static void updateSelectionAndBackground(PropertyModel m,VerticalTabItemLayout v,ColorStateList c){}
    static void updateBackgroundInsets(View v){}

    static ColorStateList getActionButtonTintList(Context c,boolean s,boolean i){return ColorStateList.valueOf(0);}
    static final WeakHashMap<VerticalTabRailLayout,NativePalette> sArcNativePalettes=new WeakHashMap<>();
    static final class NativePalette NATIVE_PALETTE
    BINDER_HELPERS
    static int token(String name,int seed,boolean dark,int fallback){try{return (int)ArcDesktopPolicy.class.getMethod(name,int.class,boolean.class).invoke(null,seed,dark);}catch(NoSuchMethodException e){return fallback;}catch(Exception e){throw new AssertionError(e);}}
    static int radius(int width,float density){try{return (int)ArcDesktopPolicy.class.getMethod("selectedTabRadius",int.class,float.class).invoke(null,width,density);}catch(NoSuchMethodException e){return 0;}catch(Exception e){throw new AssertionError(e);}}
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    public static void main(String[] args){String s=args[0];
        if(s.equals("policy")) {
            int[] seeds=java.util.stream.IntStream.concat(java.util.stream.IntStream.of(0xffedae9f,0xff000000,0xffffffff,0xff53657b,0xff706b86,0xff00ff00),
                    java.util.stream.IntStream.iterate(0,n->n<=0xffffff,n->n+7919).map(n->0xff000000|n)).toArray();
            for(int seed:seeds)for(boolean dark:new boolean[]{false,true}){
                int a=token("gradientStart",seed,dark,ArcDesktopPolicy.surface(seed,dark)),b=token("gradientEnd",seed,dark,a);
                check(a!=b,"vertical gradient must have distinct endpoints");int fg=token("gradientForeground",seed,dark,ArcDesktopPolicy.foreground(a));
                check(ArcDesktopPolicy.contrast(a,fg)>=4.5&&ArcDesktopPolicy.contrast(b,fg)>=4.5,"text contrast across gradient");
                check(ArcDesktopPolicy.contrast(ArcDesktopPolicy.selection(a),a)>=1.5&&ArcDesktopPolicy.contrast(ArcDesktopPolicy.selection(a),b)>=1.5,"selected tab must stand out from sidebar seed="+Integer.toHexString(seed)+" dark="+dark+" start="+ArcDesktopPolicy.contrast(ArcDesktopPolicy.selection(a),a)+" end="+ArcDesktopPolicy.contrast(ArcDesktopPolicy.selection(a),b));
            }
            int lavender=ArcDesktopPolicy.gradientStart(0xff706b86,false);
            check((ArcDesktopPolicy.selection(lavender)&255)>(lavender&255),"default light selection must illuminate the capsule");
            check(ArcDesktopPolicy.selection(lavender)!=ArcDesktopPolicy.selection(ArcDesktopPolicy.gradientStart(0xff706b86,true)),"incognito selection is theme specific");
            check(radius(0,1)==14&&radius(0,2)==28,"first bind before root measurement keeps rounded native shape");
            check(radius(1382,1)==14&&radius(2764,2)==28,"14px reference radius must normalize with density");
        } else if(s.equals("controls")) {
            Drawable d=ArcDesktopAppearance.controlBackground(new Context(),false,12);
            check(d instanceof RippleDrawable,"control uses native ripple");RippleDrawable ripple=(RippleDrawable)d;
            check(ripple.content instanceof StateListDrawable,"control uses native view state changes");StateListDrawable states=(StateListDrawable)ripple.content;
            check(states.states.size()==4,"press hover focus and rest each resolve");
            check(states.states.get(0)[0]==android.R.attr.state_pressed&&states.states.get(1)[0]==android.R.attr.state_hovered&&states.states.get(2)[0]==android.R.attr.state_focused,"native state priority");
            check(((GradientDrawable)states.drawables.get(3)).color==0,"control is integrated at rest");
            for(int n=0;n<3;n++)check(((GradientDrawable)states.drawables.get(n)).color!=0,"each interaction remains visible");
            check(((GradientDrawable)states.drawables.get(0)).radius==12,"control keeps requested dp radius");
            Drawable favorite=ArcDesktopAppearance.favoriteBackground(new Context(),false,12);
            check(favorite instanceof LayerDrawable,"favorite has faint tile surface");LayerDrawable tile=(LayerDrawable)favorite;
            check(((GradientDrawable)tile.layers[0]).color>>>24>0&&((GradientDrawable)tile.layers[0]).color>>>24<32,"favorite fill is quiet");
            check(tile.layers[1] instanceof RippleDrawable,"favorite retains native interaction overlay");
            check(ArcDesktopAppearance.rowTextColor(new Context(),true,false)==ArcDesktopPolicy.foreground(ArcDesktopAppearance.selection(new Context(),false)),"selected text uses actual bright surface");
        } else if(s.equals("gradient")) {
            View parent=new View();ArcDesktopAppearance.applySidebarBackground(parent,false);
            check(parent.background instanceof GradientDrawable,"parent must own native vertical gradient");GradientDrawable bg=(GradientDrawable)parent.background;int updates=bg.updates;
            ArcDesktopAppearance.applySidebarBackground(parent,false);check(parent.background==bg&&bg.updates==updates,"stable palette must reuse drawable without color updates");
            VerticalTabRailLayout rail=new VerticalTabRailLayout();Drawable original=rail.background;rail.label.color=5;rail.mNewTabButton.tint=ColorStateList.valueOf(6);updateIncognitoColors(rail,false);check(rail.background==null,"nested rail must not mask parent gradient");
            ArcDesktopAppearance.desktop=false;IncognitoUtils.window=true;updateIncognitoColors(rail,false);check(rail.background==original,"MOBILE dedicated-window path restores exact original background");
            check(rail.label.color==5&&rail.mNewTabButton.tint.color==6,"MOBILE dedicated-window path restores native label and button palette");
        } else if(s.equals("palette")) {
            Context c=new Context();int active=getBackgroundTintList(c,true,false,false).color;
            check(active==ArcDesktopAppearance.selection(c,false),"selected native row uses Arc selection");
            check(getBackgroundTintList(c,false,true,false).color==27,"Arc cannot flatten native multiselection into active selection");
            VerticalTabItemLayout tab=new VerticalTabItemLayout();PropertyModel m=new PropertyModel();m.multi=true;updateRegularColors(m,tab);
            check(tab.title.color==ArcDesktopPolicy.foreground(27),"multiselection text must contrast its native fill");
            check(getBackgroundTintList(c,false,false,false).color==0,"unselected row stays integrated");
            check(ArcDesktopPolicy.contrast(active,getTextColor(c,true,false))>=4.5,"selected row title stays readable");
            m.incognito=true;IncognitoUtils.window=true;m.multi=false;m.selected=true;updateRegularColors(m,tab);
            check(tab.title.color==getTextColor(c,true,true),"dedicated incognito Arc keeps actual dark palette");
            check(isIncognito(m,c),"Arc incognito color resolver cannot suppress branded model in dedicated window");
            ArcDesktopAppearance.desktop=false;check(!isIncognito(m,c),"MOBILE dedicated window keeps original native activity-theme routing");check(getBackgroundTintList(c,true,false,true).color==31,"MOBILE incognito native selection unchanged");
        } else if(s.equals("tabs")) {
            VerticalTabItemLayout tab=new VerticalTabItemLayout();GradientDrawable bg=new GradientDrawable();bg.radius=3;tab.background=new InsetDrawable(bg);PropertyModel m=new PropertyModel();m.selected=true;
            updateRegularColors(m,tab);check(bg.radius==14,"native tab shape needs14px rounded corners");check(tab.title.size==21,"14sp must respect1.5 font scale");
            ArcDesktopAppearance.desktop=false;updateRegularColors(m,tab);check(bg.radius==3&&tab.title.size==16,"MOBILE native radius/text size restore exactly");
        } else if(s.equals("hover")) {
            VerticalTabItemLayout tab=new VerticalTabItemLayout();GradientDrawable shape=new GradientDrawable();shape.radius=3;tab.background=shape;PropertyModel m=new PropertyModel();
            updateRegularColors(m,tab);ColorStateList original=ColorStateList.valueOf(0);tab.tint=original;
            applyHoverBackgroundState(m,tab,true,original);check(tab.tint.color==ArcDesktopAppearance.interaction(tab.getContext(),false),"Arc hover uses softer theme derived tint");
            applyHoverBackgroundState(m,tab,false,original);check(tab.tint==original,"hover exit restores native default tint");
            m.selected=true;tab.tint=ColorStateList.valueOf(42);applyHoverBackgroundState(m,tab,true,original);check(tab.tint.color==42,"selected tab retains its active color on hover");
            ArcDesktopAppearance.desktop=false;m.selected=false;applyHoverBackgroundState(m,tab,true,original);check(tab.tint.color==18,"MOBILE retains native hover tint");
            m.multi=true;applyHoverBackgroundState(m,tab,true,original);check(tab.tint.color==19,"native multiselected hover remains distinct");
        } else if(s.equals("newtab")) {
            VerticalTabRailLayout rail=new VerticalTabRailLayout();updateIncognitoColors(rail,false);
            check(rail.mNewTabButton.lp.height>=48&&rail.mNewTabButton.getMinimumHeight()>=48,"deemphasis cannot shrink native48dp hit target");
            check(rail.mNewTabButton.tint!=null&&rail.mNewTabButton.tint.color==0,"native plus must not paint a prominent flat pill by default");
            check(rail.mNewTabButton.tint.interaction==ArcDesktopAppearance.interaction(rail.getContext(),false),"native plus hover/press/focus uses soft control surface");
            check(rail.mNewTabButton.imageAlpha<255,"plus icon should have lower prominence");check(rail.mNewTabButton.scale==ImageView.ScaleType.CENTER_INSIDE,"small icon stays within native button");
            ArcDesktopAppearance.desktop=false;rail.updateFooterLayout();check(rail.mNewTabButton.lp.height==40&&rail.mNewTabButton.minHeight==0&&rail.mNewTabButton.imageAlpha==255&&rail.mNewTabButton.scale==ImageView.ScaleType.FIT_CENTER,"MOBILE restores upstream button geometry and rendering");
        }
        System.out.println("PASS "+s);
    }
}
'''


class ArcAppearanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='arc-appearance-');cls.addClassCleanup(cls.temp.cleanup);cls.work=Path(cls.temp.name)
        app=APPEARANCE.read_text();rail=(NATIVE/'VerticalTabRailLayout.java').read_text();tab=(NATIVE/'TabVerticalViewBinder.java').read_text();binder=(NATIVE/'VerticalTabListViewBinder.java').read_text()
        def methods(text,signatures,optional=False):
            if not optional:
                for sig in signatures:
                    if sig not in text:raise AssertionError("Existing production method missing: "+sig)
            return '\n'.join(sig+' '+(method_body(text,re.escape(sig)) if sig in text else ('{return null;}' if 'Drawable ' in sig else '{return false;}' if ' boolean ' in sig else '{return 0;}' if ' int ' in sig else '{}')) for sig in signatures)
        appearance=methods(app,[
            'public static void applySidebarBackground(View view, boolean incognito)',
            'public static void applyTabTextSize(TextView title)',
            'public static void applyTabCorners(View view)',
            'public static ColorStateList newTabBackgroundTint(Context context, boolean incognito)',
            'public static Drawable controlBackground(Context context, boolean incognito, float radiusDp)',
            'public static Drawable favoriteBackground(Context context, boolean incognito, float radiusDp)',
            'private static GradientDrawable controlShape(Context context, int color, float radiusDp)',
            'public static int rowTextColor(Context context, boolean selected, boolean incognito)',
        ],optional=True)
        state=method_body(app,re.escape('private static final class SidebarBackground')) if 'private static final class SidebarBackground' in app else '{}'
        rails=methods(rail,[
            'public void setArcTransparentBackground(boolean active)',
            'private void updateArcNewTabAppearance()',
            'void updateFooterLayout()',
        ],optional=True)
        binders=methods(tab,['private static boolean isIncognito(PropertyModel model)',
            'private static boolean isIncognito(PropertyModel model, Context context)',
            'private static ColorStateList getBackgroundTintList(\n            Context context, boolean isSelected, boolean isMultiSelected, boolean isIncognito)',
            'private static @ColorInt int getTextColor(\n            Context context, boolean isSelected, boolean isIncognito)',
            'private static void updateRegularColors(PropertyModel model, VerticalTabItemLayout view)',
            'private static void applyHoverBackgroundState(\n            PropertyModel model,\n            ViewGroup view,\n            boolean isHovered,\n            @Nullable ColorStateList defaultBackgroundColor)'])+'\n'+methods(binder,['private static void updateIncognitoColors(VerticalTabRailLayout view, boolean isIncognito)'])
        palette=method_body(binder,re.escape('private static final class NativePalette')) if 'private static final class NativePalette' in binder else '{}'
        java=JAVA.replace('NATIVE_PALETTE',palette).replace('SIDEBAR_STATE',state).replace('APPEARANCE_HELPERS',appearance).replace('RAIL_HELPERS',rails).replace('BINDER_HELPERS',binders)
        java=java.replace('@Nullable ','').replace('@ColorInt ','')
        # Static imports resolve helpers in the nested native Appearance service.
        java=java.replace('ArcDesktopPolicy.ARC_TAB_TEXT_SIZE_SP','14f')
        p=cls.work/'AppearanceProbe.java';p.write_text(java)
        home=Path(os.environ.get('JAVA_HOME','/usr/lib/jvm/java-17-openjdk-arm64'));cls.java=str(home/'bin/java');cls.javac=str(home/'bin/javac')
        cp=str(window_core_jar());cls.cp=str(cls.work)+':'+cp
        window=list((ROOT/'chromium').rglob('ArchiumWindowClass.java'))
        result=subprocess.run([cls.javac,'--release','17','-cp',cp,'-d',str(cls.work),str(POLICY),*map(str,window),str(p)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)

    def probe(self,scenario):
        r=subprocess.run([self.java,'-ea','-cp',self.cp,'AppearanceProbe',scenario],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_policy_gradient_contrast_selection_and_density_radius(self):self.probe('policy')
    def test_native_controls_are_transparent_at_rest_and_interactive(self):self.probe('controls')
    def test_continuous_cached_sidebar_background_and_native_mobile_restore(self):self.probe('gradient')
    def test_native_active_and_multiselection_colors_remain_distinct(self):self.probe('palette')
    def test_native_regular_tab_radius_and_accessible_text_restore(self):self.probe('tabs')
    def test_native_hover_keeps_unselected_selected_and_multiselected_states(self):self.probe('hover')
    def test_native_new_tab_has_smaller_icon_and_48dp_hit_target(self):self.probe('newtab')

    def test_complete_appearance_and_native_helpers_compile_against_android37(self):
        jar=Path(os.environ.get('ANDROID_HOME','/opt/android-sdk'))/'platforms/android-37.0/android.jar'
        if not jar.exists():self.skipTest('Android37 API jar unavailable')
        metric=self.work/'ArchiumWindowMetrics.java'
        metric.write_text('''package org.chromium.chrome.browser.desktop_policy;
import android.content.Context;
public class ArchiumWindowMetrics {public static int currentWidthDp(Context c){return 1000;}}
''')
        rail=(NATIVE/'VerticalTabRailLayout.java').read_text()
        # Compile the shipped declarations, including TYPE_USE-only Nullable:
        # synthetic unannotated fields cannot detect invalid nested-type syntax.
        fields='\n'.join(re.findall(r'^    private [^\n]+ mArc[^\n]+;',rail,re.MULTILINE))
        nullable=self.work/'org/chromium/build/annotations/Nullable.java'
        nullable.parent.mkdir(parents=True,exist_ok=True)
        nullable.write_text('''package org.chromium.build.annotations;
import java.lang.annotation.ElementType;
import java.lang.annotation.Target;
@Target(ElementType.TYPE_USE) public @interface Nullable {}
''')
        helpers='\n'.join(sig+' '+method_body(rail,re.escape(sig)) for sig in [
            'public void setArcTransparentBackground(boolean active)',
            'private void updateArcNewTabAppearance()',
        ])
        program='''
import android.content.Context;
import android.view.View;
import android.graphics.drawable.Drawable;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import org.chromium.build.annotations.Nullable;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopAppearance;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class AppearanceAndroidApiProbe extends View {
    AppearanceAndroidApiProbe(Context c){super(c);}
    FIELDS
    ImageButton mNewTabButton;
    HELPERS
}
'''.replace('HELPERS',helpers).replace('FIELDS',fields)
        p=self.work/'AppearanceAndroidApiProbe.java';p.write_text(program)
        cp=str(jar)+':'+str(window_core_jar())+':'+str(self.work)
        result=subprocess.run([self.javac,'--release','17','-cp',cp,'-d',str(self.work),str(nullable),str(metric),str(APPEARANCE),str(p)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
