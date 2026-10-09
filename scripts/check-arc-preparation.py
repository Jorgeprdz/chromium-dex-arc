#!/usr/bin/env python3
"""Check Archium patch application, pure Java behavior and isolated Android API compilation.

Android dependency stubs only allow type checking new adapters, not APK/runtime validation.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID_JAR = Path('/opt/android-sdk/platforms/android-36/android.jar')


def run(*args, **kwargs):
    subprocess.run(args, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-sources', action='store_true')
    parser.add_argument('--android-jar', type=Path, default=ANDROID_JAR)
    parser.add_argument('--test-original-account-delegate', action='store_true')
    args = parser.parse_args()
    window_spec = importlib.util.spec_from_file_location('window_core', ROOT / 'scripts/fetch-window-core.py')
    window_module = importlib.util.module_from_spec(window_spec)
    window_spec.loader.exec_module(window_module)
    window_jar = window_module.ensure_jar()
    manifest = json.loads((ROOT / 'patches/upstream-files.json').read_text())
    patch = ROOT / 'patches/archium-desktop.patch'
    assert hashlib.sha256(patch.read_bytes()).hexdigest() == manifest['patch_sha256']
    spec = importlib.util.spec_from_file_location('apply_arc', ROOT / 'scripts/apply-arc-patches.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='archium-check-') as tmp:
        work = Path(tmp)
        checkout = work / 'src'
        checkout.mkdir()
        for name, sha in manifest['originals'].items():
            if sha is None:
                continue
            source = ROOT / '.source-reference' / name
            if not source.exists() and args.fetch_sources:
                url = 'https://chromium.googlesource.com/chromium/src/+/' + manifest['revision'] + '/' + name + '?format=TEXT'
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(base64.b64decode(urllib.request.urlopen(url, timeout=30).read()))
            if not source.exists():
                raise SystemExit('Missing pinned original; rerun --fetch-sources: ' + name)
            assert hashlib.sha256(source.read_bytes()).hexdigest() == sha, name
            dest = checkout / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        run('git', '-C', str(checkout), 'init', '-q')
        run('git', '-C', str(checkout), 'add', '.')
        run('git', '-C', str(checkout), '-c', 'user.name=Archium check', '-c',
            'user.email=check@example.invalid', 'commit', '-qm', 'Pinned sparse files')
        # This temporary sparse checkout has a synthetic commit. Original-file hashes above prove
        # its input; production CLI always requires the real pinned Chromium commit.
        revision = module.git(checkout, 'rev-parse', 'HEAD')
        module.apply_to_checkout(checkout, patch, manifest['originals'], revision)
        for name, sha in manifest['modified'].items():
            assert hashlib.sha256((checkout / name).read_bytes()).hexdigest() == sha, name
            overlay = ROOT / 'chromium' / name
            if not overlay.exists():
                overlay = ROOT / '.source-modified' / name
            assert overlay.is_file(), 'Missing delivery source: ' + name
            assert overlay.read_bytes() == (checkout / name).read_bytes(), 'Stale patch: ' + name
            if name.endswith('.xml'):
                ET.parse(checkout / name)
        print(f'Pinned patch: all {len(manifest["originals"])} files applied and hashes matched', flush=True)
        classes = work / 'classes'
        pure = list((ROOT / 'chromium').rglob('ArchiumWindowClass.java')) + list((ROOT / 'chromium').rglob('ArcDesktopPolicy.java')) + list((ROOT / 'chromium').rglob('ArchiumAutofillPolicy.java'))
        pure += list((ROOT / 'chromium').rglob('ArchiumPasswordCsv.java'))
        pure += list((ROOT / 'chromium').rglob('ArcSidebarState.java'))
        pure += list((ROOT / 'chromium').rglob('ArcSidebarStore.java'))
        pure += list((ROOT / 'chromium').rglob('ArcTabActions.java'))
        pure += list((ROOT / 'chromium').rglob('ArcCollectionsController.java'))
        run('javac', '-cp', str(window_jar), '-d', str(classes), *map(str, pure), str(ROOT / 'tests/java/ArcDesktopPolicyTest.java'), str(ROOT / 'tests/java/ArcDesktopGeometryTest.java'),
            str(ROOT / 'tests/java/ArchiumAutofillPolicyTest.java'), str(ROOT / 'tests/java/ArchiumWindowClassTest.java'),
            str(ROOT / 'tests/java/ArchiumPasswordCsvTest.java'),
            str(ROOT / 'tests/java/ArcSidebarStateTest.java'), str(ROOT / 'tests/java/ArcSidebarStoreTest.java'), str(ROOT / 'tests/java/ArcTabActionsTest.java'), str(ROOT / 'tests/java/ArcCollectionsControllerTest.java'))
        run('java', '-cp', str(classes), 'ArchiumWindowClassTest')
        run('java', '-cp', str(classes), 'ArcDesktopPolicyTest')
        run('java', '-cp', str(classes), 'ArcDesktopGeometryTest')
        run('java', '-cp', str(classes), 'ArcSidebarStateTest')
        run('java', '-cp', str(classes), 'ArcSidebarStoreTest')
        run('java', '-cp', str(classes), 'ArcTabActionsTest')
        run('java', '-cp', str(classes), 'ArcCollectionsControllerTest')
        run('java', '-cp', str(classes), 'ArchiumAutofillPolicyTest')
        run('java', '-Xmx256m', '-cp', str(classes), 'ArchiumPasswordCsvTest')
        if not args.android_jar.is_file():
            raise SystemExit('Missing Android SDK jar; pass --android-jar')
        stubs = work / 'contracts'
        definitions = {
            'org.chromium.chrome.R': 'public final class R { public static final class string { public static final int arc_bookmarks=1, arc_frame_color=2, arc_bookmark_root=3, arc_google_login=4, arc_autofill=5, arc_reset_color=6, arc_color_format=7, arc_interface=8, arc_interface_auto=9, arc_interface_arc=10, arc_interface_mobile=11; } public static final class id { public static final int toolbar=1, desktop_window_spacer=2; } }',
            'org.chromium.chrome.browser.profiles.Profile': 'public class Profile { public boolean isOffTheRecord(){return false;} public boolean shutdownStarted(){return false;} public Profile getOriginalProfile(){return this;} }',
            'org.chromium.components.bookmarks.BookmarkId': 'public class BookmarkId { public long getId(){return 0;} public int getType(){return 0;} }',
            'org.chromium.url.GURL': 'public class GURL { public GURL(){} public GURL(String url){} public String getSpec() { return ""; } }',
            'org.chromium.components.bookmarks.BookmarkItem': 'public class BookmarkItem { public String getTitle(){return "";} public boolean isFolder(){return false;} public boolean isEditable(){return true;} public BookmarkId getId(){return null;} public BookmarkId getParentId(){return null;} public org.chromium.url.GURL getUrl(){return null;} }',
            'org.chromium.chrome.browser.bookmarks.BookmarkModelObserver': 'public abstract class BookmarkModelObserver { public abstract void bookmarkModelChanged(); }',
            'org.chromium.chrome.browser.bookmarks.BookmarkModel': 'public class BookmarkModel { public void addObserver(BookmarkModelObserver o){} public void removeObserver(BookmarkModelObserver o){} public boolean isBookmarkModelLoaded(){return true;} public boolean finishLoadingBookmarkModel(Runnable r){return false;} public org.chromium.components.bookmarks.BookmarkId getDesktopFolderId(){return null;} public java.util.List<org.chromium.components.bookmarks.BookmarkId> getChildIds(org.chromium.components.bookmarks.BookmarkId id){return null;} public java.util.List<org.chromium.components.bookmarks.BookmarkId> getTopLevelFolderIds(){return null;} public org.chromium.components.bookmarks.BookmarkItem getBookmarkById(org.chromium.components.bookmarks.BookmarkId id){return null;} }',
            'org.chromium.chrome.browser.tabmodel.IncognitoStateProvider': 'public class IncognitoStateProvider { public interface IncognitoStateObserver { void onIncognitoStateChanged(boolean i); } public boolean isIncognitoSelected(){return false;} public void addIncognitoStateObserverAndTrigger(IncognitoStateObserver o){o.onIncognitoStateChanged(false);} public void removeObserver(IncognitoStateObserver o){} }',
            'org.chromium.components.favicon.LargeIconBridge': 'public class LargeIconBridge { public interface LargeIconCallback { void onLargeIconAvailable(android.graphics.Bitmap icon, int color, boolean fallback, int type); } public LargeIconBridge(org.chromium.chrome.browser.profiles.Profile p){} public boolean getLargeIconForUrl(org.chromium.url.GURL url,int size,LargeIconCallback cb){return true;} public void destroy(){} }',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayout': 'public class VerticalTabRailLayout extends android.view.View { public VerticalTabRailLayout(android.content.Context c){super(c);} public void setDesktopWindowSpacerHost(android.view.View v){} public void setArcAvailableTabHeight(int height,boolean active){} }',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListViewBinder': 'public class VerticalTabListViewBinder { public static void refreshArcAppearance(VerticalTabRailLayout v,boolean i){} }',
            'org.chromium.chrome.browser.toolbar.top.ToolbarTablet': 'public class ToolbarTablet extends android.view.View { public ToolbarTablet(android.content.Context c){super(c);} public void onThemeColorChanged(int color,boolean animate){} }',
            'org.chromium.chrome.browser.lifecycle.ConfigurationChangedObserver': 'public interface ConfigurationChangedObserver { void onConfigurationChanged(android.content.res.Configuration c); }',
            'org.chromium.chrome.browser.lifecycle.ActivityLifecycleDispatcher': 'public interface ActivityLifecycleDispatcher { void register(ConfigurationChangedObserver o); void unregister(ConfigurationChangedObserver o); }',
            'androidx.recyclerview.widget.RecyclerView': 'public class RecyclerView extends android.view.ViewGroup { public RecyclerView(android.content.Context c){super(c);} public abstract static class Adapter<T> { public void notifyDataSetChanged(){} } public Adapter<?> getAdapter(){return null;} protected void onLayout(boolean c,int l,int t,int r,int b){} }',
            'androidx.preference.Preference': 'public class Preference { public interface OnPreferenceClickListener { boolean onPreferenceClick(Preference p); } public Preference(android.content.Context c){} public void setTitle(CharSequence s){} public void setSummary(CharSequence s){} public void setEnabled(boolean e){} public void setOnPreferenceClickListener(OnPreferenceClickListener l){} }',
            'androidx.preference.PreferenceCategory': 'public class PreferenceCategory extends Preference { public PreferenceCategory(android.content.Context c){super(c);} public boolean addPreference(Preference p){return true;} public void removeAll(){} }',
            'androidx.preference.PreferenceScreen': 'public class PreferenceScreen extends PreferenceCategory { public PreferenceScreen(android.content.Context c){super(c);} }',
            'androidx.preference.PreferenceManager': 'public class PreferenceManager { public PreferenceScreen createPreferenceScreen(android.content.Context c){return new PreferenceScreen(c);} }',
            'org.chromium.base.supplier.SettableMonotonicObservableSupplier': 'public class SettableMonotonicObservableSupplier<T> { public void set(T v){} }',
            'org.chromium.base.supplier.ObservableSuppliers': 'public class ObservableSuppliers { public static <T> SettableMonotonicObservableSupplier<T> createMonotonic(){return new SettableMonotonicObservableSupplier<T>();} }',
            'org.chromium.components.browser_ui.settings.SettingsFragment': 'public interface SettingsFragment { public @interface AnimationType { int PROPERTY=1; } }',
            'org.chromium.chrome.browser.settings.ChromeBaseSettingsFragment': 'public class ChromeBaseSettingsFragment { public void onCreate(android.os.Bundle b){} public void onCreatePreferences(android.os.Bundle b,String key){} public android.app.Activity requireActivity(){return new android.app.Activity();} public android.content.Context requireContext(){return requireActivity();} public org.chromium.chrome.browser.profiles.Profile getProfile(){return new org.chromium.chrome.browser.profiles.Profile();} public androidx.preference.PreferenceManager getPreferenceManager(){return new androidx.preference.PreferenceManager();} public void setPreferenceScreen(androidx.preference.PreferenceScreen s){} public org.chromium.base.supplier.SettableMonotonicObservableSupplier<String> getPageTitle(){return null;} public int getAnimationType(){return 0;} public void startActivityForResult(android.content.Intent intent,int requestCode){} public void onActivityResult(int requestCode,int resultCode,android.content.Intent data){} public void onDestroy(){} public boolean isAdded(){return true;} public android.content.res.Resources getResources(){return requireContext().getResources();} }',
            'org.chromium.base.ContextUtils': 'public class ContextUtils { public static android.content.Context getApplicationContext(){return null;} }',
            'org.jni_zero.JniType': '@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.PARAMETER,java.lang.annotation.ElementType.METHOD}) public @interface JniType { String value(); }',
            'org.jni_zero.NativeMethods': 'public @interface NativeMethods {}',
            'org.jni_zero.CalledByNative': '@java.lang.annotation.Target(java.lang.annotation.ElementType.METHOD) public @interface CalledByNative {}',
            'org.jni_zero.JNINamespace': '@java.lang.annotation.Target(java.lang.annotation.ElementType.TYPE) public @interface JNINamespace { String value(); }',
            'org.chromium.base.Callback': 'public interface Callback<T> { void onResult(T value); }',
            'org.chromium.google_apis.gaia.GaiaId': 'public class GaiaId {}',
            'org.chromium.components.signin.AuthException': 'public class AuthException extends Exception {}',
            'org.chromium.components.signin.AccessTokenData': 'public class AccessTokenData {}',
            'org.chromium.components.signin.AccountManagerDelegate': 'public interface AccountManagerDelegate { public interface AccountsChangeObserver{} public @interface CapabilityResponse{int EXCEPTION=0;} void attachAccountsChangeObserver(AccountsChangeObserver o); android.accounts.Account[] getAccountsSynchronous(); AccessTokenData getAccessToken(android.accounts.Account a,String s); void invalidateAccessToken(String s) throws AuthException; int hasCapability(android.accounts.Account a,String s); void createAddAccountIntent(String email,org.chromium.base.Callback<android.content.Intent> c); void updateCredentials(android.accounts.Account a,android.app.Activity activity,org.chromium.base.Callback<Boolean> c); org.chromium.google_apis.gaia.GaiaId getAccountGaiaId(String e); void confirmCredentials(android.accounts.Account a,android.app.Activity activity,org.chromium.base.Callback<android.os.Bundle> c); }',
        }
        resources = ET.parse(ROOT / 'chromium/chrome/android/java/res/values/arc_strings.xml')
        # Chromium cfd94726: toolbar/java/res/layout/toolbar_tablet.xml references
        # these navigation strings/drawables and the real LocationBar IDs.
        string_names = [node.attrib['name'] for node in resources.getroot()] + [
            'accessibility_toolbar_btn_back', 'accessibility_toolbar_btn_forward',
            'accessibility_btn_refresh', 'accessibility_btn_stop_loading',
        ]
        string_ids = ', '.join(f'{name}={i}' for i, name in enumerate(string_names, 1))
        id_names = ('toolbar', 'desktop_window_spacer', 'location_bar',
                    'location_bar_holder', 'collapse_button', 'menu_button_wrapper',
                    'extensions_toolbar_container', 'coordinator')
        view_ids = ', '.join(f'{name}={i}' for i, name in enumerate(id_names, 1))
        definitions['org.chromium.chrome.R'] = ('public final class R { public static final class string { public static final int '
                + string_ids + '; } public static final class id { public static final int '
                + view_ids + '; } public static final class drawable { public static final int '
                'btn_back=1, btn_forward=2, btn_reload_stop=3; } public static final class integer { '
                'public static final int reload_button_level_reload=1, reload_button_level_stop=2; } }')
        definitions.update({
            # Shared native bookmark projection contracts, pinned at cfd94726. Persistence,
            # native model behavior and actual JNI remain outside this isolated API check.
            'org.chromium.chrome.browser.bookmarks.BookmarkUtils': 'public class BookmarkUtils { public static java.util.List<org.chromium.components.bookmarks.BookmarkId> getDesktopBookmarkIds(BookmarkModel m){return java.util.Collections.emptyList();} }',
            'org.chromium.chrome.browser.bookmarks.BookmarkOpener': '''public interface BookmarkOpener {
                boolean openBookmarkInCurrentTab(org.chromium.components.bookmarks.BookmarkId id,boolean incognito);
                boolean openBookmarksInNewTabs(java.util.List<org.chromium.components.bookmarks.BookmarkId> ids,boolean incognito,Integer launchType);
                boolean openBookmarksInNewWindow(java.util.List<org.chromium.components.bookmarks.BookmarkId> ids,boolean incognito);
                boolean isOpenInNewWindowSupported();
            }''',
            'org.chromium.chrome.browser.bookmarks.BookmarkManagerOpener': '''public interface BookmarkManagerOpener {
                void showBookmarkManager(android.app.Activity a,org.chromium.chrome.browser.tab.Tab t,org.chromium.chrome.browser.profiles.Profile p,org.chromium.components.bookmarks.BookmarkId folder);
                void startEditActivity(android.app.Activity a,org.chromium.chrome.browser.profiles.Profile p,org.chromium.components.bookmarks.BookmarkId id);
                void startFolderPickerActivity(android.app.Activity a,org.chromium.chrome.browser.profiles.Profile p,org.chromium.components.bookmarks.BookmarkId... ids);
            }''',
            'org.chromium.chrome.browser.bookmarks.R': 'public final class R { public static final class string { public static final int contextmenu_open_in_new_tab=1, contextmenu_open_in_new_window=2, contextmenu_edit_bookmark_ellipsis=3, bookmark_item_move=4, contextmenu_open_bookmarks_manager=5; } }',
            'org.chromium.chrome.browser.ui.side_ui.SideUiCoordinator': 'public interface SideUiCoordinator { class SideUiSpecs {} class UiUpdateRequest {} }',
            'org.chromium.chrome.browser.ui.side_ui.SideUiStateProvider': 'public interface SideUiStateProvider { void addObserver(SideUiObserver o); void removeObserver(SideUiObserver o); }',
            'org.chromium.chrome.browser.ui.side_ui.SideUiObserver': '''public interface SideUiObserver {
                default void onTransitionBegun(SideUiCoordinator.SideUiSpecs s,SideUiCoordinator.UiUpdateRequest r){}
                default void onTransitionEnded(SideUiCoordinator.SideUiSpecs s,SideUiCoordinator.UiUpdateRequest r){}
                default void onSideUiSpecsChanged(SideUiCoordinator.SideUiSpecs s,SideUiCoordinator.UiUpdateRequest r){}
            }''',
            # Minimal type contracts from cfd94726's CompositorViewHolder,
            # TouchEventObserver and NullableObservableSupplier. Stub bodies are
            # never used as evidence of compositor/touch/browser runtime behavior.
            'org.chromium.chrome.browser.compositor.CompositorViewHolder': '''public class CompositorViewHolder extends android.widget.FrameLayout {
                public CompositorViewHolder(android.content.Context c, android.util.AttributeSet attrs){super(c, attrs);}
                public android.view.View getActiveSurfaceView(){return null;}
                public org.chromium.chrome.browser.fullscreen.FullscreenManager getFullscreenManager(){return new org.chromium.chrome.browser.fullscreen.FullscreenManager();}
                public void addTouchEventObserver(org.chromium.components.browser_ui.widget.TouchEventObserver o){}
                public void removeTouchEventObserver(org.chromium.components.browser_ui.widget.TouchEventObserver o){}
            }''',
            'org.chromium.chrome.browser.fullscreen.FullscreenManager': 'public class FullscreenManager { public boolean getPersistentFullscreenMode(){return false;} }',
            'org.chromium.components.browser_ui.widget.TouchEventObserver': '''public interface TouchEventObserver {
                boolean onInterceptTouchEvent(android.view.MotionEvent e);
                default boolean mayInterceptTouchSequenceInWebContents(){return false;}
                default boolean onTouchEvent(android.view.MotionEvent e){return false;}
                default boolean dispatchTouchEvent(android.view.MotionEvent e){return false;}
            }''',
            'org.chromium.base.supplier.NullableObservableSupplier': 'public interface NullableObservableSupplier<T> extends java.util.function.Supplier<T> { T addSyncObserverAndCall(org.chromium.base.Callback<T> c); void removeObserver(org.chromium.base.Callback<T> c); }',
            # These two presentation APIs are Archium additions in the delivered
            # .source-modified VerticalTabListCoordinator, not upstream inventions.
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListCoordinator': '''public class VerticalTabListCoordinator {
                public void setTabVisibilityPredicate(java.util.function.IntPredicate predicate){}
                public void refreshTabPresentation(){}
            }''',
            'org.chromium.chrome.browser.tab.Tab': 'public class Tab { public int getId(){return 1;} public org.chromium.url.GURL getUrl(){return new org.chromium.url.GURL();} public String getTitle(){return "Title";} public boolean isDestroyed(){return false;} public boolean isClosing(){return false;} public boolean isLoading(){return false;} public boolean canGoBack(){return false;} public void goBack(){} public boolean canGoForward(){return false;} public void goForward(){} public void reload(){} public void stopLoading(){} public void addObserver(TabObserver o){} public void removeObserver(TabObserver o){} }',
            'org.chromium.chrome.browser.tab.TabObserver': '''public interface TabObserver {
                default void onLoadStarted(Tab t,boolean differentDocument){}
                default void onLoadStopped(Tab t,boolean differentDocument){}
                default void onNavigationStateChanged(){}
                default void onNavigationEntriesAppended(Tab t){}
                default void onNavigationEntriesDeleted(Tab t){}
                default void onContentChanged(Tab t){}
                default void onDidFinishNavigationInPrimaryMainFrame(Tab t,org.chromium.content_public.browser.NavigationHandle navigation){}
                default void onClosingStateChanged(Tab t,boolean closing){}
                default void onDestroyed(Tab t){}
            }''',
            'org.chromium.chrome.browser.tab.TabLaunchType': 'public class TabLaunchType { public static final int FROM_CHROME_UI=1, FROM_BOOKMARK_BAR_BACKGROUND=2; }',
            'org.chromium.chrome.browser.tab.TabSelectionType': 'public class TabSelectionType { public static final int FROM_USER=1; }',
            'org.chromium.content_public.browser.LoadUrlParams': 'public class LoadUrlParams { public LoadUrlParams(String url){} }',
            'org.chromium.content_public.browser.NavigationHandle': 'public class NavigationHandle {}',
            'org.chromium.chrome.browser.tabmodel.TabCreator': 'public interface TabCreator { org.chromium.chrome.browser.tab.Tab createNewTab(org.chromium.content_public.browser.LoadUrlParams p,int type,org.chromium.chrome.browser.tab.Tab parent); }',
            'org.chromium.chrome.browser.tabmodel.TabClosureParams': 'public class TabClosureParams { public static Builder closeTab(org.chromium.chrome.browser.tab.Tab t){return new Builder();} public static class Builder { public Builder allowUndo(boolean b){return this;} public TabClosureParams build(){return new TabClosureParams();} } }',
            'org.chromium.chrome.browser.tabmodel.TabRemover': 'public interface TabRemover { void closeTabs(TabClosureParams p,boolean allowDialog); }',
            'org.chromium.chrome.browser.tabmodel.TabModelObserver': 'public interface TabModelObserver { default void didAddTab(org.chromium.chrome.browser.tab.Tab t,int type,int creationState,boolean markedForSelection){} default void didSelectTab(org.chromium.chrome.browser.tab.Tab t,int type,int lastId){} default void restoreCompleted(){} default void tabClosureCommitted(org.chromium.chrome.browser.tab.Tab t){} default void onTabCloseCommitted(java.util.List<org.chromium.chrome.browser.tab.Tab> t,boolean all,boolean restore,int source){} }',
            'org.chromium.chrome.browser.tabmodel.TabModel': 'public interface TabModel { org.chromium.chrome.browser.profiles.Profile getProfile(); org.chromium.chrome.browser.tab.Tab getTabById(int id); boolean isClosurePending(int id); void cancelTabClosure(int id); int getCount(); org.chromium.chrome.browser.tab.Tab getTabAt(int i); void setIndex(int i,int type); void pinTab(int id,boolean dialog); void unpinTab(int id); TabRemover getTabRemover(); void addObserver(TabModelObserver o); void removeObserver(TabModelObserver o); boolean isTabModelRestored(); org.chromium.base.supplier.NullableObservableSupplier<org.chromium.chrome.browser.tab.Tab> getCurrentTabSupplier(); }',
            'org.chromium.base.ThreadUtils': 'public class ThreadUtils { public static void assertOnUiThread(){} }',
            'org.chromium.components.prefs.PrefService': 'public class PrefService { public String getString(String key){return "";} public void setString(String key,String value){} }',
            'org.chromium.components.user_prefs.UserPrefs': 'public class UserPrefs { public static org.chromium.components.prefs.PrefService get(org.chromium.chrome.browser.profiles.Profile p){return new org.chromium.components.prefs.PrefService();} }',
            'org.chromium.chrome.browser.profiles.ProfileKeyedMap': 'public class ProfileKeyedMap<T> { public @interface ProfileSelection { int OWN_INSTANCE=0; } public ProfileKeyedMap(int selection,org.chromium.base.Callback<T> cleanup){} public static <T> org.chromium.base.Callback<T> noRequiredCleanupAction(){return null;} public T getForProfile(Profile p,java.util.function.Function<Profile,T> factory){return factory.apply(p);} }',
        })
        definitions['org.chromium.chrome.browser.bookmarks.BookmarkModel'] = definitions[
            'org.chromium.chrome.browser.bookmarks.BookmarkModel'].replace(
                'public class BookmarkModel {',
                'public class BookmarkModel { public static BookmarkModel getForProfile(org.chromium.chrome.browser.profiles.Profile p){return new BookmarkModel();}')
        # Share the minimal, pinned authority contracts with the executed adapter regression.
        # These bodies remain synthetic and are not API/runtime compilation evidence.
        arc_spec = importlib.util.spec_from_file_location(
            'arc_session_regression', ROOT / 'scripts/test-arc-native-session.py')
        arc_module = importlib.util.module_from_spec(arc_spec)
        arc_spec.loader.exec_module(arc_module)
        for name in (
                'org.chromium.chrome.browser.tabmodel.TabList',
                'org.chromium.chrome.browser.tabmodel.TabModel',
                'org.chromium.chrome.browser.tabmodel.TabModelObserver',
                'org.chromium.chrome.browser.tabmodel.TabModelSelector',
                'org.chromium.chrome.browser.tabwindow.TabWindowManager',
                'org.chromium.chrome.browser.app.tabwindow.TabWindowManagerSingleton'):
            definitions[name] = arc_module.DEFINITIONS[name]
        for annotation in ['Nullable', 'NullMarked', 'NullUnmarked']:
            definitions['org.chromium.build.annotations.' + annotation] = '@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.TYPE,java.lang.annotation.ElementType.METHOD,java.lang.annotation.ElementType.PACKAGE}) public @interface ' + annotation + ' {}'
        for name, body in definitions.items():
            file = stubs / (name.replace('.', '/') + '.java')
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('package ' + name.rsplit('.', 1)[0] + ';\n' + body + '\n')
        new_java = list((ROOT / 'chromium').rglob('*.java'))
        account_path = 'components/signin/public/android/java/src/org/chromium/components/signin/NullAccountManagerDelegate.java'
        account = (ROOT / '.source-reference' if args.test_original_account_delegate else checkout) / account_path
        run('javac', '-cp', str(args.android_jar) + ':' + str(window_jar), '-d', str(classes),
            *map(str, stubs.rglob('*.java')), *map(str, new_java), str(account), str(ROOT / 'tests/java/NullAccountDelegateTest.java'), str(ROOT / 'tests/android/window/ArchiumPasswordManagerBridgeJni.java'))
        print('New Android adapters: isolated SDK API compilation passed (dependency contracts stubbed)', flush=True)
        run('java', '-cp', str(classes) + ':' + str(args.android_jar), 'NullAccountDelegateTest')
        run('python3', str(ROOT / 'scripts/test-password-settings-lifecycle.py'),
            '--android-jar', str(args.android_jar), '--source-root', str(checkout))
        run('python3', str(ROOT / 'scripts/test-arc-native-session.py'),
            '--source-root', str(checkout))
        run('python3', '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'),
            '-p', 'test_group_projection.py')
        print('Full Chromium build/native tests and browser password/Arc/adaptive/input acceptance remain pending', flush=True)


if __name__ == '__main__':
    main()
