"""Execute collection methods at bounded view/favicon API boundaries, not device rendering.

The probes catch placeholder eyes, lost native identity/actions and discarded favicon fallback
results. Chromium drawable generation and Android view rendering require the built APK.
"""
from pathlib import Path
import re
import os
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body

SOURCE = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsView.java'

BOUNDARY = r'''
import java.util.*;
import java.util.function.*;
class android {
    static class R {static class drawable {static final int ic_menu_view=1,ic_menu_agenda=2;}}
    static class widget {static class ImageView {enum ScaleType {CENTER_INSIDE}}}
}
class TextUtils {enum TruncateAt {END}}
class Gravity {static final int START=1,CENTER_VERTICAL=2;}
class R {static class string {static final int arc_spaces=1;}}
class Typeface {static final int NORMAL=0;final String family;Typeface(String f){family=f;}static Typeface create(String f,int s){return new Typeface(f);}}
class ArcDesktopPolicy {static final int ARC_TAB_TEXT_SIZE_SP=14,ARC_PRINCIPAL_TEXT_SIZE_SP=14,ARC_SECONDARY_TEXT_SIZE_SP=12,ARC_NAV_ROW_HEIGHT_DP=38;}
class Button extends View {
    String text;Object background=new Object();int minWidth=64,minHeight=48,color,size;boolean singleLine;TextUtils.TruncateAt ellipsize;Typeface typeface;
    Button(Context c){}void setText(String t){text=t;}void setAllCaps(boolean a){}void setTextSize(int s){size=s;}void setTypeface(Typeface t){typeface=t;}
    void setContentDescription(String s){}
    void setMinWidth(int w){minWidth=w;}void setMinimumWidth(int w){}void setMinHeight(int h){minHeight=h;}void setMinimumHeight(int h){}
    void setPadding(int a,int b,int c,int d){}void setSingleLine(boolean s){singleLine=s;}
    void setEllipsize(TextUtils.TruncateAt t){ellipsize=t;}void setGravity(int g){}void setBackground(Object b){background=b;}
    void setBackgroundTintList(Object t){}void setStateListAnimator(Object a){}void setElevation(int e){}void setTextColor(int c){color=c;}
}
class Bitmap {final String kind;Bitmap(String k){kind=k;}}
class GURL {final String url;GURL(String u){url=u;}String getSpec(){return url;}boolean isEmpty(){return url.isEmpty();}}
class Context {Resources getResources(){return new Resources();}String getString(int id){return "Spaces";}}
class Resources {Metrics getDisplayMetrics(){return new Metrics();}}
class Metrics {float density=1;}
class View {
    static final int GONE=8,VISIBLE=0;Object tag;int visibility;Runnable click;Consumer<View> longClick;
    Object getTag(){return tag;}void setTag(Object t){tag=t;}void setVisibility(int v){visibility=v;}
    void setOnClickListener(Consumer<View> r){click=()->r.accept(this);}
    interface LongClick {boolean run(View v);}void setOnLongClickListener(LongClick r){longClick=v->r.run(v);}
}
class ViewGroup extends View {final List<View> children=new ArrayList<>();int getChildCount(){return children.size();}View getChildAt(int n){return children.get(n);}}
class LinearLayout extends ViewGroup {void removeAllViews(){children.clear();}void addView(View v,LayoutParams p){children.add(v);}}
class LayoutParams {LayoutParams(int w,int h){}}
class ImageButton extends View {
    int resource,filtersCleared;Bitmap bitmap;Object drawable,tint,background;String description,tooltip;
    ImageButton(Context c){}Context getContext(){return new Context();}Resources getResources(){return new Resources();}
    void setImageResource(int n){resource=n;}void setImageBitmap(Bitmap b){bitmap=b;resource=0;}
    void setImageDrawable(Object d){drawable=d;resource=0;}void clearColorFilter(){filtersCleared++;}
    void setImageTintList(Object t){tint=t;}void setScaleType(android.widget.ImageView.ScaleType t){}
    void setPadding(int a,int b,int c,int d){}void setContentDescription(String d){description=d;}
    void setTooltipText(String t){tooltip=t;}
    void setBackground(Object b){background=b;}void setBackgroundTintList(Object t){}void setStateListAnimator(Object a){}void setElevation(int e){}
}
class ArcSidebarState {static class Entry {final String id,title,url;Entry(String i,String t,String u){id=i;title=t;url=u;}}}
class BookmarkItem {final String id,title;final boolean folder;final GURL url;
    BookmarkItem(String i,String t,boolean f,String u){id=i;title=t;folder=f;url=new GURL(u);}
    boolean isFolder(){return folder;}String getId(){return id;}String getTitle(){return title;}GURL getUrl(){return url;}}
class ArcNativeBookmarksBridge {final List<BookmarkItem> items=new ArrayList<>();BookmarkItem opened,menu;
    List<BookmarkItem> items(){return items;}void open(BookmarkItem i){opened=i;}void showMenu(View v,BookmarkItem i){menu=i;}}
class RoundedIconGenerator {}
class FaviconUtils {
    record Icon(Bitmap bitmap,String url,int color,int size){}
    static RoundedIconGenerator createRoundedRectangleIconGenerator(Context c){return new RoundedIconGenerator();}
    static Object getIconDrawableWithoutFilter(Bitmap b,GURL u,int color,RoundedIconGenerator g,Resources r,int size){return new Icon(b,u.getSpec(),color,size);}
    static Bitmap createGenericFaviconBitmap(Context c,int size,Integer color){return new Bitmap("native globe");}
}
class ArcDesktopAppearance {static final Object QUIET=new Object(),FAVORITE=new Object();static Object controlBackground(Context c,boolean p,float r){return QUIET;}static Object favoriteBackground(Context c,boolean p,float r){return FAVORITE;}static int rowTextColor(Context c,boolean s,boolean p){return p?0xffffff:0x333333;}}
'''


