import java.util.HashSet;
import java.util.Set;
import org.chromium.chrome.browser.arc.ArcSidebarState;
import org.chromium.chrome.browser.arc.ArcSidebarStore;
import org.chromium.chrome.browser.arc.ArcTabActions;
import org.chromium.chrome.browser.arc.ArcCollectionsController;

/** Production collection/state logic; only the Chromium command boundary is simulated. */
// SIMULATED_BOUNDARY: production Arc controller/state with a fake native-tab command boundary.
public final class ArcCollectionsControllerTest {
    private static final class Native implements ArcTabActions.NativeTabs {
        Storage persistence;
        final Set<Integer> ids = new HashSet<>();
        int pinned = -1, unpinned = -1, selected = -1, opens, spaceChanges, stateChanges, closeCalls;
        public boolean exists(int id) { return ids.contains(id); }
        public int open(String url) { opens++; ids.add(100 + opens); return 100 + opens; }
        public void select(int id) { selected = id; }
        public void pin(int id) { pinned = id; }
        public void unpin(int id) { unpinned = id; }
        public void close(int id) { closeCalls++; }
        public void onSpaceChanged(ArcSidebarState state) { published(state); spaceChanges++; }
        public void onArcStateChanged(ArcSidebarState state) { published(state); stateChanges++; }
        private void published(ArcSidebarState state) {
            if (persistence != null) check(state.serialize().equals(persistence.value),
                    "Native callback must observe already persisted state");
        }
    }
    private static final class Storage implements ArcSidebarStore.Persistence {
        String value = "";
        boolean fail;
        public String read() { return value; }
        public void write(String state) {
            if (fail) throw new IllegalStateException("synthetic write failure");
            value = state;
        }
    }
    private static void check(boolean condition, String reason) {
        if (!condition) throw new AssertionError(reason);
    }
    private static void delete(ArcCollectionsController controller, String method, String id) {
        try { ArcCollectionsController.class.getMethod(method, String.class).invoke(controller, id); }
        catch (java.lang.reflect.InvocationTargetException failure) {
            throw (RuntimeException) failure.getCause();
        } catch (ReflectiveOperationException failure) { throw new AssertionError("Missing " + method, failure); }
    }
    private static void safeDeletion() {
        Storage persistence = new Storage();
        ArcSidebarStore store = new ArcSidebarStore(persistence);
        Native tabs = new Native(); tabs.persistence = persistence; tabs.ids.add(51);
        ArcCollectionsController controller = new ArcCollectionsController(store, new ArcTabActions(store, tabs), tabs);
        String target = controller.state().selectedSpace();
        String source = controller.createSpace("Delete me");
        String folder = controller.createFolder(null, "Dissolve me");
        String entry = controller.rememberTab(51, "https://safe.test", "Safe", false);
        controller.move(entry, source, folder, 0);
        int spaces = tabs.spaceChanges, updates = tabs.stateChanges;
        String before = persistence.value;
        persistence.fail = true;
        try { delete(controller, "deleteFolder", folder); throw new AssertionError("Failed folder deletion accepted"); }
        catch (IllegalStateException expected) {}
        try { delete(controller, "deleteSpace", source); throw new AssertionError("Failed Space deletion accepted"); }
        catch (IllegalStateException expected) {}
        check(before.equals(persistence.value) && before.equals(controller.state().serialize()),
                "Failed deletions retain both stored and published metadata");
        check(tabs.spaceChanges == spaces && tabs.stateChanges == updates && tabs.ids.contains(51)
                        && tabs.closeCalls == 0 && tabs.unpinned == -1,
                "Failed deletions issue no native tab or observer commands");
        persistence.fail = false;
        delete(controller, "deleteFolder", folder);
        check(controller.state().entry(entry).folderId == null && tabs.stateChanges == updates + 1,
                "Folder deletion publishes promoted entries after save");
        delete(controller, "deleteSpace", source);
        check(controller.state().selectedSpace().equals(target) && tabs.spaceChanges == spaces + 1,
                "Space deletion selects retained Space after save");
        check(controller.state().entry(entry).tabId == 51 && tabs.ids.contains(51)
                        && tabs.closeCalls == 0 && tabs.unpinned == -1,
                "Safe deletion preserves real tab and pinned state");
        controller.destroy();
        try { delete(controller, "deleteFolder", folder); throw new AssertionError("Destroyed command accepted"); }
        catch (IllegalStateException expected) {}
    }
    public static void main(String[] args) {
        safeDeletion();
        Storage persistence = new Storage();
        ArcSidebarStore store = new ArcSidebarStore(persistence);
        Native nativeTabs = new Native(); nativeTabs.ids.add(7);
        ArcTabActions actions = new ArcTabActions(store, nativeTabs);
        ArcCollectionsController controller = new ArcCollectionsController(store, actions, nativeTabs);
        String personal = controller.state().selectedSpace();
        String pinned = controller.rememberTab(7, "https://example.test/", "Example", false);
        check(nativeTabs.pinned == 7, "real pin command issued");
        check(controller.state().entries(personal).size() == 1, "persisted pin rendered in selected Space");
        check(controller.open(pinned) == ArcTabActions.Result.SELECTED && nativeTabs.opens == 0,
                "existing real tab selected without creating duplicate");
        check(controller.rememberTab(7, "https://example.test/", "Example", true).equals(pinned),
                "conversion keeps entry identity");
        check(controller.state().favorites().size() == 1 && controller.state().entries(personal).isEmpty(),
                "favorite replaces pin placement");
        String work = controller.createSpace("Work");
        check(controller.state().selectedSpace().equals(work), "new Space selected atomically");
        check(nativeTabs.spaceChanges == 1, "native session notified only after Space persistence");
        check(controller.state().favorites().get(0).id.equals(pinned), "favorites shared across Spaces");
        check(controller.rememberTab(7, "https://example.test/", "Example", false).equals(pinned),
                "moving back from favorites keeps identity");
        check(controller.state().entries(work).get(0).id.equals(pinned), "pin moved into current Space");
        String folder = controller.createFolder(null, "Reading");
        int beforeMoveRefresh = nativeTabs.stateChanges;
        controller.move(pinned, work, folder, 0);
        check(controller.state().entry(pinned).folderId.equals(folder), "folder move persists");
        check(nativeTabs.stateChanges == beforeMoveRefresh + 1,
                "moving ownership refreshes Arc presentation without switching Spaces");
        controller.selectSpace(personal);
        check(controller.state().entries(controller.state().selectedSpace()).isEmpty(),
                "Space selection changes actual visible pinned collection");
        check(nativeTabs.spaceChanges == 2, "existing Space switch reaches native session");
        controller.selectSpace(work);
        check(nativeTabs.spaceChanges == 3, "switching back reaches native session");
        check(nativeTabs.closeCalls == 0 && nativeTabs.ids.contains(7),
                "Space switches never close real tabs in the global native model");
        ArcSidebarState reopened = new ArcSidebarStore(persistence).load();
        check(reopened.selectedSpace().equals(work) && reopened.entry(pinned).folderId.equals(folder),
                "Space/folder selection survives reopened store");
        persistence.fail = true;
        try { controller.remove(pinned); throw new AssertionError("failed removal accepted"); }
        catch (IllegalStateException expected) {}
        check(nativeTabs.unpinned == -1 && controller.state().entry(pinned) != null,
                "failed persistence leaves native pin and metadata intact");
        persistence.fail = false;
        controller.remove(pinned);
        check(nativeTabs.unpinned == 7 && controller.state().entries(work).isEmpty(),
                "removal reuses native unpin and keeps real tab open");

        nativeTabs.ids.add(8);
        String favorite = controller.rememberTab(8, "https://shared.test/", "Shared", true);
        check(!controller.state().hasTabSpace(8), "Favorite has no Space ownership while shared");
        controller.remove(favorite);
        check(controller.state().hasTabSpace(8) && controller.state().visibleTabForPresentation(8, true),
                "removing an open Favorite adopts it into active Space without closing it");
        check(nativeTabs.ids.contains(8) && nativeTabs.closeCalls == 0,
                "removing a Favorite never closes the global native tab");

        nativeTabs.ids.remove(7);
        try { controller.rememberTab(7, "https://example.test/", "Example", false);
            throw new AssertionError("inactive tab accepted"); }
        catch (IllegalStateException expected) {}
        controller.destroy();
        try { controller.createSpace("Late"); throw new AssertionError("destroyed controller wrote state"); }
        catch (IllegalStateException expected) {}
        check(new ArcSidebarStore(null).load().favorites().isEmpty(), "private store receives no regular favorites");
        System.out.println("ArcCollectionsController: native pin/select/unpin, stable conversion, Spaces/folders, reopen and failures passed (command boundary simulated)");
    }
}
