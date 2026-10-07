// Copyright 2026 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package org.chromium.chrome.browser.arc;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.IntPredicate;

/** Profile-owned Arc metadata. Native TabModel remains the owner of every real tab. */
public final class ArcSidebarState {
    private static final int VERSION = 1;
    private static final int MAX_ITEMS = 10000;
    private static final int MAX_SERIALIZED = 1048576;

    public static final class Space {
        public final String id;
        public final String name;
        private Space(String id, String name) { this.id = id; this.name = name; }
    }
    public static final class Folder {
        public final String id;
        public final String spaceId;
        public final String parentId;
        public final String name;
        private Folder(String id, String spaceId, String parentId, String name) {
            this.id = id; this.spaceId = spaceId; this.parentId = parentId; this.name = name;
        }
    }
    public static final class Entry {
        public final String id;
        public final String spaceId;
        public final String folderId;
        public final String url;
        public final String title;
        public final Integer tabId;
        public final boolean favorite;
        private Entry(String id, String spaceId, String folderId, String url, String title,
                Integer tabId, boolean favorite) {
            this.id = id; this.spaceId = spaceId; this.folderId = folderId;
            this.url = url; this.title = title; this.tabId = tabId; this.favorite = favorite;
        }
        private Entry withTab(Integer tabId) {
            return new Entry(id, spaceId, folderId, url, title, tabId, favorite);
        }
    }

    private final Map<String, Space> mSpaces = new LinkedHashMap<>();
    private final Map<String, Folder> mFolders = new LinkedHashMap<>();
    private final List<Entry> mEntries = new ArrayList<>();
    private final Map<Integer, String> mTabSpaces = new LinkedHashMap<>();
    private String mSelected;

    public ArcSidebarState() { mSelected = addSpace("Personal"); }
    public String selectedSpace() { return mSelected; }
    public List<Space> spaces() { return List.copyOf(mSpaces.values()); }
    public List<Folder> folders(String spaceId) {
        requireSpace(spaceId);
        List<Folder> result = new ArrayList<>();
        for (Folder folder : mFolders.values()) {
            if (spaceId.equals(folder.spaceId)) result.add(folder);
        }
        return Collections.unmodifiableList(result);
    }
    public List<Entry> entries(String spaceId) {
        requireSpace(spaceId);
        List<Entry> result = new ArrayList<>();
        for (Entry entry : mEntries) {
            if (!entry.favorite && spaceId.equals(entry.spaceId)) result.add(entry);
        }
        return Collections.unmodifiableList(result);
    }
    public List<Entry> favorites() {
        List<Entry> result = new ArrayList<>();
        for (Entry entry : mEntries) if (entry.favorite) result.add(entry);
        return Collections.unmodifiableList(result);
    }
    public Entry entry(String id) {
        for (Entry entry : mEntries) if (entry.id.equals(id)) return entry;
        throw invalid();
    }
    public void selectSpace(String id) { requireSpace(id); mSelected = id; }
    public String addSpace(String name) {
        bounded(name, 256); capacity(mSpaces.size());
        String id = UUID.randomUUID().toString();
        mSpaces.put(id, new Space(id, name));
        return id;
    }
    public String addFolder(String spaceId, String parentId, String name) {
        requireFolder(spaceId, parentId); bounded(name, 256); capacity(mFolders.size());
        String id = UUID.randomUUID().toString();
        mFolders.put(id, new Folder(id, spaceId, parentId, name));
        return id;
    }
    public void moveFolder(String id, String parentId) {
        Folder folder = mFolders.get(id);
        if (folder == null) throw invalid();
        requireFolder(folder.spaceId, parentId);
        for (String ancestor = parentId; ancestor != null;
                ancestor = mFolders.get(ancestor).parentId) {
            if (id.equals(ancestor)) throw invalid();
        }
        mFolders.put(id, new Folder(id, folder.spaceId, parentId, folder.name));
    }
    public String pin(String spaceId, String folderId, String url, String title, Integer tabId) {
        requireFolder(spaceId, folderId);
        return addEntry(spaceId, folderId, url, title, tabId, false);
    }
    public String favorite(String url, String title, Integer tabId) {
        return addEntry(null, null, url, title, tabId, true);
    }
    private String addEntry(String spaceId, String folderId, String url, String title,
            Integer tabId, boolean favorite) {
        bounded(url, 8192); bounded(title, 256); requireFreeTab(tabId, null);
        capacity(mEntries.size());
        String id = UUID.randomUUID().toString();
        mEntries.add(new Entry(id, spaceId, folderId, url, title, tabId, favorite));
        if (tabId != null && !favorite) associateTab(tabId, spaceId);
        return id;
    }
    public void bindTab(String id, int tabId) {
        Entry entry = entry(id); requireFreeTab(tabId, id);
        mEntries.set(mEntries.indexOf(entry), entry.withTab(tabId));
        // A newly created native tab can be adopted synchronously by ArcNativeTabSession before
        // this bind completes. Favorites are shared across Spaces, so scrub that temporary owner.
        if (entry.favorite) mTabSpaces.remove(tabId);
        else associateTab(tabId, entry.spaceId);
    }
    public void tabClosed(int tabId) {
        for (int i = 0; i < mEntries.size(); i++) {
            if (Integer.valueOf(tabId).equals(mEntries.get(i).tabId)) {
                mEntries.set(i, mEntries.get(i).withTab(null));
            }
        }
        mTabSpaces.remove(tabId);
    }
    /**
     * Clears IDs only when profile-wide native authority confirms they may be forgotten. A local
     * Activity's restored tab list cannot prove another window's persisted IDs absent. Closed
     * pinned entries keep their canonical URL/title, and pending closures retain their bindings.
     */
    public void reconcileTabsAfterRestore(IntPredicate mayForgetTabId) {
        for (int i = 0; i < mEntries.size(); i++) {
            Entry entry = mEntries.get(i);
            if (entry.tabId != null && mayForgetTabId.test(entry.tabId)) {
                mEntries.set(i, entry.withTab(null));
            }
        }
        mTabSpaces.keySet().removeIf(mayForgetTabId::test);
        // Favorites are global collection entries, not Space-owned open-tab rows. Repair any
        // residual ownership left by a synchronous didAddTab() or older persisted state.
        for (Entry entry : mEntries) {
            if (entry.favorite && entry.tabId != null) mTabSpaces.remove(entry.tabId);
        }
    }
    public void associateTab(int tabId, String spaceId) {
        if (tabId < 0) throw invalid();
        requireSpace(spaceId);
        if (!mTabSpaces.containsKey(tabId)) capacity(mTabSpaces.size());
        mTabSpaces.put(tabId, spaceId);
    }
    public boolean hasTabSpace(int tabId) { return mTabSpaces.containsKey(tabId); }
    public boolean isFavoriteTab(int tabId) {
        for (Entry entry : mEntries) {
            if (entry.favorite && Integer.valueOf(tabId).equals(entry.tabId)) return true;
        }
        return false;
    }
    /** Returns whether a native tab is valid in the selected Arc context for selection. */
    public boolean visibleTab(int tabId) {
        if (isFavoriteTab(tabId)) return true;
        String owner = mTabSpaces.get(tabId);
        return owner != null && mSelected.equals(owner);
    }

