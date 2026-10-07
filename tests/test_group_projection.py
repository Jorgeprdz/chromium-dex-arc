"""Execute actual native group methods at a synthetic Java model boundary.

This catches projection cardinality bugs without claiming Chromium/Robolectric execution.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management'


def method(source, declaration):
    start = source.index(declaration)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class NativeGroupProjectionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        mediator = (BASE / 'TabListMediator.java').read_text()
        nested = (BASE / 'NestedLayoutDelegate.java').read_text()
        insert = method(mediator, 'int insertChildTabs(')
        remove = method(nested, 'private void removeChildTabs(')
        move = method(nested, 'public void didMoveTabGroup(')
        anchor = method(nested, 'private int getInsertionIndexOfGroup(')
        helper = (method(nested, 'private int getPresentedChildCount(')
                  if 'private int getPresentedChildCount(' in nested else '')
        visibility = (method(mediator, 'boolean isTabHiddenForPresentation(')
                      if 'boolean isTabHiddenForPresentation(' in mediator
                      else 'boolean isTabHiddenForPresentation(Tab tab) { return mTabVisibilityPredicate != null && !mTabVisibilityPredicate.test(tab.getId()); }')
        java = '''import java.util.*;
import java.util.function.IntPredicate;
class Token { final int id; Token(int id){this.id=id;} }
class Key<T> {}
class PropertyModel {
    final Map<Key<?>,Object> data = new HashMap<>();
    <T> T get(Key<T> key){return (T)data.get(key);}
    <T> void set(Key<T> key,T value){data.put(key,value);}
}
class TabProperties {
    static final Key<Token> TAB_GROUP_HEADER_ID = new Key<>(), TAB_GROUP_ID = new Key<>();
    static final Key<Integer> TAB_ID = new Key<>();
    static final Key<Boolean> IS_COLLAPSED = new Key<>();
    static boolean isTabGroupCollapsed(PropertyModel m){return Boolean.TRUE.equals(m.get(IS_COLLAPSED));}
    static boolean isTabInGroup(PropertyModel m){return m.get(TAB_GROUP_ID)!=null;}
}
class Tab {
    final int id; final Token group;
    Tab(int id, Token group){this.id=id;this.group=group;}
    int getId(){return id;} Token getTabGroupId(){return group;}
}
class ListItem { final PropertyModel model; ListItem(PropertyModel m){model=m;} }
class TabListModel extends ArrayList<ListItem> {
    int indexFromTabGroupId(Token group){for(int i=0;i<size();i++)if(get(i).model.get(TabProperties.TAB_GROUP_HEADER_ID)==group)return i;return -1;}
    int indexFromTabId(int id){for(int i=0;i<size();i++)if(Objects.equals(get(i).model.get(TabProperties.TAB_ID),id))return i;return -1;}
    void removeAt(int i){remove(i);} void move(int from,int to){add(to,remove(from));}
}
class TabModel {
    static final int INVALID_TAB_INDEX=-1;
    final List<Tab> nativeTabs=new ArrayList<>();
    List<Tab> getTabsInGroup(Token group){List<Tab> out=new ArrayList<>();for(Tab t:nativeTabs)if(t.group==group)out.add(t);return out;}
    int getTabCountForGroup(Token group){return getTabsInGroup(group).size();}
    Tab getTabAt(int i){return i>=0&&i<nativeTabs.size()?nativeTabs.get(i):null;}
    int getCount(){return nativeTabs.size();}
}
class Mediator {
    final TabModel tabs; final TabListModel rows; IntPredicate mTabVisibilityPredicate;
    Mediator(TabModel tabs,TabListModel rows){this.tabs=tabs;this.rows=rows;}
    TabModel getCurrentTabModelChecked(){return tabs;}
    void addTabInfoToModelForTab(Tab tab,int index){PropertyModel m=new PropertyModel();m.set(TabProperties.TAB_ID,tab.id);m.set(TabProperties.TAB_GROUP_ID,tab.group);rows.add(index,new ListItem(m));}
''' + visibility + insert + '''
}
class Nested {
    final Mediator mMediator; final TabListModel mModelList;
    Nested(Mediator m){mMediator=m;mModelList=m.rows;}
    int getIndexFromTabId(int id){return mModelList.indexFromTabId(id);}
''' + helper + remove + move + anchor + '''
    void collapse(Token group){removeChildTabs(group);}
}
public class GroupProjectionBoundaryProbe {
    static final Token GROUP = new Token(1);
    static Tab a=new Tab(1,GROUP), b=new Tab(2,GROUP), c=new Tab(3,null), d=new Tab(4,null);
    static void equal(Object want,Object got){if(!want.equals(got))throw new AssertionError("want "+want+", got "+got);}
    static List<Integer> ids(TabListModel rows){List<Integer> out=new ArrayList<>();for(ListItem item:rows)out.add(item.model.get(TabProperties.TAB_ID));return out;}
    public static void main(String[] args){
        TabModel nativeModel=new TabModel(); nativeModel.nativeTabs.addAll(List.of(a,b,c,d));
        TabListModel rows=new TabListModel();
        PropertyModel header=new PropertyModel();header.set(TabProperties.TAB_GROUP_HEADER_ID,GROUP);header.set(TabProperties.TAB_ID,0);header.set(TabProperties.IS_COLLAPSED,false);rows.add(new ListItem(header));
        Mediator mediator=new Mediator(nativeModel,rows); mediator.mTabVisibilityPredicate=id->id!=2;
        Nested nested=new Nested(mediator);
        int nativeCount=4;
        switch(args[0]){
            case "expand":
                mediator.addTabInfoToModelForTab(c,1);
                equal(1,mediator.insertChildTabs(GROUP,0));
                equal(List.of(0,1,3),ids(rows));break;
            case "collapse":
                mediator.addTabInfoToModelForTab(a,1);mediator.addTabInfoToModelForTab(c,2);
                nested.collapse(GROUP);equal(List.of(0,3),ids(rows));break;
            case "move":
                mediator.addTabInfoToModelForTab(a,1);mediator.addTabInfoToModelForTab(c,2);mediator.addTabInfoToModelForTab(d,3);
                nativeModel.nativeTabs.clear();nativeModel.nativeTabs.addAll(List.of(c,a,b,d));
                nested.didMoveTabGroup(GROUP,0,1);equal(List.of(3,0,1,4),ids(rows));break;
            case "move-hidden-anchor":
                mediator.addTabInfoToModelForTab(a,1);mediator.addTabInfoToModelForTab(c,2);mediator.addTabInfoToModelForTab(d,3);
                nativeModel.nativeTabs.clear();nativeModel.nativeTabs.addAll(List.of(c,a,b,new Tab(5,null),d));
                nativeCount=5;
                nested.didMoveTabGroup(GROUP,0,1);equal(List.of(3,0,1,4),ids(rows));break;
            case "unfiltered":
                mediator.mTabVisibilityPredicate=null;
                equal(2,mediator.insertChildTabs(GROUP,0));equal(List.of(0,1,2),ids(rows));
                nested.collapse(GROUP);equal(List.of(0),ids(rows));break;
            default:throw new AssertionError(args[0]);
        }
        equal(nativeCount,nativeModel.getCount());
    }
}
'''
        source = cls.work / 'GroupProjectionBoundaryProbe.java'
        source.write_text(java)
        compiled = subprocess.run(['javac', '-d', str(cls.work), str(source)], capture_output=True, text=True)
        if compiled.returncode:
            raise AssertionError(compiled.stderr)

    def probe(self, case):
        result = subprocess.run(['java', '-cp', str(self.work), 'GroupProjectionBoundaryProbe', case], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_expand_never_inserts_other_space_child(self): self.probe('expand')
    def test_collapse_preserves_unrelated_following_row(self): self.probe('collapse')
    def test_group_move_counts_presented_children(self): self.probe('move')
    def test_group_move_skips_hidden_native_anchor(self): self.probe('move-hidden-anchor')
    def test_null_predicate_keeps_original_group_behavior(self): self.probe('unfiltered')
