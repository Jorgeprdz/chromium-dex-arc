#!/usr/bin/env python3
"""Execute pinned click policy and delivered Android forwarding predicates on host, not JNI/GPU."""
import argparse,subprocess,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pinned',type=Path,default=ROOT/'.source-reference');p.add_argument('--work',type=Path,required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
PINNED_SHA256={'ui/base/window_open_disposition.h': '089c25f933c1e28e375f04e888201ae64b9f2ba30556d9e1fe25414cf63c0fbd', 'ui/base/window_open_disposition_utils.cc': 'cbbf39c0931b2290dd9b2fd3608fa578fcdb3751a4bc524e823da7cf6766a81c'}
for name,digest in PINNED_SHA256.items():
 if hashlib.sha256((a.pinned/name).read_bytes()).hexdigest()!=digest:raise ValueError("Pinned click policy changed: "+name)
header=a.pinned/'ui/base/window_open_disposition.h'
for path,body in {
 'build/build_config.h':'#define IS_APPLE 0\n#define BUILDFLAG(x) x\n',
 'ui/base/window_open_disposition_utils.h':'#include "ui/base/window_open_disposition.h"\nnamespace ui {WindowOpenDisposition DispositionFromClick(bool,bool,bool,bool,bool,WindowOpenDisposition);}\n',
 'ui/base/window_open_disposition.h':header.read_text(),
 'ui/events/event_constants.h':'namespace ui {enum {EF_MIDDLE_MOUSE_BUTTON=1,EF_ALT_DOWN=2,EF_CONTROL_DOWN=4,EF_COMMAND_DOWN=8,EF_SHIFT_DOWN=16};}\n'
}.items():
 dest=a.work/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(body)
source=(ROOT/'.source-modified/components/embedder_support/android/delegate/web_contents_delegate_android.cc').read_text()
start=source.index('WebContents* WebContentsDelegateAndroid::OpenURLFromTab(');body=source[start:source.index('void WebContentsDelegateAndroid::NavigationStateChanged',start)]
guard=re.search(r'if \((!source.*?)\) \{\s*NOTIMPLEMENTED',body,re.S).group(1)
branch=re.search(r'if \((disposition == WindowOpenDisposition::NEW_FOREGROUND_TAB.*?)\) \{',body,re.S).group(1)
probe='''#include <cassert>
#include "ui/base/window_open_disposition_utils.h"
bool accepted(bool source,WindowOpenDisposition disposition){return !(GUARD);}
bool forwards(WindowOpenDisposition disposition){return BRANCH;}
int main(){using W=WindowOpenDisposition;
 assert(ui::DispositionFromClick(false,true,true,false,false,W::CURRENT_TAB)==W::NEW_SPLIT_VIEW);
 assert(ui::DispositionFromClick(false,false,true,false,false,W::CURRENT_TAB)==W::NEW_BACKGROUND_TAB);
 assert(ui::DispositionFromClick(false,true,false,false,false,W::CURRENT_TAB)==W::SAVE_TO_DISK);
 assert(ui::DispositionFromClick(false,true,true,false,true,W::CURRENT_TAB)==W::NEW_FOREGROUND_TAB);
 assert(accepted(true,W::NEW_SPLIT_VIEW));assert(forwards(W::NEW_SPLIT_VIEW));
 assert(!accepted(false,W::NEW_SPLIT_VIEW));assert(!accepted(true,W::SAVE_TO_DISK));assert(!forwards(W::CURRENT_TAB));
}'''.replace('GUARD',guard).replace('BRANCH',branch)
f=a.work/'probe.cc';f.write_text(probe);exe=a.work/'probe'
subprocess.run(['g++','-std=c++17','-I',str(a.work),str(a.pinned/'ui/base/window_open_disposition_utils.cc'),str(f),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
print('PASS pinned click policy + actual Android forwarding predicates; JNI/full Chromium pending')
