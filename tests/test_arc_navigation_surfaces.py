"""Execute root visibility/search routing against pinned native surface methods.

Bounded JVM doubles cover observer dispatch, flags and surface ownership. They do not
establish Android rendering, Samsung window focus, or JNI bookmark-model acceptance.
"""
from pathlib import Path
import hashlib
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body

FIXTURES = ROOT / 'tests/fixtures/arc-caption'
COORD = ROOT / '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java'
RAIL = ROOT / '.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListCoordinator.java'


def method(source, signature):
    return re.sub(r'@(Nullable|BookmarkBarVisibilityState|TabSearchEntryPoint)\s+', '', signature + ' ' + method_body(source, re.escape(signature)))


def optional_method(source, signature):
    return method(source, signature) if signature in source else ''


BOOKMARKS = r'''
import java.util.*;
class View {static final int VISIBLE=0,INVISIBLE=4;}
class TopControlVisibility {static final int VISIBLE=0,HIDDEN=1;}
class ChromeFeatureList {static final int BOOKMARKS_BAR_NTP=1;static boolean triState;static boolean isEnabled(int feature){return triState;}}
class BookmarkBarVisibilityState {static final int ALWAYS_HIDE=0,ALWAYS_SHOW=1,ONLY_SHOW_ON_NTP=2;}
class Profile {boolean enabled=true,onNtp;int state=1;List<String> nativeBookmarks=List.of("https://account.test/","https://local.test/");int writes;}
class Supplier<T> {T value;Supplier(T v){value=v;}T get(){return value;}}
class R {static class dimen {static final int bookmark_bar_item_min_width=1,bookmark_bar_item_max_width=2;}}
class Configuration {}
class Activity {Resources resources=new Resources();Resources getResources(){return resources;}static class Resources{int getDimensionPixelSize(int id){return id==1?90:240;}}}
class BookmarkBarUtils {
    static boolean isBookmarkBarVisible(Activity a,Profile p,boolean xr){return p.enabled&&!xr;}
    static int getBookmarkBarVisibilityState(Activity a,Profile p,boolean xr){return xr?0:p.state;}
    static boolean isBookmarkBarVisibleForState(Activity a,Profile p,boolean xr,Object tab){return !xr&&(p.state==1||(p.state==2&&p.onNtp));}
}
class ObserverList<T> implements Iterable<T> {List<T> values=new ArrayList<>();void addObserver(T o){values.add(o);}void removeObserver(T o){values.remove(o);}public Iterator<T> iterator(){return List.copyOf(values).iterator();}}
class NativeProvider {
    OBSERVER_INTERFACE
    Activity mActivity=new Activity();Supplier<Profile> mProfileSupplier;Supplier<Boolean> mXrSpaceModeObservableSupplier=new Supplier<>(false);
    ObserverList<BookmarkBarVisibilityObserver> mObservers=new ObserverList<>();NativeProvider(Profile p){mProfileSupplier=new Supplier<>(p);}
    void emit(){notifyVisibilityChange();}void configuration(Configuration c){processConfigurationChange(c);}
    PROVIDER_METHODS
}
class NativeBookmarks implements NativeProvider.BookmarkBarVisibilityObserver {
    static final int VISIBLE=View.VISIBLE,INVISIBLE=View.INVISIBLE;
    boolean mShouldBookmarkBarBeShown=true,mIsInFullscreenMode;int mContentHeight=52,mHairlineHeight=1;
    static class Visibility {boolean visible;void setVisibility(boolean v){visible=v;}}
    static class Mediator extends Visibility {int dismissals;void dismissPopupMenu(){dismissals++;}}
    static class Constraints {int min,max;void setItemWidthConstraints(int a,int b){min=a;max=b;}}
    static class Stacker {int updates;void requestLayerUpdateSync(boolean animate){updates++;}}
    static class Controls {int getAndroidControlsVisibility(){return View.VISIBLE;}float getBrowserControlHiddenRatio(){return 0;}int getTopControlOffset(){return 0;}}
    final Visibility mBookmarkBarSceneLayer=new Visibility();final Mediator mMediator=new Mediator();
    final Constraints mBookmarkBarItemsLayoutManager=new Constraints();final Stacker mTopControlsStacker=new Stacker();
    final Controls mBrowserControlsStateProvider=new Controls();boolean registered=true;
    void unregisterResource(){registered=false;}void registerResource(){registered=true;}void handleBookmarkBarChange(){}
    NATIVE_METHODS
}
class BookmarkNavigationProbe {
    Activity mActivity=new Activity();Profile profile=new Profile();Supplier<Profile> mProfileSupplier=new Supplier<>(profile);
    Supplier<Boolean> mXrSpaceModeObservableSupplier=new Supplier<>(false);Supplier<Object> mActivityTabProvider=new Supplier<>(new Object());
    NativeProvider mBookmarkBarVisibilityProvider=new NativeProvider(profile);NativeBookmarks mBookmarkBarCoordinator;
    boolean mArcToolbarSuppressed;int controlHeightUpdates;
    BookmarkNavigationProbe(){mBookmarkBarVisibilityProvider.addObserver(new NativeProvider.BookmarkBarVisibilityObserver(){ROOT_OBSERVER});}
    void createBookmarkBarIfNecessary(){if(mBookmarkBarCoordinator==null){mBookmarkBarCoordinator=new NativeBookmarks();COORDINATOR_REGISTRATION}
        else mBookmarkBarCoordinator.setVisibility(true);}
    void updateTopControlsHeight(boolean animate){controlHeightUpdates++;}
    ROOT_METHODS
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    static void hidden(BookmarkNavigationProbe p,String message){check(p.mBookmarkBarCoordinator==null||(!p.mBookmarkBarCoordinator.mShouldBookmarkBarBeShown
        &&p.mBookmarkBarCoordinator.getTopControlHeight()==0&&!p.mBookmarkBarCoordinator.mBookmarkBarSceneLayer.visible
        &&!p.mBookmarkBarCoordinator.mMediator.visible),message);}
    static void shown(BookmarkNavigationProbe p,String message){check(p.mBookmarkBarCoordinator!=null&&p.mBookmarkBarCoordinator.mShouldBookmarkBarBeShown
        &&p.mBookmarkBarCoordinator.getTopControlHeight()==53&&p.mBookmarkBarCoordinator.mBookmarkBarSceneLayer.visible
        &&p.mBookmarkBarCoordinator.mMediator.visible,message);}
    public static void main(String[]args){BookmarkNavigationProbe p=new BookmarkNavigationProbe();
        p.updateBookmarkBarVisibility();p.mBookmarkBarCoordinator.setVisibility(true);shown(p,"native preferred bookmark bar initially visible");
        List<String> original=p.profile.nativeBookmarks;
        if(args[0].equals("provider")){
            p.mArcToolbarSuppressed=true;p.updateBookmarkBarVisibility();hidden(p,"ARC replaces horizontal bookmarks with native sidebar tiles");
            p.mBookmarkBarVisibilityProvider.emit();hidden(p,"visible preference emissions cannot re-show ARC horizontal bar");
            check(!p.getBookmarkBarVisibility(),"ARC visibility consumers see no horizontal bar");
            p.mBookmarkBarVisibilityProvider.configuration(new Configuration());
            check(p.mBookmarkBarCoordinator.mBookmarkBarItemsLayoutManager.min==90&&p.mBookmarkBarCoordinator.mBookmarkBarItemsLayoutManager.max==240
                &&p.mBookmarkBarCoordinator.mMediator.dismissals==1,"native coordinator retains width constraints observer while ARC owns visibility");
            hidden(p,"configuration callback cannot reclaim ARC horizontal bar");
            p.mArcToolbarSuppressed=false;p.updateBookmarkBarVisibility();shown(p,"MOBILE restores unchanged native visible preference");
            p.mArcToolbarSuppressed=true;p.profile.enabled=false;p.mBookmarkBarVisibilityProvider.emit();
            p.mArcToolbarSuppressed=false;p.updateBookmarkBarVisibility();hidden(p,"MOBILE preserves a preference switched off during ARC");
        }else if(args[0].equals("tri")){
            ChromeFeatureList.triState=true;p.profile.state=BookmarkBarVisibilityState.ONLY_SHOW_ON_NTP;p.profile.onNtp=true;
            p.mArcToolbarSuppressed=true;p.mBookmarkBarVisibilityProvider.emit();hidden(p,"NTP tri-state observer respects ARC ownership");
            p.mArcToolbarSuppressed=false;p.updateBookmarkBarVisibility();shown(p,"MOBILE restores ONLY_SHOW_ON_NTP on native NTP");
            p.profile.onNtp=false;p.updateBookmarkBarVisibility();hidden(p,"MOBILE hides native bar away from NTP");
            p.profile.state=BookmarkBarVisibilityState.ALWAYS_SHOW;p.updateBookmarkBarVisibility();shown(p,"MOBILE preserves ALWAYS_SHOW");
            p.mArcToolbarSuppressed=true;p.mBookmarkBarVisibilityProvider.configuration(new Configuration());hidden(p,"tri-state configuration stays hidden in ARC");
        }else throw new AssertionError(args[0]);
        check(p.profile.nativeBookmarks==original&&p.profile.nativeBookmarks.size()==2&&p.profile.writes==0,"composition never alters native bookmark data or preferences");
    }
}
'''


