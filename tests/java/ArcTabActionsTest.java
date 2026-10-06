import java.util.HashSet;
import java.util.Set;
import org.chromium.chrome.browser.arc.ArcSidebarState;
import org.chromium.chrome.browser.arc.ArcSidebarStore;
import org.chromium.chrome.browser.arc.ArcTabActions;

/** Real controller/state, simulated boundary only for commands requiring Chromium TabModel. */
public final class ArcTabActionsTest {
    private static final class Native implements ArcTabActions.NativeTabs {
        final Set<Integer> ids = new HashSet<>();
        int next = 100, opened, selected = -1, closeRequested = -1, pinned = -1;
        boolean failOpen;
        public boolean exists(int id) { return ids.contains(id); }
        public int open(String url) {
            if (failOpen) return -1;
            opened++; int id = next++; ids.add(id); return id;
        }
        public void select(int id) { if (!exists(id)) throw new AssertionError("Invalid selection"); selected = id; }
        public void close(int id) { closeRequested = id; }
        public void pin(int id) { pinned = id; }
        public void unpin(int id) { if (pinned == id) pinned = -1; }
    }
    private static final class Storage implements ArcSidebarStore.Persistence {
        String value = "";
        boolean fail;
        public String read() { return value; }
        public void write(String value) {
            if (fail) throw new IllegalStateException("synthetic failure");
            this.value = value;
        }
    }
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        Storage persistence = new Storage();
        ArcSidebarStore store = new ArcSidebarStore(persistence);
        ArcSidebarState state = store.load();
        String entry = state.pin(state.selectedSpace(), null, "https://example.test/", "Inicio", null);
        store.save(state);
        Native nativeTabs = new Native();
        ArcTabActions actions = new ArcTabActions(store, nativeTabs);
        check(actions.selectOrOpen(entry) == ArcTabActions.Result.OPENED, "Closed pin opens a real tab");
        check(nativeTabs.opened == 1 && nativeTabs.selected == 100 && nativeTabs.pinned == 100,
                "New association uses real native open/select/pin commands");
        check(store.load().entry(entry).tabId == 100, "Opened native ID persisted");
        check(actions.selectOrOpen(entry) == ArcTabActions.Result.SELECTED, "Repeated click selects");
        check(nativeTabs.opened == 1, "Repeated click creates no duplicate");
        actions.closeTab(100);
        check(nativeTabs.closeRequested == 100, "Close invokes native controller");
        check(store.load().entry(entry).tabId == 100, "Request alone does not erase association before native close");
        nativeTabs.ids.remove(100);
        actions.onTabClosed(100);
        check(store.load().entry(entry).tabId == null, "Confirmed close clears association");
        check(store.load().entry(entry).url.equals("https://example.test/"), "Confirmed close preserves canonical pin");
        nativeTabs.failOpen = true;
        check(actions.selectOrOpen(entry) == ArcTabActions.Result.NOT_OPENED, "Native creation failure surfaces");
        check(store.load().entry(entry).tabId == null, "Creation failure does not persist a fake ID");
        nativeTabs.failOpen = false;
        persistence.fail = true;
        check(actions.selectOrOpen(entry) == ArcTabActions.Result.PERSISTENCE_ERROR, "Metadata write failure surfaces");
        int nativeCount = nativeTabs.opened;
        check(actions.selectOrOpen(entry) == ArcTabActions.Result.PERSISTENCE_ERROR, "Write failure can be retried");
        check(nativeTabs.opened == nativeCount, "Failed persistence does not duplicate the newly opened native tab");
        persistence.fail = false;
        check(actions.selectOrOpen(entry) == ArcTabActions.Result.SELECTED, "Recovered write binds the existing tab");
        check(nativeTabs.opened == nativeCount, "Recovery does not create another tab");
        actions.destroy();
        check(actions.selectOrOpen(entry) == ArcTabActions.Result.NOT_OPENED, "Destroyed controller cannot open tab");
        check(nativeTabs.opened == nativeCount, "No native effect after destruction");
        System.out.println("ArcTabActions: reopen/select/close, native failure, failed metadata retry and lifecycle passed (command boundary simulated)");
    }
}
