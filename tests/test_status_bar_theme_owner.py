"""Compile the delivered edge helper; fake OS/suppliers record contrast ownership, not pixels."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.source-modified/ui/edge_to_edge/android/java/src/org/chromium/ui/edge_to_edge/EdgeToEdgeSystemBarColorHelper.java'
BOUNDARIES = {
'android.graphics.Color': 'public class Color { public static final int TRANSPARENT=0; }',
'android.view.WindowManager': 'public interface WindowManager { class LayoutParams { public static final int FLAG_TRANSLUCENT_NAVIGATION=1, FLAG_TRANSLUCENT_STATUS=2, FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS=4; }}',
'android.view.Window': 'public class Window { public Object getDecorView(){return this;} public void clearFlags(int f){} public void addFlags(int f){} }',
'org.chromium.base.Callback': 'public interface Callback<T> {void onResult(T v);}',
'org.chromium.base.supplier.NonNullObservableSupplier': 'public interface NonNullObservableSupplier<T>{T get(); void addSyncObserverAndPostIfNonNull(org.chromium.base.Callback<T> c); void removeObserver(org.chromium.base.Callback<T> c);}',
'org.chromium.base.supplier.OneshotSupplier': 'public interface OneshotSupplier<T>{T get(); void onAvailable(org.chromium.base.Callback<T> c);}',
'org.chromium.build.annotations.NullMarked': 'public @interface NullMarked {}',
'org.chromium.build.annotations.Nullable': '@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.METHOD}) public @interface Nullable {}',
'org.chromium.ui.edge_to_edge.SystemBarColorHelper': 'public interface SystemBarColorHelper {boolean canSetStatusBarColor(); void setStatusBarColor(int c); void setNavigationBarColor(int c); void setNavigationBarDividerColor(int c);}',
'org.chromium.ui.edge_to_edge.BaseSystemBarColorHelper': '''public abstract class BaseSystemBarColorHelper implements SystemBarColorHelper {
protected int mStatusBarColor,mNavBarColor,mNavBarDividerColor; protected boolean mForceLightStatusBarColor;
public static int contrast; public static boolean forced;
public void destroy(){} protected abstract void applyStatusBarColor(); protected abstract void applyNavBarColor(); protected abstract void applyNavigationBarDividerColor();
public void setStatusBarColor(int c){mStatusBarColor=c;applyStatusBarColor();} public void setNavigationBarColor(int c){mNavBarColor=c;applyNavBarColor();} public void setNavigationBarDividerColor(int c){mNavBarDividerColor=c;applyNavigationBarDividerColor();}
protected static void updateNavigationBarIconColor(Object v,int c){} protected static void updateStatusBarIconColor(Object v,int c){contrast=c;forced=false;} protected static void updateStatusBarWithLightIconColor(Object v){forced=true;}
}''',
'org.chromium.ui.edge_to_edge.WindowSystemBarColorHelper': '''public class WindowSystemBarColorHelper {
public WindowSystemBarColorHelper(android.view.Window w){} public void destroy(){} public int getStatusBarColor(){return 0;} public int getNavigationBarColor(){return 0;} public int getNavigationBarDividerColor(){return 0;}
public void setStatusBarColor(int c){} public void setNavigationBarColor(int c){} public void setNavigationBarDividerColor(int c){} public void setStatusBarContrastEnforced(boolean b){} public void setNavigationBarContrastEnforced(boolean b){}
}'''
}
PROBE = '''package org.chromium.ui.edge_to_edge;
import org.chromium.base.Callback; import org.chromium.base.supplier.*;
public class StatusContrastProbe {
static class Fits implements NonNullObservableSupplier<Boolean> {boolean value=true; Callback<Boolean> observer; public Boolean get(){return value;} public void addSyncObserverAndPostIfNonNull(Callback<Boolean> c){observer=c;} public void removeObserver(Callback<Boolean> c){observer=null;} void set(boolean v){value=v;observer.onResult(v);}}
static class Delegate implements OneshotSupplier<SystemBarColorHelper>{Callback<SystemBarColorHelper> observer; public SystemBarColorHelper get(){return null;} public void onAvailable(Callback<SystemBarColorHelper> c){observer=c;}}
static void same(int want){if(BaseSystemBarColorHelper.contrast!=want)throw new AssertionError("Contrast backing: expected "+want+" actual "+BaseSystemBarColorHelper.contrast);}
static void override(EdgeToEdgeSystemBarColorHelper h,Integer c)throws Exception {
try {h.getClass().getMethod("setStatusBarIconContrastColorOverride",Integer.class).invoke(h,c);}catch(NoSuchMethodException e){/* Reproduce old owner behavior before fix. */}}
public static void main(String[] args)throws Exception {
Fits fits=new Fits(); Delegate delegate=new Delegate(); EdgeToEdgeSystemBarColorHelper h=new EdgeToEdgeSystemBarColorHelper(new android.view.Window(),fits,delegate,true);
h.setStatusBarColor(0xff123456);same(0xff123456); // Default/native Desktop behavior.
for(int backing:new int[]{0xffffffff,0xff202124}) {
override(h,backing);h.setStatusBarColor(0);fits.set(false);same(backing);fits.set(true);same(backing);delegate.observer.onResult(null);same(backing);
h.mForceLightStatusBarColor=true;h.setStatusBarColor(0);if(!BaseSystemBarColorHelper.forced)throw new AssertionError("Forced native icons lost");h.mForceLightStatusBarColor=false;
}
override(h,null);h.setStatusBarColor(0xffabcdef);fits.set(false);same(0xffabcdef);h.destroy();if(fits.observer!=null)throw new AssertionError("Observer leaked");
System.out.println("PASS light/dark backing survives inset/delegate updates; forced icons and native reset preserved");}}
'''
class StatusBarThemeOwnerTests(unittest.TestCase):
    def test_contrast_backing_survives_native_owner_refresh(self):
        javac,java=shutil.which('javac'),shutil.which('java')
        self.assertIsNotNone(javac);self.assertIsNotNone(java)
        with tempfile.TemporaryDirectory(prefix='archium-status-owner-') as temp:
            work=Path(temp); files=[SOURCE]
            for name,body in BOUNDARIES.items():
                package,cls=name.rsplit('.',1);f=work/(cls+'.java');f.write_text('package '+package+';'+body);files.append(f)
            probe=work/'StatusContrastProbe.java';probe.write_text(PROBE);files.append(probe)
            result=subprocess.run([javac,'-d',temp,*map(str,files)],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)
            result=subprocess.run([java,'-cp',temp,'org.chromium.ui.edge_to_edge.StatusContrastProbe'],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)
            print(result.stdout.strip())