SEARCH = r'''
class Activity {boolean arc;View decor=new View();Window getWindow(){return new Window(decor);}}
class Window {View decor;Window(View d){decor=d;}View getDecorView(){return decor;}}
class View {}class Gravity {static final int START=1,TOP=2;}
class ChromeFeatureList {static Flag sTabSearchForDesktop=new Flag();static class Flag {boolean enabled;boolean isEnabled(){return enabled;}}}
class ArcDesktopAppearance {static boolean isDesktopWindow(Activity activity){return activity.arc;}}
class TabSearchEntryPoint {static final int VERTICAL_TABS=7,NUM_ENTRIES=9;}
class RecordHistogram {static void recordEnumeratedHistogram(String key,int value,int max){}}
class RecordUserAction {static void record(String key){}}
class TabObscuringHandler {static class Target {static final int ALL_TABS_AND_TOOLBAR=1;}}
class IntentOrigin {static final int HUB=2;}class SearchType {static final int TEXT=1;}
class TabSearchOverlayProperties {static final int VISIBLE=1,EMPTY_STATE_VISIBLE=2;}
class NativeSearchOverlay {
    static class Model {boolean visible;boolean get(int key){return visible;}void set(int key,boolean value){if(key==1)visible=value;}}
    static class Popup {boolean showing;View anchor;boolean isShowing(){return showing;}void showAtLocation(View v,int gravity,int x,int y){anchor=v;showing=true;}}
    static class Fusebox {void endFuseboxInput(){}}
    static class Obscurer {static class Target {static final int ALL_TABS_AND_TOOLBAR=1;}Object obscure(int target){return new Object();}}
    static class BooleanSupplier {void set(boolean value){}}
    static class Query {int queries;void beginQuery(int origin,int type,String query,Object window){queries++;}}
    final Activity mActivity;final Model mModel=new Model();final Popup mPopupWindow=new Popup();final Query mSearchUiCoordinator=new Query();
    final Obscurer mTabObscuringHandler=new Obscurer();final BooleanSupplier mBackPressStateSupplier=new BooleanSupplier();Object mWindowAndroid=new Object(),mTabObscuringToken;
    Fusebox mFuseboxControls;boolean mEncounteredEmptyStateThisSession;
    NativeSearchOverlay(Activity a){mActivity=a;}static <T>T assumeNonNull(T t){return t;}
    void ensureInitialized(){}void updatePanelTopMargin(){}void updateExclusionRects(){}
    NATIVE_SHOW
}
class SearchRoot {
    final Activity mActivity;NativeSearchOverlay mTabSearchOverlayCoordinator;
    SearchRoot(Activity a){mActivity=a;}
    ROOT_INIT_HELPER
    ROOT_LAZY_HELPER
    void initialize() INIT_BODY
    ROOT_SHOW
    void openTabSearch(){showTabSearchOverlay(TabSearchEntryPoint.VERTICAL_TABS);}
}
class SearchRail {
    Activity activity;SearchRoot root;int hubSearches;
    interface Delegate {void openTabSearch();void openHubSearch();}
    Delegate verticalTabsActionDelegate=new Delegate(){public void openTabSearch(){root.openTabSearch();}public void openHubSearch(){hubSearches++;}};
    SearchRail(Activity a,SearchRoot r){activity=a;root=r;}
    RAIL_HELPER
    void click() SEARCH_CLICK
}
class SearchNavigationProbe {
    static void check(boolean value,String reason){if(!value)throw new AssertionError(reason);}
    public static void main(String[]args){Activity a=new Activity();a.arc=Boolean.parseBoolean(args[0]);ChromeFeatureList.sTabSearchForDesktop.enabled=Boolean.parseBoolean(args[1]);
        SearchRoot root=new SearchRoot(a);root.initialize();
        if(args.length>2&&args[2].equals("transition"))a.arc=true;
        SearchRail rail=new SearchRail(a,root);rail.click();
        if(a.arc||ChromeFeatureList.sTabSearchForDesktop.enabled){check(root.mTabSearchOverlayCoordinator!=null,"ARC routing must also initialize the native tab search overlay");
            check(rail.hubSearches==0&&root.mTabSearchOverlayCoordinator.mPopupWindow.showing&&root.mTabSearchOverlayCoordinator.mPopupWindow.anchor==a.decor
                &&root.mTabSearchOverlayCoordinator.mSearchUiCoordinator.queries==1,"ARC/desktop feature routes to native same-window DecorView overlay");}
        else check(rail.hubSearches==1&&root.mTabSearchOverlayCoordinator==null,"outside ARC feature-off retains native Hub search behavior");
    }
}
'''


