#!/usr/bin/env python3
"""Prepare/execute one bounded, independent Perfetto session on a manual local fixture.

Default is plan-only. No UI interaction, global trace stop, monitor changes,
background daemon, screenshot, input-event capture or upload.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import uuid
from r52_forensics import validate_capture

CONFIG='''buffers { size_kb: 4096 fill_policy: RING_BUFFER }
duration_ms: 8000
max_file_size_bytes: 8388608
write_into_file: true
data_sources { config { name: "android.surfaceflinger.frametimeline" } }
data_sources { config { name: "linux.ftrace" ftrace_config {
  atrace_categories: "gfx"
  atrace_categories: "view"
  atrace_apps: "app.archium.android"
} } }
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--fixture-confirmed',action='store_true')
    p.add_argument('--raw-logcat-private',action='store_true',help='Original bounded system log buffers, private output only; inspect/redact before sharing')
    a=p.parse_args();validate_capture(a.serial,1,1)
    if a.execute and not a.fixture_confirmed:raise SystemExit('Select only the original local diagnostic fixture before capture')
    if a.output.exists():raise SystemExit('Fresh private output directory required')
    a.output.mkdir(parents=True,mode=0o700)
    remote='/data/misc/perfetto-traces/archium-r52-'+uuid.uuid4().hex+'.pftrace'
    command=['adb','-s',a.serial,'shell','perfetto','--txt','-c','-','-o',remote]
    (a.output/'trace.pbtxt').write_text(CONFIG)
    record=dict(utc=datetime.now(timezone.utc).isoformat(),duration_seconds=8,buffer_kib=4096,
        executed=False,ui_actions=False,remote_trace=remote,
        note='FrameTimeline/atrace availability and permissions must be confirmed from actual output; no runtime PASS.')
    if a.execute:
        try:
            def raw(name):
                tags=['WindowManager:D','SurfaceControl:D','SurfaceFlinger:D','ViewRootImpl:D','RenderThread:D','OpenGLRenderer:D','chromium:I','*:S']
                r=subprocess.run(['adb','-s',a.serial,'logcat','-d','-v','threadtime','-t','600',*tags],capture_output=True,timeout=10)
                target=a.output/name;target.write_bytes(r.stdout);target.chmod(0o600)
                return r.returncode
            if a.raw_logcat_private:record['raw_logcat_before_exit']=raw('before-logcat.PRIVATE.txt')
            result=subprocess.run(command,input=CONFIG,text=True,capture_output=True,timeout=20)
            record['perfetto_exit_code']=result.returncode
            # Never persist arbitrary stderr/system titles in the shareable manifest.
            if result.returncode==0:
                target=a.output/'incident.PRIVATE.pftrace'
                copied=subprocess.run(['adb','-s',a.serial,'pull',remote,str(target)],capture_output=True,timeout=20)
                record['pull_exit_code']=copied.returncode
                if copied.returncode==0:target.chmod(0o600)
            if a.raw_logcat_private:record['raw_logcat_after_exit']=raw('after-logcat.PRIVATE.txt')
            record['executed']=True
            record['status']='CAPTURED' if record.get('perfetto_exit_code')==0 and record.get('pull_exit_code')==0 else 'CAPTURE_BLOCKED'
        except (OSError, subprocess.SubprocessError) as error:
            record.update(status='CAPTURE_BLOCKED', error=type(error).__name__, attempted=True)
    (a.output/'trace-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
    return 0 if not a.execute or record.get('status')=='CAPTURED' else 1


if __name__=='__main__':raise SystemExit(main())
