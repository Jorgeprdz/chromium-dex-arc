"""Delivered coordinator methods at a synthetic TabModel boundary, not Android rendering."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_group_projection import method

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListCoordinator.java'

class ReorderProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        source = SOURCE.read_text()
        refresh = method(source, 'public void refreshTabPresentation()')
        helper = method(source, 'private boolean reconcileStandaloneTabOrder(') if 'private boolean reconcileStandaloneTabOrder(' in source else ''
        java = '''import java.util.*;
import java.util.function.IntPredicate;
class Tab { static final int INVALID_TAB_ID=-1; final int id; boolean pinned; Object group;
 Tab(int id){this.id=id;} int getId(){return id;} Object getTabGroupId(){return group;} boolean getIsPinned(){return pinned;} }
class TabProperties { static final int TAB_ID=0;
 static boolean isTabOrTabGroup(PropertyModel r){return true;} static boolean isTabGroupHeader(PropertyModel r){return ((Row)r).group;} }
class PropertyModel { int get(int key){return ((Row)this).id;} }
class Row extends PropertyModel { final Row model=this; final int id; boolean group; boolean selected;
 Row(int id){this.id=id;} int get(int key){return id;} }
class Rows extends ArrayList<Row> {
 int indexFromTabId(int id){for(int i=0;i<size();i++)if(get(i).id==id)return i;return -1;}
 void move(int from,int to){add(to,remove(from));} }
class TabModel { static final int INVALID_TAB_INDEX=-1; final List<Tab> tabs=new ArrayList<>(); }
class Selector { final TabModel model=new TabModel(); boolean ready=true;
 boolean isTabStateInitialized(){return ready;} TabModel getCurrentModel(){return model;} }
public class ReorderProjectionProbe {
 final Selector mTabModelSelector=new Selector(); final Rows mModelList=new Rows();
 IntPredicate mTabVisibilityPredicate=id->true; int resets;
 List<Tab> getTabsForPresentation(TabModel model){return model.tabs.stream().filter(t->mTabVisibilityPredicate==null||mTabVisibilityPredicate.test(t.id)).toList();}
 // Explicit synthetic reset boundary: production TabListMediator clears/repopulates
 // on a changed ordered list. No RecyclerView/GPU acceptance is claimed here.
 void resetWithListOfTabs(TabModel model){resets++;mModelList.clear();for(Tab t:getTabsForPresentation(model))mModelList.add(new Row(t.id));}
''' + refresh + helper + '''
 static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
 public static void main(String[] args){
  ReorderProjectionProbe p=new ReorderProjectionProbe();
  Tab a=new Tab(1),b=new Tab(2),c=new Tab(3);p.mTabModelSelector.model.tabs.addAll(List.of(a,b,c));p.resetWithListOfTabs(p.mTabModelSelector.model);
  Map<Integer,Row> identities=new HashMap<>();for(Row r:p.mModelList)identities.put(r.id,r);
  if(args[0].equals("fallback")){p.mTabModelSelector.model.tabs.add(new Tab(4));p.refreshTabPresentation();check(p.mModelList.size()==4,"new tab lost");return;}
  if(args[0].equals("unfiltered")){p.mTabVisibilityPredicate=null;p.refreshTabPresentation();check(p.resets==2,"upstream path changed");return;}
  if(args[0].equals("group")){a.group=new Object();p.refreshTabPresentation();check(p.resets==2,"group path bypassed");return;}
  if(args[0].equals("pinned")){a.pinned=true;p.refreshTabPresentation();check(p.resets==2,"pinned path bypassed");return;}
  int selected=2;
  for(int i=0;i<30;i++){
   Collections.rotate(p.mTabModelSelector.model.tabs,1);p.refreshTabPresentation();
   for(int j=0;j<3;j++){
    Row r=p.mModelList.get(j);check(r.id==p.mTabModelSelector.model.tabs.get(j).id,"wrong A/B/C order");
    check(r==identities.get(r.id),"reorder replaced native row model while drag owns holder");r.selected=r.id==selected;
   }
   p.refreshTabPresentation();check(p.mModelList.stream().filter(r->r.selected).count()==1,"selection lost");
   check(p.mModelList.stream().filter(r->r.selected).findFirst().get().id==selected,"wrong selected tab identity");selected=selected%3+1;
  }
  check(p.resets==1,"pure reorder reset list");
 }
}'''
        path=cls.work/'ReorderProjectionProbe.java';path.write_text(java)
        result=subprocess.run(['javac','-d',str(cls.work),str(path)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)
    def run_case(self,case):
        result=subprocess.run(['java','-cp',str(self.work),'ReorderProjectionProbe',case],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_repeated_abc_reorder_preserves_models_and_selected_identity(self):self.run_case('reorder')
    def test_new_tab_keeps_structural_reset(self):self.run_case('fallback')
    def test_unfiltered_keeps_upstream_path(self):self.run_case('unfiltered')
    def test_group_keeps_group_projection(self):self.run_case('group')
    def test_pinned_keeps_pinned_projection(self):self.run_case('pinned')
