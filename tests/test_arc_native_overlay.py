"""Run shipped overlay ownership and focus clipping bodies at bounded Java APIs.

Android storage doubles make clipping observable; the second compile uses SDK37.
These probes cannot establish compositor pixels or native suggestion rendering.
"""
from pathlib import Path
import hashlib
import re
import subprocess
import tempfile
import unittest

from arc_toolbar_probe import ROOT, method_body, window_core_jar

MANAGER_REL = 'chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java'
BAR_REL = 'chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarTablet.java'


def manager_source():
    modified = ROOT / '.source-modified' / MANAGER_REL
    return (modified if modified.exists() else ROOT / '.sync-audit/arc-next-polish-20261009/white-bar-sources/ToolbarManager.java').read_text()


def clipping_body(source):
    if 'private void setExpansionAncestorClipping(boolean clip)' in source:
        return method_body(source, re.escape('private void setExpansionAncestorClipping(boolean clip)'))
    # Exercise the unfixed native focus branch, so RED fails on actual viewport state.
    body = method_body(source, r'void updateLayoutAndBackground\(')
    calls = re.findall(r'ViewUtils\.setAncestorsShouldClip(?:ToPadding|Children)\(this, false, View.NO_ID\);', body)
    return '{' + '\n'.join(call.replace('false', 'clip') for call in calls) + '}'


