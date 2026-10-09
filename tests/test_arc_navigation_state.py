"""Run the complete shipped navigation binder at native Tab/supplier boundaries.

Pinned interface/default-method excerpts constrain service doubles. This verifies
observer ownership, authoritative tab dispatch and button state, not rendering.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body

SOURCE = ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcNavigationState.java'
TAB_REF = ROOT/'.source-reference/chrome/browser/tab/java/src/org/chromium/chrome/browser/tab'
SUPPLIER_REF = ROOT/'.source-reference/base/android/java/src/org/chromium/base/supplier'
VALUES = ROOT/'.source-reference/chrome/browser/ui/android/toolbar/java/res/values/values.xml'

JAVA = r'''
import java.util.*;
import org.chromium.base.Callback;
import org.chromium.base.supplier.NullableObservableSupplier;
import org.chromium.chrome.browser.arc.ArcNavigationState;
import org.chromium.chrome.browser.tab.*;
import android.widget.ImageButton;
import org.chromium.content_public.browser.NavigationHandle;
class NavigationProbe {
    static class Current implements NullableObservableSupplier<Tab> {
        Tab value;List<Callback<Tab>> observers=new ArrayList<>();
        public Tab get(){return value;}public void removeObserver(Callback<Tab> c){observers.remove(c);}
        public Tab addObserver(Callback<Tab> c,int behavior){observers.add(c);if((behavior&1)!=0&&(value!=null||(behavior&4)!=0))c.onResult(value);return value;}
        void set(Tab t){value=t;for(Callback<Tab> c:new ArrayList<>(observers))c.onResult(t);}
    }
    static class NativeTab implements Tab {
        boolean loading,back,forward,destroyed,closing;int reloads,stops,backs,forwards,additions,removals;
        List<TabObserver> observers=new ArrayList<>();
        public boolean isLoading(){return loading;}public boolean canGoBack(){return back;}public boolean canGoForward(){return forward;}
        public boolean isDestroyed(){return destroyed;}public boolean isClosing(){return closing;}
        public void reload(){reloads++;}public void stopLoading(){stops++;}public void goBack(){backs++;}public void goForward(){forwards++;}
        public void addObserver(TabObserver o){observers.add(o);additions++;}public void removeObserver(TabObserver o){observers.remove(o);removals++;}
        TabObserver observer(){check(observers.size()==1,"exactly one native tab observer");return observers.get(0);}
    }
    static class Fixture {
        Current current=new Current();ImageButton back=new ImageButton(),forward=new ImageButton(),reload=new ImageButton();ArcNavigationState state;
        Fixture(NativeTab tab){current.value=tab;state=new ArcNavigationState(current,back,forward,reload);}
    }
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    public static void main(String[] args){String s=args[0];NativeTab t=new NativeTab();
        if(s.equals("load")) {
            t.back=true;Fixture f=new Fixture(t);check(f.back.isEnabled()&&!f.forward.isEnabled()&&f.reload.isEnabled(),"initial native capabilities");
            check(f.reload.level==RELOAD_LEVEL&&f.reload.description.equals("Refresh"),"native reload level and accessibility label");
            t.loading=true;t.observer().onLoadStarted(t,true);check(f.reload.level==STOP_LEVEL&&f.reload.description.equals("Stop loading"),"load start changes existing button toStop");
            f.reload.click();check(t.stops==1&&t.reloads==0,"loading button stops current native tab");
            t.loading=false;t.observer().onLoadStopped(t,true);check(f.reload.level==RELOAD_LEVEL,"load stop restores Reload");f.reload.click();check(t.reloads==1,"idle button reloads current native tab");
            t.loading=true;f.reload.click();check(t.stops==2,"click re-reads actual loading state before observer presentation catches up");t.loading=false;
            t.back=false;t.forward=true;t.observer().onNavigationStateChanged();check(!f.back.isEnabled()&&f.forward.isEnabled(),"native parameterless history invalidation");
            f.back.click();f.forward.click();check(t.backs==0&&t.forwards==1,"native navigation only dispatches enabled direction");
        } else if(s.equals("supplier")) {
            Fixture empty=new Fixture(null);check(!empty.back.isEnabled()&&!empty.forward.isEnabled()&&!empty.reload.isEnabled(),"synchronous supplier replay includes initial null");
            check(empty.current.observers.size()==1,"one authoritative supplier observer");empty.current.set(t);check(t.observers.size()==1&&empty.reload.isEnabled(),"null-to-live current tab refreshes without model callback");empty.state.destroy();
            Fixture f=new Fixture(t);TabObserver old=t.observer();NativeTab next=new NativeTab();next.back=true;next.loading=true;
            f.current.set(next);check(t.observers.isEmpty()&&next.observers.size()==1,"authoritative supplier swaps native observer");
            check(f.back.isEnabled()&&f.reload.level==STOP_LEVEL,"supplier notification refreshes existing buttons immediately");
            int changes=f.reload.mutations;old.onLoadStopped(t,true);old.onNavigationStateChanged();old.onDestroyed(t);check(f.reload.mutations==changes,"stale native callbacks cannot alter current controls");
            f.reload.click();check(next.stops==1&&t.stops==0,"click dispatches actual current supplier tab");
            f.current.set(null);check(next.observers.isEmpty()&&!f.back.isEnabled()&&!f.forward.isEnabled()&&!f.reload.isEnabled(),"null current tab clears observer and controls");
            f.state.bind(t);check(t.observers.isEmpty(),"manual bind must not attach obsolete tab outside supplier authority");
        } else if(s.equals("mobile")) {
            t.loading=true;Fixture f=new Fixture(t);TabObserver old=t.observer();f.state.setActive(false);
            check(t.observers.isEmpty()&&!f.reload.isEnabled(),"MOBILE releases native tab subscription");NativeTab next=new NativeTab();next.forward=true;f.current.set(next);
            check(next.observers.isEmpty(),"MOBILE supplier notifications cannot observe inactive tabs");int changes=f.reload.mutations;old.onNavigationStateChanged();check(f.reload.mutations==changes,"paused stale event no-op");f.reload.click();check(next.reloads==0,"paused hidden controls cannot dispatch");
            f.state.setActive(true);check(next.observers.size()==1&&f.forward.isEnabled()&&f.reload.level==RELOAD_LEVEL,"ARC resumes latest authoritative tab");
            f.state.setActive(true);f.state.bind(next);check(next.additions==1,"stable binding never duplicates observer");
        } else if(s.equals("destroy")) {
            Fixture f=new Fixture(t);TabObserver old=t.observer();Callback<Tab> supplier=f.current.observers.get(0);f.state.destroy();f.state.destroy();
            check(t.observers.isEmpty()&&f.current.observers.isEmpty(),"destroy removes both observers exactly once");check(t.removals==1&&!f.reload.isEnabled(),"destroy leaves safe disabled controls");
            int changes=f.reload.mutations;old.onLoadStarted(t,true);supplier.onResult(t);f.state.setActive(true);f.state.bind(t);check(f.reload.mutations==changes&&t.observers.isEmpty(),"callbacks and reactivation after destroy are no-ops");
            check(f.back.listener==null&&f.forward.listener==null&&f.reload.listener==null,"destroy releases click closures");
        } else if(s.equals("history")) {
            Fixture f=new Fixture(t);t.back=true;t.observer().onDidFinishNavigationInPrimaryMainFrame(t,new NavigationHandle());check(f.back.isEnabled(),"history commit refreshes directions while load can still be pending");t.observer().onNavigationEntriesAppended(t);check(f.back.isEnabled(),"appended native history enablesBack");t.back=false;t.forward=true;t.observer().onNavigationEntriesDeleted(t);check(!f.back.isEnabled()&&f.forward.isEnabled(),"deleted history refreshes direction state");
            t.forward=false;t.observer().onContentChanged(t);check(!f.forward.isEnabled(),"native content swap clears stale capability");
            t.closing=true;t.observer().onClosingStateChanged(t,true);check(!f.reload.isEnabled(),"closing tab cannot receive reload");t.closing=false;t.observer().onClosingStateChanged(t,false);check(f.reload.isEnabled(),"undo closure restores native controls");
            t.destroyed=true;t.observer().onDestroyed(t);check(t.observers.isEmpty()&&!f.reload.isEnabled(),"destroyed tab releases observer and disables buttons");
        }
        System.out.println("PASS "+s);
    }
}
'''


class ArcNavigationStateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.missing=not SOURCE.exists()
        if cls.missing:return
        cls.temp=tempfile.TemporaryDirectory(prefix='arc-navigation-');cls.addClassCleanup(cls.temp.cleanup);cls.work=Path(cls.temp.name)
        home=Path(os.environ.get('JAVA_HOME','/usr/lib/jvm/java-17-openjdk-arm64'));cls.javac=str(home/'bin/javac');cls.java=str(home/'bin/java')
        def write(path,text):
            p=cls.work/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);return p
        tab=(TAB_REF/'Tab.java').read_text();observer=(TAB_REF/'TabObserver.java').read_text();lifecycle=(TAB_REF/'TabLifecycle.java').read_text()
        methods=['void addObserver(TabObserver observer);','void removeObserver(TabObserver observer);','void reload();','void stopLoading();','boolean isLoading();','boolean canGoBack();','boolean canGoForward();','void goBack();','void goForward();']
        for signature in methods:
            if signature not in tab:raise AssertionError('Native Tab API mismatch: '+signature)
        life=['boolean isDestroyed();','boolean isClosing();']
        for signature in life:
            if signature not in lifecycle:raise AssertionError('Native TabLifecycle API mismatch: '+signature)
        cls.tab_source=write('org/chromium/chrome/browser/tab/Tab.java','package org.chromium.chrome.browser.tab; public interface Tab {'+'\n'.join(methods+life)+'}')
        callbacks=['onLoadStarted(Tab tab, boolean toDifferentDocument)','onLoadStopped(Tab tab, boolean toDifferentDocument)','onNavigationStateChanged()','onDidFinishNavigationInPrimaryMainFrame(Tab tab, NavigationHandle navigation)','onNavigationEntriesAppended(Tab tab)','onNavigationEntriesDeleted(Tab tab)','onContentChanged(Tab tab)','onClosingStateChanged(Tab tab, boolean closing)','onDestroyed(Tab tab)']
        bodies=['default void '+signature+' '+method_body(observer,re.escape('default void '+signature)) for signature in callbacks]
        cls.observer_source=write('org/chromium/chrome/browser/tab/TabObserver.java','package org.chromium.chrome.browser.tab;import org.chromium.content_public.browser.NavigationHandle;public interface TabObserver {'+'\n'.join(bodies)+'}')
        supplier=(SUPPLIER_REF/'NullableObservableSupplier.java').read_text();sig='default @Nullable T addSyncObserverAndCall(Callback<@Nullable T> obs)'
        supplier_method=(sig+' '+method_body(supplier,re.escape(sig))).replace('@Nullable ','')
        cls.supplier_source=write('org/chromium/base/supplier/NullableObservableSupplier.java','package org.chromium.base.supplier;import java.util.function.Supplier;import org.chromium.base.Callback;public interface NullableObservableSupplier<T> extends Supplier<T> {T addObserver(Callback<T> obs,int behavior);void removeObserver(Callback<T> obs);interface NotifyBehavior {int NOTIFY_ON_ADD=1,ALLOW_NULL_ON_ADD=4;}'+supplier_method+'}')
        cls.navigation_source=write('org/chromium/content_public/browser/NavigationHandle.java','package org.chromium.content_public.browser;public class NavigationHandle {}')
        cls.callback_source=write('org/chromium/base/Callback.java','package org.chromium.base;public interface Callback<T>{void onResult(T value);}')
        cls.thread_source=write('org/chromium/base/ThreadUtils.java','package org.chromium.base;public class ThreadUtils {public static void assertOnUiThread(){}}')
        values=VALUES.read_text();cls.reload_level=int(re.search(r'name="reload_button_level_reload">(\d+)',values).group(1));cls.stop_level=int(re.search(r'name="reload_button_level_stop">(\d+)',values).group(1))
        cls.r_source=write('org/chromium/chrome/R.java','package org.chromium.chrome;public class R {public static class integer {public static final int reload_button_level_reload=11,reload_button_level_stop=12;}public static class string {public static final int accessibility_btn_refresh=21,accessibility_btn_stop_loading=22;}}')
        cls.resources_source=write('android/content/res/Resources.java','package android.content.res;public class Resources {public int getInteger(int id){return id==11?'+str(cls.reload_level)+':'+str(cls.stop_level)+';}public String getString(int id){return id==21?"Refresh":"Stop loading";}}')
        cls.view_source=write('android/view/View.java','package android.view;public class View {public interface OnClickListener {void onClick(View v);}}')
        cls.button_source=write('android/widget/ImageButton.java','''package android.widget;import android.view.View;import android.content.res.Resources;
public class ImageButton extends View {public boolean enabled=true;public int level,mutations;public String description;public OnClickListener listener;
public Resources getResources(){return new Resources();}public void setOnClickListener(OnClickListener c){listener=c;}public void setEnabled(boolean b){enabled=b;mutations++;}public boolean isEnabled(){return enabled;}public void setImageLevel(int l){level=l;mutations++;}public void setContentDescription(CharSequence c){description=c.toString();mutations++;}public void click(){if(enabled&&listener!=null)listener.onClick(this);}}
''')
        cls.program=write('NavigationProbe.java',JAVA.replace('RELOAD_LEVEL',str(cls.reload_level)).replace('STOP_LEVEL',str(cls.stop_level)))
        cls.services=[cls.tab_source,cls.observer_source,cls.supplier_source,cls.callback_source,cls.thread_source,cls.r_source,cls.navigation_source]
        result=subprocess.run([cls.javac,'--release','17','-d',str(cls.work),*map(str,cls.services+[cls.resources_source,cls.view_source,cls.button_source,cls.program]),str(SOURCE)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)

    def probe(self,scenario):
        self.assertFalse(self.missing,'Native navigation state binder has not been implemented')
        r=subprocess.run([self.java,'-ea','-cp',str(self.work),'NavigationProbe',scenario],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_native_load_start_stop_levels_labels_and_click_dispatch(self):self.probe('load')
    def test_authoritative_current_tab_supplier_replaces_observer_and_rejects_stale_events(self):self.probe('supplier')
    def test_mobile_pauses_observation_and_arc_resumes_latest_supplier_tab(self):self.probe('mobile')
    def test_destroy_releases_supplier_tab_and_click_observers(self):self.probe('destroy')
    def test_native_history_content_closure_and_destruction_callbacks(self):self.probe('history')

    def test_complete_class_compiles_against_android37_button_api(self):
        self.assertFalse(self.missing,'Native navigation state binder has not been implemented')
        jar=Path(os.environ.get('ANDROID_HOME','/opt/android-sdk'))/'platforms/android-37.0/android.jar'
        if not jar.exists():self.skipTest('Android37 API jar unavailable')
        api=self.work/'android-api';api.mkdir(exist_ok=True)
        r=subprocess.run([self.javac,'--release','17','-cp',str(jar),'-d',str(api),*map(str,self.services),str(SOURCE)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
