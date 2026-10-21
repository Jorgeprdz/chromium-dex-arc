// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
package org.chromium.chrome.browser.ui.vertical_tabs;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.IntPredicate;

/** Window-owned row identities. Does not own, select, hide or move native tabs. */
public final class ArcSplitPairProjection {
    private final Map<Integer, int[]> mMembers = new HashMap<>();

    /** Snapshots contain stable representative, left, right and active native IDs. */
    public void set(List<int[]> snapshots, IntPredicate eligible) {
        mMembers.clear();
        for (int[] row : snapshots) {
            if (row == null || row.length != 4 || row[1] < 0 || row[2] < 0
                    || row[1] == row[2] || (row[0] != row[1] && row[0] != row[2])
                    || (row[3] != row[1] && row[3] != row[2])
                    || mMembers.containsKey(row[1]) || mMembers.containsKey(row[2])
                    || !eligible.test(row[1]) || !eligible.test(row[2])) continue;
            int[] copy = row.clone();
            mMembers.put(copy[1], copy);
            mMembers.put(copy[2], copy);
        }
    }
    public int representative(int id) {
        int[] p=mMembers.get(id); return p==null?id:p[0];
    }
    public int actionId(int id) {
        int[] p=mMembers.get(id); return p==null?id:p[3];
    }
    public int peer(int id) {
        int[] p=mMembers.get(id); return p==null?-1:(id==p[1]?p[2]:p[1]);
    }
    public int[] pair(int id) {
        int[] p=mMembers.get(id); return p==null?null:p.clone();
    }
    public List<Integer> project(List<Integer> ids) {
        List<Integer> out=new ArrayList<>();Set<Integer> seen=new HashSet<>();
        for(int id:ids) {int row=representative(id);if(seen.add(row))out.add(row);}
        return out;
    }
    /** Move both identities before a current target unit, preserving native within-unit order. */
    public List<Integer> moveUnit(List<Integer> ids,int dragged,int target) {
        return moveUnit(ids, dragged, target, false);
    }
    public List<Integer> moveUnit(List<Integer> ids,int dragged,int target, boolean after) {
        List<Integer> out=new ArrayList<>(ids);
        int representative=representative(dragged),targetRow=representative(target);
        if(representative==targetRow)return out;
        List<Integer> unit=new ArrayList<>();
        for(int id:ids)if(representative(id)==representative)unit.add(id);
        if(unit.isEmpty() || !ids.contains(target))return out;
        out.removeAll(unit);
        int at=0;
        while(at<out.size() && representative(out.get(at))!=targetRow)at++;
        if (after) {
            // A target pair can be non-adjacent in the native model; insert after its last ID.
            for (int i = at; i < out.size(); i++) {
                if (representative(out.get(i)) == targetRow) at = i + 1;
            }
        }
        out.addAll(at,unit);return out;
    }
}
