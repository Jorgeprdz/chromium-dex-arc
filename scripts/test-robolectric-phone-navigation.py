#!/usr/bin/env python3
"""Delivered phone views, glass and Desktop Command Bar; native boundaries remain explicit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from phone_native_boundaries import definitions
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);classes=a.work/'classes';classes.mkdir(exist_ok=True)
arc=ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc'
sources=[ROOT/'.source-modified/chrome/browser/ui/android/theme/java/src/org/chromium/chrome/browser/theme/ToolbarThemeColorProvider.java',arc/'ArcPhoneNavigation.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcPhoneNavigationTest.java']
sources += [arc/'ArcPhoneGlass.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcPhoneGlassTest.java']
sources += [arc/'ArcCommandBar.java',arc/'ArcOmniboxPlacement.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcCommandBarTest.java']
# Compile the unmodified pinned refresh widget, not a reimplementation of its trigger policy.
pinned_refresh=ROOT/'tests/pinned/swiperefresh'
refresh_manifest=json.loads((pinned_refresh/'manifest.json').read_text())
assert refresh_manifest['revision']==json.loads((ROOT/'patches/upstream-files.json').read_text())['revision']
for name,digest in refresh_manifest['files'].items():
    source=pinned_refresh/Path(name).name
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest, name
    sources.append(source)
sources += [arc/'ArcPhonePullReveal.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcPhonePullRevealTest.java']
sources += [arc/'ArcPhoneStatusFade.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcPhoneStatusFadeTest.java']
sources += [arc/'ArcDesktopMaterial.java',arc/'ArcDesktopMaterialDialog.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcDesktopMaterialTest.java']
# Only annotation/easing dependencies are local boundaries; native refresh state/threshold is real.
contracts=definitions();contracts['androidx.annotation.ColorRes']='public @interface ColorRes {}';contracts['androidx.interpolator.view.animation.FastOutSlowInInterpolator']='public final class FastOutSlowInInterpolator implements android.view.animation.Interpolator {private final android.view.animation.PathInterpolator curve=new android.view.animation.PathInterpolator(.4f,0f,.2f,1f);public float getInterpolation(float value){return curve.getInterpolation(value);}}';contracts.pop('org.chromium.chrome.browser.theme.ThemeColorProvider');contracts.update({'org.chromium.chrome.browser.tab.Tab':'public class Tab {}','androidx.annotation.ColorInt':'@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.METHOD,java.lang.annotation.ElementType.PARAMETER,java.lang.annotation.ElementType.FIELD,java.lang.annotation.ElementType.LOCAL_VARIABLE}) public @interface ColorInt {}','org.chromium.build.annotations.NullMarked':'public @interface NullMarked {}','org.chromium.base.Callback':'public interface Callback<T>{void onResult(T value);}', 'org.chromium.build.annotations.Nullable':'@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.METHOD}) public @interface Nullable {}'})
strings=sorted(set(re.findall(r'R.string.(\w+)',((arc/'ArcPhoneNavigation.java').read_text()+(arc/'ArcDesktopMaterialDialog.java').read_text()))))
contracts['org.chromium.chrome.R']='public class R {public static class string {'+''.join('public static final int '+s+'=android.R.string.ok;' for s in strings)+'}public static class id {public static final int tab_switcher_button=0x7f010ce0;}}'
for name,body in contracts.items():
 package,cls=name.rsplit('.',1);file=a.work/'boundaries'/(name.replace('.', '/')+'.java');file.parent.mkdir(parents=True,exist_ok=True);file.write_text('package '+package+';'+body);sources.append(file)
sources += [ROOT/'tests/fixtures/chromium-junit/ThemeColorProvider.java',
            ROOT/'tests/fixtures/chromium-junit/TestListComputer.java',
            ROOT/'tests/fixtures/chromium-junit/Allowlist.java',
            ROOT/'tests/java/PhoneNativeShadowPolicyProbe.java']
cp=a.classpath_file.read_text().strip()
# Chromium's JVM target uses the subclass mock maker; do not rely on local inline-only APIs.
plugins=a.work/'mock-maker';extension=plugins/'mockito-extensions/org.mockito.plugins.MockMaker'
extension.parent.mkdir(parents=True,exist_ok=True);extension.write_text('mock-maker-subclass\n')
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,sources)],check=True)
subprocess.run([str(a.java_home/'bin/java'),'-cp',str(classes)+':'+cp,
                'org.chromium.testing.local.PhoneNativeShadowPolicyProbe',
                str(ROOT/'tests/fixtures/chromium-junit/shadows-allowlist.txt')],check=True)
result=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(plugins)+':'+str(classes)+':'+cp,'org.junit.runner.JUnitCore','org.chromium.chrome.browser.arc.ArcPhoneNavigationTest','org.chromium.chrome.browser.arc.ArcPhoneGlassTest','org.chromium.chrome.browser.arc.ArcCommandBarTest','org.chromium.chrome.browser.arc.ArcDesktopMaterialTest','org.chromium.chrome.browser.arc.ArcPhoneStatusFadeTest','org.chromium.chrome.browser.arc.ArcPhonePullRevealTest'])
print('SCOPE=REAL_ANDROID_VIEWS; NATIVE_BOTTOM_CONTAINER_CONTROLLER_ACTIONS_MOCKED; NOT_DEVICE_ACCEPTANCE')
raise SystemExit(result.returncode)
