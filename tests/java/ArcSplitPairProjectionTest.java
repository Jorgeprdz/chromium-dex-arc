import java.util.*;
import org.chromium.chrome.browser.ui.vertical_tabs.ArcSplitPairProjection;
public final class ArcSplitPairProjectionTest {
    private static void check(boolean b) {if(!b)throw new AssertionError();}
    public static void main(String[] args) {
        var p=new ArcSplitPairProjection();
        p.set(List.of(new int[]{1,1,2,2},new int[]{4,4,5,4}),id->true);
        check(p.project(List.of(1,2,3,4,5)).equals(List.of(1,3,4)));
        check(p.representative(2)==1 && p.actionId(1)==2 && p.peer(2)==1);
        p.set(List.of(new int[]{1,2,1,2},new int[]{4,4,5,5}),id->true);
        check(p.project(List.of(2,3,1,5,4)).equals(List.of(1,3,4)));
        check(p.representative(2)==1 && p.actionId(4)==5);
        check(p.moveUnit(List.of(1,2,3,4,5),1,4).equals(List.of(3,1,2,4,5)));
        check(p.moveUnit(List.of(1,2,3,4,5),4,1).equals(List.of(4,5,1,2,3)));
        p.set(List.of(new int[]{1,1,2,1}),id->id!=2);
        check(p.project(List.of(1,2,3)).equals(List.of(1,2,3)));
        p.set(List.of(new int[]{1,1,2,1},new int[]{2,2,3,3}),id->true);
        check(p.representative(3)==3 && p.peer(1)==2);
        p.set(List.of(),id->true);check(p.representative(2)==2);
        p.set(List.of(new int[]{1,1,2,2}, new int[]{4,4,5,5}), id -> true);
        check(p.moveUnit(List.of(1,2,3,4,5),1,4,true).equals(List.of(3,4,5,1,2)));
        check(p.moveUnit(List.of(1,2,3,4,5),4,1,false).equals(List.of(4,5,1,2,3)));
        check(p.moveUnit(List.of(2,3,1,5,4),2,5,true).equals(List.of(3,5,4,2,1)));
        check(p.moveUnit(List.of(1,2,3),1,2,true).equals(List.of(1,2,3)));
        check(p.moveUnit(List.of(1,2,3),1,99,true).equals(List.of(1,2,3)));
        int[] snapshot = {1,1,2,2};
        p.set(List.of(snapshot),id -> true);
        snapshot[3] = 1;
        int[] copy = p.pair(1); copy[3] = 1;
        check(p.actionId(1) == 2); // Both input/output snapshot mutation are isolated.
        p.set(Arrays.asList(null, new int[]{1,1,1,1}, new int[]{8,1,2,1},
                new int[]{1,1,2,3}, new int[]{1,1,-1,1}, new int[]{1,1,2}), id -> true);
        check(p.project(List.of(1,2,3)).equals(List.of(1,2,3)));
        // Many current native orders, active members and swap configurations: projection keeps
        // exactly one stable row; moving a unit preserves all native IDs and other unit order.
        Random random = new Random(20261021);
        for (int run=0; run<1000; run++) {
            List<Integer> ids = new ArrayList<>(List.of(1,2,3,4,5,6,7));
            Collections.shuffle(ids,random);
            p.set(List.of(new int[]{1, run%2==0?1:2,run%2==0?2:1,run%2==0?1:2},
                    new int[]{4,4,5,run%2==0?4:5}), id -> true);
            List<Integer> projected = p.project(ids);
            check(projected.size()==5 && new HashSet<>(projected).size()==5);
            check(projected.containsAll(List.of(1,3,4,6,7)));
            int dragged=ids.get(random.nextInt(ids.size()));
            int target=ids.get(random.nextInt(ids.size()));
            boolean after=random.nextBoolean();
            List<Integer> moved=p.moveUnit(ids,dragged,target,after);
            check(new HashSet<>(moved).equals(new HashSet<>(ids)) && moved.size()==ids.size());
            if (p.representative(dragged)==p.representative(target)) {
                check(moved.equals(ids));
            } else {
                List<Integer> oldUnit=new ArrayList<>(),newUnit=new ArrayList<>();
                List<Integer> oldOther=new ArrayList<>(),newOther=new ArrayList<>();
                for(int id:ids) (p.representative(id)==p.representative(dragged)?oldUnit:oldOther).add(id);
                for(int id:moved) (p.representative(id)==p.representative(dragged)?newUnit:newOther).add(id);
                check(oldUnit.equals(newUnit) && oldOther.equals(newOther));
                check(moved.indexOf(newUnit.get(newUnit.size()-1))-moved.indexOf(newUnit.get(0))
                        ==newUnit.size()-1);
            }
        }
        System.out.println("ArcSplitPairProjectionTest PASS (15 scenarios + 1000 reordered snapshots)");
    }
}
