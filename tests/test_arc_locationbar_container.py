"""Run actual tablet focus/width method bodies with bounded Java view doubles.

This catches the sibling-host ViewRootImpl cast at LocationBarTablet's boundary;
framework layout, compositor drawing and the real IME require device validation.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body

LOCATION = 'chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarTablet.java'
# Exact body from Chromium cfd94726b7b5fb48aedcc32662f2f3fbdbadec35 ViewUtils.
# Keep the original ancestor precondition/cast to reproduce the actual failure;
# do not silently harden this test dependency and mask a bad container selection.
RELATIVE_LAYOUT_POSITION = r"""{
        assert outPosition.length == 2;
        outPosition[0] = 0;
        outPosition[1] = 0;
        if (rootView == null || childView == rootView) return;
        while (childView != null) {
            outPosition[0] += childView.getLeft();
            outPosition[1] += childView.getTop();
            if (childView.getParent() == rootView) break;
            childView = (View) childView.getParent();
        }
    }"""

JAVA = r'''
import java.util.function.BooleanSupplier;
class LocationBarContainerProbe {
    interface ViewParent {}
    static class ViewRootImpl implements ViewParent {}
    static class View implements ViewParent {
        static final int NO_ID=-1, LAYOUT_DIRECTION_RTL=1;
        ViewParent parent; int left,top,width=334,height=56,scrollX,scrollY,direction,mutations;
        int paddingLeft,paddingTop,paddingRight,paddingBottom;
        Object params=new LinearLayout.LayoutParams();float z;
        ViewParent getParent(){return parent;}int getLeft(){return left;}int getTop(){return top;}
        int getWidth(){return width;}int getMeasuredWidth(){return width;}
        int getScrollX(){return scrollX;}int getScrollY(){return scrollY;}
        int getPaddingLeft(){return paddingLeft;}int getPaddingRight(){return paddingRight;}
        int getPaddingTop(){return paddingTop;}int getPaddingBottom(){return paddingBottom;}
        int getLayoutDirection(){return direction;}
        View getRootView(){View v=this;while(v.parent instanceof View)v=(View)v.parent;return v;}
        Object getLayoutParams(){return params;}void setLayoutParams(Object p){params=p;mutations++;}
        void setPadding(int l,int t,int r,int b){paddingLeft=l;paddingTop=t;paddingRight=r;paddingBottom=b;mutations++;}
        void setTranslationZ(float v){z=v;mutations++;}void setOutlineProvider(Object o){mutations++;}
        void setBackground(Object o){mutations++;}
    }
    static class MarginLayoutParams {
        int leftMargin,rightMargin,topMargin,height,gravity;
        int start=Integer.MIN_VALUE,end=Integer.MIN_VALUE;
        int getMarginStart(){return start==Integer.MIN_VALUE?leftMargin:start;}
        int getMarginEnd(){return end==Integer.MIN_VALUE?rightMargin:end;}
        void setMarginStart(int v){start=v;}void setMarginEnd(int v){end=v;}
    }
    static class ViewGroup extends View { static class LayoutParams {static final int WRAP_CONTENT=-2;} }
    static class FrameLayout {static class LayoutParams extends MarginLayoutParams {}}
    static class LinearLayout {static class LayoutParams extends MarginLayoutParams {}}
    static class ScrollView extends ViewGroup {}
    static class Gravity {static final int TOP=48,CENTER_VERTICAL=16;}
    static class FuseboxLayoutMode {static final int SUGGESTIONS_POPOVER=1;}
    static class FuseboxState {static final int COMPACT=1,EXPANDED=2;}
    static class DeviceFormFactor {static final int MINIMUM_TABLET_WIDTH_DP=600;}
    static class WindowAndroid {Object getDisplay(){return null;}}
    static class DisplayUtil {static int dpToPx(Object d,int n){return n;}}
    static class Config {int screenWidthDp=1000;}
    static class Metrics {int widthPixels=1000;}
    static class Resources {
        final Config config=new Config();Config getConfiguration(){return config;}
        Metrics getDisplayMetrics(){return new Metrics();}
        int getDimensionPixelSize(int id){return id==R.dimen.fusebox_min_tablet_width?500:56;}
    }
    static class HostGeometry {int omniboxHeight;}
    static class R {static class dimen {
        static final int fusebox_min_tablet_width=1,modern_toolbar_tablet_background_size=2,
        location_bar_tablet_fusebox_popover_top_padding=3;
    }}
    static class ViewUtils {
        static void getRelativeLayoutPosition(View rootView,View childView,int[] outPosition) RELATIVE
        static void setAncestorsShouldClipToPadding(View v,boolean b,int id){}
        static void setAncestorsShouldClipChildren(View v,boolean b,int id){}
    }
    static class Tablet extends View {
        private View mHolder;private View mContainerView;
        private BooleanSupplier mIsFullWidthExpansionAllowedSupplier;
        int mLayoutMode,mFuseboxState=FuseboxState.COMPACT;boolean mShowFocusRing,mIsReparentedToPopover,mIsGlifActive;
        int mTargetPopoverWidth,mTargetPopoverLeftOffset,mMinWidthForExpandedActivationChip=400;
        final int[] mPositionArray=new int[2];final Resources resources=new Resources();
        final WindowAndroid mWindowAndroid=new WindowAndroid();
        final int mLocationBarTabletFuseboxPopupInset=6,mPopoverAdditionalWidth=16;
        static final int CENTERING_THRESHOLD_DP=16;
        static final float OVERLAY_Z_TRANSLATION=1,NEUTRAL_Z_TRANSLATION=0;
        Object mOutlineProvider,mFocusedPopupDrawable,mLocationBarBackground;
        EXTRA_FIELDS
        Resources getResources(){return resources;}
        void adjustVerticalTranslationForFuseboxState(int state){}
        void updatePopoverAlignmentMargins(){}void updateForegroundAndGlifAnimation(){}
        void adjustBackgroundForSuggestions(){}
        METHODS
        // Execute the actual Arc host setter around the actual native focus methods.
        void applyRootHostGeometry(int height,int side) {
            View mLocationBarHost=mHolder;HostGeometry g=new HostGeometry();g.omniboxHeight=height;
            ROOT_HOST_BODY
        }
    }
    static class Fixture {
        final View root=new View(),toolbar=new View(),nativeRow=new View(),header=new View();
        final ScrollView viewport=new ScrollView();final ViewGroup holder=new ViewGroup();
        final Tablet bar=new Tablet();final LinearLayout.LayoutParams margins=new LinearLayout.LayoutParams();
        Fixture(){root.parent=new ViewRootImpl();root.width=1000;
            toolbar.parent=root;toolbar.width=800;nativeRow.parent=toolbar;nativeRow.top=12;
            viewport.parent=root;viewport.width=334;header.parent=viewport;header.width=334;
            holder.parent=nativeRow;holder.left=100;holder.top=8;holder.width=600;holder.params=margins;
            bar.parent=holder;bar.params=new FrameLayout.LayoutParams();bar.setHolderAndContainer(holder,toolbar);
        }
        void arc(){holder.parent=header;holder.left=11;holder.top=54;holder.width=312;}
    }
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    public static void main(String[]args){Fixture f=new Fixture();String s=args[0];
        if(s.equals("native")) {
            f.bar.updateLayoutAndBackground();
            check(f.margins.topMargin==-6,"native headroom path");
            check(f.margins.leftMargin==-6&&f.margins.rightMargin==-6,"native expansion margins");
            check(f.bar.getAvailableContainerWidth()==800,"native activation-chip width");
            f.bar.mFuseboxState=0;f.bar.updateLayoutAndBackground();
            check(f.margins.leftMargin==0&&f.margins.topMargin==0&&f.holder.z==0,"native collapse restored");
        } else if(s.equals("nullcontainer")) {
            f.bar.setHolderAndContainer(f.holder,null);f.bar.updateLayoutAndBackground();
            check(f.margins.topMargin==-6,"unspecified native container keeps inset headroom");
            check(f.margins.leftMargin==-6&&f.margins.rightMargin==-6,"native root/window width path");
            check(f.bar.getAvailableContainerWidth()==1000,"unspecified container retains display fallback");
        } else if(s.equals("detached")) {
            f.arc();f.holder.parent=null;f.bar.updateLayoutAndBackground();
            check(f.holder.mutations==0&&f.bar.mutations==0,"detached focus callback cannot mutate geometry");
            f.holder.parent=new ViewRootImpl();f.bar.updateLayoutAndBackground();
            check(f.holder.mutations==0&&f.bar.mutations==0,"non-View root boundary is safe");
        } else {
            f.arc();
            if(s.equals("width")) {check(f.bar.getAvailableContainerWidth()==334,"sidebar width replaces cached800px toolbar");}
            else if(s.equals("headroom")) {
                f.bar.updateLayoutAndBackground();check(f.margins.topMargin==-6,"54px visible sidebar headroom permits6px expansion");
                // Simulate the completed Android layout after topMargin=-6.
                f.holder.top=48;f.viewport.scrollY=51;f.bar.updateLayoutAndBackground();
                check(f.margins.topMargin==-3,"scroll leaves only3px unexpanded headroom");
                f.holder.top=51;f.viewport.scrollY=70;f.bar.updateLayoutAndBackground();
                check(f.margins.topMargin==0,"negative visible headroom cannot expand above viewport");
            } else if(s.equals("mobile")) {
                f.bar.updateLayoutAndBackground();
                f.holder.parent=f.nativeRow;f.holder.left=100;f.holder.top=8;f.holder.width=600;
                f.margins.leftMargin=f.margins.rightMargin=f.margins.topMargin=0;
                f.bar.updateLayoutAndBackground();
                check(f.margins.leftMargin==-6&&f.margins.rightMargin==-6&&f.margins.topMargin==-6,"MOBILE uses cached toolbar again");
                check(f.bar.getAvailableContainerWidth()==800,"MOBILE width restored");
            } else if(s.equals("relative")) {
                for(int direction:new int[]{0,1}) {
                    f.holder.direction=direction;f.holder.left=9;f.holder.width=316;
                    f.margins.leftMargin=f.margins.rightMargin=9;
                    f.margins.setMarginStart(9);f.margins.setMarginEnd(9);
                    f.bar.updateLayoutAndBackground();
                    check(f.margins.getMarginStart()==0&&f.margins.getMarginEnd()==0,
                            "relative9px margins must not override focused viewport width334px");
                    f.bar.mFuseboxState=0;f.bar.updateLayoutAndBackground();
                    check(f.margins.getMarginStart()==9&&f.margins.getMarginEnd()==9,
                            "unfocus restores Arc9px baseline relative inset");
                    f.bar.mFuseboxState=FuseboxState.COMPACT;
                }
            } else if(s.equals("rootfocus")) {
                f.holder.left=9;f.holder.width=316;
                f.margins.leftMargin=f.margins.rightMargin=9;
                f.margins.setMarginStart(9);f.margins.setMarginEnd(9);
                f.bar.updateLayoutAndBackground();
                f.bar.applyRootHostGeometry(40,9);
                check(f.margins.height==ViewGroup.LayoutParams.WRAP_CONTENT,
                        "header geometry callback cannot replace native expanded omnibox height");
                check(f.margins.getMarginStart()==0&&f.margins.getMarginEnd()==0,
                        "header geometry callback cannot overwrite native focus expansion");
            } else if(s.equals("rootbaseline")) {
                f.holder.left=9;f.holder.width=316;
                f.margins.leftMargin=f.margins.rightMargin=9;
                f.margins.setMarginStart(9);f.margins.setMarginEnd(9);
                f.bar.updateLayoutAndBackground();
                f.bar.applyRootHostGeometry(48,5);
                check(f.margins.height==ViewGroup.LayoutParams.WRAP_CONTENT
                                &&f.margins.getMarginStart()==0,
                        "focused resize keeps native expanded geometry until unfocus");
                f.bar.mFuseboxState=0;f.bar.updateLayoutAndBackground();
                f.bar.applyRootHostGeometry(48,5);
                check(f.margins.height==48&&f.margins.getMarginStart()==5&&f.margins.getMarginEnd()==5,
                        "unfocus header layout applies current5px baseline, not stale9px snapshot");
                // The next Android layout resolves the new baseline physical margins.
                f.margins.leftMargin=f.margins.rightMargin=5;f.holder.left=5;f.holder.width=324;
                f.bar.mFuseboxState=FuseboxState.COMPACT;f.bar.updateLayoutAndBackground();
                f.bar.mFuseboxState=0;f.bar.updateLayoutAndBackground();
                check(f.margins.getMarginStart()==5&&f.margins.getMarginEnd()==5,
                        "same LayoutParams captures refreshed baseline on the next focus");
            } else if(s.equals("baselinepopover")) {
                f.holder.left=9;f.holder.width=316;
                f.margins.leftMargin=f.margins.rightMargin=9;
                f.margins.setMarginStart(9);f.margins.setMarginEnd(9);
                f.bar.setMarginsForAvailableWidth(f.margins,16,true);
                check(f.bar.mTargetPopoverWidth==334&&f.bar.mTargetPopoverLeftOffset==-9,
                        "popover must offset from actual9px inset holder, not pretend it starts at0");
                check(f.margins.leftMargin==9&&f.margins.rightMargin==9,
                        "popover leaves existing baseline holder margins unchanged");
            } else if(s.equals("baselinewidth")) {
                f.viewport.width=800;f.header.width=800;f.holder.left=100;f.holder.width=600;
                f.margins.leftMargin=f.margins.rightMargin=9;
                f.margins.setMarginStart(9);f.margins.setMarginEnd(9);
                f.bar.setMarginsForAvailableWidth(f.margins,6,false);
                check(f.margins.leftMargin==3&&f.margins.rightMargin==3,
                        "600px holder expands12px by changing baseline9px margins to3px");
                f.holder.left=94;f.holder.width=612;
                f.bar.setMarginsForAvailableWidth(f.margins,6,false);
                check(f.margins.leftMargin==3&&f.margins.rightMargin==3,
                        "repeated expansion must keep the same baseline geometry");
            } else if(s.equals("mobileparams")) {
                f.holder.left=9;f.holder.width=316;
                f.margins.leftMargin=f.margins.rightMargin=9;
                f.margins.setMarginStart(9);f.margins.setMarginEnd(9);
                f.bar.updateLayoutAndBackground();
                // Arc restores the saved native LayoutParams object, not its temporary one.
                LinearLayout.LayoutParams nativeParams=new LinearLayout.LayoutParams();
                f.holder.params=nativeParams;f.holder.parent=f.nativeRow;
                f.holder.left=100;f.holder.top=8;f.holder.width=600;
                f.bar.mFuseboxState=0;f.bar.updateLayoutAndBackground();
                check(nativeParams.start==Integer.MIN_VALUE&&nativeParams.end==Integer.MIN_VALUE,
                        "MOBILE native LayoutParams must not acquire Arc logical inset");
                f.bar.mFuseboxState=FuseboxState.COMPACT;f.bar.updateLayoutAndBackground();
                check(nativeParams.leftMargin==-6&&nativeParams.rightMargin==-6,
                        "native re-focus expands using original toolbar bounds");
            } else if(s.equals("directhost")) {
                f.header.parent=f.root;f.header.width=240;f.holder.top=30;
                f.bar.updateLayoutAndBackground();
                check(f.margins.leftMargin==-11&&f.margins.rightMargin==83,
                        "fallback direct host clamps even oversized holder to240px");
                check(f.margins.topMargin==-6,"direct live host provides real headroom");
                check(f.bar.getAvailableContainerWidth()==240,"direct host width");
            } else if(s.equals("popover")) {
                f.bar.mLayoutMode=FuseboxLayoutMode.SUGGESTIONS_POPOVER;
                f.bar.setMarginsForAvailableWidth(f.margins,16,true);
                check(f.bar.mTargetPopoverWidth==334&&f.bar.mTargetPopoverLeftOffset==-11,"popover constrained to viewport");
                check(f.margins.leftMargin==0&&f.margins.rightMargin==0,"popover preserves native holder width");
            } else {
                for(int direction:new int[]{0,1}) {
                    f.holder.direction=direction;f.margins.leftMargin=f.margins.rightMargin=0;
                    f.viewport.paddingLeft=9;f.viewport.paddingRight=13;f.viewport.scrollX=7;
                    f.holder.left=20;f.holder.width=280;
                    f.bar.setMarginsForAvailableWidth(f.margins,6,false);
                    check(f.margins.leftMargin==-4&&f.margins.rightMargin==-28,"physical target [9,321] in312px padded scrolled viewport");
                    check(f.margins.getMarginStart()==(direction==1?-28:-4)
                            &&f.margins.getMarginEnd()==(direction==1?-4:-28),
                            "resolved RTL/LTR margins must preserve physical target bounds");
                }
            }
        }
        System.out.println("PASS "+s);
    }
}
'''


class ArcLocationBarContainerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(ROOT/'.source-modified'/LOCATION).read_text()
        signatures=[
            'public void setHolderAndContainer(ViewGroup holder, @Nullable View containerView)',
            'private void updateLayoutAndBackground()',
            'private void setMarginsForAvailableWidth(\n            MarginLayoutParams layoutParams, int minHorizontalExpansionPx, boolean isPopoverMode)',
            'private @Px int getAvailableContainerWidth()',
        ]
        # Include additional production helpers without inventing test implementations.
        for signature in ['private @Nullable View getExpansionContainerView()',
                          'private void getExpansionPosition(View containerView, View childView)',
                          'private void restoreReparentedHolderMargins(MarginLayoutParams layoutParams)']:
            if signature in source:signatures.append(signature)
        methods='\n'.join(sig+' '+method_body(source,re.escape(sig)) for sig in signatures)
        methods=methods.replace('@Nullable ','').replace('@Px ','')
        fields='\n'.join(re.findall(r'^    private (?:@Nullable )?(?:MarginLayoutParams mReparentedHolderParams|int mReparentedMarginStart|int mReparentedMarginEnd).*?;',source,re.M))
        fields=fields.replace('@Nullable ','')
        relative=RELATIVE_LAYOUT_POSITION
        cls.temp=tempfile.TemporaryDirectory(prefix='arc-locationbar-container-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work=Path(cls.temp.name)
        path=cls.work/'LocationBarContainerProbe.java'
        root_source=(ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java').read_text()
        if 'private void updateLocationBarGeometry(' in root_source:
            root_host_body=method_body(root_source,r'private void updateLocationBarGeometry\(')
        else:
            root_method=method_body(root_source,r'private void applySidebarGeometry\(\)')
            host_start=root_method.index('        LinearLayout.LayoutParams url =')
            host_end=root_method.index('        if (mCollectionsView != null)',host_start)
            root_host_body=root_method[host_start:host_end]
        path.write_text(JAVA.replace('METHODS',methods).replace('RELATIVE',relative)
                        .replace('EXTRA_FIELDS',fields).replace('ROOT_HOST_BODY',root_host_body))
        java_home=Path(os.environ.get('JAVA_HOME','/usr/lib/jvm/java-17-openjdk-arm64'))
        cls.java=str(java_home/'bin/java') if (java_home/'bin/java').exists() else shutil.which('java')
        javac=str(java_home/'bin/javac') if (java_home/'bin/javac').exists() else shutil.which('javac')
        result=subprocess.run([javac,'--release','17','-d',str(cls.work),str(path)],text=True,capture_output=True)
        if result.returncode:raise AssertionError(result.stderr)

    def probe(self,scenario):
        result=subprocess.run([self.java,'-ea','-cp',str(self.work),'LocationBarContainerProbe',scenario],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_native_focus_and_collapse_keep_original_geometry(self):self.probe('native')
    def test_unspecified_container_keeps_native_root_and_window_behavior(self):self.probe('nullcontainer')
    def test_arc_focus_headroom_tracks_visible_scrolled_holder(self):self.probe('headroom')
    def test_arc_expansion_respects_padding_scroll_and_physical_rtl_bounds(self):self.probe('bounds')
    def test_arc_popover_publishes_width_without_expanding_holder(self):self.probe('popover')
    def test_arc_activation_chip_uses_current_host_width(self):self.probe('width')
    def test_detached_queued_focus_callbacks_leave_geometry_untouched(self):self.probe('detached')
    def test_mobile_round_trip_restores_cached_native_container(self):self.probe('mobile')

    def test_arc_relative_inset_expands_and_restores_on_unfocus(self):self.probe('relative')

    def test_mobile_uses_saved_native_params_without_arc_relative_margins(self):self.probe('mobileparams')
    def test_reparented_host_without_scrollview_clamps_oversized_holder(self):self.probe('directhost')

    def test_container_helpers_compile_against_actual_android_view_api(self):
        android_jar=Path(os.environ.get('ANDROID_HOME','/opt/android-sdk'))/'platforms/android-37.0/android.jar'
        if not android_jar.exists():self.skipTest('Android37 API jar unavailable')
        source=(ROOT/'.source-modified'/LOCATION).read_text()
        helpers=[]
        for signature in ['private @Nullable View getExpansionContainerView()',
                          'private void getExpansionPosition(View containerView, View childView)',
                          'private void restoreReparentedHolderMargins(MarginLayoutParams layoutParams)']:
            if signature in source:helpers.append(signature+' '+method_body(source,re.escape(signature)))
        if not helpers:self.fail('No reparent-aware container implementation to compile')
        program = """
