#!/usr/bin/env python3
"""Run the actual Arc adapter/state/store/actions at synthetic Chromium/JNI boundaries.

Contracts mirror the consumed APIs at cfd94726b7b5fb48aedcc32662f2f3fbdbadec35.
The synthetic TabModel supplies visible and comprehensive lists separately and delivers native
observer events. ProfileKeyedMap/UserPrefs replace the native Profile lifecycle/pref boundary;
they preserve exact profile identity and shared regular persistence. This focused JVM regression
does not replace real Chromium Java compilation or device multiwindow/undo acceptance.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = {
    'org.chromium.base.ThreadUtils': 'public class ThreadUtils { public static void assertOnUiThread(){} }',
    'org.chromium.base.Callback': 'public interface Callback<T> { void onResult(T value); }',
    'org.chromium.base.supplier.NullableObservableSupplier': 'public interface NullableObservableSupplier<T> extends java.util.function.Supplier<T> {}',
    'org.chromium.chrome.browser.profiles.Profile': '''public class Profile {
        private final boolean otr; public boolean shutdown;
        public Profile(boolean privateProfile){otr=privateProfile;}
        public boolean isOffTheRecord(){return otr;} public boolean shutdownStarted(){return shutdown;}
    }''',
    'org.chromium.chrome.browser.profiles.ProfileKeyedMap': '''public class ProfileKeyedMap<T> {
        public @interface ProfileSelection { int OWN_INSTANCE=0; }
        private final java.util.Map<Profile,T> stores=new java.util.IdentityHashMap<>();
        public ProfileKeyedMap(int selection,org.chromium.base.Callback<T> cleanup){
            if(selection!=ProfileSelection.OWN_INSTANCE)throw new AssertionError("Exact profile required");
        }
        public static <T> org.chromium.base.Callback<T> noRequiredCleanupAction(){return value -> {};}
        public T getForProfile(Profile p,java.util.function.Function<Profile,T> factory){
            return stores.computeIfAbsent(p,factory);
        }
    }''',
    'org.chromium.components.prefs.PrefService': '''public class PrefService {
        private final java.util.Map<String,String> values=new java.util.HashMap<>(); public int writes;
        public String getString(String key){return values.getOrDefault(key,"");}
        public void setString(String key,String value){values.put(key,value);writes++;}
    }''',
    'org.chromium.components.user_prefs.UserPrefs': '''public class UserPrefs {
        private static final java.util.Map<org.chromium.chrome.browser.profiles.Profile,org.chromium.components.prefs.PrefService>
            prefs=new java.util.IdentityHashMap<>();
        public static org.chromium.components.prefs.PrefService get(org.chromium.chrome.browser.profiles.Profile p){
            if(p.isOffTheRecord())throw new AssertionError("OTR must not persist");
            return prefs.computeIfAbsent(p,ignored -> new org.chromium.components.prefs.PrefService());
        }
    }''',
    'org.chromium.chrome.browser.tab.Tab': 'public class Tab { private final int id; public Tab(int value){id=value;} public int getId(){return id;} }',
    'org.chromium.chrome.browser.tab.TabLaunchType': 'public class TabLaunchType { public static final int FROM_CHROME_UI=1; }',
    'org.chromium.chrome.browser.tab.TabSelectionType': 'public class TabSelectionType { public static final int FROM_USER=1; }',
    'org.chromium.content_public.browser.LoadUrlParams': 'public class LoadUrlParams { public final String url; public LoadUrlParams(String value){url=value;} }',
    'org.chromium.chrome.browser.tabmodel.TabCreator': 'public interface TabCreator { org.chromium.chrome.browser.tab.Tab createNewTab(org.chromium.content_public.browser.LoadUrlParams p,int type,org.chromium.chrome.browser.tab.Tab parent); }',
    'org.chromium.chrome.browser.tabmodel.TabClosureParams': '''public class TabClosureParams {
        public final org.chromium.chrome.browser.tab.Tab tab; public final boolean undo;
        private TabClosureParams(org.chromium.chrome.browser.tab.Tab t,boolean u){tab=t;undo=u;}
        public static Builder closeTab(org.chromium.chrome.browser.tab.Tab t){return new Builder(t);}
        public static class Builder { private final org.chromium.chrome.browser.tab.Tab tab; private boolean undo;
            public Builder(org.chromium.chrome.browser.tab.Tab t){tab=t;}
            public Builder allowUndo(boolean u){undo=u;return this;}
            public TabClosureParams build(){return new TabClosureParams(tab,undo);}
        }
    }''',
    'org.chromium.chrome.browser.tabmodel.TabRemover': 'public interface TabRemover { void closeTabs(TabClosureParams p,boolean allowDialog); }',
    'org.chromium.chrome.browser.tabmodel.TabList': 'public interface TabList { int getCount(); org.chromium.chrome.browser.tab.Tab getTabAt(int i); boolean isOffTheRecord(); }',
    'org.chromium.chrome.browser.tabmodel.TabModelObserver': '''public interface TabModelObserver {
        default void didAddTab(org.chromium.chrome.browser.tab.Tab t,int type,int creationState,boolean markedForSelection){}
        default void didSelectTab(org.chromium.chrome.browser.tab.Tab t,int type,int lastId){}
        default void restoreCompleted(){} default void tabClosureUndone(org.chromium.chrome.browser.tab.Tab t){}
        default void tabClosureCommitted(org.chromium.chrome.browser.tab.Tab t){}
        default void onTabCloseCommitted(java.util.List<org.chromium.chrome.browser.tab.Tab> t,boolean all,boolean restore,int source){}
    }''',
    'org.chromium.chrome.browser.tabmodel.TabModel': '''public interface TabModel extends TabList {
        org.chromium.chrome.browser.profiles.Profile getProfile();
        org.chromium.chrome.browser.tab.Tab getTabById(int id); boolean isClosurePending(int id);
        void cancelTabClosure(int id); void setIndex(int i,int type); void pinTab(int id,boolean dialog); void unpinTab(int id);
        TabRemover getTabRemover(); void addObserver(TabModelObserver o); void removeObserver(TabModelObserver o);
        boolean isTabModelRestored(); TabList getComprehensiveModel();
        org.chromium.base.supplier.NullableObservableSupplier<org.chromium.chrome.browser.tab.Tab> getCurrentTabSupplier();
    }''',
    'org.chromium.chrome.browser.tabmodel.TabModelSelector': 'public interface TabModelSelector { java.util.List<TabModel> getModels(); boolean isTabStateInitialized(); }',
    'org.chromium.chrome.browser.tabwindow.TabWindowManager': '''public interface TabWindowManager {
        interface Observer { default void onAllTabModelStateInitialized(){} default void onTabStateInitialized(){}
            default void onTabModelSelectorAdded(org.chromium.chrome.browser.tabmodel.TabModelSelector s){} }
        void addObserver(Observer o); void removeObserver(Observer o); boolean isAllTabStateInitialized();
        java.util.Collection<org.chromium.chrome.browser.tabmodel.TabModelSelector> getAllTabModelSelectors();
        java.util.Collection<org.chromium.chrome.browser.tabmodel.TabModelSelector> getCustomTabsTabModelSelectors();
        org.chromium.chrome.browser.tabmodel.TabModelSelector getArchivedTabModelSelector();
        boolean canTabStateBeDeleted(int id);
    }''',
    'org.chromium.chrome.browser.app.tabwindow.TabWindowManagerSingleton': '''public class TabWindowManagerSingleton {
        private static org.chromium.chrome.browser.tabwindow.TabWindowManager manager;
        public static org.chromium.chrome.browser.tabwindow.TabWindowManager getInstance(){return manager;}
        public static void setTabWindowManagerForTesting(org.chromium.chrome.browser.tabwindow.TabWindowManager m){manager=m;}
    }''',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT / 'chromium')
    parser.add_argument('scenarios', nargs='*')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='archium-native-session-') as tmp:
        work = Path(tmp)
        contracts = []
        for name, body in DEFINITIONS.items():
            path = work / 'contracts' / (name.replace('.', '/') + '.java')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('package ' + name.rsplit('.', 1)[0] + ';\n' + body + '\n')
            contracts.append(path)
        sources = args.source_root / 'chrome/android/java/src/org/chromium/chrome/browser/arc'
        delivered = [sources / (name + '.java') for name in
                     ('ArcNativeTabSession', 'ArcSidebarState', 'ArcSidebarStore', 'ArcSidebarProfiles', 'ArcTabActions')]
        classes = work / 'classes'
        subprocess.run(['javac', '-d', str(classes), *map(str, contracts + delivered),
                        str(ROOT / 'tests/java/ArcNativeTabSessionSyntheticBoundaryTest.java')], check=True)
        subprocess.run(['java', '-cp', str(classes), 'ArcNativeTabSessionSyntheticBoundaryTest',
                        *args.scenarios], check=True)


if __name__ == '__main__':
    main()
