#!/usr/bin/env python3
"""Complete R5 Android helpers on Robolectric; Chromium Tab is an explicit adapter."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARC = Path('chrome/android/java/src/org/chromium/chrome/browser/arc')
JUNIT = Path('chrome/android/junit/src/org/chromium/chrome/browser/arc')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--classpath-file', type=Path, required=True)
    p.add_argument('--java-home', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--navigation-only', action='store_true')
    p.add_argument('--command-source-ref', help='Countercheck current input regressions against an older command bar')
    p.add_argument('--mutation', choices=['sidebar-order', 'actions-enter', 'rtl', 'closing'])
    a = p.parse_args()
    classes = a.work / 'classes'
    classes.mkdir(parents=True, exist_ok=True)
    adapters = {
        'Tab.java': 'package org.chromium.chrome.browser.tab; public interface Tab { boolean canGoBack(); boolean canGoForward(); boolean isDestroyed(); void goBack(); void goForward(); void reload(); void addObserver(TabObserver o); void removeObserver(TabObserver o); }',
        'TabObserver.java': 'package org.chromium.chrome.browser.tab; public interface TabObserver { default void onUrlUpdated(Tab t){} default void onNavigationEntriesDeleted(Tab t){} default void onLoadStarted(Tab t,boolean different){} default void onLoadStopped(Tab t,boolean different){} default void onHidden(Tab t,int type){} default void onDestroyed(Tab t){} }',
    }
    sources = []
    for name, contents in adapters.items():
        path = a.work / name
        path.write_text(contents)
        sources.append(str(path))
    names = ['ArcNavigationControls']
    if not a.navigation_only:
        sources.append(str(ROOT / 'chromium' / ARC / 'ArcPhoneGlass.java'))
        names += ['ArcOmniboxPlacement', 'ArcCommandBar', 'ArcSplitState']
    for name in names:
        production = ROOT / 'chromium' / ARC / (name + '.java')
        if a.command_source_ref and name == 'ArcCommandBar':
            original = subprocess.check_output(['git', 'show', a.command_source_ref + ':chromium/' + str(ARC / 'ArcCommandBar.java')], cwd=ROOT, text=True)
            production = a.work / 'countercheck' / 'ArcCommandBar.java'
            production.parent.mkdir(parents=True, exist_ok=True)
            production.write_text(original)
        if a.mutation:
            contents = production.read_text()
            if a.mutation == 'sidebar-order' and name == 'ArcOmniboxPlacement':
                contents = contents.replace('Math.min(index, destination.getChildCount())', 'destination.getChildCount()')
            if a.mutation == 'actions-enter' and name == 'ArcCommandBar':
                contents = contents.replace('(mSelected >= 0 || mActions)', 'mSelected >= 0')
            if a.mutation == 'rtl' and name == 'ArcCommandBar':
                contents = contents.replace('Gravity.LEFT | Gravity.TOP', '-1')
            if a.mutation == 'closing' and name == 'ArcCommandBar':
                contents = contents.replace('if (!animated) { cancelAnimator(); finishClose(after); }', '')
            production = a.work / (name + '.java')
            production.write_text(contents)
        sources += [str(production), str(ROOT / 'chromium' / JUNIT / (name + 'Test.java'))]
    test_classes = ['org.chromium.chrome.browser.arc.' + n + 'Test' for n in names]
    if not a.navigation_only:
        # Use the delivered method body on real Android Views. No native autocomplete claims.
        import sys
        sys.path.insert(0, str(ROOT / 'tests'))
        from arc_toolbar_probe import method_body
        container = (ROOT / '.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/suggestions/OmniboxSuggestionsContainer.java').read_text()
        body = method_body(container, r'private void adjustHorizontalPosition\(')
        probe = a.work / 'ArcSuggestionBoundsProbe.java'
        probe.write_text('''package org.chromium.chrome.browser.arc;
import static org.junit.Assert.*;
import android.app.Activity; import android.graphics.Rect; import android.view.View;
import android.widget.FrameLayout;
import org.junit.Test; import org.junit.runner.RunWith; import org.robolectric.*;
import org.robolectric.annotation.*;
@RunWith(RobolectricTestRunner.class) @Config(manifest=Config.NONE,sdk={30,36})
@GraphicsMode(GraphicsMode.Mode.LEGACY) @SQLiteMode(SQLiteMode.Mode.LEGACY)
public class ArcSuggestionBoundsProbe {
 static class Container extends FrameLayout {
  Rect mArcCommandBounds; static class Alignment {int left;} Alignment mOmniboxAlignment=new Alignment();
  Container(Activity a){super(a);} void adjustHorizontalPosition() BODY
 }
 @Test public void windowTargetSurvivesParentRailOffsetsAndRepeatedUpdates(){
  var controller=Robolectric.buildActivity(Activity.class).setup();Activity a=controller.get();
  FrameLayout root=new FrameLayout(a), rail=new FrameLayout(a);Container c=new Container(a);
  root.addView(rail);rail.addView(c);a.setContentView(root);
  root.layout(0,0,1000,800);c.mArcCommandBounds=new Rect(320,140,900,500);
  for(int offset:new int[]{216,52,280,52,216}) {
   rail.layout(offset,0,1000,800);c.layout(12,0,500,360);
   c.adjustHorizontalPosition();c.adjustHorizontalPosition();
   int[] location=new int[2];c.getLocationInWindow(location);assertEquals(320,location[0]);
  }
  c.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);c.adjustHorizontalPosition();
  int[] location=new int[2];c.getLocationInWindow(location);assertEquals(320,location[0]);
  c.mArcCommandBounds=null;c.mOmniboxAlignment.left=8;c.adjustHorizontalPosition();
  assertEquals(8f,c.getTranslationX(),0f);controller.pause().stop().destroy();
 }
}'''.replace('BODY', body))
        sources.append(str(probe))
        test_classes.append('org.chromium.chrome.browser.arc.ArcSuggestionBoundsProbe')
    cp = a.classpath_file.read_text().strip()
    subprocess.run([str(a.java_home / 'bin/javac'), '-cp', cp, '-d', str(classes), *sources], check=True)
    result = subprocess.run([str(a.java_home / 'bin/java'), '-ea',
        '-Drobolectric.conscryptMode=OFF',
        '-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2',
        '-cp', str(classes) + ':' + cp, 'org.junit.runner.JUnitCore',
        *test_classes])
    print('SCOPE=complete_R5_Android_helpers_Tab_adapter_NOT_APK_RUNTIME', flush=True)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
