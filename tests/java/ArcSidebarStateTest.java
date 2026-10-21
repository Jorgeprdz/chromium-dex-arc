import org.chromium.chrome.browser.arc.ArcSidebarState;

/** Production state roundtrips, closed-tab retention and structural validation. */
public final class ArcSidebarStateTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    private static void rejected(Runnable action, String message) {
        try { action.run(); throw new AssertionError(message); }
        catch (IllegalArgumentException expected) { }
    }
    private static void delete(ArcSidebarState state, String operation, String id) {
        try { ArcSidebarState.class.getMethod(operation, String.class).invoke(state, id); }
        catch (java.lang.reflect.InvocationTargetException failure) {
            throw (RuntimeException) failure.getCause();
        } catch (ReflectiveOperationException failure) { throw new AssertionError("Missing safe " + operation, failure); }
    }
    private static void safeDeletion() {
        ArcSidebarState state = new ArcSidebarState();
        String source = state.selectedSpace();
        String target = state.addSpace("Remaining");
        String another = state.addSpace("Later");
        String parent = state.addFolder(source, null, "Parent");
        String folder = state.addFolder(source, parent, "Dissolve");
        String child = state.addFolder(source, folder, "Child");
        String nested = state.pin(source, folder, "https://nested.test", "Nested", 41);
        String deeper = state.pin(source, child, "https://deep.test", "Deep", null);
        String global = state.favorite("https://global.test", "Global", 42);
        state.associateTab(43, source);
        state.associateTab(44, another);
        delete(state, "deleteFolder", folder);
        check(state.folders(source).stream().noneMatch(f -> f.id.equals(folder)), "Deleted folder removed");
        check(state.folders(source).stream().anyMatch(f -> f.id.equals(child) && parent.equals(f.parentId)),
                "Child folder promoted with stable identity");
        check(parent.equals(state.entry(nested).folderId) && state.entry(nested).tabId == 41,
                "Dissolved entry promoted without losing native association");
        check(child.equals(state.entry(deeper).folderId), "Deeper contents retain nested identity");
        delete(state, "deleteSpace", source);
        check(state.selectedSpace().equals(target), "First remaining Space selected deterministically");
        check(state.entry(nested).spaceId.equals(target) && state.entry(nested).id.equals(nested),
                "Space deletion transfers pins with stable metadata identity");
        check(state.folders(target).stream().anyMatch(f -> f.id.equals(child) && parent.equals(f.parentId)),
                "Space deletion preserves full folder tree");
        check(state.visibleTab(41) && state.visibleTab(43) && !state.visibleTab(44),
                "Pinned and ordinary native tabs transfer ownership without closing");
        check(state.favorites().get(0).id.equals(global) && !state.hasTabSpace(42),
                "Space deletion retains global Favorites unchanged");
        check(ArcSidebarState.deserialize(state.serialize()).serialize().equals(state.serialize()),
                "Deleted structure roundtrips without dangling references");
        state.selectSpace(target);
        delete(state, "deleteSpace", another);
        check(target.equals(state.selectedSpace()), "Deleting inactive Space keeps active selection");
        String before = state.serialize();
        rejected(() -> delete(state, "deleteSpace", target), "Cannot delete final Space");
        rejected(() -> delete(state, "deleteSpace", "missing"), "Unknown Space deletion rejected");
        rejected(() -> delete(state, "deleteFolder", "missing"), "Unknown folder deletion rejected");
        check(before.equals(state.serialize()), "Rejected deletions leave state unchanged");
    }
    public static void main(String[] args) {
        safeDeletion();
        ArcSidebarState state = new ArcSidebarState();
        String initial = state.selectedSpace();
        String work = state.addSpace("Trabajo");
        String folder = state.addFolder(initial, null, "Lectura");
        String child = state.addFolder(initial, folder, "Archivo");
        String pinned = state.pin(initial, child, "https://example.test/start", "Inicio", 7);
        String other = state.pin(initial, null, "https://other.test/", "Otro", 8);
        String favorite = state.favorite("https://favorite.test/", "Favorito", 9);
        state.associateTab(10, initial);
        state.selectSpace(work);
        state.associateTab(11, work);
        check(state.entries(work).isEmpty(), "Spaces have independent pinned entries");
        check(state.favorites().size() == 1, "Favorites shared across Spaces");
        check(state.visibleTab(11) && !state.visibleTab(10), "Space chooses native tab membership");
        check(state.hasTabSpace(10) && state.hasTabSpace(11), "native tab membership is explicit");
        check(state.visibleTab(9), "Favorite native tab is shared for selection");
        check(!state.visibleTabForPresentation(9, true),
                "Favorite is rendered by its shared collection, not duplicated in open-tab rail");
        check(state.isFavoriteTab(9) && !state.hasTabSpace(9),
                "favorite tabs remain global instead of leaking into one Space");
        state.selectSpace(initial);
        state.tabClosed(7);
        check(state.entry(pinned).tabId == null, "Closed pin loses only native association");
        check(state.entry(pinned).url.equals("https://example.test/start"), "Closed pin retains canonical URL");
        state.bindTab(pinned, 12);
        check(state.entry(pinned).tabId == 12, "Reopened pin binds one real tab");
        state.move(pinned, work, null, 0);
        check(state.entry(pinned).id.equals(pinned), "Move preserves identity");
        check(state.entries(initial).get(0).id.equals(other), "Move removes previous collection entry");
        check(state.entries(work).get(0).id.equals(pinned), "Move inserts requested order");
        state.bindTab(favorite, 13);
        check(state.favorites().get(0).id.equals(favorite), "Favorite identity remains stable");
        String serialized = state.serialize();
        ArcSidebarState restored = ArcSidebarState.deserialize(serialized);
        check(restored.serialize().equals(serialized), "Versioned roundtrip preserves identity and ordering");
        check(restored.entry(pinned).tabId == 12, "Saved association survives serialization");
        restored.reconcileTabsAfterRestore(id -> !java.util.Set.of(10, 11, 13).contains(id));
        check(restored.entry(pinned).tabId == null, "Missing native tab recovers as unopened pin");
        check(restored.entry(pinned).url.equals(state.entry(pinned).url), "Reconciliation retains URL");
        rejected(() -> restored.move(other, work, child, 0), "Cross-Space folder must be rejected");
        rejected(() -> restored.addFolder("missing", null, "bad"), "Unknown Space rejected");
        rejected(() -> restored.moveFolder(folder, child), "Folder cycle rejected");
        rejected(() -> ArcSidebarState.deserialize("future-or-corrupt"), "Invalid persistent state rejected");
        rejected(() -> restored.selectSpace("missing"), "Invalid selection rejected");
        String before = restored.serialize();
        rejected(() -> restored.move(other, work, child, 0), "Invalid move is atomic");
        check(before.equals(restored.serialize()), "Rejected move keeps entire state");
        ArcSidebarState incognito = new ArcSidebarState();
        incognito.pin(incognito.selectedSpace(), null, "https://private.test/", "Privado", 20);
        check(!incognito.serialize().equals(restored.serialize()), "Separate model owns private state");
        check(restored.entries(restored.selectedSpace()).stream().noneMatch(e -> e.tabId != null && e.tabId == 20),
                "Private native associations never enter regular model");
        rejected(() -> restored.addSpace("x".repeat(257)), "Bound names before changing state");

        // REAL_CONTRACT_TEST: production ArcSidebarState restore/presentation invariants. This does not
        // claim to exercise Chromium TabModel observer delivery; that boundary remains static-only here.
        ArcSidebarState lifecycle = new ArcSidebarState();
        String spaceA = lifecycle.selectedSpace();
        String spaceB = lifecycle.addSpace("B");
        String latePin = lifecycle.pin(spaceA, null, "https://late.test/", "Late", 123);
        lifecycle.associateTab(124, spaceB);
        lifecycle.selectSpace(spaceA);
        String preRestore = lifecycle.serialize();
        check(lifecycle.visibleTabForPresentation(123, false),
                "Persisted late tab keeps its Space while restore is pending");
        check(lifecycle.visibleTabForPresentation(999, false),
                "Unknown restore-time tab fails open until restore authority");
        check(preRestore.equals(lifecycle.serialize()),
                "Pre-restore presentation checks never clean persisted metadata");

        ArcSidebarState lateRestored = ArcSidebarState.deserialize(preRestore);
        lateRestored.reconcileTabsAfterRestore(id -> !java.util.Set.of(123, 124).contains(id));
        check(lateRestored.entry(latePin).tabId == 123
                        && lateRestored.visibleTabForPresentation(123, true),
                "Persisted tab that appears by restore completion keeps its original Space ownership");

        ArcSidebarState reordered = new ArcSidebarState();
        String reorderA = reordered.selectedSpace();
        String reorderB = reordered.addSpace("Restore B");
        reordered.associateTab(1, reorderA);
        reordered.associateTab(2, reorderB);
        reordered.associateTab(3, reorderA);
        String ownershipBefore = reordered.serialize();
        reordered.reconcileTabsAfterRestore(id -> !java.util.Set.of(3, 1, 2).contains(id));
        check(ownershipBefore.equals(reordered.serialize()),
                "Restore arrival order cannot reassign Space ownership");

        lifecycle.reconcileTabsAfterRestore(id -> !java.util.Set.of(124, 999).contains(id));
        check(lifecycle.entry(latePin).tabId == null,
                "Missing tab ID is cleaned only by post-restore reconciliation");
        check(lifecycle.entry(latePin).url.equals("https://late.test/"),
                "Closed pinned metadata retains canonical URL after reconciliation");
        check(!lifecycle.visibleTabForPresentation(999, true),
                "Unknown tab is not silently owned after restore");
        lifecycle.associateTab(999, lifecycle.selectedSpace());
        lifecycle.associateTab(999, lifecycle.selectedSpace());
        check(lifecycle.visibleTabForPresentation(999, true),
                "New tab adoption is idempotent and visible in active Space");
        lifecycle.selectSpace(spaceB);
        check(lifecycle.visibleTabForPresentation(124, true)
                        && !lifecycle.visibleTabForPresentation(999, true),
                "Active Space predicate isolates native tab ownership");

        String globalFavorite = lifecycle.favorite(
                "https://shared.test/", "Shared", /* tabId= */ null);
        lifecycle.associateTab(200, lifecycle.selectedSpace());
        lifecycle.bindTab(globalFavorite, 200);
        check(lifecycle.visibleTab(200), "Reopened Favorite remains globally selectable");
        check(!lifecycle.hasTabSpace(200),
                "Favorite bind scrubs synchronous new-tab adoption into active Space");
        check(!lifecycle.visibleTabForPresentation(200, true),
                "Reopened Favorite is not duplicated in active Space open-tab rail");
        lifecycle.unpin(globalFavorite);
        check(lifecycle.hasTabSpace(200) && lifecycle.visibleTabForPresentation(200, true),
                "Removing an open Favorite preserves the tab and adopts it into active Space");

        ArcSidebarState splitSpaces = new ArcSidebarState();
        String firstSpace = splitSpaces.selectedSpace();
        String otherSpace = splitSpaces.addSpace("Other");
        splitSpaces.associateTab(501, firstSpace);
        splitSpaces.associateTab(502, firstSpace);
        splitSpaces.associateTab(503, otherSpace);
        check(splitSpaces.sameTabSpace(501, 502), "Same Space permits a pair");
        splitSpaces.selectSpace(otherSpace);
        check(splitSpaces.sameTabSpace(501, 502), "Inactive Space pair stays compatible");
        check(!splitSpaces.sameTabSpace(501, 503), "Cross Space pair rejected");
        check(!splitSpaces.sameTabSpace(700, 701), "Two unknown tabs are not same Space");
        check(ArcSidebarState.deserialize(splitSpaces.serialize()).sameTabSpace(501,502),
                "Pair Space compatibility survives native metadata roundtrip");
        System.out.println("ArcSidebarState: identity, Spaces, restore authority, closed pins, folders, roundtrip and invalid operations passed");
    }
}
