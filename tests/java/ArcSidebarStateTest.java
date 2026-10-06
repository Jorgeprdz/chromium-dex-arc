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
    public static void main(String[] args) {
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
        check(state.visibleTab(9), "Favorite native tab is shared");
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
        restored.reconcileTabs(java.util.Set.of(10, 11, 13));
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
        System.out.println("ArcSidebarState: identity, Spaces, closed pins, folders, roundtrip and invalid operations passed");
    }
}
