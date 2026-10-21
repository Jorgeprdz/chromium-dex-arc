// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Associations for one native TabModel. Owns IDs and geometry, never Tabs or WebContents. */
final class ArcSplitPairStore {
    static final class Pair {
        final int representativeId;
        final ArcSplitState state;
        Pair(int representativeId, ArcSplitState state) {
            this.representativeId = representativeId;
            this.state = state;
        }
    }
    private final Map<Integer, Pair> mPairs = new LinkedHashMap<>();
    private final Map<Integer, Pair> mMembers = new LinkedHashMap<>();
    Pair member(int id) { return mMembers.get(id); }
    List<Pair> pairs() { return new ArrayList<>(mPairs.values()); }
    boolean add(int representative, ArcSplitState state) {
        if (!state.isSplit() || (representative != state.leftId() && representative != state.rightId())
                || mPairs.containsKey(representative) || member(state.leftId()) != null
                || member(state.rightId()) != null) return false;
        Pair pair = new Pair(representative, state);
        mPairs.put(representative, pair);
        mMembers.put(state.leftId(), pair);
        mMembers.put(state.rightId(), pair);
        return true;
    }
    void remove(Pair pair) {
        if (pair == null) return;
        mPairs.remove(pair.representativeId);
        mMembers.remove(pair.state.leftId());
        mMembers.remove(pair.state.rightId());
    }
    List<int[]> snapshot() {
        List<int[]> result = new ArrayList<>();
        for (Pair pair : mPairs.values()) result.add(new int[] {pair.representativeId,
                pair.state.leftId(), pair.state.rightId(), pair.state.activeId()});
        return result;
    }
    String encode() {
        if (mPairs.isEmpty()) return null;
        StringBuilder result = new StringBuilder("v2");
        for (Pair pair : mPairs.values()) {
            ArcSplitState state = pair.state;
            result.append(';').append(pair.representativeId).append(',').append(state.leftId())
                    .append(',').append(state.rightId()).append(',').append(state.activeId())
                    .append(',').append(state.ratio());
        }
        return result.toString();
    }
    /** Invalid entries are independent; duplicate members never overwrite an earlier valid pair. */
    static ArcSplitPairStore decode(String saved) {
        ArcSplitPairStore result = new ArcSplitPairStore();
        if (saved == null) return result;
        boolean versioned = saved.startsWith("v2;");
        for (String row : (versioned ? saved.substring(3) : saved).split(";")) {
            try {
                String[] cells = row.split(",");
                if (cells.length != (versioned ? 5 : 4)) continue;
                int offset = versioned ? 1 : 0;
                int left = Integer.parseInt(cells[offset]), right = Integer.parseInt(cells[offset + 1]);
                int active = Integer.parseInt(cells[offset + 2]);
                float ratio = Float.parseFloat(cells[offset + 3]);
                if (!Float.isFinite(ratio) || ratio < .2f || ratio > .8f) continue;
                ArcSplitState state = new ArcSplitState();
                if (!state.start(left, right) || !state.activate(active)) continue;
                state.setRatio(ratio);
                result.add(versioned ? Integer.parseInt(cells[0]) : left, state);
            } catch (IllegalArgumentException ignored) {
                // Discard only this malformed association.
            }
        }
        return result;
    }
}
