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
            if overlay.exists():
                assert overlay.read_bytes() == (checkout / name).read_bytes(), 'Stale patch: ' + name
            if name.endswith('.xml'):
                ET.parse(checkout / name)
        print(f'Pinned patch: all {len(manifest["originals"])} files applied and hashes matched', flush=True)
        classes = work / 'classes'
        pure = list((ROOT / 'chromium').rglob('ArchiumWindowClass.java')) + list((ROOT / 'chromium').rglob('ArcDesktopPolicy.java')) + list((ROOT / 'chromium').rglob('ArchiumAutofillPolicy.java'))
        pure += list((ROOT / 'chromium').rglob('ArchiumPasswordCsv.java'))
        run('javac', '-cp', str(window_jar), '-d', str(classes), *map(str, pure), str(ROOT / 'tests/java/ArcDesktopPolicyTest.java'),
            str(ROOT / 'tests/java/ArchiumAutofillPolicyTest.java'), str(ROOT / 'tests/java/ArchiumWindowClassTest.java'),
            str(ROOT / 'tests/java/ArchiumPasswordCsvTest.java'))
        run('java', '-cp', str(classes), 'ArchiumWindowClassTest')
        run('java', '-cp', str(classes), 'ArcDesktopPolicyTest')
        run('java', '-cp', str(classes), 'ArchiumAutofillPolicyTest')
        run('java', '-Xmx256m', '-cp', str(classes), 'ArchiumPasswordCsvTest')
        if not args.android_jar.is_file():
            raise SystemExit('Missing Android SDK jar; pass --android-jar')
        stubs = work / 'contracts'
        definitions = {
            'org.chromium.chrome.R': 'public final class R { public static final class string { public static final int arc_bookmarks=1, arc_frame_color=2, arc_bookmark_root=3, arc_google_login=4, arc_autofill=5, arc_reset_color=6, arc_color_format=7; } public static final class id { public static final int toolbar=1, desktop_window_spacer=2; } }',
            'org.chromium.chrome.browser.profiles.Profile': 'public class Profile {}',
            'org.chromium.components.bookmarks.BookmarkId': 'public class BookmarkId {}',
            'org.chromium.url.GURL': 'public class GURL { public String getSpec() { return ""; } }',
            'org.chromium.components.bookmarks.BookmarkItem': 'public class BookmarkItem { public String getTitle(){return "";} public boolean isFolder(){return false;} public org.chromium.url.GURL getUrl(){return null;} }',
            'org.chromium.chrome.browser.bookmarks.BookmarkModelObserver': 'public abstract class BookmarkModelObserver { public abstract void bookmarkModelChanged(); }',
            'org.chromium.chrome.browser.bookmarks.BookmarkModel': 'public class BookmarkModel { public void addObserver(BookmarkModelObserver o){} public void removeObserver(BookmarkModelObserver o){} public boolean isBookmarkModelLoaded(){return true;} public boolean finishLoadingBookmarkModel(Runnable r){return false;} public org.chromium.components.bookmarks.BookmarkId getDesktopFolderId(){return null;} public java.util.List<org.chromium.components.bookmarks.BookmarkId> getChildIds(org.chromium.components.bookmarks.BookmarkId id){return null;} public java.util.List<org.chromium.components.bookmarks.BookmarkId> getTopLevelFolderIds(){return null;} public org.chromium.components.bookmarks.BookmarkItem getBookmarkById(org.chromium.components.bookmarks.BookmarkId id){return null;} }',
            'org.chromium.chrome.browser.tabmodel.IncognitoStateProvider': 'public class IncognitoStateProvider { public interface IncognitoStateObserver { void onIncognitoStateChanged(boolean i); } public boolean isIncognitoSelected(){return false;} public void addIncognitoStateObserverAndTrigger(IncognitoStateObserver o){o.onIncognitoStateChanged(false);} public void removeObserver(IncognitoStateObserver o){} }',
            'org.chromium.components.favicon.LargeIconBridge': 'public class LargeIconBridge { public interface LargeIconCallback { void onLargeIconAvailable(android.graphics.Bitmap icon, int color, boolean fallback, int type); } public LargeIconBridge(org.chromium.chrome.browser.profiles.Profile p){} public boolean getLargeIconForUrl(org.chromium.url.GURL url,int size,LargeIconCallback cb){return true;} public void destroy(){} }',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabRailLayout': 'public class VerticalTabRailLayout extends android.view.View { public VerticalTabRailLayout(android.content.Context c){super(c);} public void setDesktopWindowSpacerHost(android.view.View v){} }',
            'org.chromium.chrome.browser.tasks.tab_management.vertical_tabs.VerticalTabListViewBinder': 'public class VerticalTabListViewBinder { public static void refreshArcAppearance(VerticalTabRailLayout v,boolean i){} }',
            'org.chromium.chrome.browser.toolbar.top.ToolbarTablet': 'public class ToolbarTablet extends android.view.View { public ToolbarTablet(android.content.Context c){super(c);} public void onThemeColorChanged(int color,boolean animate){} }',
            'org.chromium.chrome.browser.lifecycle.ConfigurationChangedObserver': 'public interface ConfigurationChangedObserver { void onConfigurationChanged(android.content.res.Configuration c); }',
            'org.chromium.chrome.browser.lifecycle.ActivityLifecycleDispatcher': 'public interface ActivityLifecycleDispatcher { void register(ConfigurationChangedObserver o); void unregister(ConfigurationChangedObserver o); }',
            'androidx.recyclerview.widget.RecyclerView': 'public class RecyclerView extends android.view.ViewGroup { public RecyclerView(android.content.Context c){super(c);} public abstract static class Adapter<T> { public void notifyDataSetChanged(){} } public Adapter<?> getAdapter(){return null;} protected void onLayout(boolean c,int l,int t,int r,int b){} }',
            'org.chromium.base.ContextUtils': 'public class ContextUtils { public static android.content.Context getApplicationContext(){return null;} }',
            'org.jni_zero.CalledByNative': '@java.lang.annotation.Target(java.lang.annotation.ElementType.METHOD) public @interface CalledByNative {}',
            'org.jni_zero.JNINamespace': '@java.lang.annotation.Target(java.lang.annotation.ElementType.TYPE) public @interface JNINamespace { String value(); }',
            'org.chromium.base.Callback': 'public interface Callback<T> { void onResult(T value); }',
            'org.chromium.google_apis.gaia.GaiaId': 'public class GaiaId {}',
            'org.chromium.components.signin.AuthException': 'public class AuthException extends Exception {}',
            'org.chromium.components.signin.AccessTokenData': 'public class AccessTokenData {}',
            'org.chromium.components.signin.AccountManagerDelegate': 'public interface AccountManagerDelegate { public interface AccountsChangeObserver{} public @interface CapabilityResponse{int EXCEPTION=0;} void attachAccountsChangeObserver(AccountsChangeObserver o); android.accounts.Account[] getAccountsSynchronous(); AccessTokenData getAccessToken(android.accounts.Account a,String s); void invalidateAccessToken(String s) throws AuthException; int hasCapability(android.accounts.Account a,String s); void createAddAccountIntent(String email,org.chromium.base.Callback<android.content.Intent> c); void updateCredentials(android.accounts.Account a,android.app.Activity activity,org.chromium.base.Callback<Boolean> c); org.chromium.google_apis.gaia.GaiaId getAccountGaiaId(String e); void confirmCredentials(android.accounts.Account a,android.app.Activity activity,org.chromium.base.Callback<android.os.Bundle> c); }',
        }
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
            *map(str, stubs.rglob('*.java')), *map(str, new_java), str(account), str(ROOT / 'tests/java/NullAccountDelegateTest.java'))
        print('New Android adapters: isolated SDK API compilation passed (dependency contracts stubbed)', flush=True)
        run('java', '-cp', str(classes) + ':' + str(args.android_jar), 'NullAccountDelegateTest')
        print('APK build and DeX/Google Autofill runtime tests remain pending', flush=True)


if __name__ == '__main__':
    main()
