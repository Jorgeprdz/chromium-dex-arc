"""Probe shipped reorder observers and filtered pruning with live row identities.

The Android adapter/reset boundary is explicit; this does not simulate RecyclerView overlays.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body

BASE = ROOT / ".source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management"

JAVA = r"""
import java.util.*;
import java.util.function.IntPredicate;
class Token {}
class Key<T> {}
class PropertyModel {
    final Map<Key<?>,Object> data = new HashMap<>();
    <T> T get(Key<T> k) { return (T)data.get(k); }
    <T> void set(Key<T> k, T v) { data.put(k,v); }
}
class TabProperties {
    static final Key<Token> TAB_GROUP_ID=new Key<>(), TAB_GROUP_HEADER_ID=new Key<>();
    static final Key<Integer> TAB_ID=new Key<>();
    static final Key<Boolean> IS_COLLAPSED=new Key<>();
    static boolean isTabOrTabGroup(PropertyModel m) { return m.data.containsKey(TAB_ID); }
    static boolean isTabGroupHeader(PropertyModel m) { return m.get(TAB_GROUP_HEADER_ID)!=null; }
    static boolean isTabInGroup(PropertyModel m) { return m.get(TAB_GROUP_ID)!=null; }
    static boolean isTabGroupCollapsed(PropertyModel m) { return Boolean.TRUE.equals(m.get(IS_COLLAPSED)); }
}
class Tab {
    static final int INVALID_TAB_ID=-1;
    final int id; final Token group;
    Tab(int id,Token group) { this.id=id; this.group=group; }
    int getId() { return id; }
    Token getTabGroupId() { return group; }
}
class ListItem { final PropertyModel model; ListItem(PropertyModel m) { model=m; } }
class TabListModel extends ArrayList<ListItem> {
    int resets;
    int indexFromTabGroupId(Token id) { for(int i=0;i<size();i++)if(get(i).model.get(TabProperties.TAB_GROUP_HEADER_ID)==id)return i;return -1; }
    int indexFromTabId(int id) { for(int i=0;i<size();i++)if(Objects.equals(get(i).model.get(TabProperties.TAB_ID),id))return i;return -1; }
    void move(int from,int to) { add(to,remove(from)); }
    void removeAt(int index) { remove(index); }
}
class TabModel {
    static final int INVALID_TAB_INDEX=-1;
    final List<Tab> tabs=new ArrayList<>();
    List<Tab> getTabsInGroup(Token id) { List<Tab> out=new ArrayList<>();for(Tab t:tabs)if(t.group==id)out.add(t);return out; }
    int getTabCountForGroup(Token id) { return getTabsInGroup(id).size(); }
    Tab getTabAt(int i) { return i>=0&&i<tabs.size()?tabs.get(i):null; }
}
class Selector {
    final TabModel model; boolean initialized=true;
    Selector(TabModel m) { model=m; }
    TabModel getCurrentModel() { return model; }
    boolean isTabStateInitialized() { return initialized; }
}
class Mediator {
    final TabModel model; Mediator(TabModel m) { model=m; }
    TabModel getCurrentTabModelChecked() { return model; }
}
class Nested {
    final Mediator mMediator; final TabListModel mModelList;
    Nested(TabModel model,TabListModel rows) { mMediator=new Mediator(model);mModelList=rows; }
    int getIndexFromTabId(int id) { return mModelList.indexFromTabId(id); }
    NESTED
}
class Observer {
    final TabListModel mModelList; final Selector mTabModelSelector;
    IntPredicate mTabVisibilityPredicate=id->id!=2&&id!=5;
    Observer(TabModel model,TabListModel rows) { mModelList=rows;mTabModelSelector=new Selector(model); }
    // Expanded-child presentation fails the real mediator's representative-count fast path.
    // Preserve reset's consequential effects: adapter clear and newly created row objects.
    void resetWithListOfTabs(TabModel model) {
        List<ListItem> before=new ArrayList<>(mModelList);mModelList.clear();mModelList.resets++;
        for(ListItem old:before) { PropertyModel p=new PropertyModel();p.data.putAll(old.model.data);mModelList.add(new ListItem(p)); }
        pruneFilteredRows(model);
    }
    OBSERVER
}
public class GroupDragRegression {
    static final Token GROUP=new Token(), HIDDEN_GROUP=new Token();
    static ListItem row(int id,Token child,Token header) {
        PropertyModel m=new PropertyModel();m.set(TabProperties.TAB_ID,id);
        if(child!=null)m.set(TabProperties.TAB_GROUP_ID,child);
        if(header!=null) { m.set(TabProperties.TAB_GROUP_HEADER_ID,header);m.set(TabProperties.IS_COLLAPSED,false); }
        return new ListItem(m);
    }
    static void check(boolean c,String message) { if(!c)throw new AssertionError(message); }
    static List<Integer> ids(TabListModel rows) { List<Integer> ids=new ArrayList<>();for(ListItem r:rows)ids.add(r.model.get(TabProperties.TAB_ID));return ids; }
    public static void main(String[] args) {
        TabModel model=new TabModel();
        Tab a=new Tab(1,GROUP), hidden=new Tab(2,GROUP), c=new Tab(3,null), d=new Tab(4,null), hiddenOther=new Tab(5,HIDDEN_GROUP);
        model.tabs.addAll(List.of(c,a,hidden,hiddenOther,d));
        TabListModel rows=new TabListModel();
        ListItem header=row(1,null,GROUP), child=row(1,GROUP,null), other=row(3,null,null), last=row(4,null,null);
        rows.addAll(List.of(header,child,other,last));
        Nested nested=new Nested(model,rows);Observer observer=new Observer(model,rows);
        switch(args[0]) {
            case "group":
                nested.didMoveTabGroup(GROUP,0,1);
                observer.didMoveTabGroup(GROUP,0,1);
                check(ids(rows).equals(List.of(3,1,1,4)),"group must move before next visible anchor");
                check(rows.get(1)==header&&rows.get(2)==child,"live dragged header/child rows must keep identity");
                check(rows.resets==0,"group move must not clear/rebuild the adapter mid-drag");break;
            case "tab":
                // The native delegate has already moved the visible standalone row in place.
                rows.move(2,0);observer.didMoveTab(c,0,3);
                check(rows.get(0)==other&&rows.get(1)==header&&rows.get(2)==child,
                        "standalone move observer must preserve existing nested row objects");
                check(rows.resets==0,"standalone move must not rebuild an expanded group");break;
            case "prune":
                rows.add(2,row(2,GROUP,null));rows.add(row(5,null,HIDDEN_GROUP));rows.add(row(5,HIDDEN_GROUP,null));
                observer.didMoveTabGroup(GROUP,0,1);
                check(ids(rows).equals(List.of(1,1,3,4)),"reorder must immediately prune hidden child and all-hidden group");
                check(rows.get(0)==header&&rows.get(1)==child,"pruning must preserve visible dragged rows");
                check(rows.resets==0,"hidden-row cleanup must not reset the whole adapter");break;
            case "membership":
                observer.didMergeTabToGroup(a,true);
                check(rows.resets==1,"group membership changes still reconcile filtered presentation");
                rows.add(row(2,GROUP,null));observer.didMoveTabOutOfGroup(a,GROUP);
                check(rows.resets==2&&!ids(rows).contains(2),"ungroup/membership reconciliation still excludes other-Space children");break;
            case "unfiltered":
                observer.mTabVisibilityPredicate=null;rows.add(row(2,GROUP,null));
                observer.didMoveTabGroup(GROUP,0,1);observer.didMoveTab(c,0,3);
                check(rows.resets==0&&ids(rows).contains(2),"MOBILE/global projection must retain native unfiltered rows");break;
        }
    }
}
"""


class ArcGroupDragProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(BASE/"vertical_tabs/VerticalTabListCoordinator.java").read_text()
        group=source[source.index("private final TabGroupObserver mPresentationGroupObserver"):]
        tab=source[source.index("mTabModelSelectorTabModelObserver ="):]
        signatures={
            "public void didMoveTabGroup(Token id, int oldIndex, int newIndex)":group,
            "public void didMergeTabToGroup(Tab tab, boolean isDestinationTab)":group,
            "public void didMoveTabOutOfGroup(Tab tab, Token oldGroupId)":group,
            "public void didMoveTab(Tab tab, int newIndex, int curIndex)":tab,
            "private void refreshTabPresentationIfFiltered()":source,
            "public void refreshTabPresentation()":source,
            "private boolean groupHasVisibleTab(TabModel tabModel, Token groupId)":source,
            "private void pruneFilteredRows(TabModel tabModel)":source,
        }
        if "private void pruneFilteredRowsAfterReorder()" in source:
            signatures["private void pruneFilteredRowsAfterReorder()"]=source
        methods=[]
        for signature,text in signatures.items():
            pattern=re.escape(signature).replace("Token\\ groupId",r"(?:@Nullable\s+)?Token\ groupId")
            methods.append(signature+" "+method_body(text,pattern))
        nested=(BASE/"NestedLayoutDelegate.java").read_text()
        nested_methods="\n".join(sig+" "+method_body(nested,re.escape(sig)) for sig in [
            "public void didMoveTabGroup(Token tabGroupId, int tabModelOldIndex, int tabModelNewIndex)",
            "private int getPresentedChildCount(Token tabGroupId)",
            "private int getInsertionIndexOfGroup(TabModel tabModel, int firstTabIndex, int tabCount)",
        ])
        cls.tmp=tempfile.TemporaryDirectory(prefix="arc-group-drag-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work=Path(cls.tmp.name)
        path=cls.work/"GroupDragRegression.java"
        path.write_text(JAVA.replace("NESTED",nested_methods).replace("OBSERVER","\n".join(methods)))
        result=subprocess.run(["javac","--release","17","-Xlint:-unchecked","-d",str(cls.work),str(path)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)

    def run_case(self,name):
        result=subprocess.run(["java","-ea","-cp",str(self.work),"GroupDragRegression",name],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_group_move_preserves_dragged_row_identity(self):self.run_case("group")
    def test_standalone_move_preserves_nested_row_identity(self):self.run_case("tab")
    def test_reorder_immediately_prunes_other_space_rows(self):self.run_case("prune")
    def test_membership_changes_still_reconcile_filtered_rows(self):self.run_case("membership")
    def test_global_unfiltered_projection_keeps_native_rows(self):self.run_case("unfiltered")