BOOKMARK_WIRING = r'''
import java.util.*;import java.util.function.*;
class Activity {}class Profile {boolean privateMode;boolean isOffTheRecord(){return privateMode;}}
class TabModel {final Profile profile=new Profile();Profile getProfile(){return profile;}}
class Current<T> implements Supplier<T> {T value;Current(T v){value=v;}public T get(){return value;}}
class BookmarkItem {boolean folder;String getUrl(){return "https://native.test/";}boolean isFolder(){return folder;}}
class ImageButton {Object bitmap;void setImageBitmap(Object icon){bitmap=icon;}}
class Trace {static List<String> events=new ArrayList<>();}
class ArcNativeTabSession {boolean destroyed;void destroy(){destroyed=true;Trace.events.add("session");}}
class ArcCollectionsController {boolean destroyed;void destroy(){destroyed=true;Trace.events.add("collections");}}
class ArcNativeBookmarksBridge {
    final Profile profile;final BooleanSupplier current;final Consumer<List<Object>> changed;final Object opener;final Supplier<Object> manager;
    boolean destroyed;
    ArcNativeBookmarksBridge(Activity a,Profile p,BooleanSupplier live,Object open,Supplier<Object> manage,Supplier<Object> tab,Consumer<List<Object>> change){
        profile=p;current=live;opener=open;manager=manage;changed=change;changed.accept(List.of());}
    void emit(){if(!destroyed&&current.getAsBoolean())changed.accept(List.of());}
    void destroy(){destroyed=true;Trace.events.add("bridge");}
}
class ArcCollectionsView {
    boolean destroyed,attached;int refreshes;Object layoutParams;ArcNativeBookmarksBridge bridge;BiConsumer<BookmarkItem,ImageButton> icons;
    Object getLayoutParams(){return layoutParams;}
    void refresh(){refreshes++;}void setNativeBookmarks(ArcNativeBookmarksBridge b,BiConsumer<BookmarkItem,ImageButton> loader){bridge=b;icons=loader;}
    void destroy(){destroyed=true;Trace.events.add("view");}
}
class NativeTabs {Object predicate=new Object();void setTabVisibilityPredicate(Object p){predicate=p;Trace.events.add("unfilter");}}
class Header {void addView(ArcCollectionsView view,int index){if(view.attached)throw new IllegalStateException("view already has parent");
    view.layoutParams=new Object();view.attached=true;Trace.events.add("attach");}
    void removeView(ArcCollectionsView view){view.attached=false;Trace.events.add("remove");}}
class Icons {
    interface Callback {void result(Object icon,int color,boolean fallback,int type);}
    int requests;Callback last;
    void getLargeIconForUrl(String url,int size,Callback callback){if(!url.equals("https://native.test/")||size!=24)throw new AssertionError("incorrect native favicon request");requests++;last=callback;}
}
class BookmarkWiringProbe {
    Activity mActivity=new Activity();TabModel mSessionModel=new TabModel();Current<TabModel> mCurrentModel=new Current<>(mSessionModel);
    ArcNativeTabSession mTabSession=new ArcNativeTabSession();ArcCollectionsController mCollections=new ArcCollectionsController();
    ArcCollectionsView mCollectionsView=new ArcCollectionsView();ArcNativeBookmarksBridge mNativeBookmarks;
    NativeTabs mNativeTabListCoordinator=new NativeTabs();Header mHeader=new Header();Icons mIcons=new Icons();
    Object mBookmarkOpener=new Object();Supplier<Object> mBookmarkManagerOpener=Object::new,mCurrentTab=Object::new;
    boolean mDestroyed,mArcToolbarCompositionActive=true;int geometries;
    int dp(int value){return value;}void applySidebarGeometry(){
        if(mCollectionsView.getLayoutParams()==null)throw new NullPointerException("native load callback runs geometry before collections view has parent LayoutParams");geometries++;}
    void bind(){TabModel model=mSessionModel;ArcNativeTabSession session=mTabSession;BINDING}
    CLEAR
    static void check(boolean value,String reason){if(!value)throw new AssertionError(reason);}
    public static void main(String[]args){BookmarkWiringProbe p=new BookmarkWiringProbe();p.bind();ArcNativeBookmarksBridge old=p.mNativeBookmarks;
        ArcCollectionsView oldView=p.mCollectionsView;
        check(oldView.bridge==old&&old.profile==p.mSessionModel.getProfile()&&old.opener==p.mBookmarkOpener&&old.manager==p.mBookmarkManagerOpener,
            "root binds native commands and the current session profile without replacing bookmarks");
        check(oldView.refreshes==1&&p.geometries==1,"synchronous native loading callback safely refreshes existing active view");
        p.mCurrentModel.value=new TabModel();old.emit();check(oldView.refreshes==1,"stale current-model guard blocks native bookmark callbacks");
        p.mCurrentModel.value=p.mSessionModel;old.emit();check(oldView.refreshes==2,"active native changes refresh the current projection");
        BookmarkItem item=new BookmarkItem();ImageButton inactiveTarget=new ImageButton();oldView.icons.accept(item,inactiveTarget);check(p.mIcons.requests==1,"regular native bookmark icon uses its own URL");
        p.mCurrentModel.value=new TabModel();p.mIcons.last.result(new Object(),0,false,0);
        check(inactiveTarget.bitmap==null,"pending regular favicon cannot repaint after current native model switches");
        p.mCurrentModel.value=p.mSessionModel;ImageButton target=new ImageButton();oldView.icons.accept(item,target);
        Icons.Callback pending=p.mIcons.last;p.clearCollections();
        check(old.destroyed&&oldView.destroyed&&!oldView.attached&&p.mNativeBookmarks==null&&p.mTabSession==null&&p.mSessionModel==null&&p.mNativeTabListCoordinator.predicate==null,
            "root teardown detaches native bookmark projection and restores unfiltered native tabs");
        check(Trace.events.indexOf("bridge")<Trace.events.indexOf("view")&&Trace.events.indexOf("bridge")<Trace.events.indexOf("session"),
            "bridge destroyed before its target view/session");
        old.emit();pending.result(new Object(),0,false,0);
        check(oldView.refreshes==2&&target.bitmap==null,"torn-down bridge and pending icon cannot repaint the detached view");
        BookmarkWiringProbe privateWindow=new BookmarkWiringProbe();privateWindow.mSessionModel.profile.privateMode=true;privateWindow.bind();
        check(privateWindow.mNativeBookmarks.profile.isOffTheRecord(),"private session remains native opener context");
        privateWindow.mCollectionsView.icons.accept(item,new ImageButton());
        check(privateWindow.mIcons.requests==0,"private native bookmarks do not fetch regular-profile icons");
        BookmarkWiringProbe folders=new BookmarkWiringProbe();folders.bind();item.folder=true;folders.mCollectionsView.icons.accept(item,new ImageButton());
        check(folders.mIcons.requests==0,"native folders retain fallback icons without URL fetches");
    }
}
'''


