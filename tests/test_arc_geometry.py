"""Execute the real pure Java geometry policy with pinned AndroidX constants."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import window_core_jar

ROOT = Path(__file__).resolve().parents[1]

class ArcGeometryTest(unittest.TestCase):
    def test_native_allocator_preserves_mobile_collapse_and_manual_resize(self):
        from arc_toolbar_probe import method_body
        rel = "chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabsSideUiCoordinator.java"
        path = ROOT / ".source-modified" / rel
        if not path.exists():
            path = ROOT / ".source-reference" / rel
        body = method_body(path.read_text(), r"private @Px int calculateRenderedWidthPx\(").replace("@Px", "")
        program = r"""
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class NativeRailGeometry {
    static class Metrics { float density=1f; }
    static class Resources { Metrics getDisplayMetrics(){return new Metrics();} }
    static class Context { Resources getResources(){return new Resources();} }
    static class View { Context getContext(){return new Context();} }
    static class RailCollapseState { static final int COLLAPSED=0, EXPANDED_FOR_HOVERING=1, EXPANDED=2; }
    static class WindowWidthBoundary { static final int DYNAMIC_EXPANDABLE=2, FULLY_EXPANDABLE=3; }
    static class ArcDesktopAppearance { static boolean arc=true; static boolean isDesktopWindow(Context c){return arc;} }
    static class VerticalTabUtils {
        static final float EXPANDED_WINDOW_WIDTH_RATIO=.33f;
        static boolean manual; static int saved;
        static boolean isManualResizeEnabled(){return manual;}
        static int getUserResizedWidthDp(){return saved;}
    }
    static class ViewUtils { static int dpToPx(Context c,int v){return v;} }
    static class MathUtils { static int clamp(int v,int lo,int hi){return Math.max(lo,Math.min(hi,v));} }
    final View mRootView=new View(); int mExpandedViewWidth=240,mCollapsedViewWidth=52;
    int mMinManualWidth=92,mMaxManualWidth=500,mLiveResizeWidth;
    private int calculateRenderedWidthPx(int boundary,int effectiveState,int windowWidthPx,int availableWidthPx) BODY
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    public static void main(String[]args){
        NativeRailGeometry r=new NativeRailGeometry();
        check(r.calculateRenderedWidthPx(3,2,1382,1062)==334,"native Arc allocator must reserve334px at reference width");
        check(r.calculateRenderedWidthPx(3,0,1382,1062)==52,"collapse reserves52px");
        ArcDesktopAppearance.arc=false;
        check(r.calculateRenderedWidthPx(3,2,1382,1062)==240,"MOBILE native width must remain240");
        ArcDesktopAppearance.arc=true; VerticalTabUtils.manual=true; VerticalTabUtils.saved=400;
        check(r.calculateRenderedWidthPx(3,2,1382,1062)==400,"native manual resize remains authoritative");
        check(r.calculateRenderedWidthPx(3,1,1382,1062)==240,"hover does not change reserved-width contract");
        System.out.println("PASS native allocator");
    }
}
""".replace("BODY",body)
        with tempfile.TemporaryDirectory(prefix="archium-native-geometry-") as tmp:
            source=Path(tmp)/"NativeRailGeometry.java"
            source.write_text(program)
            jar=window_core_jar()
            sources=list((ROOT/"chromium").rglob("ArcDesktopPolicy.java"))+list((ROOT/"chromium").rglob("ArchiumWindowClass.java"))
            compiled=subprocess.run(["javac","--release","17","-cp",str(jar),"-d",tmp,*map(str,sources),str(source)],text=True,capture_output=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run(["java","-ea","-cp",tmp+":"+str(jar),"NativeRailGeometry"],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_short_native_rail_keeps_actual_tab_area(self):
        from arc_toolbar_probe import method_body
        import re
        rel="chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabRailLayout.java"
        source=(ROOT/".source-modified"/rel).read_text()
        signature="public void setArcAvailableTabHeight(int heightPx, boolean active)"
        self.assertIn("setArcAvailableTabHeight(",source,"native rail must release secondary chrome before tab list reaches zero")
        body=method_body(source,re.escape(signature))
        java=r"""
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class NativeTabBudget {
    static class View {static final int VISIBLE=0,GONE=8;int visibility;int getVisibility(){return visibility;}void setVisibility(int v){visibility=v;} }
    static class Metrics {float density=1f;}
    static class Resources {Metrics getDisplayMetrics(){return new Metrics();}}
    View mHeaderContainer=new View(),mFooterContainer=new View();
    boolean mArcCompactChrome;int mArcOriginalHeaderVisibility,mArcOriginalFooterVisibility;
    Resources getResources(){return new Resources();}
    public void setArcAvailableTabHeight(int heightPx, boolean active) BODY
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args){
        NativeTabBudget r=new NativeTabBudget();r.setArcAvailableTabHeight(48,true);
        check(r.mHeaderContainer.visibility==8&&r.mFooterContainer.visibility==8,"48px tab allocation must not be consumed by search/new-tab chrome");
        r.setArcAvailableTabHeight(110,true);check(r.mHeaderContainer.visibility==8&&r.mFooterContainer.visibility==0,"short native rail hides search before new-tab controls");
        r.setArcAvailableTabHeight(500,true);check(r.mHeaderContainer.visibility==0&&r.mFooterContainer.visibility==0,"expansion restores native chrome");
        r.setArcAvailableTabHeight(48,true);r.setArcAvailableTabHeight(48,false);
        check(r.mHeaderContainer.visibility==0&&r.mFooterContainer.visibility==0,"MOBILE restores original native chrome");
    }
}
""".replace("BODY",body)
        with tempfile.TemporaryDirectory(prefix="arc-native-budget-") as tmp:
            p=Path(tmp)/"NativeTabBudget.java";p.write_text(java)
            jar=window_core_jar()
            sources=list((ROOT/"chromium").rglob("ArcDesktopPolicy.java"))+list((ROOT/"chromium").rglob("ArchiumWindowClass.java"))
            compiled=subprocess.run(["javac","--release","17","-cp",str(jar),"-d",tmp,*map(str,sources),str(p)],text=True,capture_output=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run(["java","-ea","-cp",tmp+":"+str(jar),"NativeTabBudget"],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_real_favorites_receive_reference_tile_geometry(self):
        from arc_toolbar_probe import method_body
        import re
        source=(ROOT/"chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsView.java").read_text()
        signature="public void applyGeometry(ArcDesktopPolicy.Geometry geometry, int availableWidthPx)"
        self.assertTrue("public void applyGeometry(" in source,"native favorite controls need shared reference sizing")
        body=method_body(source,re.escape(signature))
        java=r"""