class CollectionPresentationTest(unittest.TestCase):
    def run_probe(self, body):
        source = SOURCE.read_text()
        methods = 'private void refreshFavorites(List<ArcSidebarState.Entry> entries) ' + method_body(
            source, re.escape('private void refreshFavorites(List<ArcSidebarState.Entry> entries)'))
        for signature in [
                'private Button button(String text, Runnable action)',
                'private void styleAction(Button button)',
                'public void applyAppearance(boolean incognito)',
                'private void styleCollectionControls(View view)',
                'public static void applyFavoriteIcon(ImageButton button, GURL url, Bitmap icon, int fallbackColor)',
                'private void initializeFavoriteIcon(ImageButton favorite)',
                'private void styleFavorite(ImageButton favorite)']:
            if signature in source:
                methods += '\n' + signature + ' ' + method_body(source, re.escape(signature))
        heading = source[source.index('        mSpace = button('):source.index('        mEntries = new LinearLayout(activity);')]
        methods += '\nvoid initializeSpaceHeading() { Context activity=mActivity; ' + heading + ' }'
        program = BOUNDARY + r'''
class CollectionPresentationProbe extends LinearLayout {
    Context mActivity=new Context();LinearLayout mFavorites=new LinearLayout();View mFavoritesScroll=new View();
    ArcNativeBookmarksBridge mNativeBookmarks;boolean mDestroyed,mIncognito;Object mGeometry;
    Button mSpace;int spaceMenus;
    BiConsumer<BookmarkItem,ImageButton> mLoadNativeIcon=(item,button)->{};
    BiConsumer<ArcSidebarState.Entry,ImageButton> mLoadIcon=(entry,button)->{};
    String opened,menu;int dp(int n){return n;}int getWidth(){return 316;}
    void applyGeometry(Object geometry,int width){}void runCommand(Runnable r){if(!mDestroyed)r.run();}
    void open(String id){opened=id;}void showEntryMenu(View v,ArcSidebarState.Entry e){menu=e.id;}
    void showSpaces(){spaceMenus++;}
    static void check(boolean v,String reason){if(!v)throw new AssertionError(reason);}
    METHODS
    public static void main(String[] args){BODY}
}
'''.replace('METHODS', methods).replace('BODY', body)
        with tempfile.TemporaryDirectory(prefix='arc-collection-presentation-') as work:
            path = Path(work) / 'CollectionPresentationProbe.java'
            path.write_text(program)
            compiled = subprocess.run(['javac', '--release', '17', '-d', work, str(path)], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run(['java', '-ea', '-cp', work, 'CollectionPresentationProbe'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_and_arc_tiles_start_with_native_site_fallback_preserving_commands(self):
        self.run_probe(r'''
        var view=new CollectionPresentationProbe();view.mNativeBookmarks=new ArcNativeBookmarksBridge();
        var site=new BookmarkItem("native-id","News",false,"https://news.test/path");
        var folder=new BookmarkItem("folder-id","Documents",true,"");
        view.mNativeBookmarks.items.add(site);view.mNativeBookmarks.items.add(folder);
        var entry=new ArcSidebarState.Entry("arc-id","Saved","https://saved.test/path");
        List<String> urls=new ArrayList<>();view.mLoadNativeIcon=(item,button)->urls.add(item.getUrl().getSpec());
        view.mLoadIcon=(item,button)->urls.add(item.url);view.refreshFavorites(List.of(entry));
        var nativeTile=(ImageButton)view.mFavorites.getChildAt(0);var folderTile=(ImageButton)view.mFavorites.getChildAt(1);
        var arcTile=(ImageButton)view.mFavorites.getChildAt(2);
        check(nativeTile.resource!=android.R.drawable.ic_menu_view&&arcTile.resource!=android.R.drawable.ic_menu_view,"saved sites must never render Android eye placeholders");
        check(nativeTile.bitmap!=null&&arcTile.bitmap!=null,"native fallback visible before asynchronous local icon result");
        check(nativeTile.background==ArcDesktopAppearance.FAVORITE&&arcTile.background==ArcDesktopAppearance.FAVORITE,"favorites share subtle rounded surface and native interactions");
        check(folderTile.resource==android.R.drawable.ic_menu_agenda,"folder remains a folder control");
        check(urls.equals(List.of("https://news.test/path","https://saved.test/path")),"only sites ask native icon API using actual model URL");
        check(nativeTile.tag.equals("arc-bookmark:native-id")&&arcTile.tag.equals("arc-entry:arc-id"),"model identities stay independent");
        nativeTile.click.run();check(view.mNativeBookmarks.opened==site,"native site opens by native item");
        folderTile.click.run();check(view.mNativeBookmarks.opened==folder,"folder keeps native manager command");
        nativeTile.longClick.accept(nativeTile);check(view.mNativeBookmarks.menu==site,"native management menu stays attached");
        arcTile.click.run();check(view.opened.equals("arc-id"),"saved favorite selects existing tab by Arc identity");
        arcTile.longClick.accept(arcTile);check(view.menu.equals("arc-id"),"saved favorite management stays attached");
        view.mDestroyed=true;view.mNativeBookmarks.menu=null;nativeTile.longClick.accept(nativeTile);
        check(view.mNativeBookmarks.menu==null,"destroyed native favorite cannot open menu");
        ''')

    def test_large_icon_null_result_uses_native_url_monogram_and_supplied_color(self):
        # Missing helper is a deliberate pre-implementation failure, before Java compilation.
        self.assertTrue('public static void applyFavoriteIcon(' in SOURCE.read_text(),
                      'LargeIconBridge null result needs a native favicon fallback boundary')
        self.run_probe(r'''
        ImageButton button=new ImageButton(new Context());button.tint=new Object();
        applyFavoriteIcon(button,new GURL("https://news.test/story"),null,0xff123456);
        var fallback=(FaviconUtils.Icon)button.drawable;
        check(fallback.bitmap()==null&&fallback.url().equals("https://news.test/story")&&fallback.color()==0xff123456,"null icon must retain actual URL and native returned color for monogram");
        Bitmap real=new Bitmap("real site");applyFavoriteIcon(button,new GURL("https://news.test/story"),real,0xff123456);
        var site=(FaviconUtils.Icon)button.drawable;check(site.bitmap()==real,"native bitmap replaces fallback without changing identity");
        check(button.filtersCleared==2&&button.tint==null,"site favicon and monogram must keep their own colors");
        applyFavoriteIcon(button,new GURL(""),null,0xff123456);
        check(button.bitmap!=null,"unusable URL retains native globe");
        ''')

    def test_collection_actions_have_quiet_native_interaction_and_fit_narrow_width(self):
        self.run_probe(r'''
        var view=new CollectionPresentationProbe();int[] clicks={0};Button action=view.button("New Folder",()->clicks[0]++);
        check(action.background==ArcDesktopAppearance.QUIET,"collection action needs quiet background with native interaction states");
        check(action.minWidth==0&&action.minHeight==0&&action.singleLine&&action.ellipsize==TextUtils.TruncateAt.END,"narrow sidebar must not inherit platform button minimum size");
        action.click.run();check(clicks[0]==1,"styling preserves clickable collection command");
        view.mDestroyed=true;action.click.run();check(clicks[0]==1,"styling preserves command lifecycle guard");
        ''')

    def test_appearance_repaint_preserves_favicon_content_and_native_controls(self):
        self.run_probe(r'''
        var view=new CollectionPresentationProbe();Button space=view.button("Personal",()->{});
        Bitmap original=new Bitmap("news favicon");ImageButton site=new ImageButton(new Context());site.setImageBitmap(original);
        site.setTag("arc-bookmark:real-id");view.addView(space,new LayoutParams(316,38));
        LinearLayout nested=new LinearLayout();nested.addView(site,new LayoutParams(99,57));
        view.addView(nested,new LayoutParams(316,57));view.applyAppearance(true);
        check(space.color==0xffffff,"private section/action foreground follows active private appearance");
        check(site.bitmap==original&&site.tint==null&&site.tag.equals("arc-bookmark:real-id"),"recursive appearance must not recolor favicon or replace bookmark identity");
        check(space.background==ArcDesktopAppearance.QUIET&&site.background==ArcDesktopAppearance.FAVORITE,"sections remain quiet while nested favorite tiles retain own surface");
        view.applyAppearance(false);check(space.color==0x333333&&site.bitmap==original,"theme change updates foreground while preserving real site bitmap");
        ''')

    def test_personal_space_heading_uses_principal_text_and_preserves_native_popup_action(self):
        self.run_probe(r'''
        var view=new CollectionPresentationProbe();view.initializeSpaceHeading();
        check(view.mSpace.size==14,"Personal is a principal 14sp heading, not 12sp metadata");
        check(view.mSpace.typeface.family.equals("sans-serif-medium"),"space heading keeps semibold face");
        check(view.mSpace.singleLine&&view.mSpace.ellipsize==TextUtils.TruncateAt.END,"principal heading still fits narrow sidebar");
        view.mSpace.click.run();check(view.spaceMenus==1,"principal heading remains the interactive space selector");
        ''')

    def test_favicon_helpers_compile_against_android_sdk_and_pinned_native_signatures(self):
        sdk = Path(os.environ.get('ANDROID_JAR', '/opt/android-sdk/platforms/android-37.0/android.jar'))
        if not sdk.is_file():
            self.skipTest('Android SDK jar unavailable for native favicon API type check')
        source = SOURCE.read_text()
        signature = 'public static void applyFavoriteIcon(ImageButton button, GURL url, Bitmap icon, int fallbackColor)'
        initialize = 'private void initializeFavoriteIcon(ImageButton favorite)'
        helper = '''import android.app.Activity;
import android.graphics.Bitmap;
import android.widget.ImageButton;
import org.chromium.url.GURL;
import org.chromium.chrome.browser.ui.favicon.FaviconUtils;
class CollectionFaviconSdkProbe {
    Activity mActivity;int dp(int value){return value;}
''' + signature + method_body(source, re.escape(signature)) + '\n' + initialize + method_body(source, re.escape(initialize)) + '\n}'
        # Exact signatures from pinned cfd94726 FaviconUtils. Drawable and Resources are
        # actual Android SDK types; Chromium/JNI implementation remains a bounded contract.
        contracts = {
            'org/chromium/url/GURL.java': '''package org.chromium.url;
public class GURL {public boolean isEmpty(){return false;}}''',
            'org/chromium/components/browser_ui/widget/RoundedIconGenerator.java': '''package org.chromium.components.browser_ui.widget;
public class RoundedIconGenerator {}''',
            'org/chromium/chrome/browser/ui/favicon/FaviconUtils.java': '''package org.chromium.chrome.browser.ui.favicon;
import android.content.Context;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.drawable.Drawable;
import org.chromium.url.GURL;
import org.chromium.components.browser_ui.widget.RoundedIconGenerator;
public class FaviconUtils {
    public static RoundedIconGenerator createRoundedRectangleIconGenerator(Context context){return null;}
    public static Bitmap createGenericFaviconBitmap(Context context,int size,Integer backgroundColor){return null;}
    public static Drawable getIconDrawableWithoutFilter(Bitmap icon,GURL url,int fallbackColor,
            RoundedIconGenerator generator,Resources resources,int iconSize){return null;}
}''',
        }
        with tempfile.TemporaryDirectory(prefix='arc-favicon-sdk-') as work:
            sources = []
            for name, text in {'CollectionFaviconSdkProbe.java': helper, **contracts}.items():
                path = Path(work) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
                sources.append(str(path))
            result = subprocess.run(['javac', '--release', '17', '-cp', str(sdk), '-d', work, *sources],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
