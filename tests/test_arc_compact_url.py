"""Execute native parser/display/copy bodies and tablet lifecycle with bounded services.

These probes verify text and mode behavior; Android text measurement, native URL
canonicalization, rendering, IME and window lifecycle still require device checks.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import ROOT, method_body

BASE = 'chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/'
JAVA = r'''
import java.util.*;
import java.util.function.Consumer;
class CompactUrlProbe {
    static class TextUtils {
        static boolean isEmpty(CharSequence s){return s==null||s.length()==0;}
        static boolean equals(CharSequence a,CharSequence b){return Objects.equals(a==null?null:a.toString(),b==null?null:b.toString());}
    }
    // Services do not format or compact text. Production UrlBarData owns parsing.
    static class GURL {
        final String spec;GURL(String s){spec=s;}String getSpec(){return spec;}
        String getScheme(){int i=spec.indexOf(':');return i<0?"":spec.substring(0,i);}
        String getHost(){try{return java.net.URI.create(spec).getHost();}catch(Exception e){return "";}}
        GURL getOrigin(){return this;}static boolean isEmptyOrInvalid(GURL u){return u==null||u.spec.isEmpty();}
    }
    static class Uri {
        final String value;Uri(String s){value=s;}static Uri parse(String s){return new Uri(s);}
        String getScheme(){int i=value.indexOf(':');return i<0?null:value.substring(0,i);}
    }
    static class UrlConstants {
        static final String BLOB_SCHEME="blob",DISTILLER_SCHEME="chrome-distiller",HTTP_SCHEME="http",HTTPS_SCHEME="https",
            CHROME_SCHEME="chrome",DATA_SCHEME="data",FILE_SCHEME="file",FTP_SCHEME="ftp",INLINE_SCHEME="inline",JAVASCRIPT_SCHEME="javascript";
    }
    static class ContentUrlConstants {static final String ABOUT_SCHEME="about";}
    static class UrlUtilities {static boolean isNtpUrl(GURL u){return u.spec.equals("chrome://newtab/")||u.spec.equals("chrome-native://newtab/");}}
    static class NativePage {static boolean isChromePageUrl(GURL u,boolean off){return u.getScheme().equals("chrome");}}
    static class OmniboxCapabilities {static boolean isDesktopPlatform(){return true;}}
    static class ResettersForTesting {static void register(Runnable r){}}
    static class OmniboxViewUtil {static boolean haveEquivalentSpans(CharSequence a,CharSequence b,Class<?> c){return true;}}
    static class UrlEmphasisSpan {}
    // Preserve a style marker through subSequence to catch accidental String conversion.
    static class StyledText implements CharSequence {
        final String value;StyledText(String v){value=v;}public int length(){return value.length();}
        public char charAt(int i){return value.charAt(i);}public CharSequence subSequence(int s,int e){return new StyledText(value.substring(s,e));}
        public String toString(){return value;}
    }
    static class ScrollType {static final int NO_SCROLL=0,SCROLL_TO_TLD=1,SCROLL_TO_BEGINNING=2;}
    static class TextSelection {
        final int lo,hi;TextSelection(int a,int b){lo=a;hi=b;}int getLower(){return Math.min(lo,hi);}int getUpper(){return Math.max(lo,hi);}
        static final TextSelection SELECT_ALL=new TextSelection(0,Integer.MAX_VALUE),SELECT_END=new TextSelection(Integer.MAX_VALUE,Integer.MAX_VALUE);
        public boolean equals(Object o){return o instanceof TextSelection s&&lo==s.lo&&hi==s.hi;}
    }
    static class UrlBarProperties {static final int TEXT_STATE=1,SHOW_HINT_TEXT=2,DELEGATE=3,ALLOW_MULTILINE_INPUT=4,AUTOCOMPLETE_TEXT=5;}
    static class DisplayState {static final int SUGGESTIONS=1;}
    static class Supplier {void removeObserver(Consumer<Integer> c){}void addSyncObserverAndCallIfNonNull(Consumer<Integer> c){c.accept(0);}}
    static class AutocompleteInput {
        final GURL page;final Supplier supplier=new Supplier();AutocompleteInput(GURL u){page=u;}
        Supplier getDisplayStateSupplier(){return supplier;}GURL getPageUrl(){return page;}
        TextSelection getSelection(){return TextSelection.SELECT_ALL;}boolean hasPreviewText(){return false;}
        String getUserText(){return page.getSpec();}String getPreviewText(){return "";}
    }
    static class FuseboxSessionState {final AutocompleteInput input;FuseboxSessionState(GURL u){input=new AutocompleteInput(u);}AutocompleteInput getAutocompleteInput(){return input;}}
    static class AutocompleteText {AutocompleteText(String u,String a,String t,String l){}}
    static class UrlBarTextState {
        final CharSequence text,autofill;final int scroll,originEnd;final TextSelection selection;
        UrlBarTextState(CharSequence t,CharSequence a,int s,int e,TextSelection sel,boolean change){text=t;autofill=a;scroll=s;originEnd=e;selection=sel;}
    }
    static class UrlBarDelegate {String replacement;UrlBarData inputData;UrlBarData getUrlBarDataForCurrentInput(){return inputData;}String getReplacementCutCopyText(String t,TextSelection s){return replacement;}}
    static class Model {
        UrlBarTextState state;final UrlBarDelegate delegate=new UrlBarDelegate();
        void set(int key,Object value){if(key==UrlBarProperties.TEXT_STATE)state=(UrlBarTextState)value;}
        UrlBarDelegate get(int key){return delegate;}
    }
    DATA
    static class Mediator {
        AutocompleteInput mCurrentInput;final Consumer<Integer> mDisplayStateObserver=this::onDisplayStateChanged;boolean mShowOriginOnly;UrlBarData mUrlBarData=UrlBarData.EMPTY;
        int mScrollType=ScrollType.SCROLL_TO_TLD;TextSelection mSelection=TextSelection.SELECT_ALL;final Model mModel=new Model();
        METHODS
    }
    static class View {Object parent;Object getParent(){return parent;}}
    static class ScrollView extends View {}
    static class UrlCoordinator {
        final Mediator mediator;int pushes;UrlCoordinator(Mediator m){mediator=m;}
        void setShowOriginOnly(boolean b){pushes++;mediator.setShowOriginOnly(b);}
        boolean hasFocus(){return false;}
    }
    static class Configuration {int screenWidthDp=1000;}
    static class Resources {Configuration getConfiguration(){return new Configuration();}}
    static class Handler {void post(Runnable r){}}
    static class Glif {void start(){}}
    static class FuseboxLayoutMode {static final int SUGGESTIONS_POPOVER=1;}
    static class LayoutBase {protected void onLayout(boolean c,int l,int t,int r,int b){}}
    static class Tablet extends LayoutBase {
        View mHolder,mContainerView;UrlCoordinator mUrlCoordinator;boolean mShowsCompactUrl;
        int mLayoutLeft,mLayoutRight,mScreenWidthDp=1000,mFuseboxState,mLayoutMode;
        float mWidthChangeFraction;boolean mAnimatingWidthChange,mStartGlifOnNextLayout,mIsGlifActive;
        Handler mHandler=new Handler();Glif mGlifBorderDrawable=new Glif();
        Resources getResources(){return new Resources();}void setWidthChangeAnimationFraction(float f){}
        void onFuseboxStateChanged(int s){}
        TABLET_METHODS
    }
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
    static Mediator data(String raw,CharSequence display){Mediator m=new Mediator();m.setUrlBarData(UrlBarData.forUrlAndText(new GURL(raw),display,raw),ScrollType.SCROLL_TO_TLD,TextSelection.SELECT_ALL);return m;}
    static void shown(Mediator m,String s){check(m.mModel.state.text.toString().equals(s),"expected "+s+" got "+m.mModel.state.text);}
    public static void main(String[] args){String scenario=args[0];
        if(scenario.equals("focus")) {
            Mediator m=data("https://example.test/path?q=full#hash","example.test/path?q=full#hash");
            m.setShowOriginOnly(true);shown(m,"example.test");m.mModel.delegate.inputData=m.mUrlBarData;
            m.beginInput(new FuseboxSessionState(m.mUrlBarData.url));
            shown(m,"https://example.test/path?q=full#hash");check(m.mModel.state.scroll==ScrollType.NO_SCROLL,"editing scroll remains native");
            m.endInput();shown(m,"https://example.test");
            m.setUrlBarData(m.mModel.delegate.inputData,ScrollType.SCROLL_TO_TLD,TextSelection.SELECT_ALL);shown(m,"example.test");
        } else if(scenario.equals("copy")) {
            String raw="https://example.test/path?q=full#hash";Mediator m=data(raw,"example.test/path?q=full#hash");m.setShowOriginOnly(true);
            check(raw.equals(m.getReplacementCutCopyText("example.test",new TextSelection(0,12))),"copy compact display must retain path query and fragment");
            check(m.getReplacementCutCopyText("example.test",new TextSelection(1,5))==null,"partial selection stays native");
            m.mModel.delegate.replacement="https://functional.example/full/path";
            check(m.mModel.delegate.replacement.equals(m.getReplacementCutCopyText("example.test",new TextSelection(0,12))),"native rewritten URL copy delegate takes precedence");
            m.mModel.delegate.replacement=null;m.mCurrentInput=new AutocompleteInput(m.mUrlBarData.url);m.pushTextToModel(false);
            check(raw.equals(m.getReplacementCutCopyText(raw,new TextSelection(0,raw.length()))),"focused native full copy");
        } else if(scenario.equals("urls")) {
            String[][] cases={
                {"https://localhost:8443/long/path","localhost:8443/long/path","localhost:8443"},
                {"http://192.0.2.1:8080/path","192.0.2.1:8080/path","192.0.2.1:8080"},
                {"https://[2001:db8::1]:8443/path","[2001:db8::1]:8443/path","[2001:db8::1]:8443"},
                {"http://example.test/path","http://example.test/path","http://example.test"},
                {"https://xn--mgbh0fb.test/path","مثال.test/path","مثال.test"},
                {"file:///storage/emulated/0/report.pdf","file:///storage/emulated/0/report.pdf","file:///storage/emulated/0/report.pdf"},
                {"chrome://settings/privacy","chrome://settings/privacy","chrome://settings/privacy"},
                {"data:text/plain,hello/world","data:text/plain,hello/world","data:text/plain,hello/world"}};
            for(String[] c:cases){Mediator m=data(c[0],new StyledText(c[1]));m.setShowOriginOnly(true);shown(m,c[2]);
                check(m.mUrlBarData.url.getSpec().equals(c[0]),"navigation URL changed");check(m.mModel.state.autofill.toString().equals(c[0]),"autofill full URL changed");
                if(c[0].startsWith("http"))check(m.mModel.state.text instanceof StyledText,"security emphasis lost");}
        } else if(scenario.equals("empty")) {
            for(boolean incognito:new boolean[]{false,true}){
                check(!UrlBarData.shouldShowUrl(new GURL("chrome://newtab/"),incognito),"NTP suppression changed");
                Mediator m=new Mediator();m.setShowOriginOnly(true);shown(m,"");
                m.setUrlBarData(UrlBarData.forNonUrlText("search terms"),ScrollType.NO_SCROLL,TextSelection.SELECT_ALL);shown(m,"search terms");
            }
        } else if(scenario.equals("mobile")) {
            Mediator m=data("https://example.test/full/path","example.test/full/path");
            Tablet t=new Tablet();View toolbar=new View(),row=new View(),header=new View(),root=new View();ScrollView viewport=new ScrollView();
            toolbar.parent=root;row.parent=toolbar;viewport.parent=root;header.parent=viewport;
            t.mHolder=new View();t.mContainerView=toolbar;t.mUrlCoordinator=new UrlCoordinator(m);t.mHolder.parent=row;
            t.onLayout(true,0,0,600,56);shown(m,"example.test/full/path");
            t.mHolder.parent=header;t.onLayout(true,0,0,240,40);shown(m,"example.test");
            int pushes=t.mUrlCoordinator.pushes;t.onLayout(false,0,0,240,40);check(t.mUrlCoordinator.pushes==pushes,"unchanged layout rewrites text");
            t.mHolder.parent=row;t.onLayout(true,0,0,600,56);shown(m,"example.test/full/path");
            t.mHolder.parent=null;t.onLayout(true,0,0,0,0);shown(m,"example.test/full/path");
        }
        System.out.println("PASS "+scenario);
    }
}
'''


class ArcCompactUrlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='arc-compact-url-');cls.addClassCleanup(cls.temp.cleanup);cls.work=Path(cls.temp.name)
        def source(name):
            p=ROOT/'.source-modified'/(BASE+name+'.java')
            return (p if p.exists() else ROOT/'.source-reference'/(BASE+name+'.java')).read_text()
        def methods(text,signatures):
            return '\n'.join(sig+' '+method_body(text,re.escape(sig)) for sig in signatures)
        mediator=methods(source('UrlBarMediator'),[
            '/* package */ boolean isInInputSession()',
            'void beginInput(FuseboxSessionState sessionState)',
            'void endInput()',
            'private void onDisplayStateChanged(@DisplayState int displayState)',
            '/* package */ void pushCurrentInputToModel()',
            'public void setAutocompleteText(\n            String userText,\n            @Nullable String autocompleteText,\n            @Nullable String additionalText,\n            @Nullable String siteSearchLabel)',
            'private void updateShowHintText(String text)',
            'public boolean setUrlBarData(\n            UrlBarData data, @ScrollType int scrollType, TextSelection selection)',
            '/* package */ void pushTextToModel(boolean originChanged)',
            'protected static boolean isNewTextEquivalentToExistingText(\n            UrlBarData existingUrlData, UrlBarData newUrlData)',
            'private @Nullable GURL getOrigin(@Nullable GURL gurl)',
            'void setShowOriginOnly(boolean showOriginOnly)',
            'public @Nullable String getReplacementCutCopyText(String currentText, TextSelection selection)',
            'private static String getUrlContentsPrePath(String url, String host)',
        ])
        tablet=source('LocationBarTablet')
        tablet_methods=methods(tablet,[
            'protected void onLayout(boolean changed, int left, int top, int right, int bottom)',
            'private @Nullable View getExpansionContainerView()',
        ])
        if 'private void updateCompactUrlDisplay()' in tablet:
            tablet_methods+=methods(tablet,['private void updateCompactUrlDisplay()'])
        data=source('UrlBarData');data=data[data.index('public class UrlBarData'):].replace('public class UrlBarData','static class UrlBarData')
        java=JAVA.replace('    DATA\n',data+'\n').replace('TABLET_METHODS',tablet_methods).replace('METHODS',mediator)
        java=java.replace('@Nullable ','').replace('@ScrollType ','').replace('@Override','').replace('@DisplayState ','')
        path=cls.work/'CompactUrlProbe.java';path.write_text(java)
        home=Path(os.environ.get('JAVA_HOME','/usr/lib/jvm/java-17-openjdk-arm64'))
        cls.java=str(home/'bin/java') if (home/'bin/java').exists() else shutil.which('java')
        javac=str(home/'bin/javac') if (home/'bin/javac').exists() else shutil.which('javac')
        result=subprocess.run([javac,'--release','17','-d',str(cls.work),str(path)],capture_output=True,text=True)
        if result.returncode:raise AssertionError(result.stderr)

    def probe(self,scenario):
        p=subprocess.run([self.java,'-ea','-cp',str(self.work),'CompactUrlProbe',scenario],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_native_origin_format_preserves_ports_ips_internal_file_and_security_styles(self):self.probe('urls')
    def test_input_session_displays_full_address_and_blur_restores_origin(self):self.probe('focus')
    def test_copying_entire_compact_address_preserves_full_native_url(self):self.probe('copy')
    def test_ntp_incognito_empty_and_search_text_keep_native_behavior(self):self.probe('empty')
    def test_layout_enables_compaction_only_in_sidebar_and_restores_mobile(self):self.probe('mobile')

    def test_compact_display_helper_compiles_against_android37_view_api(self):
        jar=Path(os.environ.get('ANDROID_HOME','/opt/android-sdk'))/'platforms/android-37.0/android.jar'
        if not jar.exists():self.skipTest('Android37 API jar unavailable')
        text=(ROOT/'.source-modified'/(BASE+'LocationBarTablet.java')).read_text()
        helpers='\n'.join(sig+' '+method_body(text,re.escape(sig)) for sig in [
            'private @Nullable View getExpansionContainerView()',
            'private void updateCompactUrlDisplay()',
        ]).replace('@Nullable ','')
        program='''
import android.view.View;
import android.widget.ScrollView;
class CompactUrlAndroidApiProbe {
    View mHolder,mContainerView;boolean mShowsCompactUrl;
    static class UrlBarCoordinator {void setShowOriginOnly(boolean value){}}
    UrlBarCoordinator mUrlCoordinator;
    HELPERS
}
'''.replace('HELPERS',helpers)
        path=self.work/'CompactUrlAndroidApiProbe.java';path.write_text(program)
        home=Path(os.environ.get('JAVA_HOME','/usr/lib/jvm/java-17-openjdk-arm64'))
        javac=str(home/'bin/javac') if (home/'bin/javac').exists() else shutil.which('javac')
        result=subprocess.run([javac,'--release','17','-cp',str(jar),'-d',str(self.work),str(path)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
