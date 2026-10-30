#!/usr/bin/env python3
"""Run the delivered camera PopupMenu on real Android views; native JNI is a boundary."""
from pathlib import Path
import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classpath-file',type=Path,required=True)
    parser.add_argument('--java-home',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    work=args.work
    work.mkdir(parents=True,exist_ok=True)
    labels = {n.attrib['name']: n.text for n in ET.parse(ROOT/'chromium/chrome/android/java/res/values/arc_strings.xml').getroot() if n.tag == 'string' and n.attrib['name'].startswith('arc_camera_')}
    fields = ''.join(f'public static final int {name}={0x7f010000+i};' for i, name in enumerate(labels))
    values = ','.join(f'Map.entry(string.{name},{json.dumps(value, ensure_ascii=False)})' for name,value in labels.items())
    boundaries = {
        'org.chromium.chrome.R': f'public class R {{public static class string {{{fields}}} public static final java.util.Map<Integer,String> labels=java.util.Map.ofEntries({values});}}',
        'org.chromium.build.annotations.NullMarked': 'public @interface NullMarked {}',
        'org.chromium.build.annotations.Nullable': 'public @interface Nullable {}',
        'org.chromium.content_public.browser.WebContents': 'public class WebContents {public int turns=1;public boolean destroyed;public boolean isDestroyed(){return destroyed;}}',
        'org.chromium.chrome.browser.content.ContentUtils': 'public class ContentUtils {public static int getArcCameraOrientation(org.chromium.content_public.browser.WebContents tab){return tab.turns;}public static void setArcCameraOrientation(org.chromium.content_public.browser.WebContents tab,int turns){tab.turns=turns;}}',
    }
    sources = [ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCameraControls.java', ROOT/'tests/java/ArcCameraControlsHostTest.java']
    for name, body in boundaries.items():
        package, _ = name.rsplit('.',1)
        source = work/(name.replace('.', '/')+'.java')
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('package '+package+';import java.util.Map;'+body)
        sources.append(source)
    classes = work/'classes'
    classes.mkdir(exist_ok=True)
    cp = args.classpath_file.read_text().strip()
    subprocess.run([str(args.java_home/'bin/javac'),'-cp',cp,'-d',str(classes),*map(str,sources)],check=True)
    subprocess.run([str(args.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(classes)+':'+cp,'org.junit.runner.JUnitCore','org.chromium.chrome.browser.arc.ArcCameraControlsHostTest'],check=True)

    print('SCOPE=REAL_ANDROID_POPUP_MENU; JNI_AND_WEB_CONTENTS_ARE_BOUNDARIES; NOT_DEVICE_ACCEPTANCE')

if __name__=='__main__':
    main()
