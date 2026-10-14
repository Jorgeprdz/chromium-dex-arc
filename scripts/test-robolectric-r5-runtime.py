#!/usr/bin/env python3
"""Execute delivered command bridge and Fusebox policy bodies with Android views.

Chromium construction/session activation are explicit adapters, not APK runtime.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from arc_toolbar_probe import method_body
from test_r5_native_command_api import native_definition


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classpath-file', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    classes = args.work / 'classes'
    classes.mkdir(exist_ok=True)
    arc = ROOT / 'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
    omnibox = ROOT / '.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox'
    shell = (arc / 'ArcDesktopCoordinator.java').read_text()
    bridge = method_body(shell, r'mCommandBar.setBoundsChangedListener\(\(\) ->')
    rail_layout = method_body(shell, r'mLayoutListener = \(v, l, t, r, b, ol, ot, or, ob\) ->')
    budget = method_body((arc / 'ArcCollectionsView.java').read_text(), r'void setBudget\(')
    mediator = (omnibox / 'LocationBarMediator.java').read_text()
    reparent = method_body(mediator, r'private void updateReparentingState\(')
    activation = method_body(mediator, r'session.activate\(')
    initial_input = activation[:activation.index('                    var editingTextSelection =')] + '}'
    alignment = method_body((omnibox / 'OmniboxSuggestionsDropdownEmbedderImpl.java').read_text(), r'if \(commandLocation instanceof LocationBarLayout locationBar')
    layout = args.work / 'LocationBarLayout.java'
    layout.write_text('package org.chromium.chrome.browser.omnibox;\n' + native_definition((omnibox / 'LocationBarLayout.java').read_text()))
    nullable = args.work / 'Nullable.java'
    nullable.write_text('package org.chromium.build.annotations; @java.lang.annotation.Target(java.lang.annotation.ElementType.TYPE_USE) public @interface Nullable {}')
    fixture = args.work / 'CommandRuntimeProbe.java'
    fixture.write_text(r'''
import static org.junit.Assert.*;
import android.app.Activity;
import android.graphics.Rect;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import org.junit.Test;
import org.junit.After;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.*;
import org.chromium.chrome.browser.omnibox.LocationBarLayout;
class R { static class id { static final int location_bar=10, omnibox_suggestions_dropdown=11; } }
@interface FuseboxLayoutMode { int SUGGESTIONS_POPOVER=1; }
class DisplayState { static final int SUGGESTIONS=3; }
@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY)
@SQLiteMode(SQLiteMode.Mode.LEGACY)
public class CommandRuntimeProbe {
    final java.util.List<org.robolectric.android.controller.ActivityController<Activity>> activities=new java.util.ArrayList<>();
    Activity activity(){var controller=Robolectric.buildActivity(Activity.class).setup();activities.add(controller);return controller.get();}
    @After public void teardown(){for(var controller:activities)controller.pause().stop().destroy();org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();}
    static class Command {
        boolean showing=true;
        boolean isShowing(){return showing;} boolean isActions(){return false;}
        Rect resultsBoundsInWindow(){return new Rect(500,120,1100,400);}
        void commitNativeNavigation(){} void close(boolean animated,Runnable after){showing=false;}
    }
    static class Shell {
        final Activity mActivity;
        final View mFrameRoot;
        final FrameLayout mLocationBarHost;
        final View location;
        final Command mCommandBar=new Command();
        Shell(Activity a,FrameLayout root,FrameLayout holder,View nativeBar){
            mActivity=a;mFrameRoot=root;mLocationBarHost=holder;location=nativeBar;
        }
        void boundsChanged() BRIDGE
    }
    static class Input {
        String text="page.example/",initial="page.example/";
        Object preview=new Object();
        int getDisplayState(){return DisplayState.SUGGESTIONS;}
        Input setInitialInput(String value,Object preview){initial=value;return this;}
        Input setUserText(String value){text=value;return this;}
        void setPreviewMatchUrl(Object value){preview=value;}
    }
    static class Supplier { int get(){return FuseboxLayoutMode.SUGGESTIONS_POPOVER;} }
    static class Fusebox { Supplier getFuseboxLayoutModeSupplier(){return new Supplier();} }
    static class Mediator {
        final Fusebox mFuseboxCoordinator=new Fusebox();
        final LocationBarLayout mLocationBarLayout;
        final Input mCurrentInput=new Input();
        final Object mAutocompleteCoordinator=new Object();
        boolean parented;
        Mediator(LocationBarLayout bar){mLocationBarLayout=bar;}
        boolean isParentedToSuggestionsContainer(){return parented;}
        void reparentToSuggestionsContainer(){parented=true;}
        void reparentToToolbar(){parented=false;}
        void updateReparentingState() REPARENT
        void afterNativeSessionActivation(boolean activateNewSession) INITIAL_INPUT
    }
    @Test public void newCommandStartsEmptyAfterDesktopSessionInjectedThePageUrl() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            LocationBarLayout bar=new LocationBarLayout(a);Mediator mediator=new Mediator(bar);
            bar.setArcCommandBar(new Rect(500,120,1100,400),false,()->{},()->{});
            mediator.afterNativeSessionActivation(true);
            assertEquals("",mediator.mCurrentInput.text);assertEquals("",mediator.mCurrentInput.initial);
            assertNull("Prior origin/preview must not leak into the new command",mediator.mCurrentInput.preview);
            mediator.mCurrentInput.text="unfinished draft";
            mediator.afterNativeSessionActivation(false);assertEquals("unfinished draft",mediator.mCurrentInput.text);
            bar.setArcCommandBar(null,false,null,null);mediator.mCurrentInput.text="page.example/";
            mediator.afterNativeSessionActivation(true);assertEquals("page.example/",mediator.mCurrentInput.text);
        } finally {a.finish();}
    }
    static class Alignment {
        final FrameLayout contentView;
        final View mAnchorView;
        int left,top,width,height,paddingLeft,paddingRight,paddingBottom;
        int windowSpace=800,contentSpace=800;
        Alignment(FrameLayout content,View anchor){contentView=content;mAnchorView=anchor;}
        void align(LocationBarLayout locationBar) ALIGNMENT
    }
    static class Rail {
        final View mRail;
        final org.chromium.chrome.browser.arc.ArcFrameDispatch mAppearanceDispatch = new org.chromium.chrome.browser.arc.ArcFrameDispatch(() -> true);
        boolean mDestroyed;
        Rail(Activity a) {mRail=new View(a);a.setContentView(mRail);}
        void scheduleAppearance() {mAppearanceDispatch.schedule(mRail, () -> {rebindCollections();applyAppearance();});}
        int refreshes;
        void rebindCollections(){refreshes++;} void applyAppearance(){refreshes++;}
        void onLayout(int l,int t,int r,int b,int ol,int ot,int or,int ob) RAIL_LAYOUT
    }
    static class Budget extends android.widget.ScrollView {
        int mBudget=-1;Budget(Activity a){super(a);}void setBudget(int pixels) BUDGET
    }
    @Test public void stableRailBoundsAndCollectionBudgetDoNotScheduleAnotherFrame() {
        Rail rail=new Rail(activity());rail.onLayout(0,0,216,800,0,0,216,800);assertEquals(0,rail.refreshes);
        rail.onLayout(0,0,52,800,0,0,216,800);
        assertEquals("Do not mutate navigation during a layout pass",0,rail.refreshes);
        org.robolectric.Shadows.shadowOf(android.os.Looper.getMainLooper()).idle();
        assertEquals(2,rail.refreshes);
    }
    @Test public void stableCollectionBudgetDoesNotInvalidateTheBrowser() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            Budget scroll=new Budget(a);scroll.setBudget(240);
            scroll.measure(View.MeasureSpec.makeMeasureSpec(200,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(240,View.MeasureSpec.EXACTLY));
            scroll.layout(0,0,200,240);assertFalse(scroll.isLayoutRequested());
            scroll.setBudget(240);assertFalse("Stable budget must not relayout the whole browser",scroll.isLayoutRequested());
            scroll.setBudget(100);assertTrue(scroll.isLayoutRequested());
        } finally {a.finish();}
    }
    @Test public void rtlNativeSuggestionsUseThePanelPhysicalLeftEdge() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            a.getApplicationInfo().flags|=android.content.pm.ApplicationInfo.FLAG_SUPPORTS_RTL;
            FrameLayout root=new FrameLayout(a);View anchor=new View(a);anchor.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
            LocationBarLayout bar=new LocationBarLayout(a);android.widget.EditText editor=new android.widget.EditText(a);
            editor.setId(R.id.url_bar);editor.setText("query");bar.addView(editor);
            root.addView(anchor);root.addView(bar);a.setContentView(root);root.layout(0,0,1200,800);
            anchor.measure(View.MeasureSpec.makeMeasureSpec(984,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(56,View.MeasureSpec.EXACTLY));
            anchor.layout(216,0,1200,56);
            bar.setArcCommandBar(new Rect(500,120,1100,400),false,()->{},()->{});
            Alignment alignment=new Alignment(root,anchor);alignment.align(bar);
            int[] origin=new int[2];anchor.getLocationInWindow(origin);
            assertEquals(500,origin[0]+anchor.getWidth()-alignment.width+alignment.left);
        } finally {a.finish();}
    }
    @Test public void suggestionsSubtractTheNativeSideUiOriginExactlyOnce() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            FrameLayout root=new FrameLayout(a);View anchor=new View(a);
            LocationBarLayout bar=new LocationBarLayout(a);
            android.widget.EditText editor=new android.widget.EditText(a);editor.setId(R.id.url_bar);editor.setText("query");bar.addView(editor);
            root.addView(anchor);root.addView(bar);a.setContentView(root);
            root.layout(0,0,1200,800);anchor.layout(216,0,1200,56);
            bar.setArcCommandBar(new Rect(500,120,1100,400),false,()->{},()->{});
            Alignment alignment=new Alignment(root,anchor);alignment.align(bar);
            int[] anchorWindow=new int[2];anchor.getLocationInWindow(anchorWindow);
            assertEquals("Suggestions already start at the Side UI origin",500,anchorWindow[0]+alignment.left);
            assertEquals(600,alignment.width);assertEquals(280,alignment.height);
        } finally {a.finish();}
    }
    @Test public void closingClearsNativeBridgeEvenAfterFuseboxMovesTheEditor() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            FrameLayout root=new FrameLayout(a),holder=new FrameLayout(a),popover=new FrameLayout(a);
            LocationBarLayout bar=new LocationBarLayout(a);bar.setId(R.id.location_bar);
            root.addView(holder);root.addView(popover);holder.addView(bar);a.setContentView(root);
            Shell shell=new Shell(a,root,holder,bar);shell.boundsChanged();
            assertNotNull(bar.getArcCommandResults());
            holder.removeView(bar);popover.addView(bar);
            shell.mCommandBar.showing=false;shell.boundsChanged();
            assertNull("Cancellation must clear the real native editor, even outside its holder",bar.getArcCommandResults());
            assertFalse("Native endInput must run, rather than delegate to an already closed panel",bar.closeArcCommandBarForInputEnd());
        } finally {a.finish();}
    }
    @Test public void commandKeepsEditorInHeaderWhileNativeAutocompleteRemainsActive() {
        Activity a=Robolectric.buildActivity(Activity.class).setup().get();
        try {
            LocationBarLayout bar=new LocationBarLayout(a);
            Mediator mediator=new Mediator(bar);
            bar.setArcCommandBar(new Rect(500,120,1100,400),false,()->{},()->{});
            mediator.updateReparentingState();
            assertFalse("Command header owns the editor; Fusebox must not move it again",mediator.parented);
            bar.setArcCommandBar(null,false,null,null);
            mediator.updateReparentingState();assertTrue("Normal Ctrl+L keeps upstream popover behavior",mediator.parented);
        } finally {a.finish();}
    }
}
'''.replace('BRIDGE', bridge).replace('REPARENT', reparent).replace('ALIGNMENT', alignment).replace('INITIAL_INPUT', initial_input).replace('RAIL_LAYOUT', rail_layout).replace('BUDGET', budget).replace('omnibox_suggestions_dropdown=11;', 'omnibox_suggestions_dropdown=11,url_bar=12;').replace('Activity a=Robolectric.buildActivity(Activity.class).setup().get();', 'Activity a=activity();'))
    cp = args.classpath_file.read_text().strip()
    subprocess.run([str(args.java_home / 'bin/javac'), '-cp', cp, '-d', str(classes), str(layout), str(arc / 'ArcFrameDispatch.java'), str(nullable), str(fixture)], check=True)
    result = subprocess.run([str(args.java_home / 'bin/java'), '-ea', '-Drobolectric.conscryptMode=OFF', '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2', '-cp', str(classes) + ':' + cp, 'org.junit.runner.JUnitCore', 'CommandRuntimeProbe'])
    print('SCOPE=delivered_native_bridge_and_Fusebox_policy_bodies_NOT_APK_RUNTIME', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
