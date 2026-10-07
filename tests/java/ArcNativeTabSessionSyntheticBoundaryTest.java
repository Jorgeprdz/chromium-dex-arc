import org.chromium.chrome.browser.arc.ArcNativeTabSession;
import org.chromium.chrome.browser.arc.ArcSidebarProfiles;
import org.chromium.chrome.browser.arc.ArcSidebarState;
import org.chromium.chrome.browser.arc.ArcSidebarStore;
import org.chromium.chrome.browser.arc.ArcTabActions;
import org.chromium.chrome.browser.app.tabwindow.TabWindowManagerSingleton;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.tabmodel.TabList;
import org.chromium.chrome.browser.tabmodel.TabModel;
import org.chromium.chrome.browser.tabmodel.TabModelObserver;
import org.chromium.chrome.browser.tabmodel.TabModelSelector;
import org.chromium.chrome.browser.tabmodel.TabRemover;
import org.chromium.chrome.browser.tabwindow.TabWindowManager;
import org.chromium.base.supplier.NullableObservableSupplier;
import org.chromium.components.user_prefs.UserPrefs;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Runs production Arc behavior; native tab/restore/JNI/pref delivery is a synthetic boundary. */
public final class ArcNativeTabSessionSyntheticBoundaryTest {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    // Simulates the consumed native contract, including the separate pending-closure list.
    // It is deliberately test-only, not a replacement production TabModel.
    private static final class SyntheticModel implements TabModel {
        final Profile profile;
        final boolean otr;
        final Map<Integer, Tab> visible = new LinkedHashMap<>();
        final Map<Integer, Tab> pending = new LinkedHashMap<>();
        final List<TabModelObserver> observers = new ArrayList<>();
        boolean restored = true;
        int current = -1, opened, selected, pinned;
        SyntheticModel(Profile p) { profile = p; otr = p != null && p.isOffTheRecord(); }
        SyntheticModel(boolean emptyOtrStub) { profile = null; otr = emptyOtrStub; }
        void add(int id) { visible.put(id, new Tab(id)); if (current < 0) current = id; }
        void emitAdd(int id) {
            add(id);
            for (TabModelObserver o : List.copyOf(observers)) o.didAddTab(visible.get(id), 0, 0, false);
        }
        void completeRestore() {
            restored = true;
            for (TabModelObserver o : List.copyOf(observers)) o.restoreCompleted();
        }
        void pend(int id) {
            Tab tab = visible.remove(id); pending.put(id, tab);
            if (current == id) current = visible.isEmpty() ? -1 : visible.keySet().iterator().next();
        }
        void commit(int id, boolean batch) {
            Tab tab = pending.remove(id);
            if (tab == null) tab = visible.remove(id);
            for (TabModelObserver o : List.copyOf(observers)) {
                if (batch) o.onTabCloseCommitted(List.of(tab), false, true, 0);
                else o.tabClosureCommitted(tab);
            }
        }
        public Profile getProfile() { return profile; }
        public boolean isOffTheRecord() { return otr; }
        public int getCount() { return visible.size(); }
        public Tab getTabAt(int i) { return new ArrayList<>(visible.values()).get(i); }
        public Tab getTabById(int id) { return visible.get(id); }
        public boolean isClosurePending(int id) { return pending.containsKey(id); }
        public void cancelTabClosure(int id) {
            Tab tab = pending.remove(id); if (tab == null) return;
            visible.put(id, tab); current = id;
            for (TabModelObserver o : List.copyOf(observers)) o.tabClosureUndone(tab);
        }
        public void setIndex(int i, int type) { current = getTabAt(i).getId(); selected++; }
        public void pinTab(int id, boolean dialog) { check(visible.containsKey(id), "pin visible native tab"); pinned++; }
        public void unpinTab(int id) {}
        public TabRemover getTabRemover() {
            return (params, dialog) -> { check(params.undo, "Arc closure remains undoable"); pend(params.tab.getId()); };
        }
        public void addObserver(TabModelObserver o) { observers.add(o); }
        public void removeObserver(TabModelObserver o) { observers.remove(o); }
        public boolean isTabModelRestored() { return restored; }
        public NullableObservableSupplier<Tab> getCurrentTabSupplier() { return () -> visible.get(current); }
        public TabList getComprehensiveModel() {
            List<Tab> all = new ArrayList<>(visible.values()); all.addAll(pending.values());
            return new TabList() {
                public int getCount() { return all.size(); }
                public Tab getTabAt(int i) { return all.get(i); }
                public boolean isOffTheRecord() { return otr; }
            };
        }
    }
    private static final class SyntheticSelector implements TabModelSelector {
        final List<TabModel> models;
        boolean initialized = true;
        SyntheticSelector(TabModel... values) { models = List.of(values); }
        public List<TabModel> getModels() { return models; }
        public boolean isTabStateInitialized() { return initialized; }
    }
    private static final class SyntheticManager implements TabWindowManager {
        final List<TabModelSelector> windows = new ArrayList<>(), custom = new ArrayList<>();
        final List<Observer> observers = new ArrayList<>();
        final Set<Integer> reparented = new HashSet<>();
        TabModelSelector archive;
        boolean globalReady, throwSelectors, throwDeletion;
        public void addObserver(Observer o) { observers.add(o); o.onTabStateInitialized(); }
        public void removeObserver(Observer o) { observers.remove(o); }
        public boolean isAllTabStateInitialized() { return globalReady; }
        public Collection<TabModelSelector> getAllTabModelSelectors() {
            if (throwSelectors) throw new IllegalStateException("Authority unavailable");
            return windows;
        }
        public Collection<TabModelSelector> getCustomTabsTabModelSelectors() { return custom; }
        public TabModelSelector getArchivedTabModelSelector() { return archive; }
        public boolean canTabStateBeDeleted(int id) {
            if (throwDeletion) throw new IllegalStateException("Deletion authority unavailable");
            // Exact pinned manager guard: archive readiness and regular tab lookup; the latch
            // and incomplete normal/headless selectors are deliberately NOT checked here.
            if (archive == null || !archive.isTabStateInitialized() || reparented.contains(id)) return false;
            List<TabModelSelector> selectors = new ArrayList<>(windows); selectors.addAll(custom); selectors.add(archive);
            for (TabModelSelector s : selectors) for (TabModel m : s.getModels()) {
                if (m.getTabById(id) != null) return false;
            }
            return true;
        }
        void allReady() {
            globalReady = true;
            for (Observer o : List.copyOf(observers)) o.onAllTabModelStateInitialized();
        }
        void added(SyntheticSelector s) {
            windows.add(s);
            for (Observer o : List.copyOf(observers)) o.onTabModelSelectorAdded(s);
        }
    }
    private static final class Fixture {
        final Profile profile = new Profile(false);
        final SyntheticModel local = new SyntheticModel(profile);
        final SyntheticManager manager = new SyntheticManager();
        final ArcSidebarStore store = ArcSidebarProfiles.getForProfile(profile);
        int refreshes;
        Fixture() {
            local.add(10);
            manager.windows.add(new SyntheticSelector(local, new SyntheticModel(true)));
            manager.archive = new SyntheticSelector(new SyntheticModel(profile));
            TabWindowManagerSingleton.setTabWindowManagerForTesting(manager);
        }
        ArcNativeTabSession attach(SyntheticModel model, boolean active) {
            return new ArcNativeTabSession(model, (params, type, parent) -> {
                model.opened++; int id = 10000 + model.opened; model.emitAdd(id); return model.getTabById(id);
            }, () -> active, () -> refreshes++);
        }
        ArcNativeTabSession attach() { return attach(local, true); }
        String pin(int id) {
            ArcSidebarState state = store.load();
            String entry = state.pin(state.selectedSpace(), null, "https://pin.test/" + id, "Pin " + id, id);
            store.save(state); return entry;
        }
    }

