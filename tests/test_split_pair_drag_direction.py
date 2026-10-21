"""Run delivered onMove/ID movement at a synthetic native model boundary; no Android UI claim."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_group_projection import method

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListItemTouchHelperCallback.java'
HELPER = ROOT / 'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcSplitPairProjection.java'

class SplitPairDragDirectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        source = SOURCE.read_text()
        methods = ''.join(method(source, signature) for signature in (
            'public boolean onMove(', 'public boolean moveArcUnit(', 'private boolean arcSameSection('))
        java = '''import java.util.*;
import java.util.function.Supplier;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcSplitPairProjection;
class Token {}
class PropertyModel {}
class RecyclerView {
 static class ViewHolder {int id; ViewHolder(int id){this.id=id;}
  int getItemViewType(){return 0;} int getBindingAdapterPosition(){return 42;} }
}
class ViewHolder extends RecyclerView.ViewHolder {PropertyModel model=new PropertyModel();ViewHolder(int id){super(id);}}
class TabProperties {static class UiType {static final int TAB_GROUP=1;}}
class Tab {static final int INVALID_TAB_ID=-1;final int id;Tab(int id){this.id=id;}
 int getId(){return id;} boolean isClosing(){return false;} boolean getIsPinned(){return false;}
 Token getTabGroupId(){return null;}}
class TabModel implements Iterable<Tab> {static final int INVALID_TAB_INDEX=-1;final List<Tab> tabs=new ArrayList<>();
 public Iterator<Tab> iterator(){return tabs.iterator();} int getCount(){return tabs.size();}
 Tab getTabById(int id){for(Tab t:tabs)if(t.id==id)return t;return null;} int indexOf(Tab tab){return tabs.indexOf(tab);}
 void moveTab(int id,int insertionIndex){Tab tab=getTabById(id);int from=indexOf(tab);tabs.remove(from);
  tabs.add(insertionIndex>from?insertionIndex-1:insertionIndex,tab);}
}
// Ordinary/group branch boundaries compile the complete delivered method. These tests enter
// only its pair branch; crossing into the original native branch fails explicitly.
class NestedTabReorderUtils {
 static boolean tryUngroupChildTab(Object... args){throw new AssertionError("ordinary branch");}
 static boolean tryMergeStandaloneTab(Object... args){throw new AssertionError("ordinary branch");}
 static int calculateDestinationIndex(Object... args){throw new AssertionError("ordinary branch");}
 static void moveTabOrGroup(Object... args){throw new AssertionError("ordinary branch");}
}
public class SplitPairDragDirectionProbe {
 final TabModel model=new TabModel(); final Supplier<TabModel> mCurrentTabModelSupplier=()->model;
 final ArcSplitPairProjection mArcSplitPairs=new ArcSplitPairProjection(); int mSelectedTabIndex;
 boolean hasTabPropertiesModel(RecyclerView.ViewHolder h){return true;}
 int getTabId(RecyclerView.ViewHolder h){return h.id;}
 boolean isArcPair(RecyclerView.ViewHolder h){return mArcSplitPairs.peer(h.id)>=0;}
 boolean isSolitaryChild(RecyclerView.ViewHolder h){return false;}
 Token getTabGroupId(RecyclerView.ViewHolder h){return null;}
''' + methods + '''
 List<Integer> projected(){List<Integer> ids=new ArrayList<>();for(Tab tab:model)ids.add(tab.id);return mArcSplitPairs.project(ids);}
 public static void main(String[] args){
  SplitPairDragDirectionProbe p=new SplitPairDragDirectionProbe();
  boolean targetPair=args[0].equals("target-pair");
  for(int id:targetPair?new int[]{2,3,1,5,4}:new int[]{2,3,1})p.model.tabs.add(new Tab(id));
  p.mArcSplitPairs.set(targetPair?List.of(new int[]{1,1,2,1},new int[]{4,4,5,4}):List.of(new int[]{1,1,2,1}),id->true);
  int from=args[0].equals("ordinary-up")?3:1;
  int to=targetPair?4:(from==3?1:3);
  if(!p.onMove(new RecyclerView(),new ViewHolder(from),new ViewHolder(to)))throw new AssertionError("move rejected");
  List<Integer> expected=targetPair?List.of(3,4,1):List.of(3,1);
  if(!p.projected().equals(expected))throw new AssertionError("expected "+expected+", actual "+p.projected());
 }
}'''
        path = cls.work / 'SplitPairDragDirectionProbe.java'
        path.write_text(java)
        result = subprocess.run(['javac', '-d', str(cls.work), str(HELPER), str(path)], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def probe(self, case):
        result = subprocess.run(['java', '-cp', str(self.work), 'SplitPairDragDirectionProbe', case], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pair_down_when_representative_follows_peer(self): self.probe('pair-down')
    def test_ordinary_up_over_pair_whose_representative_follows_peer(self): self.probe('ordinary-up')
    def test_pair_down_over_second_pair_with_representative_after_peer(self): self.probe('target-pair')