    /**
     * Returns whether a real native tab belongs in the active Space open-tab presentation. Favorites
     * are rendered by the shared Favorites collection and are intentionally not duplicated here.
     * While restore is pending, an unknown tab remains visible rather than being misclassified or
     * adopted. Once restore is authoritative, unknown tabs are expected to be adopted by
     * ArcNativeTabSession.
     */
    public boolean visibleTabForPresentation(int tabId, boolean restoreComplete) {
        if (isFavoriteTab(tabId)) return false;
        String owner = mTabSpaces.get(tabId);
        if (owner != null) return mSelected.equals(owner);
        return !restoreComplete;
    }
    public void move(String id, String spaceId, String folderId, int index) {
        Entry entry = entry(id);
        if (entry.favorite) throw invalid();
        requireFolder(spaceId, folderId);
        int size = entries(spaceId).size() - (spaceId.equals(entry.spaceId) ? 1 : 0);
        if (index < 0 || index > size) throw invalid();
        mEntries.remove(entry);
        Entry moved = new Entry(id, spaceId, folderId, entry.url, entry.title, entry.tabId, false);
        int at = mEntries.size();
        int ordinal = 0;
        for (int i = 0; i < mEntries.size(); i++) {
            Entry candidate = mEntries.get(i);
            if (!candidate.favorite && spaceId.equals(candidate.spaceId)) {
                if (ordinal++ == index) { at = i; break; }
            }
        }
        mEntries.add(at, moved);
        if (entry.tabId != null) associateTab(entry.tabId, spaceId);
    }
    public void unpin(String id) {
        Entry removed = entry(id);
        mEntries.remove(removed);
        // Removing a global Favorite must not orphan its still-open native tab from every Space.
        if (removed.favorite && removed.tabId != null) associateTab(removed.tabId, mSelected);
    }

    /** Changes placement without replacing the canonical entry or native tab identity. */
    public void setFavorite(String id, boolean favorite) {
        Entry entry = entry(id);
        if (entry.favorite == favorite && (favorite || mSelected.equals(entry.spaceId))) return;
        mEntries.set(mEntries.indexOf(entry), new Entry(entry.id,
                favorite ? null : mSelected, null, entry.url, entry.title, entry.tabId, favorite));
        if (entry.tabId != null) {
            if (favorite) mTabSpaces.remove(entry.tabId);
            else associateTab(entry.tabId, mSelected);
        }
    }

