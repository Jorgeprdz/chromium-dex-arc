"""Run shipped header styling and favicon callback bodies at view/service boundaries."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body

COORD=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java'

JAVA=r'''
import java.util.*;
class HeaderPresentationProbe {
    static class android {static class R {static class attr {static final int state_enabled=1;}}}
    static class Drawable {int resting=0xffaabbcc;}
    static class GradientDrawable extends Drawable {void setColor(int c){resting=c;}void setCornerRadius(int r){}}
    static class ColorStateList {final int[] colors;ColorStateList(int[][] states,int[] values){colors=values;}}
    static class View {Drawable background=new Drawable();void setBackground(Drawable d){background=d;}}
    static class ViewGroup extends View {final List<View> children=new ArrayList<>();int getChildCount(){return children.size();}View getChildAt(int i){return children.get(i);}}
    static class TextView extends View {int textColor;void setTextColor(int c){textColor=c;}}
    static class Button extends TextView {}
    static class ImageButton extends View {int filter=0;ColorStateList tint;Object bitmap;Object drawable;
        void setColorFilter(int c){filter=c;}void clearColorFilter(){filter=0;}void setImageTintList(ColorStateList c){tint=c;}void setImageBitmap(Object b){bitmap=b;}}
    static class Incognito {boolean isIncognitoSelected(){return false;}}
    static class ArcDesktopAppearance {static Drawable controlBackground(Object c,boolean i,float radius){Drawable d=new Drawable();d.resting=0;return d;}}
    static class ArcCollectionsView extends ViewGroup {
        final ImageButton favicon=new ImageButton();ArcCollectionsView(){favicon.bitmap=new Object();children.add(favicon);}
        void applyAppearance(boolean incognito){}
        static void applyFavoriteIcon(ImageButton button,GURL url,Object icon,int color){
            button.bitmap=icon;button.drawable=icon==null?url.value+":"+color:icon;
        }
    }
    static class GURL {final String value;GURL(String s){value=s;}}
    static class org {static class chromium {static class url {static class GURL extends HeaderPresentationProbe.GURL {GURL(String s){super(s);}}}}}
    static class Entry {String url="https://example.com/";}
    static class Item {GURL getUrl(){return new GURL("https://bookmark.test/");}}
    static class Supplier {Object model;Object get(){return model;}}
    final Object mActivity=new Object();final Incognito mIncognitoStateProvider=new Incognito();
    final View mLocationBarHost=new View(),mCollapseButton=new View(),mMenuButtonWrapper=new View(),mExtensionsToolbarHost=new View();
    final ViewGroup mNavigationControls=new ViewGroup();
    boolean mDestroyed;Object session=new Object(),mTabSession=session,model=new Object();
    final Supplier mCurrentModel=new Supplier();final Entry entry=new Entry();final Item item=new Item();
    final ImageButton button=new ImageButton();HeaderPresentationProbe(){mCurrentModel.model=model;}
    int dp(int n){return n;}
    TINT
    void entryCallback(Object icon,int color,boolean fallback,int type) ENTRY_CALLBACK
    void bookmarkCallback(Object icon,int color,boolean fallback,int type) BOOKMARK_CALLBACK
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    public static void main(String[]args){
        HeaderPresentationProbe p=new HeaderPresentationProbe();
        if(args[0].equals("navigation")){
            ImageButton back=new ImageButton();p.mNavigationControls.children.add(back);
            p.tintHeader(p.mNavigationControls,0xff123456,0xffffffff);
            check(back.background.resting==0,"navigation must have no permanent solid Android button background");
            check(back.tint!=null&&back.tint.colors[0]!=back.tint.colors[1],"disabled navigation icon must have a distinct native tint state");
        }else if(args[0].equals("favicon")){
            ArcCollectionsView favorites=new ArcCollectionsView();Object original=favorites.favicon.bitmap;
            p.tintHeader(favorites,0xff123456,0xffffffff);
            check(favorites.favicon.filter==0&&favorites.favicon.bitmap==original,"collection favicon keeps original pixel colors and identity");
        }else if(args[0].equals("fallback")){
            p.entryCallback(null,0xffabcdef,true,0);
            check("https://example.com/:-5517841".equals(p.button.drawable),"Arc entry callback must deliver null bitmap and returned color to fallback renderer");
            p.bookmarkCallback(null,0xffabcdef,true,0);
            check("https://bookmark.test/:-5517841".equals(p.button.drawable),"bookmark callback must deliver its own real URL and fallback color");
        }else if(args[0].equals("stale")){
            p.mTabSession=new Object();Object before=p.button.drawable;
            p.entryCallback(null,0xffabcdef,true,0);p.bookmarkCallback(null,0xffabcdef,true,0);
            check(p.button.drawable==before,"callbacks from obsolete profile/session cannot repaint live favorites");
        }
    }
}
'''

class ArcHeaderPresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=COORD.read_text()
        signature='private void tintHeader(View view, int foreground, int selection)'
        callbacks=list(re.finditer(r'\(icon, color, fallback, type\) ->',source))
        if len(callbacks)!=2:raise AssertionError('Expected two profile-bound icon callbacks')
        bodies=[method_body(source[c.start():],re.escape('(icon, color, fallback, type) ->')) for c in callbacks]
        program=JAVA.replace('TINT',signature+' '+method_body(source,re.escape(signature))).replace('ENTRY_CALLBACK',bodies[0]).replace('BOOKMARK_CALLBACK',bodies[1])
        cls.temp=tempfile.TemporaryDirectory(prefix='arc-header-presentation-');cls.addClassCleanup(cls.temp.cleanup)
        cls.work=Path(cls.temp.name);path=cls.work/'HeaderPresentationProbe.java';path.write_text(program)
        result=subprocess.run(['javac','--release','17','-d',str(cls.work),str(path)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)
    def probe(self,case):
        result=subprocess.run(['java','-ea','-cp',str(self.work),'HeaderPresentationProbe',case],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_navigation_quiet_rest_and_disabled_icon_state(self):self.probe('navigation')
    def test_header_repaint_never_tints_collection_favicons(self):self.probe('favicon')
    def test_both_real_icon_callbacks_consume_fallback(self):self.probe('fallback')
    def test_icon_callbacks_reject_obsolete_session(self):self.probe('stale')
