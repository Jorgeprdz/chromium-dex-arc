"""Execute shipped dropdown geometry; service doubles bound this to the alignment contract.

The Android companion probe supplies attached framework views and a real ViewRootImpl.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, dropdown_body, method_body, DROPDOWN

PREFIX = r'''
import java.util.function.Supplier;
import java.util.function.BooleanSupplier;
class ArcOmniboxResizeProbe {
    interface Parent {}
    static class WindowRoot implements Parent {}
    static class View implements Parent {
        static final int LAYOUT_DIRECTION_RTL=1;
        Parent parent; Object token; int left,top,width,height,direction,paddingLeft,paddingRight,scrollY;
        Parent getParent(){return parent;}
        View getRootView(){return this;} View findViewById(int id){return this;}
        int getLeft(){return left;} int getTop(){return top;}
        int getWidth(){return width;} int getHeight(){return height;}
        int getMeasuredWidth(){return width;} int getMeasuredHeight(){return height;}
        int getPaddingTop(){return 0;} int getPaddingLeft(){return paddingLeft;} int getPaddingRight(){return paddingRight;} int getLayoutDirection(){return direction;}
        Object getWindowToken(){return token;} Object getRootWindowInsets(){return null;}
        void getLocationInWindow(int[] result){
            result[0]=left;result[1]=top;
            Parent next=parent;
            while(next instanceof View){View view=(View)next;result[0]+=view.left;result[1]+=view.top-view.scrollY;next=view.parent;}
        }
    }
    static class Context { Resources getResources(){return new Resources();} }
    static class Resources { int getDimensionPixelSize(int id){return 48;} }
'''
MAIN = r'''
    static void check(boolean condition,String message){if(!condition)throw new AssertionError(message);}
    public static void main(String[] args) {
        Object token=new Object();
        View content=new View(),anchor=new View(),header=new View(),bar=new View();
        content.parent=new WindowRoot();content.token=token;content.width=800;content.height=900;
        anchor.parent=content;anchor.token=token;anchor.left=240;anchor.top=40;anchor.width=560;anchor.height=56;
        header.parent=content;header.token=token;header.top=40;header.width=240;header.height=860;
        bar.parent=header;bar.token=token;bar.left=10;bar.top=50;bar.width=220;bar.height=42;
        Dropdown dropdown=new Dropdown();dropdown.mBaseChromeLayout=content;dropdown.mAnchorView=anchor;
        dropdown.mAlignmentView=bar;dropdown.mContext=new Context();
        String scenario=args[0];
        if(scenario.equals("vertical") || scenario.equals("scroll")) {
            dropdown.onGlobalLayout();
            check(dropdown.mOmniboxAlignmentSupplier.value.top==132,"initial sidebar Y");
            int changes=dropdown.mOmniboxAlignmentSupplier.updates;
            dropdown.onGlobalLayout();
            check(dropdown.mOmniboxAlignmentSupplier.updates==changes,"unchanged layout is stable");
            if(scenario.equals("scroll")){header.scrollY=14;dropdown.onScrollChanged();}
            else {bar.top+=14;dropdown.onGlobalLayout();}
            check(dropdown.mOmniboxAlignmentSupplier.value.top==(scenario.equals("scroll")?118:146),
                    "sidebar Y must refresh independently of toolbar Y");
        } else if(scenario.equals("detached") || scenario.equals("foreign")) {
            bar.token=scenario.equals("detached")?null:new Object();
            dropdown.recalculateOmniboxAlignment();
            OmniboxAlignment empty=dropdown.mOmniboxAlignmentSupplier.value;
            check(empty.width==0 && empty.height==0 && empty.left==0 && empty.top==0,
                    "detached window must publish safe nonnegative dimensions");
            bar.token=token;
            dropdown.recalculateOmniboxAlignment();
            check(dropdown.mOmniboxAlignmentSupplier.value.width>0,
                    "valid after detach must restore live alignment");
        } else if(scenario.equals("descendant")) {
            bar.parent=anchor;bar.top=0;
            dropdown.recalculateOmniboxAlignment();OmniboxAlignment a=dropdown.mOmniboxAlignmentSupplier.value;
            check(a.left==10 && a.top==96 && a.width==220,"native geometry changed");
        } else {
            for(boolean phone:new boolean[]{true,false})for(int direction:new int[]{0,1})for(int i=0;i<30;i++) {
                dropdown.phone=phone;content.direction=direction;anchor.direction=direction;content.width=600+10*i;
                if(scenario.equals("overflow")){bar.left=content.width-70;bar.width=220;}
                else if(scenario.equals("padding")){content.paddingLeft=20;content.paddingRight=30;bar.left=10;bar.width=220;}
                else {content.paddingLeft=content.paddingRight=0;bar.left=10;bar.width=220;}
                if(scenario.equals("keyboard")){dropdown.mKeyboardHeightSupplier=()->800;}
                if(scenario.equals("bottom")){dropdown.mControlsPositionSupplier=()->ControlsPosition.BOTTOM;}
                dropdown.recalculateOmniboxAlignment();OmniboxAlignment a=dropdown.mOmniboxAlignmentSupplier.value;
                int natural=direction==View.LAYOUT_DIRECTION_RTL
                        ?content.width-content.paddingRight-a.width:content.paddingLeft;
                int physicalLeft=natural+a.left;
                check(a.top==132 && a.width>=0 && physicalLeft>=content.paddingLeft
                        && physicalLeft+a.width<=content.width-content.paddingRight,"resize bounds");
                if(scenario.equals("overflow"))check(a.width==70,"dropdown crosses right window edge");
                else if(scenario.equals("padding")) {
                    check(physicalLeft==20 && a.width==220,"RTL/LTR translate relative to content padding");
                } else check(physicalLeft==10 && a.width==220,"sidebar uses visible bar, not toolbar");
                if(scenario.equals("keyboard"))check(a.height==0,"negative remaining height");
                else check(a.height>0,"dropdown unavailable");
            }
        }
        System.out.println("PASS "+scenario);
    }
}
'''


class ArcOmniboxResizeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        template = (ROOT / 'tests/android/toolbar/ArcOmniboxResizeTest.java.in').read_text()
        services = template[template.index('    static class ControlsPosition'):template.index('    public static class ProbeActivity')]
        services = services.replace('android.R.dimen.app_icon_size', '1').replace('android.view.WindowInsets', 'Object')
        body = dropdown_body().replace('android.R.id.content', '1')
        production = (ROOT / '.source-modified' / DROPDOWN).read_text()
        def extra(name):
            import re
            signature = re.escape(name) + r'\(View view\)' if name != 'onGlobalLayout' else r'public void onGlobalLayout\(\)'
            signature = signature.replace(r'\(View view\)', r'\(View view\)')
            return method_body(production, signature)
        # Include the exact production observer and positional tracking bodies.
        functions = (
            'void onScrollChanged() ' + (method_body(production, r'onScrollChanged\(\)') if 'public void onScrollChanged()' in production else '{}') + '\n'
            'void onGlobalLayout() ' + extra('onGlobalLayout') + '\n'
            'boolean verticalOffsetInWindowChanged(View view) ' + extra('verticalOffsetInWindowChanged') + '\n'
            'boolean alignmentVerticalOffsetInWindowChanged(View view) ' + extra('alignmentVerticalOffsetInWindowChanged') + '\n'
            'boolean horizontalOffsetInWindowChanged(View view) ' + extra('horizontalOffsetInWindowChanged') + '\n'
            'boolean insetsHaveChanged(View view){return false;}\n'
        )
        adapted_services = services.replace('int[] mPositionArray=new int[2];',
                'int[] mPositionArray=new int[2]; int mVerticalOffsetInWindow; '
                'int mAlignmentVerticalOffsetInWindow; int mHorizontalOffsetInWindow;')
        adapted_services = adapted_services.replace('void recalculateOmniboxAlignment() __DROPDOWN_BODY__',
                'void recalculateOmniboxAlignment() __DROPDOWN_BODY__\n' + functions)
        adapted_services = adapted_services.replace(
                'OmniboxAlignment value; void set(OmniboxAlignment value){this.value=value;}',
                'OmniboxAlignment value; int updates; void set(OmniboxAlignment value){this.value=value; updates++;}')
        source = PREFIX + adapted_services.replace('__DROPDOWN_BODY__', body) + MAIN
        path = cls.work / 'ArcOmniboxResizeProbe.java'
        path.write_text(source)
        subprocess.run(['javac', '-d', str(cls.work), str(path)],check=True,capture_output=True,text=True)

    def probe(self, scenario):
        result = subprocess.run(['java','-ea','-cp',str(self.work),'ArcOmniboxResizeProbe',scenario],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('PASS '+scenario,result.stdout)

    def test_reparented_sidebar_handles_resize_phone_tablet_and_rtl(self): self.probe('resize')
    def test_dropdown_does_not_cross_right_window_edge(self): self.probe('overflow')
    def test_rtl_translation_with_parent_padding(self): self.probe('padding')
    def test_vertical_only_sidebar_reposition_triggers_alignment(self): self.probe('vertical')
    def test_scroll_without_layout_tracks_reparented_omnibox(self): self.probe("scroll")
    def test_keyboard_occlusion_never_produces_negative_height(self): self.probe('keyboard')
    def test_reparented_top_bar_ignores_hidden_bottom_toolbar(self): self.probe('bottom')
    def test_native_descendant_preserves_original_alignment(self): self.probe('descendant')
    def test_detached_and_foreign_windows_publish_no_alignment(self):
        for scenario in ['detached','foreign']:
            with self.subTest(scenario=scenario): self.probe(scenario)
