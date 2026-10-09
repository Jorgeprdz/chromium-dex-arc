"""Execute the shipped native bookmark projection against bounded native/Android doubles.

These JVM probes establish adapter commands and lifetime, not Android rendering or JNI acceptance.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body, window_core_jar

ARC = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
BRIDGE = ARC / 'ArcNativeBookmarksBridge.java'
COLLECTIONS = ARC / 'ArcCollectionsView.java'

STUBS = {
    'android/app/Activity.java': 'package android.app; public class Activity {}',
    'android/view/View.java': 'package android.view; public class View {}',
    'android/view/MenuItem.java': '''package android.view; public class MenuItem {
        public final int title; private boolean enabled=true; public MenuItem(int t){title=t;}
        public MenuItem setEnabled(boolean value){enabled=value;return this;}
        public boolean isEnabled(){return enabled;} public int getItemId(){return title;}}
    ''',
    'android/view/Menu.java': '''package android.view; public class Menu {
        public final java.util.List<MenuItem> items=new java.util.ArrayList<>();
        public MenuItem add(int group,int id,int order,int title){MenuItem i=new MenuItem(title);items.add(i);return i;}}
    ''',
    'android/widget/PopupMenu.java': '''package android.widget; public class PopupMenu {
        public interface OnMenuItemClickListener {boolean onMenuItemClick(android.view.MenuItem item);}
        public static PopupMenu latest; public boolean dismissed; private final android.view.Menu menu=new android.view.Menu();
        private OnMenuItemClickListener listener;
        public PopupMenu(android.app.Activity a,android.view.View v){latest=this;}
        public android.view.Menu getMenu(){return menu;} public void show(){} public void dismiss(){dismissed=true;}
        public void setOnMenuItemClickListener(OnMenuItemClickListener l){listener=l;}
        public void click(int title){for(var i:menu.items)if(i.title==title&&i.isEnabled()){listener.onMenuItemClick(i);return;}
            throw new AssertionError("missing/enabled menu title "+title);}}
    ''',
    'org/chromium/url/GURL.java': '''package org.chromium.url; public class GURL {
        private final String url; public GURL(String s){url=s;} public String getSpec(){return url;}}
    ''',
    'org/chromium/components/bookmarks/BookmarkId.java': '''package org.chromium.components.bookmarks;
        public record BookmarkId(long id){public long getId(){return id;} public int getType(){return 0;}}
    ''',
    'org/chromium/components/bookmarks/BookmarkItem.java': '''package org.chromium.components.bookmarks;
        public record BookmarkItem(BookmarkId id,String title,org.chromium.url.GURL url,boolean folder,BookmarkId parentId,boolean editable) {
            public BookmarkId getId(){return id;} public String getTitle(){return title;} public org.chromium.url.GURL getUrl(){return url;}
            public boolean isFolder(){return folder;} public BookmarkId getParentId(){return parentId;}
            public boolean isEditable(){return editable;}}
    ''',
    'org/chromium/chrome/browser/profiles/Profile.java': '''package org.chromium.chrome.browser.profiles;
        public class Profile {public boolean privateMode,shutdown; public org.chromium.chrome.browser.bookmarks.BookmarkModel model;
        public boolean isOffTheRecord(){return privateMode;} public boolean shutdownStarted(){return shutdown;}}
    ''',
    'org/chromium/chrome/browser/tab/Tab.java': 'package org.chromium.chrome.browser.tab; public class Tab {}',
    'org/chromium/chrome/browser/tab/TabLaunchType.java': '''package org.chromium.chrome.browser.tab;
        public class TabLaunchType {public static final int FROM_BOOKMARK_BAR_BACKGROUND=91;}
    ''',
    'org/chromium/chrome/browser/bookmarks/BookmarkModelObserver.java': '''package org.chromium.chrome.browser.bookmarks;
        public abstract class BookmarkModelObserver {public abstract void bookmarkModelChanged();
        public void bookmarkModelLoaded(){bookmarkModelChanged();}}
    ''',
    'org/chromium/chrome/browser/bookmarks/BookmarkModel.java': '''package org.chromium.chrome.browser.bookmarks;
        public class BookmarkModel {
            public boolean loaded; public int loadRequests; public final java.util.List<BookmarkModelObserver> observers=new java.util.ArrayList<>();
            public final java.util.Map<org.chromium.components.bookmarks.BookmarkId,org.chromium.components.bookmarks.BookmarkItem> nodes=new java.util.HashMap<>();
            public final java.util.List<org.chromium.components.bookmarks.BookmarkId> account=new java.util.ArrayList<>(),local=new java.util.ArrayList<>();
            public static BookmarkModel getForProfile(org.chromium.chrome.browser.profiles.Profile p){return p.model;}
            public void addObserver(BookmarkModelObserver o){observers.add(o);} public void removeObserver(BookmarkModelObserver o){observers.remove(o);}
            public boolean isBookmarkModelLoaded(){return loaded;}
            public boolean finishLoadingBookmarkModel(Runnable r){loadRequests++; if(loaded)r.run();return loaded;}
            public org.chromium.components.bookmarks.BookmarkItem getBookmarkById(org.chromium.components.bookmarks.BookmarkId id){return nodes.get(id);}
            public void changed(){for(var o:java.util.List.copyOf(observers))o.bookmarkModelChanged();}
            public void finish(){loaded=true;for(var o:java.util.List.copyOf(observers))o.bookmarkModelLoaded();}}
    ''',
    'org/chromium/chrome/browser/bookmarks/BookmarkUtils.java': '''package org.chromium.chrome.browser.bookmarks;
        public class BookmarkUtils {public static java.util.List<org.chromium.components.bookmarks.BookmarkId> getDesktopBookmarkIds(BookmarkModel m){
            if(!m.loaded)throw new AssertionError("queried unloaded model"); var ids=new java.util.ArrayList<>(m.account);ids.addAll(m.local);return ids;}}
    ''',
    'org/chromium/chrome/browser/bookmarks/BookmarkOpener.java': '''package org.chromium.chrome.browser.bookmarks;
        import org.chromium.components.bookmarks.BookmarkId; public interface BookmarkOpener {
            boolean openBookmarkInCurrentTab(BookmarkId id,boolean incognito);
            boolean openBookmarksInNewTabs(java.util.List<BookmarkId> ids,boolean incognito,Integer launchType);
            boolean openBookmarksInNewWindow(java.util.List<BookmarkId> ids,boolean incognito);
            boolean isOpenInNewWindowSupported();}
    ''',
    'org/chromium/chrome/browser/bookmarks/BookmarkManagerOpener.java': '''package org.chromium.chrome.browser.bookmarks;
        public interface BookmarkManagerOpener {
            void showBookmarkManager(android.app.Activity a,org.chromium.chrome.browser.tab.Tab t,org.chromium.chrome.browser.profiles.Profile p,org.chromium.components.bookmarks.BookmarkId folder);
            void startEditActivity(android.app.Activity a,org.chromium.chrome.browser.profiles.Profile p,org.chromium.components.bookmarks.BookmarkId id);
            void startFolderPickerActivity(android.app.Activity a,org.chromium.chrome.browser.profiles.Profile p,org.chromium.components.bookmarks.BookmarkId... ids);}
    ''',
    'org/chromium/chrome/browser/bookmarks/R.java': '''package org.chromium.chrome.browser.bookmarks;
        public class R {public static class string {public static final int contextmenu_open_in_new_tab=1,
            contextmenu_open_in_new_window=2,contextmenu_edit_bookmark_ellipsis=3,bookmark_item_move=4,
            contextmenu_open_bookmarks_manager=5;}}
    ''',
}

HARNESS = r'''
import android.app.Activity;import android.view.View;import android.widget.PopupMenu;
import java.util.*;import java.util.concurrent.atomic.AtomicBoolean;
import org.chromium.chrome.browser.arc.ArcNativeBookmarksBridge;
import org.chromium.chrome.browser.bookmarks.*;import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.tab.*;import org.chromium.components.bookmarks.*;import org.chromium.url.GURL;
public class NativeBookmarksProbe {
    static void check(boolean value,String reason){if(!value)throw new AssertionError(reason);}
    static BookmarkItem item(long id,String title,boolean folder,boolean editable){
        return new BookmarkItem(new BookmarkId(id),title,new GURL("https://site"+id+".test/"),folder,new BookmarkId(100),editable);}
    static class Commands implements BookmarkOpener,BookmarkManagerOpener {
        final List<String> calls=new ArrayList<>();BookmarkId target;Profile profile;boolean incognito;Integer launch;
        void call(String name,BookmarkId id,boolean privateMode){calls.add(name);target=id;incognito=privateMode;}
        public boolean openBookmarkInCurrentTab(BookmarkId id,boolean p){call("current",id,p);return true;}
        public boolean openBookmarksInNewTabs(List<BookmarkId> ids,boolean p,Integer type){call("new",ids.get(0),p);launch=type;return true;}
        public boolean openBookmarksInNewWindow(List<BookmarkId> ids,boolean p){call("window",ids.get(0),p);return true;}
        public boolean isOpenInNewWindowSupported(){return true;}
        public void showBookmarkManager(Activity a,Tab t,Profile p,BookmarkId folder){profile=p;call("manager",folder,p.privateMode);}
        public void startEditActivity(Activity a,Profile p,BookmarkId id){profile=p;call("edit",id,p.privateMode);}
        public void startFolderPickerActivity(Activity a,Profile p,BookmarkId... ids){profile=p;call("move",ids[0],p.privateMode);}
    }
    public static void main(String[]args){
        Profile profile=new Profile(); BookmarkModel model=new BookmarkModel();profile.model=model;
        AtomicBoolean current=new AtomicBoolean(true);Commands commands=new Commands();List<List<BookmarkItem>> updates=new ArrayList<>();
        BookmarkItem local=item(1,"Local",false,true),account=item(2,"Account",false,true),folder=item(3,"Folder",true,true),managed=item(4,"Managed",false,false);
        model.nodes.put(local.getId(),local);model.nodes.put(account.getId(),account);model.nodes.put(folder.getId(),folder);model.nodes.put(managed.getId(),managed);
        model.account.add(account.getId());model.local.add(local.getId());model.local.add(folder.getId());
        ArcNativeBookmarksBridge bridge=new ArcNativeBookmarksBridge(new Activity(),profile,current::get,commands,()->commands,Tab::new,updates::add);
        check(bridge.items().isEmpty(),"unloaded native bookmarks reserve no tiles");check(model.loadRequests==1,"kick native partner loading once");
        model.finish();check(bridge.items().equals(List.of(account,local,folder)),"account and local native order preserved, including folders");
        if(args[0].equals("projection")){
            BookmarkItem renamed=item(1,"Renamed",false,true);model.nodes.put(local.getId(),renamed);model.changed();
            check(bridge.items().get(1).getTitle().equals("Renamed"),"observer refreshes bookmark edits and URLs");
            model.account.clear();model.changed();check(bridge.items().equals(List.of(renamed,folder)),"account folder removal drops obsolete tiles");
            model.local.clear();model.changed();check(bridge.items().isEmpty(),"empty native bar clears tiles");
        }else if(args[0].equals("commands")){
            bridge.open(local);check(commands.calls.equals(List.of("current"))&&commands.target.equals(local.getId())&&!commands.incognito,"native id opens current regular tab");
            profile.privateMode=true;bridge.open(account);check(commands.incognito&&commands.target.equals(account.getId()),"shared regular bookmarks remain usable in incognito via private native opener");
            bridge.open(folder);check(commands.calls.get(2).equals("manager")&&commands.target.equals(folder.getId())&&commands.profile==profile,"folder opens bounded native manager");
            model.nodes.remove(local.getId());int count=commands.calls.size();bridge.open(local);check(commands.calls.size()==count,"removed stale bookmark can't open URL snapshot");
        }else if(args[0].equals("menu")){
            bridge.showMenu(new View(),local);PopupMenu menu=PopupMenu.latest;menu.click(R.string.contextmenu_open_in_new_tab);
            check(commands.launch==TabLaunchType.FROM_BOOKMARK_BAR_BACKGROUND&&commands.target.equals(local.getId()),"menu preserves native new-tab launch type and identity");
            profile.privateMode=true;menu.click(R.string.contextmenu_open_in_new_window);
            check(!commands.incognito&&commands.calls.get(1).equals("window"),"native New window keeps regular window semantics from incognito");
            profile.privateMode=false;menu.click(R.string.contextmenu_edit_bookmark_ellipsis);check(commands.calls.get(2).equals("edit")&&commands.profile==profile,"native edit activity uses same profile");
            menu.click(R.string.bookmark_item_move);check(commands.calls.get(3).equals("move")&&commands.target.equals(local.getId()),"native folder picker retains real move operation");
            menu.click(R.string.contextmenu_open_bookmarks_manager);check(commands.target.equals(local.getParentId()),"management retains real bookmark parent");
            bridge.showMenu(new View(),managed);for(var i:PopupMenu.latest.getMenu().items)if(i.title==R.string.contextmenu_edit_bookmark_ellipsis||i.title==R.string.bookmark_item_move)check(!i.isEnabled(),"managed/noneditable bookmarks cannot be modified");
            current.set(false);int count=commands.calls.size();menu.click(R.string.contextmenu_open_in_new_tab);check(commands.calls.size()==count,"stale native menu cannot issue commands");
        }else if(args[0].equals("lifecycle")){
            int changes=updates.size();current.set(false);model.changed();check(updates.size()==changes&&bridge.items().isEmpty(),"stale profile/session neither publishes nor returns bookmark snapshots");
            current.set(true);profile.shutdown=true;bridge.open(local);check(commands.calls.isEmpty(),"shutdown profile cannot navigate");profile.shutdown=false;
            bridge.showMenu(new View(),local);PopupMenu menu=PopupMenu.latest;bridge.destroy();bridge.destroy();
            check(model.observers.isEmpty()&&menu.dismissed,"destroy detaches owned observer and popup idempotently");
            model.changed();bridge.open(local);check(commands.calls.isEmpty()&&updates.size()==changes,"destroyed bridge ignores queued callbacks and commands");
            model.loaded=false;ArcNativeBookmarksBridge pending=new ArcNativeBookmarksBridge(new Activity(),profile,()->true,commands,()->commands,Tab::new,updates::add);
            pending.destroy();changes=updates.size();model.finish();check(updates.size()==changes&&pending.items().isEmpty(),"loading completion after destroy cannot republish native favorites");
            profile.model=null;ArcNativeBookmarksBridge unavailable=new ArcNativeBookmarksBridge(new Activity(),profile,()->true,commands,()->null,()->null,updates::add);
            check(unavailable.items().isEmpty(),"temporarily unavailable native model is empty");unavailable.destroy();
        }else throw new AssertionError(args[0]);
        bridge.destroy();
    }
}
'''


class NativeBookmarkBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='arc-native-bookmarks-')
        cls.tmp = Path(cls.work.name)
        for name, source in STUBS.items():
            path = cls.tmp / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source)
        (cls.tmp / 'NativeBookmarksProbe.java').write_text(HARNESS)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def run_probe(self, scenario):
        self.assertTrue(BRIDGE.exists(), 'Arc native bookmark model projection is missing')
        compiled = self.tmp / 'NativeBookmarksProbe.class'
        if not compiled.exists():
            result = subprocess.run(['javac', '--release', '17', '-d', str(self.tmp),
                                     str(BRIDGE), *map(str, self.tmp.rglob('*.java'))], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(['java', '-ea', '-cp', str(self.tmp), 'NativeBookmarksProbe', scenario], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_account_local_projection_observes_changes(self):
        self.run_probe('projection')

    def test_native_commands_private_mode_and_removed_items(self):
        self.run_probe('commands')

    def test_native_menu_routes_edit_move_and_background_new_tab(self):
        self.run_probe('menu')

    def test_loading_stale_session_null_model_and_destroy(self):
        self.run_probe('lifecycle')


    def test_real_favorite_layout_wraps_and_mirrors_columns(self):
        source = ARC / 'ArcFavoriteTiles.java'
        self.assertTrue(source.exists(), 'Three-column wrapping native favorite layout is missing')
        program = r'''
class Context {}
class View {
    static final int GONE=8,LAYOUT_DIRECTION_RTL=1;int visibility,w,h,l,t,r,b;Object params;
    int getVisibility(){return visibility;}int getMeasuredWidth(){return w;}int getMeasuredHeight(){return h;}
    Object getLayoutParams(){return params;}void layout(int l,int t,int r,int b){this.l=l;this.t=t;this.r=r;this.b=b;}
    static class MeasureSpec {static final int UNSPECIFIED=0;static int getSize(int n){return n;}static int makeMeasureSpec(int n,int mode){return n;}}
}
class LinearLayout extends View {
    static class LayoutParams {int width,height,topMargin,bottomMargin,start,end;int getMarginStart(){return start;}int getMarginEnd(){return end;}}
    java.util.List<View> children=new java.util.ArrayList<>();int measuredWidth,measuredHeight,direction;LinearLayout(Context c){}
    int getChildCount(){return children.size();}View getChildAt(int i){return children.get(i);}
    int getPaddingLeft(){return 0;}int getPaddingRight(){return 0;}int getPaddingTop(){return 0;}int getPaddingBottom(){return 0;}
    int getLayoutDirection(){return direction;}int getSuggestedMinimumWidth(){return 0;}int getSuggestedMinimumHeight(){return 0;}
    static int resolveSizeAndState(int desired,int spec,int state){return desired;}
    void measureChildWithMargins(View child,int ws,int wu,int hs,int hu){LayoutParams p=(LayoutParams)child.params;child.w=p.width;child.h=p.height;}
    void setMeasuredDimension(int width,int height){measuredWidth=width;measuredHeight=height;}
    protected void onMeasure(int w,int h){}protected void onLayout(boolean c,int l,int t,int r,int b){}
}
SOURCE
class FavoriteWrappingProbe {
    static void check(boolean b,String reason){if(!b)throw new AssertionError(reason);}
    public static void main(String[]args){ArcFavoriteTiles tiles=new ArcFavoriteTiles(new Context());
        int[] widths={99,100,100,99,100,100,99};int[] gaps={9,8,0,9,8,0,0};
        for(int i=0;i<7;i++){View child=new View();LinearLayout.LayoutParams p=new LinearLayout.LayoutParams();
            p.width=widths[i];p.height=57;p.end=gaps[i];p.bottomMargin=i<6?8:0;child.params=p;tiles.children.add(child);}
        tiles.onMeasure(316,0);check(tiles.measuredHeight==187,"actual layout measures all three rows");
        tiles.onLayout(true,0,0,316,187);View third=tiles.children.get(2),fourth=tiles.children.get(3);
        check(third.l==216&&third.r==316&&third.t==0,"third tile ends at sidebar boundary");
        check(fourth.l==0&&fourth.t==65&&fourth.b==122,"fourth tile wraps beneath first with section spacing");
        tiles.direction=View.LAYOUT_DIRECTION_RTL;tiles.onLayout(true,0,0,316,187);
        check(tiles.children.get(0).l==217&&third.l==0&&fourth.l==217,"RTL mirrors logical columns on every row");
    }
}
'''
        raw = re.sub(r'^package .*?;\n|^import .*?;\n', '', source.read_text(), flags=re.M)
        raw = raw.replace('public final class ArcFavoriteTiles', 'final class ArcFavoriteTiles')
        with tempfile.TemporaryDirectory(prefix='arc-native-wrap-') as tmp:
            path = Path(tmp) / 'FavoriteWrappingProbe.java'; path.write_text(program.replace('SOURCE', raw))
            result = subprocess.run(['javac', '--release', '17', '-d', tmp, str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(['java', '-ea', '-cp', tmp, 'FavoriteWrappingProbe'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_seven_favorites_use_three_rows_of_reference_tiles(self):
        body = method_body(COLLECTIONS.read_text(), re.escape('public void applyGeometry(ArcDesktopPolicy.Geometry geometry, int availableWidthPx)'))
        program = r'''
import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
class BookmarkTileRows {
    static class LayoutParams {int width,height,bottomMargin,end;int getMarginEnd(){return end;}void setMarginEnd(int n){end=n;}}
    static class View {static final int VISIBLE=0,GONE=8;LayoutParams p=new LayoutParams();int visibility;
        LayoutParams getLayoutParams(){return p;}void setLayoutParams(LayoutParams n){p=n;}void setVisibility(int n){visibility=n;}}
    static class Row extends View {java.util.List<View> children=new java.util.ArrayList<>();int getChildCount(){return children.size();}View getChildAt(int i){return children.get(i);}}
    Row mFavorites=new Row();View mFavoritesScroll=new View(),mSpace=new View();ArcDesktopPolicy.Geometry mGeometry;void setPadding(int l,int t,int r,int b){}
    public void applyGeometry(ArcDesktopPolicy.Geometry geometry,int availableWidthPx) BODY
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    public static void main(String[]args){BookmarkTileRows layout=new BookmarkTileRows();var g=ArcDesktopPolicy.geometry(1382,863,334,1,false);
        for(int i=0;i<7;i++)layout.mFavorites.children.add(new View());layout.applyGeometry(g,316);
        check(layout.mFavoritesScroll.p.height==187,"seven native favorites must wrap into three 57px rows with 8px spacing");
        check(layout.mFavorites.children.get(2).p.getMarginEnd()==0,"third column ends the row without horizontal overflow");
        check(layout.mFavorites.children.get(3).p.width==99,"next row starts first reference column");
        for(int i=0;i<30;i++)layout.mFavorites.children.add(new View());layout.applyGeometry(g,316);
        check(layout.mFavoritesScroll.p.height==187,"large bookmark bars keep a three-row viewport and scroll remaining favorites");
        check(layout.mFavorites.children.get(36).p.width==99,"large bookmark bar retains every real favorite");
        layout.mFavorites.children.clear();layout.applyGeometry(g,316);check(layout.mFavoritesScroll.visibility==View.GONE,"zero native favorites leave no empty row");
    }
}
'''.replace('BODY', body)
        with tempfile.TemporaryDirectory(prefix='arc-native-tile-rows-') as tmp:
            path = Path(tmp) / 'BookmarkTileRows.java'; path.write_text(program)
            cp = str(window_core_jar())
            sources = list((ROOT / 'chromium').rglob('ArcDesktopPolicy.java')) + list((ROOT / 'chromium').rglob('ArchiumWindowClass.java'))
            result = subprocess.run(['javac', '--release', '17', '-cp', cp, '-d', tmp, *map(str, sources), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(['java', '-ea', '-cp', tmp + ':' + cp, 'BookmarkTileRows'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