class ArcNavigationSurfaceTest(unittest.TestCase):
    def run_java(self, name, source, *args):
        with tempfile.TemporaryDirectory(prefix='arc-navigation-surfaces-') as tmp:
            path = Path(tmp) / (name + '.java'); path.write_text(source)
            result = subprocess.run(['javac', '--release', '17', '-d', tmp, str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(['java', '-ea', '-cp', tmp, name, *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def bookmark_program(self):
        provider = (FIXTURES / 'BookmarkBarVisibilityProvider.java').read_text()
        native = (FIXTURES / 'BookmarkBarCoordinator.java').read_text()
        root = COORD.read_text()
        interface = 'public interface BookmarkBarVisibilityObserver ' + method_body(provider, r'public interface BookmarkBarVisibilityObserver')
        interface = re.sub(r'@BookmarkBarVisibilityState\s+', '', interface)
        provider_methods = '\n'.join(method(provider, signature) for signature in [
            'public void addObserver(BookmarkBarVisibilityObserver observer)',
            'private void notifyVisibilityChange()',
            'private void processConfigurationChange(Configuration configuration)'])
        native_methods = '\n'.join(method(native, signature) for signature in [
            'public void setVisibility(boolean isVisible)', 'public int getTopControlHeight()',
            'private void updateSceneLayerVisibility()', 'private void updateAndroidWidgetVisibility()',
            'public void onItemWidthConstraintsChanged(int minWidth, int maxWidth)'])
        root_methods = '\n'.join(method(root, signature) for signature in [
            'private void updateBookmarkBarIfNecessary(boolean visible)',
            'private void updateBookmarkBarVisibility()', 'public boolean getBookmarkBarVisibility()'])
        root_methods += optional_method(root, 'private boolean shouldShowHorizontalBookmarkBar(boolean requestedVisible)')
        observer_start = root.index('mBookmarkBarVisibilityObserver =')
        observer = root[observer_start:root.index('mBookmarkBarVisibilityProvider.addObserver(mBookmarkBarVisibilityObserver)', observer_start)]
        root_observer = '\n'.join(method(observer, signature) for signature in [
            'public void onVisibilityChanged(boolean visibility)',
            'public void onVisibilityChanged_TriState(\n                                @BookmarkBarVisibilityState int visibilityState)'])
        create = method_body(root, re.escape('private void createBookmarkBarIfNecessary()'))
        registration = ''
        needle = 'if (mBookmarkBarVisibilityProvider != null)'
        if needle in create:
            registration = needle + ' ' + method_body(create, re.escape(needle))
        replacements = {'OBSERVER_INTERFACE': interface, 'PROVIDER_METHODS': provider_methods,
                        'NATIVE_METHODS': native_methods, 'ROOT_OBSERVER': root_observer,
                        'ROOT_METHODS': root_methods, 'COORDINATOR_REGISTRATION': registration}
        source = BOOKMARKS
        for key, value in replacements.items(): source = source.replace(key, value)
        return source

    def search_program(self):
        root = COORD.read_text(); rail = RAIL.read_text()
        block = method_body(root, re.escape('private void initializeSideUi(Profile currentlySelectedProfile)'))
        lazy_signature = 'private void initializeTabSearchOverlayIfNecessary()'
        lazy = optional_method(root, lazy_signature)
        if lazy:
            constructor = 'new TabSearchOverlayCoordinator('
            first = lazy.index(constructor); cursor = first + len(constructor); depth = 1
            while depth:
                depth += (lazy[cursor] == '(') - (lazy[cursor] == ')'); cursor += 1
            # Double only the native constructor boundary; retain the production initialization guard.
            lazy = lazy[:first] + 'new NativeSearchOverlay(mActivity)' + lazy[cursor:]
            init_body = '{initializeTabSearchOverlayIfNecessary();}'
        else:
            end = block.index('mTabSearchOverlayCoordinator =')
            candidates = list(re.finditer(r'if\s*\([^{};]*\)\s*\{', block[:end]))
            self.assertTrue(candidates, 'native overlay initialization condition unavailable')
            condition = candidates[-1].group(0)[:-1].strip()
            init_body = '{' + condition + ' {mTabSearchOverlayCoordinator=new NativeSearchOverlay(mActivity);}}'
        search_start = rail.index('VerticalTabListProperties.ON_SEARCH_CLICK_LISTENER')
        click = method_body(rail[search_start:], r'v ->')
        native_show = method((FIXTURES / 'TabSearchOverlayCoordinator.java').read_text(), 'public void show(@TabSearchEntryPoint int entryPoint)')
        replacements = {'ROOT_INIT_HELPER': optional_method(root, 'private boolean shouldInitializeTabSearchOverlay()'),
                        'ROOT_LAZY_HELPER': lazy, 'INIT_BODY': init_body,
                        'ROOT_SHOW': method(root, 'public void showTabSearchOverlay(@TabSearchEntryPoint int entryPoint)'), 'RAIL_HELPER': optional_method(rail, 'private static boolean shouldUseTabSearchOverlay(Activity activity)'),
                        'SEARCH_CLICK': click, 'NATIVE_SHOW': native_show}
        source = SEARCH
        for key, value in replacements.items(): source = source.replace(key, value)
        return source

    def test_arc_horizontal_bar_hides_and_mobile_restores_native_preferences(self):
        self.run_java('BookmarkNavigationProbe', self.bookmark_program(), 'provider')

    def test_arc_hides_ntp_tri_state_and_preserves_native_width_observer(self):
        self.run_java('BookmarkNavigationProbe', self.bookmark_program(), 'tri')

    def test_arc_feature_off_initializes_and_dispatches_native_overlay(self):
        self.run_java('SearchNavigationProbe', self.search_program(), 'true', 'false')

    def test_mobile_start_then_arc_lazily_initializes_native_overlay(self):
        self.run_java('SearchNavigationProbe', self.search_program(), 'false', 'false', 'transition')

    def test_outside_arc_feature_off_preserves_hub_search(self):
        self.run_java('SearchNavigationProbe', self.search_program(), 'false', 'false')

    def test_outside_arc_feature_on_preserves_native_overlay(self):
        self.run_java('SearchNavigationProbe', self.search_program(), 'false', 'true')


    def test_native_bookmark_wiring_guards_profile_icons_and_teardown(self):
        coordinator = (ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java').read_text()
        rebind = method_body(coordinator, re.escape('private void rebindCollections()'))
        needle = 'mCollectionsView = new ArcCollectionsView('
        start = rebind.index(needle) + len(needle); depth = 1
        while depth:
            depth += (rebind[start] == '(') - (rebind[start] == ')'); start += 1
        start = rebind.index(';', start) + 1
        # Execute all real attachment and bridge statements after view construction, in source order.
        binding = rebind[start:rebind.rfind('}')]
        clear = method(coordinator, 'private void clearCollections()')
        self.run_java('BookmarkWiringProbe', BOOKMARK_WIRING.replace('BINDING', binding).replace('CLEAR', clear))

    def test_pinned_native_fixture_provenance(self):
        for name, expected in {
            'BookmarkBarVisibilityProvider.java': '887c16c0d398682ed1a99f9cb92cc4459542774b9a22c573b1592424eba4630d',
            'BookmarkBarCoordinator.java': 'f823c292a7e1cbce6d76905927d8717ab80d938ac49fcdfdcc4c26bdfd7a0e3c',
            'TabSearchOverlayCoordinator.java': '47b73ebca636064f84a9e6b7aff6adc34f0dc7747b96ea3512e1db862a08e156',
        }.items():
            with self.subTest(name=name): self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()
