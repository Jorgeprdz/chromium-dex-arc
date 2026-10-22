#!/usr/bin/env python3
"""Delivered phone views/menu on Android; native container/controller/actions remain explicit boundaries."""
import argparse
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
sources=[arc/'ArcPhoneNavigation.java',ROOT/'chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcPhoneNavigationTest.java']
contracts=definitions();contracts.update({'org.chromium.base.Callback':'public interface Callback<T>{void onResult(T value);}', 'org.chromium.build.annotations.Nullable':'@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE,java.lang.annotation.ElementType.METHOD}) public @interface Nullable {}'})
strings=sorted(set(re.findall(r'R.string.(\w+)',sources[0].read_text())))
contracts['org.chromium.chrome.R']='public class R {public static class string {'+''.join('public static final int '+s+'=android.R.string.ok;' for s in strings)+'}}'
for name,body in contracts.items():
 package,cls=name.rsplit('.',1);file=a.work/(cls+'.java');file.write_text('package '+package+';'+body);sources.append(file)
cp=a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,sources)],check=True)
result=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','org.chromium.chrome.browser.arc.ArcPhoneNavigationTest'])
print('SCOPE=REAL_ANDROID_VIEWS; NATIVE_BOTTOM_CONTAINER_CONTROLLER_ACTIONS_MOCKED; NOT_DEVICE_ACCEPTANCE')
raise SystemExit(result.returncode)
