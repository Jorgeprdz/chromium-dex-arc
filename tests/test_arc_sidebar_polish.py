"""Run shipped layout methods; these view doubles do not establish device acceptance."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body, window_core_jar

COLLECTIONS = ROOT / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsView.java"
COORD = ROOT / "chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java"


class SidebarPolishTest(unittest.TestCase):
    def run_java(self, name, program):
        with tempfile.TemporaryDirectory(prefix="arc-polish-") as tmp:
            path = Path(tmp) / (name + ".java")
            path.write_text(program)
            policy = list((ROOT / "chromium").rglob("ArcDesktopPolicy.java"))
            window = list((ROOT / "chromium").rglob("ArchiumWindowClass.java"))
            cp = str(window_core_jar())
            result = subprocess.run(["javac", "--release", "17", "-cp", cp, "-d", tmp,
                                     *map(str, policy + window), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(["java", "-ea", "-cp", tmp + ":" + cp, name], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_favorites_and_space_section_gap(self):
        source = COLLECTIONS.read_text()
        body = method_body(source, re.escape("public void applyGeometry(ArcDesktopPolicy.Geometry geometry, int availableWidthPx)"))
        self.run_java("CollectionGeometry", r"""
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class CollectionGeometry {
    static class LayoutParams {int width, height, bottomMargin, end; int getMarginEnd(){return end;} void setMarginEnd(int n){end=n;}}
    static class View {static final int VISIBLE=0,GONE=8; LayoutParams p=new LayoutParams();int visibility;
        LayoutParams getLayoutParams(){return p;} void setLayoutParams(LayoutParams n){p=n;} void setVisibility(int n){visibility=n;}}
    static class Row extends View {java.util.List<View> children=new java.util.ArrayList<>();int getChildCount(){return children.size();}View getChildAt(int i){return children.get(i);}}
    Row mFavorites=new Row();View mFavoritesScroll=new View(),mSpace=new View();ArcDesktopPolicy.Geometry mGeometry;
    void setPadding(int l,int t,int r,int b){}
    public void applyGeometry(ArcDesktopPolicy.Geometry geometry,int availableWidthPx) BODY
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    public static void main(String[]args){CollectionGeometry r=new CollectionGeometry();var g=ArcDesktopPolicy.geometry(1382,863,334,1,false);
        r.applyGeometry(g,316);check(r.mFavoritesScroll.visibility==View.GONE,"empty favorites must not reserve a57px blank band");
        check(r.mSpace.p.bottomMargin==8,"Space and New Folder require8dp of separate section spacing");
        for(int i=0;i<3;i++)r.mFavorites.children.add(new View());r.applyGeometry(g,316);
        check(r.mFavoritesScroll.visibility==View.VISIBLE&&r.mFavoritesScroll.p.height==57,"real favorites retain reference height");
        check(r.mFavorites.getChildAt(0).p.width==99&&r.mFavorites.getChildAt(1).p.width==100&&r.mFavorites.getChildAt(2).p.width==100,"three favorite reference widths remain99/100/100");
        check(r.mFavoritesScroll.p.bottomMargin==8,"favorites and Spaces also need section spacing");
        r.mFavorites.children.clear();r.applyGeometry(ArcDesktopPolicy.geometry(2764,1726,668,2,true),632);
        check(r.mFavoritesScroll.visibility==View.GONE&&r.mSpace.p.bottomMargin==16,"empty state and gap update across density/RTL");
    }
}
""".replace("BODY", body))

    def test_disabled_passwords_do_not_create_autofill_footer(self):
        source = COORD.read_text()
        start = source.index("        mFooter = new LinearLayout(activity);")
        end = source.index("        // Preserve Chromium's native app menu", start)
        block = source[start:end]
        self.run_java("FooterActions", r"""
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class FooterActions {
    static class Activity{}
    static class Button {String text;Button(String s){text=s;}void setContentDescription(String s){}}
    static class LinearLayout {static class LayoutParams {LayoutParams(int w,int h,int weight){}} java.util.List<Button> children=new java.util.ArrayList<>();LinearLayout(Activity a){}void addView(Button b,LayoutParams p){children.add(b);}}
    LinearLayout mFooter;Button mPasswordButton;int dp(int n){return n;}Button button(String s,Runnable r){return new Button(s);}
    FooterActions(boolean localPasswordsEnabled){Activity activity=new Activity();Runnable openPasswordSettings=()->{};BLOCK}
    public static void main(String[]args){FooterActions disabled=new FooterActions(false);
        if(!disabled.mFooter.children.isEmpty())throw new AssertionError("arc-media must not add unrelated Autofill settings shortcut");
        FooterActions enabled=new FooterActions(true);if(enabled.mFooter.children.size()!=1||!enabled.mFooter.children.get(0).text.equals("Passwords"))throw new AssertionError("enabled local-password build retains its own action");
    }
}
""".replace("BLOCK", block))

    def test_native_expanded_omnibox_owns_holder_during_resize(self):
        source = COORD.read_text()
        signature = "private void updateLocationBarGeometry(ArcDesktopPolicy.Geometry g, int side)"
        if signature in source:
            body = method_body(source, re.escape(signature))
        else:
            start = source.index("        LinearLayout.LayoutParams url =")
            end = source.index("        if (mCollectionsView != null)", start)
            body = "{" + source[start:end] + "}"
        self.run_java("FocusedHolderGeometry", r"""
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class FocusedHolderGeometry {
    static class ViewGroup {static class LayoutParams {static final int WRAP_CONTENT=-2;}}
    static class LinearLayout {static class LayoutParams extends ViewGroup.LayoutParams {int height,start,end;int getMarginStart(){return start;}int getMarginEnd(){return end;}void setMarginStart(int n){start=n;}void setMarginEnd(int n){end=n;}}}
    static class View {LinearLayout.LayoutParams p=new LinearLayout.LayoutParams();int layouts;LinearLayout.LayoutParams getLayoutParams(){return p;}void setLayoutParams(LinearLayout.LayoutParams n){p=n;layouts++;}}
    View mLocationBarHost=new View();
    private void updateLocationBarGeometry(ArcDesktopPolicy.Geometry g,int side) BODY
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    public static void main(String[]args){FocusedHolderGeometry r=new FocusedHolderGeometry();var g=ArcDesktopPolicy.geometry(1382,863,334,1,false);
        r.updateLocationBarGeometry(g,g.sideInset);check(r.mLocationBarHost.p.height==49&&r.mLocationBarHost.p.start==9,"unfocused holder follows reference geometry");
        r.mLocationBarHost.p.height=-2;r.mLocationBarHost.p.start=r.mLocationBarHost.p.end=0;int layouts=r.mLocationBarHost.layouts;
        r.updateLocationBarGeometry(g,g.sideInset);check(r.mLocationBarHost.p.height==-2&&r.mLocationBarHost.p.start==0&&r.mLocationBarHost.layouts==layouts,"header relayout must not overwrite native expanded omnibox geometry");
        var resized=ArcDesktopPolicy.geometry(2764,1726,668,2,true);r.updateLocationBarGeometry(resized,resized.sideInset);
        check(r.mLocationBarHost.p.height==-2&&r.mLocationBarHost.p.start==0,"focused resize leaves holder geometry to LocationBarTablet");
        // Native unfocus exits WRAP_CONTENT and restores its previous inset. The next layout
        // must adopt the CURRENT window policy, rather than keeping the original focus snapshot.
        r.mLocationBarHost.p.height=56;r.mLocationBarHost.p.start=r.mLocationBarHost.p.end=9;
        r.updateLocationBarGeometry(resized,resized.sideInset);check(r.mLocationBarHost.p.height==98&&r.mLocationBarHost.p.start==18&&r.mLocationBarHost.p.end==18,"unfocus adopts live resized baseline");
        layouts=r.mLocationBarHost.layouts;r.updateLocationBarGeometry(resized,resized.sideInset);check(layouts==r.mLocationBarHost.layouts,"stable baseline must not request another layout");
    }
}
""".replace("BODY", body))
