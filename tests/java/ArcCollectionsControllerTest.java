import java.util.HashSet;
import java.util.Set;
import org.chromium.chrome.browser.arc.ArcSidebarState;
import org.chromium.chrome.browser.arc.ArcSidebarStore;
import org.chromium.chrome.browser.arc.ArcTabActions;
import org.chromium.chrome.browser.arc.ArcCollectionsController;

/** Production collection/state logic; only the Chromium command boundary is simulated. */
public final class ArcCollectionsControllerTest {
    private static final class Native implements ArcTabActions.NativeTabs {
        final Set<Integer> ids = new HashSet<>();
        int pinned = -1, unpinned = -1, selected = -1, opens, spaceChanges;
        public boolean exists(int id) { return ids.contains(id); }
        public int open(String url) { opens++; ids.add(100 + opens); return 100 + opens; }
        public void select(int id) { selected = id; }
        public void pin(int id) { pinned = id; }
        public void unpin(int id) { unpinned = id; }
        public void close(int id) {}
        public void onSpaceChanged(ArcSidebarState state) { spaceChanges++; }
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
    public static void main(String[] args) {
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
        controller.move(pinned, work, folder, 0);
        check(controller.state().entry(pinned).folderId.equals(folder), "folder move persists");
        controller.selectSpace(personal);
        check(controller.state().entries(controller.state().selectedSpace()).isEmpty(),
                "Space selection changes actual visible pinned collection");
        check(nativeTabs.spaceChanges == 2, "existing Space switch reaches native session");
        controller.selectSpace(work);
        check(nativeTabs.spaceChanges == 3, "switching back reaches native session");
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
