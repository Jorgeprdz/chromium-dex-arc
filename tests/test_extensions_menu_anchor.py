"""Execute the native coordinator's actual programmatic show method on a host JVM."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.source-modified/chrome/browser/ui/android/toolbar/java/src/org/chromium/chrome/browser/toolbar/extensions/ExtensionsToolbarCoordinatorImpl.java'


def method(source, signature):
    start = source.index(signature)
    opened = source.index('{', start)
    depth, end = 1, opened + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class ExtensionsMenuAnchorTests(unittest.TestCase):
    def test_waits_for_visible_laid_out_native_anchor(self):
        source = SOURCE.read_text()
        body = method(source, 'public void showExtensionsMenu()')
        if 'private static boolean isMenuAnchorReady(' in source:
            body += method(source, 'private static boolean isMenuAnchorReady(')
        if 'private void cancelPendingMenuShow()' in source:
            body += method(source, 'private void cancelPendingMenuShow()')
        harness = r'''
import java.util.*;
public class NativeMenuAnchorTest {
 @interface Nullable {}
 static class ViewTreeObserver {
  interface OnPreDrawListener {boolean onPreDraw();}
  List<OnPreDrawListener> listeners=new ArrayList<>();
  boolean isAlive(){return true;}
  void addOnPreDrawListener(OnPreDrawListener l){listeners.add(l);}
  void removeOnPreDrawListener(OnPreDrawListener l){listeners.remove(l);}
  void draw(){for(OnPreDrawListener l:new ArrayList<>(listeners))l.onPreDraw();}
 }
 static class Rect {}
 static class View {
  boolean shown,layoutRequested;int width,height,clicks;
  ViewTreeObserver observer=new ViewTreeObserver();List<Runnable> posted=new ArrayList<>();
  void post(Runnable r){posted.add(r);}
  void drainPosts(){for(Runnable r:new ArrayList<>(posted))r.run();posted.clear();}
  boolean isShown(){return shown;}
  boolean isLayoutRequested(){return layoutRequested;}
  int getWidth(){return width;}int getHeight(){return height;}
  boolean getGlobalVisibleRect(Rect r){return shown&&width>0&&height>0;}
  ViewTreeObserver getViewTreeObserver(){return observer;}
  void requestLayout(){layoutRequested=true;}
  Runnable onClick;
  boolean performClick(){clicks++;if(onClick!=null)onClick.run();return true;}
 }
 static class ListMenuButton extends View {}
 static class R {static class id {static int extensions_menu_button=1,menu_button_wrapper=2;}}
 static class Root {View appMenu;View findViewById(int id){return appMenu;}}
 static class Container {
  ListMenuButton button=new ListMenuButton();Root root=new Root();
  Root getRootView(){return root;}
  ListMenuButton findViewById(int id){return button;}
 }
 static class Menu {boolean open,opening;View anchor;boolean isExtensionsMenuOpen(){return open;}
 boolean isExtensionsMenuOpeningOrOpen(){return open||opening;}
 void setMenuAnchorView(View v){anchor=v;}}
 boolean mIsDestroyed,mShowExtensionsMenuPending;
 ViewTreeObserver.OnPreDrawListener mShowMenuPreDrawListener;
 ViewTreeObserver mPendingMenuObserver;
 Container mContainer=new Container();Menu mExtensionsMenuCoordinator=new Menu();
 NativeMenuAnchorTest(){mContainer.button.onClick=()->mExtensionsMenuCoordinator.opening=true;}
 void updateMenuIconVisibility(){}
''' + body + r'''
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[] args){
  NativeMenuAnchorTest c=new NativeMenuAnchorTest();ListMenuButton b=c.mContainer.button;
  c.showExtensionsMenu();b.drainPosts();
  check(b.clicks==0,"must not click before the containing row is shown and measured");
  b.observer.draw();check(b.clicks==0,"hidden row cannot anchor native popup");
  b.shown=true;b.observer.draw();check(b.clicks==0,"zero-size anchor is not ready");
  b.width=48;b.height=48;b.layoutRequested=true;
  b.observer.draw();check(b.clicks==0,"must finish pending anchor layout");
  c.showExtensionsMenu();b.layoutRequested=false;b.observer.draw();
  check(b.clicks==1,"ready native button must be clicked exactly once");
  b.observer.draw();check(b.clicks==1,"listener must be removed after opening");
  c.mExtensionsMenuCoordinator.open=true;c.showExtensionsMenu();b.observer.draw();
  check(b.clicks==1,"already open native popup must not be retriggered");
  NativeMenuAnchorTest compact=new NativeMenuAnchorTest();
  View appButton=new View();appButton.shown=true;appButton.width=48;appButton.height=48;
  compact.mContainer.root.appMenu=appButton;compact.showExtensionsMenu();
  compact.mContainer.button.observer.draw();
  check(compact.mContainer.button.clicks==1,"compact row must use the visible native app-menu anchor");
  check(compact.mExtensionsMenuCoordinator.anchor==appButton,"native RectProvider needs the selected visible anchor");
  NativeMenuAnchorTest ignored=new NativeMenuAnchorTest();ListMenuButton ib=ignored.mContainer.button;
  ib.shown=true;ib.width=48;ib.height=48;ib.onClick=()->{};
  ignored.showExtensionsMenu();ib.layoutRequested=false;ib.observer.draw();
  check(ib.clicks==1,"first native click was delivered");
  check(!ignored.mShowExtensionsMenuPending,"ignored click must release pending programmatic request");
  ib.onClick=()->ignored.mExtensionsMenuCoordinator.opening=true;
  ignored.showExtensionsMenu();ib.layoutRequested=false;ib.observer.draw();
  check(ib.clicks==2&&ignored.mShowExtensionsMenuPending,"later request must reach native initialization");
  NativeMenuAnchorTest destroyed=new NativeMenuAnchorTest();destroyed.mIsDestroyed=true;
  destroyed.showExtensionsMenu();destroyed.mContainer.button.observer.draw();
  check(destroyed.mContainer.button.clicks==0,"destroyed native owner must ignore requests");
 }
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'NativeMenuAnchorTest.java'
            path.write_text(harness)
            subprocess.run(['javac',str(path)],check=True,capture_output=True)
            result = subprocess.run(['java','-ea','-cp',tmp,'NativeMenuAnchorTest'],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)

    def test_native_rect_provider_resets_anchor_on_dismiss(self):
        source = SOURCE.with_name('ExtensionsMenuCoordinator.java').read_text()
        bodies = '\n'.join(method(source, signature) for signature in [
            'public RectProvider getRectProvider(',
            'void setMenuAnchorView(',
            'public void onPopupMenuDismissed()',
            'boolean isExtensionsMenuOpeningOrOpen()',
        ])
        harness = r'''
import java.util.*;
public class NativeAnchorOwnerTest {
 @interface Nullable {}
 static class View {}
 static class RectProvider {View view;RectProvider(View v){view=v;}}
 static class MenuBuilderHelper {static RectProvider getRectProvider(View v){return new RectProvider(v);}}
 static class TimeUtils {static long elapsedRealtimeMillis(){return 123;}}
 static class Delegate {void requestLayoutWithViewUtils(){}}
 View mExtensionsMenuButton=new View(),mMenuAnchorView;
 boolean mIsMenuOpen=true;Object mMediator;long mLastDismissalTimeMs;
 Delegate mMenuButtonPinningDelegate=new Delegate();List<Object> mExtensionModels=new ArrayList<>();
 void destroyMediator(){mMediator=null;}
''' + bodies + r'''
 public static void main(String[] args){
  NativeAnchorOwnerTest c=new NativeAnchorOwnerTest();View fallback=new View();
  assert c.getRectProvider(null).view==c.mExtensionsMenuButton;
  assert c.isExtensionsMenuOpeningOrOpen();c.mIsMenuOpen=false;
  assert !c.isExtensionsMenuOpeningOrOpen();c.mMediator=new Object();
  assert c.isExtensionsMenuOpeningOrOpen();
  c.setMenuAnchorView(fallback);assert c.getRectProvider(null).view==fallback;
  c.onPopupMenuDismissed();assert !c.mIsMenuOpen;
  assert !c.isExtensionsMenuOpeningOrOpen();
  assert c.getRectProvider(null).view==c.mExtensionsMenuButton;
 }
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'NativeAnchorOwnerTest.java'
            path.write_text(harness)
            subprocess.run(['javac',str(path)],check=True,capture_output=True)
            result = subprocess.run(['java','-ea','-cp',tmp,'NativeAnchorOwnerTest'],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)

if __name__ == '__main__':
    unittest.main()