import java.util.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class FavoritesGeometry {
    static class LayoutParams {int width,height,left,right;LayoutParams(){width=52;height=48;}int getMarginStart(){return left;}int getMarginEnd(){return right;}void setMarginStart(int v){left=v;}void setMarginEnd(int v){right=v;}}
    static class View {LayoutParams params=new LayoutParams();LayoutParams getLayoutParams(){return params;}void setLayoutParams(LayoutParams p){params=p;}void setPadding(int l,int t,int r,int b){}}
    static class LinearLayout extends View {List<View> children=new ArrayList<>();int getChildCount(){return children.size();}View getChildAt(int i){return children.get(i);}}
    View mFavoritesScroll=new View();LinearLayout mFavorites=new LinearLayout();ArcDesktopPolicy.Geometry mGeometry;
    void setPadding(int l,int t,int r,int b){}
    public void applyGeometry(ArcDesktopPolicy.Geometry geometry, int availableWidthPx) BODY
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[]args){FavoritesGeometry r=new FavoritesGeometry();for(int i=0;i<3;i++)r.mFavorites.children.add(new View());
        r.applyGeometry(ArcDesktopPolicy.geometry(1382,863,334,1f,false),316);
        int[] widths={99,100,100},gaps={9,8,0};
        for(int i=0;i<3;i++){LayoutParams p=r.mFavorites.children.get(i).params;check(p.width==widths[i]&&p.height==57&&p.right==gaps[i],"favorite tile dimensions/gaps differ from reference at index"+i);}
        check(r.mFavoritesScroll.params.height==57,"native favorites row must share57px height");
    }
}
""".replace("BODY",body)
        with tempfile.TemporaryDirectory(prefix="arc-favorites-geometry-") as tmp:
            p=Path(tmp)/"FavoritesGeometry.java";p.write_text(java)
            jar=window_core_jar()
            sources=list((ROOT/"chromium").rglob("ArcDesktopPolicy.java"))+list((ROOT/"chromium").rglob("ArchiumWindowClass.java"))
            compiled=subprocess.run(["javac","--release","17","-cp",str(jar),"-d",tmp,*map(str,sources),str(p)],text=True,capture_output=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run(["java","-ea","-cp",tmp+":"+str(jar),"FavoritesGeometry"],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_native_row_height_and_mobile_restore(self):
        from arc_toolbar_probe import method_body
        source=(ROOT/".source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java").read_text()
        body=method_body(source,r"private static void updateTabItemSize\(").replace("@RailCollapseState ","")
        java=r"""
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class NativeRowGeometry {
    static class Metrics {float density=1f;} static class Resources {Metrics getDisplayMetrics(){return new Metrics();}}
    static class Context {Resources getResources(){return new Resources();}}
    static class View {int getWidth(){return 1382;}int getHeight(){return 863;}}
    static class ViewGroup extends View {static class LayoutParams {int width,height;}LayoutParams p=new LayoutParams();Context getContext(){return new Context();}View getRootView(){return new View();}LayoutParams getLayoutParams(){return p;}void setLayoutParams(LayoutParams n){p=n;}}
    static class PropertyModel {int state;int get(int key){return state;}}
    static class TabProperties {static final int RAIL_COLLAPSE_STATE=0;}
    static class RailCollapseState {static final int COLLAPSED=0,EXPANDED=2;}
    static class VerticalTabRailCollapseController {static boolean shouldUseCollapsedPositioning(int s){return s==0;}}
    static class ArcDesktopAppearance {static boolean active=true;static boolean isDesktopWindow(Context c){return active;}}
    static int getCollapsedTabItemWidth(Context c){return 44;}static int getCollapsedTabItemHeight(Context c){return 44;}
    private static void updateTabItemSize(PropertyModel model,ViewGroup view,int expandedWidth,int expandedHeight) BODY
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args){PropertyModel p=new PropertyModel();p.state=2;ViewGroup v=new ViewGroup();
        updateTabItemSize(p,v,316,48);check(v.p.height==49&&v.p.width==316,"native selected tab should use49px reference row");
        p.state=0;updateTabItemSize(p,v,316,48);check(v.p.height==44&&v.p.width==44,"collapsed icon row preserves native sizing");
        p.state=2;ArcDesktopAppearance.active=false;updateTabItemSize(p,v,316,48);check(v.p.height==48,"MOBILE preserves upstream expandedHeight");
    }
}
""".replace("BODY",body)
        with tempfile.TemporaryDirectory(prefix="arc-native-row-") as tmp:
            p=Path(tmp)/"NativeRowGeometry.java";p.write_text(java)
            jar=window_core_jar()
            sources=list((ROOT/"chromium").rglob("ArcDesktopPolicy.java"))+list((ROOT/"chromium").rglob("ArchiumWindowClass.java"))
            compiled=subprocess.run(["javac","--release","17","-cp",str(jar),"-d",tmp,*map(str,sources),str(p)],text=True,capture_output=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run(["java","-ea","-cp",tmp+":"+str(jar),"NativeRowGeometry"],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_reference_and_responsive_geometry(self):
        jar = window_core_jar()
        sources = list((ROOT / "chromium").rglob("ArcDesktopPolicy.java"))
        sources += list((ROOT / "chromium").rglob("ArchiumWindowClass.java"))
        with tempfile.TemporaryDirectory(prefix="archium-geometry-java-") as tmp:
            compiled = subprocess.run(["javac", "--release", "17", "-cp", str(jar), "-d", tmp,
                *map(str,sources), str(ROOT / "tests/java/ArcDesktopGeometryTest.java")], text=True,capture_output=True)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            result = subprocess.run(["java","-ea","-cp",tmp+":"+str(jar),"ArcDesktopGeometryTest"],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn("PASS Arc geometry",result.stdout)

if __name__ == "__main__":
    unittest.main()