def run_java(test, program, name, sdk=False):
    with tempfile.TemporaryDirectory(prefix='arc-overlay-') as tmp:
        source = Path(tmp) / (name + '.java')
        source.write_text(program)
        args = ['javac', '--release', '17', '-d', tmp]
        if sdk:
            args += ['-cp', '/opt/android-sdk/platforms/android-37.0/android.jar']
        result = subprocess.run(args + [str(source)], capture_output=True, text=True)
        test.assertEqual(result.returncode, 0, result.stderr)
        if not sdk:
            result = subprocess.run(['java', '-ea', '-cp', tmp, name], capture_output=True, text=True)
            test.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ArcNativeOverlayTest(unittest.TestCase):
    def test_native_overlay_ownership_follows_arc_caption_replacement_and_destroy(self):
        manager = manager_source()
        setter = method_body(manager, re.escape('public void setArcToolbarSceneLayerSuppressed(boolean suppressed)'))
        update = method_body(manager, re.escape('private void updateToolbarSceneLayerSuppression()'))
        destroy = method_body(manager, re.escape('public void destroy()'))
        # Exercise the actual release boundary before unrelated Chromium services tear down.
        destroy = destroy[:destroy.index('        if (mAppInstalledDelegate != null)')] + '}'
        root = (ROOT / '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java').read_text()
        composition = method_body(root, re.escape('private void setArcToolbarSuppressed(boolean suppressed)'))
        program = '''import java.util.*;
            class ArcComposition {
                static class View {static final int GONE=8;int visibility;int getVisibility(){return visibility;}void setVisibility(int v){visibility=v;}void clearFocus(){}}
                static class R {static class id {static final int toolbar=1,toolbar_hairline=2;}}
                static class Activity {View toolbar=new View(),hairline=new View();View findViewById(int id){return id==1?toolbar:hairline;}}
                static class Manager {
                    boolean mIsDestroyed,mIsXrFsm,mIsVerticalTabsHiddenDueToNarrow,mArcToolbarSceneLayerSuppressed;
                    static class Supplier {boolean value;void set(boolean v){value=v;}}
                    Supplier mSuppressToolbarSceneLayerSupplier=new Supplier();Object coordinator=new Object();
                    Object getTopToolbarCoordinator(){return coordinator;}
                    public void setArcToolbarSceneLayerSuppressed(boolean suppressed) SETTER
                    private void updateToolbarSceneLayerSuppression() UPDATE
                    public void destroy() DESTROY
                }
                static class Controls {boolean suppressed;void setArcToolbarSuppressed(boolean v){suppressed=v;}}
                static class Stacker {Set<Object> layers=new HashSet<>();void addControl(Object l){layers.add(l);}void removeControl(Object l){layers.remove(l);}void requestLayerUpdateSync(boolean b){}}
                Activity mActivity=new Activity();Manager mToolbarManager=new Manager();Controls mControlContainer=new Controls();
                Stacker mTopControlsStacker=new Stacker();Object mArcCaptionLayer=new Object();
                boolean mArcToolbarSuppressed;int mArcToolbarOriginalVisibility,mArcToolbarHairlineOriginalVisibility;
                void registerArcCaptionObserver(){}void unregisterArcCaptionObserver(){}void updateBookmarkBarVisibility(){}
                private void setArcToolbarSuppressed(boolean suppressed) COMPOSITION
                static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
                public static void main(String[] args){ArcComposition p=new ArcComposition();
                    p.mTopControlsStacker.addControl(p.mToolbarManager.coordinator);
                    p.setArcToolbarSuppressed(true);
                    check(p.mToolbarManager.mSuppressToolbarSceneLayerSupplier.value,"composition must actually suppress native overlay");
                    check(p.mControlContainer.suppressed&&p.mActivity.toolbar.visibility==8,"native input and View suppression remain aligned");
                    check(p.mTopControlsStacker.layers.equals(Set.of(p.mArcCaptionLayer)),"caption replaces toolbar once");
                    p.mToolbarManager.mIsXrFsm=true;p.setArcToolbarSuppressed(false);
                    check(p.mToolbarManager.mSuppressToolbarSceneLayerSupplier.value,"MOBILE cannot clear XR overlay suppression");
                    check(!p.mControlContainer.suppressed&&p.mActivity.toolbar.visibility==0,"MOBILE restores native View and input ownership");
                    check(p.mTopControlsStacker.layers.equals(Set.of(p.mToolbarManager.coordinator)),"MOBILE restores original toolbar stack layer");
                    p.mToolbarManager.mIsXrFsm=false;p.setArcToolbarSuppressed(true);p.mToolbarManager.destroy();
                    check(p.mToolbarManager.mIsDestroyed&&!p.mToolbarManager.mArcToolbarSceneLayerSuppressed&&!p.mToolbarManager.mSuppressToolbarSceneLayerSupplier.value,"destroy releases ARC suppression before native dependencies");
                    p.mToolbarManager.setArcToolbarSceneLayerSuppressed(true);
                    check(!p.mToolbarManager.mArcToolbarSceneLayerSuppressed,"late callbacks cannot reacquire destroyed overlay");
                }
            }'''.replace('SETTER', setter).replace('UPDATE', update).replace('DESTROY', destroy).replace('COMPOSITION', composition)
        run_java(self, program, 'ArcComposition')

    def test_caption_layer_uses_pinned_native_interface_and_nested_annotation_apis(self):
        fixtures = ROOT / 'tests/fixtures/arc-caption'
        self.assertEqual(hashlib.sha256((fixtures / 'TopControlLayer.java').read_bytes()).hexdigest(),
                         '488b60c0928699ea30e0d0d2ac85331fb33fc9a65bcf39b3dfec91ddb975daff')
        self.assertEqual(hashlib.sha256((fixtures / 'TopControlsStacker.java').read_bytes()).hexdigest(),
                         '969b2bb53e31c75027b33a7c7a6e7889dffc61ce58336cafb32ec2ce616eff11')
        layer = (fixtures / 'TopControlLayer.java').read_text()
        stacker = (fixtures / 'TopControlsStacker.java').read_text()
        native_types = '\n'.join('public @interface ' + name + ' ' + method_body(
            stacker, re.escape('public @interface ' + name))
            for name in ('TopControlType', 'TopControlVisibility', 'ScrollBehavior'))
        source = (ROOT / '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java').read_text()
        start = source.index('private final TopControlLayer mArcCaptionLayer =')
        end = source.index('\n    };', start) + len('\n    };')
        # Retain real production annotation imports and uses instead of replacing them with ints.
        imports = '\n'.join(re.findall(r'^import org.chromium.chrome.browser.browser_controls.TopControl[^;]+;', source, re.M))
        program = imports + '''
            import org.chromium.chrome.browser.ui.vertical_tabs.ArcDesktopPolicy;
            class CaptionNativeApi {
                static class AppHeaderState {boolean isInDesktopWindow(){return true;}int getAppHeaderHeight(){return 40;}}
                static class DesktopWindowStateManager {AppHeaderState getAppHeaderState(){return new AppHeaderState();}}
                static class FullscreenManager {boolean getPersistentFullscreenMode(){return false;}}
                static class Stacker {int getHeightFromLayerToTop(int type){return 0;}}
                FullscreenManager mFullscreenManager=new FullscreenManager();Stacker mTopControlsStacker=new Stacker();
                DesktopWindowStateManager getDesktopWindowStateManager(){return new DesktopWindowStateManager();}
                LAYER
            }'''.replace('LAYER', source[start:end])
        with tempfile.TemporaryDirectory(prefix='arc-caption-api-') as tmp:
            files = {
                'org/chromium/chrome/browser/browser_controls/TopControlLayer.java': layer,
                'org/chromium/chrome/browser/browser_controls/TopControlsStacker.java':
                    'package org.chromium.chrome.browser.browser_controls;public class TopControlsStacker {' + native_types + '}',
                'org/chromium/chrome/browser/browser_controls/BrowserControlsOffsetTagsInfo.java':
                    'package org.chromium.chrome.browser.browser_controls;public class BrowserControlsOffsetTagsInfo {}',
                'org/chromium/build/annotations/NullMarked.java':
                    'package org.chromium.build.annotations;public @interface NullMarked {}',
                'org/chromium/build/annotations/Nullable.java':
                    'package org.chromium.build.annotations;import java.lang.annotation.*;@Target({ElementType.TYPE_USE,ElementType.PARAMETER})public @interface Nullable {}',
                'CaptionNativeApi.java': program,
            }
            paths = []
            for name, body in files.items():
                path = Path(tmp) / name;path.parent.mkdir(parents=True, exist_ok=True);path.write_text(body);paths.append(path)
            paths += list((ROOT / 'chromium').rglob('ArcDesktopPolicy.java'))
            paths += list((ROOT / 'chromium').rglob('ArchiumWindowClass.java'))
            jar = window_core_jar()
            result = subprocess.run(['javac', '--release', '17', '-cp', str(jar), '-d', tmp, *map(str, paths)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_arc_reason_survives_native_reason_updates_and_releases_independently(self):
        source = manager_source()
        setter = (method_body(source, re.escape('public void setArcToolbarSceneLayerSuppressed(boolean suppressed)'))
                  if 'public void setArcToolbarSceneLayerSuppressed(boolean suppressed)' in source else '{}')
        update = method_body(source, re.escape('private void updateToolbarSceneLayerSuppression()'))
        # The real native callers both funnel through this same recomputation.
        program = '''class OverlayOwnership {
            boolean mIsDestroyed,mIsXrFsm,mIsVerticalTabsHiddenDueToNarrow,mArcToolbarSceneLayerSuppressed;
            static class Supplier {boolean value;void set(boolean v){value=v;}}
            Supplier mSuppressToolbarSceneLayerSupplier=new Supplier();
            public void setArcToolbarSceneLayerSuppressed(boolean suppressed) SETTER
            private void updateToolbarSceneLayerSuppression() UPDATE
            static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
            public static void main(String[] args){OverlayOwnership p=new OverlayOwnership();
                p.setArcToolbarSceneLayerSuppressed(true);
                check(p.mSuppressToolbarSceneLayerSupplier.value,"ARC must hide native overlay even when toolbar View is GONE");
                p.updateToolbarSceneLayerSuppression();
                check(p.mSuppressToolbarSceneLayerSupplier.value,"native resize cannot clear ARC suppression");
                p.mIsXrFsm=true;p.updateToolbarSceneLayerSuppression();p.setArcToolbarSceneLayerSuppressed(false);
                check(p.mSuppressToolbarSceneLayerSupplier.value,"MOBILE must preserve XR suppression");
                p.mIsXrFsm=false;p.mIsVerticalTabsHiddenDueToNarrow=true;p.updateToolbarSceneLayerSuppression();
                p.setArcToolbarSceneLayerSuppressed(true);p.setArcToolbarSceneLayerSuppressed(false);
                check(p.mSuppressToolbarSceneLayerSupplier.value,"MOBILE must preserve narrow suppression");
                p.mIsVerticalTabsHiddenDueToNarrow=false;p.updateToolbarSceneLayerSuppression();
                check(!p.mSuppressToolbarSceneLayerSupplier.value,"MOBILE restores overlay after other reasons clear");
                p.setArcToolbarSceneLayerSuppressed(true);p.setArcToolbarSceneLayerSuppressed(false);
                check(!p.mSuppressToolbarSceneLayerSupplier.value,"destroy release cannot leave ARC ownership");
            }
        }'''.replace('SETTER', setter).replace('UPDATE', update)
        run_java(self, program, 'OverlayOwnership')

    def test_focus_cannot_unclip_arc_scroll_viewport_or_sibling_tabs(self):
        source = (ROOT / '.source-modified' / BAR_REL).read_text()
        body = clipping_body(source)
        layout = method_body(source, r'void updateLayoutAndBackground\(')
        focus = '\n'.join(re.findall(r'(?:ViewUtils\.setAncestorsShouldClip(?:ToPadding|Children)\(this, false, View.NO_ID\)|setExpansionAncestorClipping\(false\));', layout))
        blur = '\n'.join(re.findall(r'(?:ViewUtils\.setAncestorsShouldClip(?:ToPadding|Children)\(this, true, View.NO_ID\)|setExpansionAncestorClipping\(true\));', layout))
        expansion = method_body(source, re.escape('private @Nullable View getExpansionContainerView()'))
        program = '''class FocusClipping {
            static class View {static final int NO_ID=-1;Object parent;Object getParent(){return parent;}}
            static class ViewGroup extends View {
                boolean children=true,padding=true;
                void setClipChildren(boolean v){children=v;}void setClipToPadding(boolean v){padding=v;}
            }
            static class ScrollView extends ViewGroup {}
            static class ViewUtils {
                static void setAncestorsShouldClipToPadding(ViewGroup p,boolean c,int id){while(p!=null){p.padding=c;p=p.parent instanceof ViewGroup g?g:null;}}
                static void setAncestorsShouldClipChildren(ViewGroup p,boolean c,int id){while(p!=null){p.children=c;p=p.parent instanceof ViewGroup g?g:null;}}
            }
            static class Bar extends ViewGroup {
                View mHolder,mContainerView;boolean mIsReparentedToPopover;
                private View getExpansionContainerView() EXPANSION
                private void setExpansionAncestorClipping(boolean clip) BODY
                void focus(){FOCUS}void blur(){BLUR}
            }
            static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
            public static void main(String[] args){
                ViewGroup root=new ViewGroup(),header=new ViewGroup(),toolbar=new ViewGroup();ScrollView viewport=new ScrollView();
                Bar b=new Bar();b.mHolder=new ViewGroup();b.mContainerView=toolbar;
                b.parent=b.mHolder;b.mHolder.parent=header;header.parent=viewport;viewport.parent=root;
                b.focus();
                check(viewport.children&&viewport.padding,"focused ARC header cannot draw below its 243px viewport into tabs");
                check(root.children&&root.padding,"focus must not alter coordinator clipping or its sibling dropdown");
                check(!b.children&&!header.children,"native URL expansion inside ARC header stays available");
                b.blur();check(b.children&&header.children,"blur restores inner clipping");
                b.mHolder.parent=toolbar;toolbar.parent=root;b.focus();
                check(!toolbar.children&&!root.children,"MOBILE keeps native full ancestor expansion");
                b.blur();
                b.mHolder.parent=header;b.mIsReparentedToPopover=true;b.focus();
                check(!viewport.children&&!root.children,"popover keeps native floating expansion contract");
            }
        }'''.replace('EXPANSION', expansion).replace('BODY', body).replace('FOCUS', focus).replace('BLUR', blur)
        run_java(self, program, 'FocusClipping')

    def test_focus_clipping_helper_compiles_with_android_sdk37(self):
        source = (ROOT / '.source-modified' / BAR_REL).read_text()
        program = '''import android.content.Context;import android.view.View;import android.view.ViewGroup;
            import android.widget.FrameLayout;import android.widget.ScrollView;
            class FocusClippingSdk extends FrameLayout {
                View mHolder,mContainerView;boolean mIsReparentedToPopover;
                FocusClippingSdk(Context c){super(c);}
                private View getExpansionContainerView() EXPANSION
                private void setExpansionAncestorClipping(boolean clip) BODY
                static class ViewUtils {
                    static void setAncestorsShouldClipToPadding(ViewGroup p,boolean clip,int id){}
                    static void setAncestorsShouldClipChildren(ViewGroup p,boolean clip,int id){}
                }
            }'''.replace('EXPANSION', method_body(source, re.escape('private @Nullable View getExpansionContainerView()'))).replace('BODY', clipping_body(source))
        run_java(self, program, 'FocusClippingSdk', sdk=True)