    private static void twoWindows() {
        Fixture f = new Fixture(); SyntheticModel other = new SyntheticModel(f.profile); other.add(20); other.add(21);
        f.manager.windows.add(new SyntheticSelector(other)); f.manager.globalReady = true;
        ArcSidebarState state = f.store.load(); String a = state.selectedSpace(), b = state.addSpace("B");
        String pin = state.pin(a, null, "https://window.test/", "Window A", 20);
        state.associateTab(10, b); state.selectSpace(b); f.store.save(state);
        other.pend(20);
        ArcNativeTabSession session = f.attach();
        check(f.store.load().entry(pin).tabId != null, "Window B must preserve Window A collection binding");
        check(f.store.load().hasTabSpace(20), "Window A Space owner survives Window B restore");
        check(!f.store.load().hasTabSpace(21), "Other window unknown tab is not adopted into B");
        ArcNativeTabSession aSession = f.attach(other, false);
        check(aSession.store() == session.store(), "Exact same profile shares real production store");
        check(!f.store.load().visibleTab(20), "Existing A owner remains A after its adoption");
        session.destroy(); aSession.destroy();
    }
    private static void pendingUndo() {
        Fixture f = new Fixture(); f.local.add(30); String pin = f.pin(30); f.local.pend(30); f.manager.globalReady = true;
        ArcNativeTabSession session = f.attach();
        check(f.store.load().entry(pin).tabId != null, "Comprehensive pending closure preserves pin binding");
        check(f.store.load().hasTabSpace(30), "Pending undo preserves original Space owner");
        int before = f.refreshes;
        check(session.actions().selectOrOpen(pin) == ArcTabActions.Result.SELECTED, "Click undoes same real pinned tab");
        check(f.local.opened == 0 && f.local.getTabById(30) != null, "Undo does not create replacement native tab");
        check(f.refreshes > before, "Undo refreshes native presentation");
        session.actions().closeTab(30);
        check(f.store.load().entry(pin).tabId != null, "Pending close does not clear canonical binding");
        f.local.commit(30, false);
        check(f.store.load().entry(pin).tabId == null, "Final closure clears binding");
        check(f.store.load().entry(pin).url.equals("https://pin.test/30"), "Final closure retains canonical URL");
        f.local.add(31); String batch = f.pin(31); f.local.commit(31, true);
        check(f.store.load().entry(batch).tabId == null, "Batch close commitment clears binding"); session.destroy();
    }
    private static void pendingUnknown() {
        Fixture f = new Fixture(); f.local.add(30); f.local.pend(30);
        ArcNativeTabSession session = f.attach();
        check(f.store.load().hasTabSpace(30), "Unknown comprehensive local tab is adopted while pending closure");
        f.local.cancelTabClosure(30);
        check(f.store.load().hasTabSpace(30), "Native undo preserves adopted membership");
        // A restored/reparented pending tab can arrive without this adapter seeing didAddTab.
        f.local.add(31); f.local.pend(31); f.local.cancelTabClosure(31);
        check(f.store.load().hasTabSpace(31), "Native undo defensively adopts a locally unknown tab"); session.destroy();
    }
    private static void partialRestore() {
        Fixture f = new Fixture(); String late = f.pin(40); f.local.restored = false;
        String before = f.store.load().serialize(); ArcNativeTabSession session = f.attach();
        f.local.emitAdd(11);
        check(before.equals(f.store.load().serialize()), "Pre-restore native additions cannot mutate ownership");
        check(f.local.opened == 0, "Incomplete restore cannot create native tab");
        f.local.completeRestore();
        check(f.store.load().entry(late).tabId != null, "Unloaded window metadata survives local restore completion");
        check(f.store.load().hasTabSpace(11), "Local restore adopts its completed unknown IDs");
        ArcSidebarState otherWindowSelection = f.store.load();
        otherWindowSelection.selectSpace(otherWindowSelection.addSpace("Other window selected empty Space"));
        f.store.save(otherWindowSelection); int selections = f.local.selected;
        f.manager.allReady();
        check(f.store.load().entry(late).tabId == null, "All-window readiness retries guarded stale cleanup");
        check(f.local.opened == 0 && f.local.selected == selections,
                "Authority event refresh cannot choose/create a tab for another window's Space selection"); session.destroy();
    }
    private static void incompleteSelector() {
        Fixture f = new Fixture(); String stale = f.pin(40); f.manager.globalReady = true;
        SyntheticModel unloaded = new SyntheticModel(f.profile); unloaded.restored = false;
        SyntheticSelector selector = new SyntheticSelector(unloaded); selector.initialized = false; f.manager.added(selector);
        ArcNativeTabSession session = f.attach();
        check(f.store.load().entry(stale).tabId != null, "Latched global readiness cannot override new incomplete selector");
        selector.initialized = true; f.manager.allReady();
        check(f.store.load().entry(stale).tabId != null, "Selector initialization cannot override incomplete exact-profile model");
        unloaded.restored = true; f.manager.allReady();
        check(f.store.load().entry(stale).tabId == null, "Fully ready models authorize guarded absence cleanup"); session.destroy();
    }
    private static void archiveAndCustom() {
        Fixture f = new Fixture(); String stale = f.pin(40); f.manager.globalReady = true;
        TabModelSelector archive = f.manager.archive; f.manager.archive = null;
        ArcNativeTabSession session = f.attach();
        check(f.store.load().entry(stale).tabId != null, "Archive absence defers cleanup");
        f.manager.archive = archive; ((SyntheticSelector) archive).initialized = false; f.manager.allReady();
        check(f.store.load().entry(stale).tabId != null, "Uninitialized archive defers cleanup");
        ((SyntheticSelector) archive).initialized = true;
        SyntheticModel custom = new SyntheticModel(f.profile); custom.add(40); custom.add(41);
        f.manager.custom.add(new SyntheticSelector(custom)); String customPending = f.pin(41); custom.pend(41);
        SyntheticModel archived = (SyntheticModel) archive.getModels().get(0); archived.add(42); String archivedPin = f.pin(42);
        String reparented = f.pin(43); f.manager.reparented.add(43); f.manager.allReady();
        check(f.store.load().entry(stale).tabId != null, "Custom native tab remains protected");
        check(f.store.load().entry(customPending).tabId != null, "Custom pending closure comprehensive IDs remain protected");
        check(f.store.load().entry(archivedPin).tabId != null, "Archived native tab remains protected");
        check(f.store.load().entry(reparented).tabId != null, "Final deletion guard protects in-flight reparenting");
        String absent = f.pin(44); f.manager.allReady();
        check(f.store.load().entry(absent).tabId == null, "Ready exact profile clears absent native binding");
        check(!f.store.load().hasTabSpace(44), "Ready exact profile clears absent Space owner");
        check(f.store.load().entry(absent).title.equals("Pin 44"), "Cleanup preserves canonical closed pin title"); session.destroy();
    }
    private static void profileIsolation() {
        Fixture f = new Fixture(); f.manager.globalReady = true;
        Profile otherRegular = new Profile(false); SyntheticModel unrelated = new SyntheticModel(otherRegular); unrelated.add(60);
        f.manager.windows.add(new SyntheticSelector(unrelated));
        Profile otr = new Profile(true); SyntheticModel privateModel = new SyntheticModel(otr); privateModel.add(50); privateModel.add(53);
        f.manager.windows.add(new SyntheticSelector(privateModel));
        ArcSidebarStore privateStore = ArcSidebarProfiles.getForProfile(otr);
        ArcSidebarState state = privateStore.load(); String p = state.pin(state.selectedSpace(), null, "https://private.test/", "Private unresolved", 51);
        String livePrivate = state.favorite("https://private-live.test/", "Private favorite", 50);
        privateStore.save(state); String regularStale = f.pin(52);
        ArcNativeTabSession session = f.attach(privateModel, true);
        check(privateStore != f.store, "OTR profile owns a separate production store");
        check(privateStore.load().entry(p).tabId != null, "Regular all-window latch cannot prune unresolved OTR metadata");
        check(privateStore.load().hasTabSpace(53) && !f.store.load().hasTabSpace(53), "OTR local adoption never enters regular metadata");
        check(privateStore.load().isFavoriteTab(50) && !privateStore.load().hasTabSpace(50), "OTR Favorite remains global across Spaces");
        check(!privateStore.load().hasTabSpace(60), "Unrelated profile IDs cannot enter OTR metadata");
        ArcNativeTabSession regular = f.attach();
        check(f.store.load().entry(regularStale).tabId == null, "Initialized other profiles and empty OTR stub permit regular cleanup");
        check(!f.store.load().hasTabSpace(60), "Regular adoption ignores other profile IDs");
        session.actions().closeTab(50);
        check(privateStore.load().entry(livePrivate).tabId != null, "OTR pending undo preserves Favorite binding");
        privateModel.commit(50, false);
        check(privateStore.load().entry(livePrivate).tabId == null
                        && privateStore.load().entry(livePrivate).url.equals("https://private-live.test/"),
                "OTR final closure clears only native Favorite binding");
        check(privateStore.load().entry(p).tabId != null, "OTR final closure leaves other unresolved ownership intact");
        session.destroy(); regular.destroy();
    }
    private static void uncertainProfile() {
        Fixture f = new Fixture(); f.manager.globalReady = true; String stale = f.pin(70);
        f.manager.windows.add(new SyntheticSelector(new SyntheticModel(false)));
        ArcNativeTabSession session = f.attach();
        check(f.store.load().entry(stale).tabId != null, "Unknown regular model profile defers deletion"); session.destroy();
        Fixture unknownOtr = new Fixture(); unknownOtr.manager.globalReady = true; String o = unknownOtr.pin(73);
        SyntheticModel privateStub = new SyntheticModel(true); privateStub.add(74); privateStub.pend(74);
        unknownOtr.manager.windows.add(new SyntheticSelector(privateStub));
        ArcNativeTabSession privateUnknown = unknownOtr.attach();
        check(unknownOtr.store.load().entry(o).tabId != null, "Nonempty pending OTR model without profile cannot prove absence");
        privateUnknown.destroy();
        Fixture shutdown = new Fixture(); shutdown.manager.globalReady = true;
        SyntheticModel dying = new SyntheticModel(shutdown.profile); shutdown.profile.shutdown = true;
        // Attach before shutdown starts, then retry with a shutdown model authority.
        shutdown.profile.shutdown = false; ArcNativeTabSession attached = shutdown.attach();
        shutdown.pin(72); shutdown.profile.shutdown = true; shutdown.manager.windows.add(new SyntheticSelector(dying));
        String before = shutdown.store.load().serialize(); shutdown.manager.allReady();
        check(before.equals(shutdown.store.load().serialize()), "Shutdown exact profile cannot authorize cleanup"); attached.destroy();
    }
    private static void localUnregistered() {
        Fixture f = new Fixture(); f.manager.windows.clear(); f.manager.globalReady = true; String local = f.pin(10);
        ArcNativeTabSession session = f.attach();
        check(f.store.load().entry(local).tabId != null, "Current comprehensive model protected even before manager registration"); session.destroy();
    }
    private static void authorityUnavailable() {
        Fixture f = new Fixture(); f.manager.globalReady = true; f.manager.throwSelectors = true;
        String unresolved = f.pin(80); ArcNativeTabSession session = f.attach();
        check(f.store.load().entry(unresolved).tabId != null, "Failed selector lookup preserves unresolved metadata");
        check(f.store.load().hasTabSpace(10), "Unknown window authority does not prevent local adoption");
        f.manager.throwSelectors = false; f.manager.throwDeletion = true; f.manager.allReady();
        check(f.store.load().entry(unresolved).tabId != null && f.store.load().hasTabSpace(80),
                "Failed deletion guard preserves both binding and owner"); session.destroy();
    }
    private static void destroyedCallbacks() {
        Fixture f = new Fixture(); f.pin(10); f.local.restored = false;
        ArcNativeTabSession session = f.attach();
        check(f.manager.observers.size() == 1, "Session observes manager authority");
        TabModelObserver modelCallback = f.local.observers.get(0);
        TabWindowManager.Observer managerCallback = f.manager.observers.get(0);
        session.destroy(); session.destroy();
        check(f.local.observers.isEmpty() && f.manager.observers.isEmpty(), "Destroy removes both observers exactly once");
        String before = f.store.load().serialize(); int writes = UserPrefs.get(f.profile).writes, refreshes = f.refreshes;
        modelCallback.didAddTab(new Tab(90), 0, 0, false); modelCallback.restoreCompleted();
        modelCallback.tabClosureUndone(new Tab(10)); modelCallback.tabClosureCommitted(new Tab(10));
        modelCallback.onTabCloseCommitted(List.of(new Tab(10)), false, true, 0);
        managerCallback.onAllTabModelStateInitialized();
        check(before.equals(f.store.load().serialize()) && writes == UserPrefs.get(f.profile).writes,
                "Late callbacks after destroy cannot write metadata");
        check(refreshes == f.refreshes && session.actions().selectOrOpen("unknown") == ArcTabActions.Result.NOT_OPENED,
                "Destroyed session cannot refresh or act");
    }
    public static void main(String[] args) {
        Map<String, Runnable> cases = new LinkedHashMap<>();
        cases.put("two-windows", ArcNativeTabSessionSyntheticBoundaryTest::twoWindows);
        cases.put("pending-undo", ArcNativeTabSessionSyntheticBoundaryTest::pendingUndo);
        cases.put("pending-unknown", ArcNativeTabSessionSyntheticBoundaryTest::pendingUnknown);
        cases.put("partial-restore", ArcNativeTabSessionSyntheticBoundaryTest::partialRestore);
        cases.put("incomplete-selector", ArcNativeTabSessionSyntheticBoundaryTest::incompleteSelector);
        cases.put("archive-custom", ArcNativeTabSessionSyntheticBoundaryTest::archiveAndCustom);
        cases.put("profile-isolation", ArcNativeTabSessionSyntheticBoundaryTest::profileIsolation);
        cases.put("uncertain-profile", ArcNativeTabSessionSyntheticBoundaryTest::uncertainProfile);
        cases.put("local-unregistered", ArcNativeTabSessionSyntheticBoundaryTest::localUnregistered);
        cases.put("authority-unavailable", ArcNativeTabSessionSyntheticBoundaryTest::authorityUnavailable);
        cases.put("destroyed-callbacks", ArcNativeTabSessionSyntheticBoundaryTest::destroyedCallbacks);
        int failures = 0;
        for (String name : args.length == 0 ? cases.keySet() : List.of(args)) {
            try { cases.get(name).run(); System.out.println("PASS " + name); }
            catch (AssertionError failure) { failures++; System.err.println("FAIL " + name + ": " + failure.getMessage()); }
        }
        if (failures != 0) throw new AssertionError(failures + " adapter regressions failed");
        System.out.println("ArcNativeTabSession: production adapter/state/store/actions passed at synthetic native boundaries");
    }
}
