"""Run delivered presentation methods at a synthetic TabModel boundary, not Android UI."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_group_projection import method

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListCoordinator.java'
PROJECTION = ROOT / 'chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcSplitPairProjection.java'


class TabPresentationProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        source = SOURCE.read_text()
        java = '''import java.util.*;
import java.util.function.IntPredicate;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcSplitPairProjection;
@interface Nullable {}
class Token {}
class Tab {
    final int id; final Token group;
    Tab(int id, Token group) { this.id=id; this.group=group; }
    int getId() { return id; } Token getTabGroupId() { return group; }
}
class TabModel {
    final List<Tab> representatives=new ArrayList<>();
    final Map<Integer, Tab> byId=new HashMap<>();
    final Map<Token, List<Tab>> groups=new HashMap<>();
    List<Tab> getRepresentativeTabList() { return representatives; }
    Tab getTabById(int id) { return byId.get(id); }
    boolean isTabInTabGroup(Tab tab) { return groups.containsKey(tab.group); }
    List<Tab> getTabsInGroup(Token group) { return groups.getOrDefault(group, List.of()); }
}
public class PresentationProbe {
    IntPredicate mTabVisibilityPredicate;
    final ArcSplitPairProjection mArcSplitPairs=new ArcSplitPairProjection();
''' + method(source, 'private @Nullable Tab getVisibleRepresentative(') + method(source, 'private List<Tab> getTabsForPresentation(') + '''
    static void check(boolean value) { if (!value) throw new AssertionError("presentation lost native Tab identity/order"); }
    public static void main(String[] args) {
        PresentationProbe p=new PresentationProbe(); TabModel model=new TabModel();
        Tab a=new Tab(1,null), b=new Tab(2,null), c=new Tab(3,null);
        model.representatives.addAll(List.of(a,b,c));
        switch(args[0]) {
            case "ordinary":
                // Existing TabModel fixtures expose authoritative representatives without a lookup.
                p.mTabVisibilityPredicate=id -> id!=2;
                check(p.getTabsForPresentation(model).equals(List.of(a,c)));
                p.mTabVisibilityPredicate=null;
                check(p.getTabsForPresentation(model).equals(List.of(a,b,c))); break;
            case "group":
                Token group=new Token(); Tab header=new Tab(4,group);
                model.representatives.clear(); model.representatives.addAll(List.of(header,c));
                check(p.getTabsForPresentation(model).equals(List.of(header,c))); break;
            case "hidden-group-representative":
                Token g=new Token(); Tab hidden=new Tab(4,g), visible=new Tab(5,g);
                model.groups.put(g,List.of(hidden,visible));
                model.representatives.clear(); model.representatives.addAll(List.of(hidden,c));
                p.mTabVisibilityPredicate=id -> id!=4;
                check(p.getTabsForPresentation(model).equals(List.of(visible,c))); break;
            case "pair":
                // B arrives before A; both must map to the real A and emit only one shared row.
                model.representatives.clear(); model.representatives.addAll(List.of(b,c,a));
                model.byId.put(1,a); model.byId.put(2,b); model.byId.put(3,c);
                p.mArcSplitPairs.set(List.of(new int[]{1,1,2,2}),id -> true);
                check(p.getTabsForPresentation(model).equals(List.of(a,c)));
                check(p.mArcSplitPairs.actionId(1)==2); break;
            default: throw new AssertionError(args[0]);
        }
        check(model.representatives.size()==(args[0].contains("group")?2:3));
    }
}'''
        path = cls.work / 'PresentationProbe.java'
        path.write_text(java)
        result = subprocess.run(['javac', '-d', str(cls.work), str(PROJECTION), str(path)], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def probe(self, case):
        result = subprocess.run(['java', '-cp', str(self.work), 'PresentationProbe', case], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_unpaired_tabs_preserve_objects_and_visibility(self): self.probe('ordinary')
    def test_group_header_preserves_native_object(self): self.probe('group')
    def test_hidden_group_representative_uses_visible_child(self): self.probe('hidden-group-representative')
    def test_pair_resolves_stable_representative_from_secondary(self): self.probe('pair')
