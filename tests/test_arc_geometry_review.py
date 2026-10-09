"""Executable regressions for the three independent review findings."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body, DROPDOWN

class GeometryReviewRegressionTest(unittest.TestCase):
    def run_java(self, name, source):
        with tempfile.TemporaryDirectory(prefix="arc-review-regression-") as tmp:
            path=Path(tmp)/(name+".java");path.write_text(source)
            result=subprocess.run(["javac","--release","17","-d",tmp,str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(["java","-ea","-cp",tmp,name],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_gone_native_chrome_does_not_consume_pinned_budget(self):
        source=(ROOT/".source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabRailLayout.java").read_text()
        body=method_body(source,r"protected void onMeasure\(")
        self.run_java("PinnedBudget",r"""
class PinnedBudget extends PinnedBudgetBase {
    static class View {static final int VISIBLE=0,GONE=8;int visibility,height=48;ViewGroup.LayoutParams p=new ConstraintLayout.LayoutParams();int getVisibility(){return visibility;}int getMeasuredHeight(){return height;}ViewGroup.LayoutParams getLayoutParams(){return p;}}
    static class ViewGroup {static class LayoutParams{}}
    static class ConstraintLayout {static class LayoutParams extends ViewGroup.LayoutParams {int matchConstraintMaxHeight;}}
    static class MeasureSpec {static int getSize(int n){return n;}}
    View mPinnedTabsRecyclerView=new View(),mHeaderContainer=new View(),mFooterContainer=new View(),mSpacerView=new View();
    protected void onMeasure(int widthMeasureSpec,int heightMeasureSpec) BODY
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[]args){PinnedBudget r=new PinnedBudget();r.mSpacerView.visibility=8;
        r.onMeasure(334,200);check(((ConstraintLayout.LayoutParams)r.mPinnedTabsRecyclerView.p).matchConstraintMaxHeight==52,"expanded pinned budget fixture");
        r.mHeaderContainer.visibility=r.mFooterContainer.visibility=8;r.onMeasure(334,48);
        check(((ConstraintLayout.LayoutParams)r.mPinnedTabsRecyclerView.p).matchConstraintMaxHeight==24,"GONE chrome must not subtract stale48px heights");
        r.onMeasure(334,0);check(((ConstraintLayout.LayoutParams)r.mPinnedTabsRecyclerView.p).matchConstraintMaxHeight>0,"zero must never mean unlimited pinned tabs");
    }
}
class PinnedBudgetBase {protected void onMeasure(int w,int h){}}
""".replace("BODY",body))

    def test_caption_budget_uses_requested_height_before_layout(self):
        source=(ROOT/"chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java").read_text()
        if "private int captionHeight()" in source:
            body=method_body(source,re.escape("private int captionHeight()"))
        else:
            line=re.search(r"int caption = [^;]+;",source).group(0)
            body="{ "+line+" return caption; }"
        self.run_java("RequestedCaption",r"""
class RequestedCaption {
    static class View {static final int VISIBLE=0,GONE=8;int visibility,height=40;LayoutParams p=new LayoutParams();int getVisibility(){return visibility;}int getHeight(){return height;}LayoutParams getLayoutParams(){return p;}}
    static class LayoutParams {int height=24;}
    final View mCaptionSpacer=new View();
    private int captionHeight() BODY
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[]args){RequestedCaption r=new RequestedCaption();
        check(r.captionHeight()==24,"caption40to24 must use requested24 before layout");
        r.mCaptionSpacer.height=24;r.mCaptionSpacer.p.height=40;check(r.captionHeight()==40,"caption24to40 must not overallocate header from stale24");
        r.mCaptionSpacer.visibility=8;check(r.captionHeight()==0,"MOBILE removes hidden caption budget");
    }
}
""".replace("BODY",body))

    def test_dropdown_scroll_listener_releases_on_detach_and_destroy(self):
        source=(ROOT/".source-modified"/DROPDOWN).read_text()
        methods="\n".join("public void "+name+"() "+method_body(source,re.escape("public void "+name+"()")) for name in ("onAttachedToWindow","onDetachedFromWindow","destroy"))
        self.run_java("DropdownListeners",r"""
class DropdownListeners {
    static class ViewTreeObserver {int global,scroll;boolean alive=true;boolean isAlive(){return alive;}void addOnGlobalLayoutListener(Object o){global++;}void removeOnGlobalLayoutListener(Object o){global--;}void addOnScrollChangedListener(Object o){scroll++;}void removeOnScrollChangedListener(Object o){scroll--;}}
    static class View {ViewTreeObserver tree=new ViewTreeObserver();int layout;void addOnLayoutChangeListener(Object o){layout++;}void removeOnLayoutChangeListener(Object o){layout--;}ViewTreeObserver getViewTreeObserver(){return tree;}}
    static class Resources {Object getConfiguration(){return new Object();}}
    static class Context {Resources getResources(){return new Resources();}void unregisterComponentCallbacks(Object o){}}
    static class Insets {void removeObserver(Object o){}}
    final View mAnchorView=new View(),mAlignmentView=new View();final Context mContext=new Context();
    final Insets mTopInsetProvider=new Insets();final Object mTopInsetProviderObserver=new Object();
    ViewTreeObserver mObservedViewTreeObserver;
    void onConfigurationChanged(Object c){}void recalculateOmniboxAlignment(){}
    METHODS
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[]args){DropdownListeners r=new DropdownListeners();r.onAttachedToWindow();
        check(r.mAnchorView.tree.scroll==1,"scroll must register once with attached dropdown");
        r.onAttachedToWindow();check(r.mAnchorView.tree.scroll==1&&r.mAnchorView.tree.global==1,"repeated attach must not duplicate observers");
        r.onDetachedFromWindow();check(r.mAnchorView.tree.scroll==0&&r.mAnchorView.tree.global==0,"detach releases both observers");
        r.onAttachedToWindow();r.destroy();check(r.mAnchorView.tree.scroll==0&&r.mAnchorView.tree.global==0,"destroy releases observers even without prior detach");
    }
}
""".replace("METHODS",methods))
