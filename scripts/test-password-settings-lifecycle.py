#!/usr/bin/env python3
"""Execute the delivered password settings lifecycle through synthetic Android/JNI boundaries.

Compiles the actual fragment/bridge/CSV against an Android SDK, then executes preference
construction/cleanup and import review/summary callbacks on JVM contracts. The synchronous
virtual onCreatePreferences dispatch is
copied from AndroidX snapshot 16506667, preference-1.3.0-20261003.052004-1 (lines 143-163),
as preserved in .sync-audit/fix-chain/upstream/PreferenceFragmentCompat.java. This is a focused
regression, not a Robolectric/device/Chromium API compatibility gate.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

# These classes replace Android constructors that throw "Stub!" in the SDK jar. Untouched SDK
# classes provide the remaining type signatures. Dialog messages/listeners execute on a synthetic
# AlertDialog; SAF, crypto and JNI do not execute.
DEFINITIONS = {
    'android.content.Context': 'public class Context { public ContentResolver getContentResolver(){return null;} }',
    'android.app.Activity': 'public class Activity extends android.content.Context { public static final int RESULT_OK=-1; }',
    'android.os.Looper': 'public class Looper { public static Looper getMainLooper(){return new Looper();} }',
    'android.os.Handler': 'public class Handler { public Handler(Looper l){} public boolean post(Runnable r){r.run(); return true;} }',
    'android.app.AlertDialog': '''public class AlertDialog implements android.content.DialogInterface {
        public static final int BUTTON_POSITIVE=-1, BUTTON_NEGATIVE=-2;
        public static AlertDialog lastShown;
        public CharSequence title, message;
        private android.content.DialogInterface.OnClickListener positive, negative;
        private android.content.DialogInterface.OnDismissListener dismissed;
        private android.content.DialogInterface.OnCancelListener cancelled;
        public void show(){lastShown=this;}
        public void dismiss(){if(dismissed!=null)dismissed.onDismiss(this);}
        public void cancel(){if(cancelled!=null)cancelled.onCancel(this); dismiss();}
        public void clickPositive(){if(positive!=null)positive.onClick(this,BUTTON_POSITIVE); dismiss();}
        public void clickNegative(){if(negative!=null)negative.onClick(this,BUTTON_NEGATIVE); dismiss();}
        public void setOnDismissListener(android.content.DialogInterface.OnDismissListener l){dismissed=l;}
        public void setOnShowListener(android.content.DialogInterface.OnShowListener l){}
        public android.widget.Button getButton(int which){return null;}
        public static class Builder {
            private final AlertDialog dialog=new AlertDialog();
            public Builder(android.content.Context context){}
            public Builder setTitle(CharSequence s){dialog.title=s; return this;}
            public Builder setMessage(CharSequence s){dialog.message=s; return this;}
            public Builder setView(android.view.View v){return this;}
            public Builder setItems(CharSequence[] items,android.content.DialogInterface.OnClickListener l){return this;}
            public Builder setPositiveButton(CharSequence s,android.content.DialogInterface.OnClickListener l){dialog.positive=l; return this;}
            public Builder setPositiveButton(int s,android.content.DialogInterface.OnClickListener l){dialog.positive=l; return this;}
            public Builder setNegativeButton(CharSequence s,android.content.DialogInterface.OnClickListener l){dialog.negative=l; return this;}
            public Builder setNegativeButton(int s,android.content.DialogInterface.OnClickListener l){dialog.negative=l; return this;}
            public Builder setNeutralButton(CharSequence s,android.content.DialogInterface.OnClickListener l){return this;}
            public Builder setOnCancelListener(android.content.DialogInterface.OnCancelListener l){dialog.cancelled=l; return this;}
            public AlertDialog create(){return dialog;}
        }
    }''',
    'androidx.preference.Preference': '''public class Preference {
        public interface OnPreferenceClickListener { boolean onPreferenceClick(Preference p); }
        private CharSequence title; private boolean enabled=true;
        public Preference(android.content.Context c){} public void setTitle(CharSequence t){title=t;}
        public CharSequence getTitle(){return title;} public void setSummary(CharSequence s){}
        public void setEnabled(boolean e){enabled=e;} public boolean isEnabled(){return enabled;}
        public void setOnPreferenceClickListener(OnPreferenceClickListener l){}
    }''',
    'androidx.preference.PreferenceCategory': '''public class PreferenceCategory extends Preference {
        private final java.util.List<Preference> rows=new java.util.ArrayList<>();
        public PreferenceCategory(android.content.Context c){super(c);}
        public boolean addPreference(Preference p){rows.add(p); return true;}
        public void removeAll(){rows.clear();} public int getPreferenceCount(){return rows.size();}
        public Preference getPreference(int i){return rows.get(i);}
    }''',
    'androidx.preference.PreferenceScreen': 'public class PreferenceScreen extends PreferenceCategory { public PreferenceScreen(android.content.Context c){super(c);} }',
    'androidx.preference.PreferenceManager': 'public class PreferenceManager { public PreferenceScreen createPreferenceScreen(android.content.Context c){return new PreferenceScreen(c);} }',
    'org.chromium.chrome.browser.settings.ChromeBaseSettingsFragment': '''public class ChromeBaseSettingsFragment {
        private org.chromium.chrome.browser.profiles.Profile profile;
        private androidx.preference.PreferenceScreen screen;
        public void setProfile(org.chromium.chrome.browser.profiles.Profile p){profile=p;}
        public org.chromium.chrome.browser.profiles.Profile getProfile(){return profile;}
        public void onCreate(android.os.Bundle b){onCreatePreferences(b,null);}
        public void onCreatePreferences(android.os.Bundle b,String key){}
        public android.app.Activity requireActivity(){return new android.app.Activity();}
        public android.content.Context requireContext(){return requireActivity();}
        public androidx.preference.PreferenceManager getPreferenceManager(){return new androidx.preference.PreferenceManager();}
        public void setPreferenceScreen(androidx.preference.PreferenceScreen s){screen=s;}
        public androidx.preference.PreferenceScreen getPreferenceScreen(){return screen;}
        public org.chromium.base.supplier.SettableMonotonicObservableSupplier<String> getPageTitle(){return null;}
        public int getAnimationType(){return 0;} public void onDestroy(){} public boolean isAdded(){return true;}
        public android.content.res.Resources getResources(){return null;}
        public void startActivityForResult(android.content.Intent i,int code){}
        public void onActivityResult(int request,int result,android.content.Intent data){}
    }''',
    'org.chromium.chrome.browser.profiles.Profile': 'public class Profile { private final boolean otr; public Profile(boolean o){otr=o;} public boolean isOffTheRecord(){return otr;} }',
    'org.chromium.base.supplier.SettableMonotonicObservableSupplier': 'public class SettableMonotonicObservableSupplier<T> { public void set(T v){} }',
    'org.chromium.base.supplier.ObservableSuppliers': 'public class ObservableSuppliers { public static <T> SettableMonotonicObservableSupplier<T> createMonotonic(){return new SettableMonotonicObservableSupplier<T>();} }',
    'org.chromium.components.browser_ui.settings.SettingsFragment': 'public interface SettingsFragment { public @interface AnimationType { int PROPERTY=1; } }',
    'org.chromium.chrome.browser.password_manager.ArchiumPasswordManagerBridgeJni': '''public final class ArchiumPasswordManagerBridgeJni {
        public static int initialized, refreshed, destroyed, cancelled, previewRequest, confirmedRequest;
        public static int[] confirmedDecisions; public static char[][] lastPasswords;
        public static boolean enabled=true, throwPreview;
        public static void reset(){initialized=refreshed=destroyed=cancelled=previewRequest=confirmedRequest=0;
            enabled=true; throwPreview=false; confirmedDecisions=null; lastPasswords=null; android.app.AlertDialog.lastShown=null;}
        private static final ArchiumPasswordManagerBridge.Natives INSTANCE=new ArchiumPasswordManagerBridge.Natives(){
            public boolean isLocalEnabled(){return enabled;}
            public long init(ArchiumPasswordManagerBridge b,org.chromium.chrome.browser.profiles.Profile p,android.app.Activity a){initialized++; return 1;}
            public void refresh(long p){refreshed++;}
            public void add(long p,int r,String u,String n,char[] s){}
            public void update(long p,int r,long id,String n,char[] s){}
            public void delete(long p,int r,long id){} public void reveal(long p,int r,long id){}
            public void export(long p,int r){} public void previewImport(long p,int r,String[] u,String[] n,char[][] s){
                previewRequest=r; lastPasswords=s; if(throwPreview)throw new IllegalStateException("synthetic JNI failure");}
            public void confirmImport(long p,int r,int[] d){confirmedRequest=r; confirmedDecisions=d.clone();}
            public void cancelImport(long p){cancelled++;}
            public void destroy(long p){destroyed++;}
        };
        public static ArchiumPasswordManagerBridge.Natives get(){return INSTANCE;}
    }''',
}
for name in ('NullMarked', 'Nullable'):
    DEFINITIONS['org.chromium.build.annotations.' + name] = (
        '@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.TYPE,'
        'java.lang.annotation.ElementType.METHOD,java.lang.annotation.ElementType.FIELD,java.lang.annotation.ElementType.PARAMETER})'
        ' public @interface ' + name + ' {}')
for name in ('CalledByNative', 'NativeMethods'):
    DEFINITIONS['org.jni_zero.' + name] = 'public @interface ' + name + ' {}'
DEFINITIONS['org.jni_zero.JniType'] = (
    '@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.PARAMETER})'
    ' public @interface JniType { String value(); }')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--android-jar', type=Path, default=Path('/opt/android-sdk/platforms/android-36/android.jar'))
    parser.add_argument('--source-root', type=Path, default=ROOT / 'chromium',
                        help='delivered Chromium overlay or applied checkout (also permits RED baseline)')
    args = parser.parse_args()
    if not args.android_jar.is_file():
        raise SystemExit('Missing Android SDK jar: ' + str(args.android_jar))
    with tempfile.TemporaryDirectory(prefix='archium-password-lifecycle-') as tmp:
        work = Path(tmp)
        contracts = []
        for name, body in DEFINITIONS.items():
            path = work / 'contracts' / (name.replace('.', '/') + '.java')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('package ' + name.rsplit('.', 1)[0] + ';\n' + body + '\n')
            contracts.append(path)
        sources = args.source_root / ('chrome/browser/password_manager/android/java/src/'
                                      'org/chromium/chrome/browser/password_manager')
        delivered = [sources / (name + '.java') for name in
                     ('ArchiumPasswordCsv', 'ArchiumPasswordManagerBridge', 'ArchiumPasswordSettingsFragment')]
        classes = work / 'classes'
        subprocess.run(['javac', '-cp', str(args.android_jar), '-d', str(classes),
                        *map(str, contracts + delivered),
                        str(ROOT / 'tests/java/ArchiumPasswordSettingsLifecycleSyntheticBoundaryTest.java')], check=True)
        subprocess.run(['java', '-cp', str(classes) + ':' + str(args.android_jar),
                        'ArchiumPasswordSettingsLifecycleSyntheticBoundaryTest'], check=True)


if __name__ == '__main__':
    main()
