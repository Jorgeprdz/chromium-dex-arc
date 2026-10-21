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
        set_pairs = method(source, 'public void setArcSplitPairs(')
        helper = method(source, 'private boolean reconcileStandaloneTabOrder(') if 'private boolean reconcileStandaloneTabOrder(' in source else ''
        java = '''import org.chromium.chrome.browser.ui.vertical_tabs.ArcSplitPairProjection;
import java.util.*;
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
class TabModel implements Iterable<Tab> { static final int INVALID_TAB_INDEX=-1; final List<Tab> tabs=new ArrayList<>();
 public Iterator<Tab> iterator(){return tabs.iterator();} }
class Selector { final TabModel model=new TabModel(); boolean ready=true;
 boolean isTabStateInitialized(){return ready;} TabModel getCurrentModel(){return model;} }
public class ReorderProjectionProbe {
 final Selector mTabModelSelector=new Selector(); final Rows mModelList=new Rows();
 IntPredicate mTabVisibilityPredicate=id->true; int resets;
 final ArcSplitPairProjection pairs=new ArcSplitPairProjection();
 final ArcSplitPairProjection mArcSplitPairs=pairs;
 List<int[]> mArcPairSnapshots=new ArrayList<>(); TabModel mArcPairSnapshotModel;
 // Android observer/favicon boundaries. The real pure projection is compiled below; no native
 // title/favicon or TabModelSelector lifecycle acceptance is claimed by this reorder fixture.
 final MediatorBoundary mMediator=new MediatorBoundary();
 static class MediatorBoundary {int refreshes;void refreshArcSplitPairRows(){refreshes++;}}
 void updateArcPairProjection(TabModel model){pairs.set(mArcPairSnapshots,id->mTabVisibilityPredicate==null||mTabVisibilityPredicate.test(id));}
 List<Tab> getTabsForPresentation(TabModel model){List<Tab> rows=new ArrayList<>();
  List<Integer> ids=model.tabs.stream().filter(t->mTabVisibilityPredicate==null||mTabVisibilityPredicate.test(t.id)).map(t->t.id).toList();
  for(int id:pairs.project(ids))for(Tab t:model.tabs)if(t.id==id){rows.add(t);break;}return rows;}
 // Explicit synthetic reset boundary: production TabListMediator clears/repopulates
 // on a changed ordered list. No RecyclerView/GPU acceptance is claimed here.
 void resetWithListOfTabs(TabModel model){resets++;mModelList.clear();for(Tab t:getTabsForPresentation(model))mModelList.add(new Row(t.id));}
''' + refresh + helper + set_pairs + '''
 static int pairsAction(ReorderProjectionProbe p){return p.pairs.actionId(1);}
 static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
 public static void main(String[] args){
  ReorderProjectionProbe p=new ReorderProjectionProbe();
  Tab a=new Tab(1),b=new Tab(2),c=new Tab(3);p.mTabModelSelector.model.tabs.addAll(List.of(a,b,c));p.resetWithListOfTabs(p.mTabModelSelector.model);
  if(args[0].equals("active-only")){
   p.setArcSplitPairs(List.of(new int[]{1,1,2,1}));
   Row row=p.mModelList.get(p.mModelList.indexFromTabId(1));
   int resets=p.resets;
   a.pinned=true;b.pinned=true; // Same projected shape also avoids grouped/pinned reset paths.
   a.group=new Object();b.group=a.group;
   for(int i=0;i<30;i++){
    p.setArcSplitPairs(List.of(new int[]{1,i%2==0?2:1,i%2==0?1:2,i%2==0?2:1}));
    check(p.pairs.actionId(1)==(i%2==0?2:1),"active member did not refresh");
    check(p.mModelList.get(p.mModelList.indexFromTabId(1))==row,"active/swap replaced row");
    check(p.resets==resets,"active/swap reset grouped/pinned list");
   }
   check(p.mMediator.refreshes>=30,"metadata was not rebound");return;
  }
  if(args[0].equals("pair")){
   p.mArcPairSnapshots.add(new int[]{1,1,2,2});p.updateArcPairProjection(p.mTabModelSelector.model);
   p.resetWithListOfTabs(p.mTabModelSelector.model);
   Row pairRow=p.mModelList.get(0),normalRow=p.mModelList.get(1);
   for(int i=0;i<30;i++){
    Collections.rotate(p.mTabModelSelector.model.tabs,1);p.refreshTabPresentation();
    check(p.mModelList.size()==2,"pair duplicated");
    check(p.mModelList.get(p.mModelList.indexFromTabId(1))==pairRow,"pair row replaced");
    check(p.mModelList.get(p.mModelList.indexFromTabId(3))==normalRow,"normal row replaced");
    check(pairsAction(p)==2,"pair action lost active second member");
   }
   check(p.resets==2,"pair reorder rebuilt native list");return;
  }
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
        result=subprocess.run(['javac','-d',str(cls.work),str(ROOT/'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcSplitPairProjection.java'),str(path)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)
    def run_case(self,case):
        result=subprocess.run(['java','-cp',str(self.work),'ReorderProjectionProbe',case],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_repeated_abc_reorder_preserves_models_and_selected_identity(self):self.run_case('reorder')
    def test_new_tab_keeps_structural_reset(self):self.run_case('fallback')
    def test_unfiltered_keeps_upstream_path(self):self.run_case('unfiltered')
    def test_group_keeps_group_projection(self):self.run_case('group')
    def test_pinned_keeps_pinned_projection(self):self.run_case('pinned')

    def test_repeated_pair_reorder_preserves_both_row_models(self):self.run_case('pair')

    def test_active_member_and_swap_rebind_without_group_or_pinned_reset(self):self.run_case('active-only')
