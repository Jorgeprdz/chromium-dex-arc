#!/usr/bin/env python3
"""Host Robolectric validation of optional metadata helper, never GPU/APK acceptance."""
import argparse
from pathlib import Path
import subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--classpath-file',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
source=Path(__file__).resolve().parents[1]/'tests/fixtures/rendering/r52'
cp=a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(a.work),str(source/'ArcViewProbe.java'),str(source/'ArcViewProbeTest.java')],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(a.work)+':'+cp,'org.junit.runner.JUnitCore','ArcViewProbeTest'])
print('SCOPE=HOST_VIEW_METADATA_ONLY_NOT_CHROMIUM_DIALOG_OR_GPU',flush=True)
raise SystemExit(r.returncode)
