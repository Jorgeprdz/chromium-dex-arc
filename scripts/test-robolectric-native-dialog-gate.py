#!/usr/bin/env python3
"""Exercise delivered presenter methods with real Android views and explicit JNI/resource adapters.

Pinned upstream sources are supplied separately, never a Chromium checkout/build.
This is not installed-APK, WindowManager, QEMU or GPU validation.
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
CHROME='chrome/android/java/src/org/chromium/chrome/browser/modaldialog/ChromeTabModalPresenter.java'
BASE='components/browser_ui/modaldialog/android/java/src/org/chromium/components/browser_ui/modaldialog/TabModalPresenter.java'
MANAGER='chrome/android/java/src/org/chromium/chrome/browser/fullscreen/BrowserControlsManager.java'
UTIL='chrome/browser/browser_controls/android/java/src/org/chromium/chrome/browser/browser_controls/BrowserControlsUtils.java'
JS='components/javascript_dialogs/android/java/src/org/chromium/components/javascript_dialogs/JavascriptModalDialog.java'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--pinned-source-dir',type=Path,required=True);p.add_argument('--classpath-file',type=Path,required=True)
p.add_argument('--java-home',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
p.add_argument('--baseline',action='store_true',help='Use pinned unmodified presenter for the RED control')
a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
catalog=json.loads((ROOT/'tests/fixtures/rendering/r52b/upstream-sources.json').read_text())
texts={k:(a.pinned_source_dir/k).read_text() for k in (CHROME,BASE,MANAGER,UTIL,JS)}
for path,text in texts.items():
 if hashlib.sha256(text.encode()).hexdigest()!=catalog['files'][path]:
  raise SystemExit('BLOCKED_UPSTREAM_SOURCE_HASH: '+path)
if not a.baseline:
 for path in (CHROME,JS):
  if (ROOT/'.source-modified'/path).exists():texts[path]=(ROOT/'.source-modified'/path).read_text()
def extract(src,result,name,params,access='public'):
 return access+' '+result+' '+name+'('+params+') '+method_body(src,r'\b'+re.escape(result)+r'\s+'+re.escape(name)+r'\s*\(')
chrome=[('void','showDialogContainer',''),('void','onControlsOffsetChanged','int topOffset,int topControlsMinHeightOffset,boolean topControlsMinHeightChanged,int bottomOffset,int bottomControlsMinHeightOffset,boolean bottomControlsMinHeightChanged,boolean requestNewFrame,boolean isVisibilityForced'),('void','onTopControlsHeightChanged','int topControlsHeight,int topControlsMinHeight'),('void','onBottomControlsHeightChanged','int bottomControlsHeight,int bottomControlsMinHeight')]
for name in ('areBrowserControlsReadyForDialog','maybeRunPendingEnterAnimation'):
 if re.search(r'\b(?:boolean|void) '+name+r'\(',texts[CHROME]):chrome.append(('boolean' if name.startswith('are') else 'void',name,''))
if 'public void onControlsPositionChanged(' in texts[CHROME]:chrome.append(('void','onControlsPositionChanged','int controlsPosition'))
# Trace metadata is a delivered method, compiled unchanged; privacy behavior is tested below.
if 'private void traceDialogState(' in texts[CHROME]:chrome.append(('void','traceDialogState','String stage'))
if 'protected void runEnterAnimation()' in texts[CHROME]:chrome.append(('void','runEnterAnimation',''))
chrome.append(('void','removeDialogView','PropertyModel model'))
chrome_methods='\n'.join(extract(texts[CHROME],*row) for row in chrome)
manager='\n'.join(extract(texts[MANAGER],result,name,'') for result,name in [('float','getBrowserControlHiddenRatio'),('float','getTopControlHiddenRatio'),('float','getBottomControlHiddenRatio')])
base='\n'.join(extract(texts[BASE],'void',name,'') for name in ['runEnterAnimation','runExitAnimation'])+'\n'+extract(texts[BASE],'void','removeDialogView','PropertyModel model')
js='\n'.join(extract(texts[JS],'void',name,params) for name,params in [('onClick','PropertyModel model,int buttonType'),('onDismiss','PropertyModel model,int dismissalCause')])
if 'private void traceDialogState(' in texts[JS]:js+='\n'+extract(texts[JS],'void','traceDialogState','String stage')
source=(ROOT/'tests/fixtures/rendering/r52b/NativeDialogGateProbe.java.in').read_text().replace('__CHROME__',chrome_methods).replace('__MANAGER__',manager).replace('__BASE__',base).replace('__JS__',js).replace('__UTIL__',extract(texts[UTIL],'boolean','areBrowserControlsFullyVisible','Controls stateProvider','public static'))
f=a.work/'NativeDialogGateProbe.java';f.write_text(source)
(a.work/'source-hashes.json').write_text(json.dumps({k:hashlib.sha256(v.encode()).hexdigest() for k,v in texts.items()},indent=2)+'\n')
cp=a.classpath_file.read_text().strip()
subprocess.run([str(a.java_home/'bin/javac'),'-cp',cp,'-d',str(a.work),str(f)],check=True)
r=subprocess.run([str(a.java_home/'bin/java'),'-ea','-Drobolectric.conscryptMode=OFF','-Drobolectric.dependency.repo.url=https://repo.maven.apache.org/maven2','-cp',str(a.work)+':'+cp,'org.junit.runner.JUnitCore','NativeDialogGateProbe'])
print('SCOPE=PINNED_METHODS_REAL_ANDROID_VIEWS; JNI_RESOURCES_CONTROLS_INPUTS_ARE_ADAPTERS; DEVICE=NOT_TESTED',flush=True)
sys.exit(r.returncode)