    private void requireSpace(String id) { if (!mSpaces.containsKey(id)) throw invalid(); }
    private void requireFolder(String spaceId, String id) {
        requireSpace(spaceId);
        if (id != null) {
            Folder folder = mFolders.get(id);
            if (folder == null || !spaceId.equals(folder.spaceId)) throw invalid();
        }
    }
    private void requireFreeTab(Integer tabId, String owner) {
        if (tabId == null) return;
        if (tabId < 0) throw invalid();
        for (Entry entry : mEntries) {
            if (tabId.equals(entry.tabId) && !entry.id.equals(owner)) throw invalid();
        }
    }
    private static void bounded(String value, int limit) {
        if (value == null || value.isEmpty() || value.length() > limit) throw invalid();
    }
    private static void capacity(int count) { if (count >= MAX_ITEMS) throw invalid(); }
    private static IllegalArgumentException invalid() {
        return new IllegalArgumentException("Invalid Arc sidebar state");
    }
    private static void nullable(DataOutputStream output, String value) throws IOException {
        output.writeBoolean(value != null);
        if (value != null) output.writeUTF(value);
    }
    private static String nullable(DataInputStream input) throws IOException {
        return input.readBoolean() ? input.readUTF() : null;
    }
    private static int count(DataInputStream input) throws IOException {
        int result = input.readInt();
        if (result < 0 || result > MAX_ITEMS) throw invalid();
        return result;
    }
    public String serialize() {
        try {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            DataOutputStream output = new DataOutputStream(bytes);
            output.writeInt(VERSION); output.writeUTF(mSelected);
            output.writeInt(mSpaces.size());
            for (Space space : mSpaces.values()) {
                output.writeUTF(space.id); output.writeUTF(space.name);
            }
            output.writeInt(mFolders.size());
            for (Folder folder : mFolders.values()) {
                output.writeUTF(folder.id); output.writeUTF(folder.spaceId);
                nullable(output, folder.parentId); output.writeUTF(folder.name);
            }
            output.writeInt(mEntries.size());
            for (Entry entry : mEntries) {
                output.writeUTF(entry.id); output.writeBoolean(entry.favorite);
                nullable(output, entry.spaceId); nullable(output, entry.folderId);
                output.writeUTF(entry.url); output.writeUTF(entry.title);
                output.writeInt(entry.tabId == null ? -1 : entry.tabId);
            }
            output.writeInt(mTabSpaces.size());
            for (Map.Entry<Integer, String> entry : mTabSpaces.entrySet()) {
                output.writeInt(entry.getKey()); output.writeUTF(entry.getValue());
            }
            output.flush();
            String result = Base64.getEncoder().encodeToString(bytes.toByteArray());
            if (result.length() > MAX_SERIALIZED) throw invalid();
            return result;
        } catch (IOException error) { throw invalid(); }
    }
    public static ArcSidebarState deserialize(String encoded) {
        bounded(encoded, MAX_SERIALIZED);
        try {
            DataInputStream input = new DataInputStream(new ByteArrayInputStream(
                    Base64.getDecoder().decode(encoded)));
            if (input.readInt() != VERSION) throw invalid();
            String selected = input.readUTF();
            ArcSidebarState state = new ArcSidebarState();
            state.mSpaces.clear();
            int spaces = count(input);
            for (int i = 0; i < spaces; i++) {
                String id = input.readUTF(), name = input.readUTF();
                bounded(id, 64); bounded(name, 256);
                if (state.mSpaces.put(id, new Space(id, name)) != null) throw invalid();
            }
            state.selectSpace(selected);
            int folders = count(input);
            for (int i = 0; i < folders; i++) {
                String id = input.readUTF(), space = input.readUTF(), parent = nullable(input);
                String name = input.readUTF();
                bounded(id, 64); bounded(name, 256); state.requireSpace(space);
                if (state.mFolders.put(id, new Folder(id, space, parent, name)) != null) throw invalid();
            }
            for (Folder folder : state.mFolders.values()) {
                state.requireFolder(folder.spaceId, folder.parentId);
                Set<String> seen = new java.util.HashSet<>();
                for (String ancestor = folder.id; ancestor != null;
                        ancestor = state.mFolders.get(ancestor).parentId) {
                    if (!seen.add(ancestor)) throw invalid();
                }
            }
            int entries = count(input);
            Set<String> entryIds = new java.util.HashSet<>();
            for (int i = 0; i < entries; i++) {
                String id = input.readUTF(); boolean favorite = input.readBoolean();
                String space = nullable(input), folder = nullable(input);
                String url = input.readUTF(), title = input.readUTF(); int nativeId = input.readInt();
                bounded(id, 64); bounded(url, 8192); bounded(title, 256);
                if (!entryIds.add(id) || nativeId < -1) throw invalid();
                if (favorite) { if (space != null || folder != null) throw invalid(); }
                else state.requireFolder(space, folder);
                Integer tabId = nativeId == -1 ? null : nativeId;
                state.requireFreeTab(tabId, null);
                state.mEntries.add(new Entry(id, space, folder, url, title, tabId, favorite));
            }
            int tabs = count(input);
            for (int i = 0; i < tabs; i++) {
                int tab = input.readInt(); String space = input.readUTF();
                if (state.mTabSpaces.containsKey(tab)) throw invalid();
                state.associateTab(tab, space);
            }
            for (Entry entry : state.mEntries) {
                if (!entry.favorite && entry.tabId != null
                        && !entry.spaceId.equals(state.mTabSpaces.get(entry.tabId))) throw invalid();
            }
            if (input.read() != -1) throw invalid();
            return state;
        } catch (IOException error) { throw invalid(); }
    }
}