import android.content.Context;
import android.view.View;
import android.view.ViewGroup.MarginLayoutParams;
import android.widget.ScrollView;
class LocationBarAndroidApiProbe extends View {
    LocationBarAndroidApiProbe(Context context){super(context);}
    View mHolder,mContainerView;MarginLayoutParams mReparentedHolderParams;
    int mReparentedMarginStart,mReparentedMarginEnd;int[] mPositionArray=new int[2];
    HELPERS
}
""".replace('HELPERS','\n'.join(helpers).replace('@Nullable ',''))
        path=self.work/'LocationBarAndroidApiProbe.java';path.write_text(program)
        java_home=Path(os.environ.get('JAVA_HOME','/usr/lib/jvm/java-17-openjdk-arm64'))
        javac=str(java_home/'bin/javac') if (java_home/'bin/javac').exists() else shutil.which('javac')
        result=subprocess.run([javac,'--release','17','-cp',str(android_jar),'-d',str(self.work),str(path)],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_popover_alignment_accounts_for_arc_baseline_inset(self):self.probe('baselinepopover')
    def test_focus_expansion_undoes_only_expansion_delta_from_arc_inset(self):self.probe('baselinewidth')

    def test_header_geometry_callback_preserves_native_focus_expansion(self):self.probe('rootfocus')
    def test_same_params_resize_refreshes_baseline_after_unfocus(self):self.probe('rootbaseline')
