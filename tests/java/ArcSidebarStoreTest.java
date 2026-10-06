import org.chromium.chrome.browser.arc.ArcSidebarState;
import org.chromium.chrome.browser.arc.ArcSidebarStore;

public final class ArcSidebarStoreTest {
    private static final class Storage implements ArcSidebarStore.Persistence {
        String value = "";
        boolean failWrites;
        public String read() { return value; }
        public void write(String next) {
            if (failWrites) throw new IllegalStateException("synthetic write failure");
            value = next;
        }
    }
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        Storage storage = new Storage();
        ArcSidebarStore store = new ArcSidebarStore(storage);
        ArcSidebarState current = store.load();
        String id = current.pin(current.selectedSpace(), null, "https://example.test/", "Inicio", 3);
        store.save(current);
        ArcSidebarStore reopened = new ArcSidebarStore(storage);
        check(reopened.load().entry(id).url.equals("https://example.test/"), "Profile storage reopens pin");
        ArcSidebarState uncommitted = reopened.load();
        uncommitted.tabClosed(3);
        check(reopened.load().entry(id).tabId == 3, "Uncommitted draft does not mutate cached state");
        storage.failWrites = true;
        try { reopened.save(uncommitted); throw new AssertionError("Write failure must surface"); }
        catch (IllegalStateException expected) { }
        check(reopened.load().entry(id).tabId == 3, "Write failure preserves previous committed state");
        check(new ArcSidebarStore(storage).load().entry(id).tabId == 3, "Write failure preserves storage");
        ArcSidebarStore privateStore = new ArcSidebarStore(null);
        ArcSidebarState privateState = privateStore.load();
        privateState.pin(privateState.selectedSpace(), null, "https://private.test/", "Privado", 4);
        privateStore.save(privateState);
        check(privateStore.load().entries(privateState.selectedSpace()).size() == 1, "Private state lives in memory");
        ArcSidebarState newPrivate = new ArcSidebarStore(null).load();
        check(newPrivate.entries(newPrivate.selectedSpace()).isEmpty(),
                "New private session has no prior entries");
        check(!storage.value.contains("private.test"), "Private store never writes regular persistence");
        Storage damaged = new Storage(); damaged.value = "invalid-original";
        try { new ArcSidebarStore(damaged).load(); throw new AssertionError("Invalid profile state must surface"); }
        catch (IllegalArgumentException expected) { }
        check(damaged.value.equals("invalid-original"), "Invalid state is not replaced silently");
        System.out.println("ArcSidebarStore: restart, draft isolation, failed write, private memory and damaged state passed");
    }
}
