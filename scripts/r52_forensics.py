#!/usr/bin/env python3
"""Offline fixture pixel oracle and explicit, bounded Android metadata capture.

No navigation, input injection, installation, graphics flags, raw Logcat persistence
or supervisor mutation. PIXEL_MATCH certifies only the supplied image regions.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from PIL import Image, ImageChops

PACKAGE = 'app.archium.android'
VIEW = re.compile(r'(?P<class>[\w.$]+)\{(?P<id>[0-9a-f]+)\s+(?P<flags>[A-Z.]+)\s+[A-Z.]+\s+(?P<l>-?\d+),(?P<t>-?\d+)-(?P<r>-?\d+),(?P<b>-?\d+)(?:[^}\n]*?\s(?P<resource>app:id/[\w_]+))?[^}\n]*\}')


def parse_views(text):
    result = []
    for match in VIEW.finditer(text):
        d = match.groupdict(); flags = d['flags']
        result.append(dict(kind=d['class'], view_id=d['id'], resource=d['resource'],
            bounds=[int(d[k]) for k in ('l','t','r','b')],
            visibility={'V':'VISIBLE','G':'GONE','I':'INVISIBLE'}.get(flags[0],'UNKNOWN'),
            flags=flags, z='NOT_AVAILABLE', elevation='NOT_AVAILABLE',
            window_token='NOT_AVAILABLE_FROM_VIEW_DUMP'))
    return result[:600]


def dialog_observation(rows):
    matches=[r for r in rows if r['resource']=='app:id/tab_modal_dialog_container']
    if not matches:return dict(state='UNKNOWN',cause='NOT_PROVEN')
    r=matches[-1];l,t,right,bottom=r['bounds']
    state='CONTAINER_GONE_ZERO_BOUNDS' if r['visibility']=='GONE' and (right<=l or bottom<=t) else 'CONTAINER_OBSERVED'
    return dict(state=state,cause='NOT_PROVEN',container=r,
        note='A closed container may be GONE/zero; synchronize with an active open event.')


def gpu_events(text):
    result=[]
    patterns=[('CONTEXT_LOST',r'context.?lost'),('FENCE_TIMEOUT',r'fence.*timeout'),
              ('SURFACE_LIFECYCLE',r'surfaceCreated|surfaceDestroyed|surfaceChanged'),
              ('BUFFER_QUEUE',r'BufferQueue'),('GPU_ERROR',r'VK_ERROR_[A-Z_]+|EGL_[A-Z_]+|GL_[A-Z_]+')]
    for line in text.splitlines():
        for kind,pattern in patterns:
            match=re.search(pattern,line,re.I)
            if match:
                code=re.search(r'VK_ERROR_[A-Z_]+|EGL_[A-Z_]+|GL_[A-Z_]+',line)
                stamp=re.match(r'(\d\d-\d\d \d\d:\d\d:\d\d\.\d+)',line)
                result.append(dict(kind=kind,code=code.group() if code else kind,
                    timestamp=stamp.group(1) if stamp else 'UNKNOWN'))
                break
    return result[:300]


def window_metadata(text):
    # Export handles and numeric fields only. Window titles, URLs and intents are dropped.
    out=[]
    for block in re.split(r'(?=  Window #\d+)',text):
        head=block.splitlines()[0] if block.splitlines() else ''
        if PACKAGE not in head:continue
        identifier=re.search(r'Window\{([0-9a-f]+)',head)
        row=dict(window_id=identifier.group(1) if identifier else 'UNKNOWN')
        for key,pattern in {'display_id':r'mDisplayId=(\d+)',
                'has_surface':r'mHasSurface=(true|false)',
                'view_visibility':r'mViewVisibility=(0x[0-9a-f]+)',
                'alpha':r'\balpha=([\d.]+)', 'dim_amount':r'\bdim=([\d.]+)',
                'token_handle':r'WindowToken\{([0-9a-f]+)',
                'frame':r'mFrame=(\[-?\d+,-?\d+\]\[-?\d+,-?\d+\])'}.items():
            m=re.search(pattern,block);row[key]=m.group(1) if m else 'NOT_AVAILABLE'
        row['surface_z']='NOT_AVAILABLE_FROM_WINDOW_DUMP'
        out.append(row)
    return out[:20]


def compare_pixels(reference,candidate,regions,tolerance=3,max_changed_fraction=0.001):
    if not 0<=tolerance<=255 or not 0<=max_changed_fraction<=1:raise ValueError('Invalid comparison thresholds')
    with Image.open(reference) as ref,Image.open(candidate) as current:
        if ref.format!='PNG' or current.format!='PNG':raise ValueError('Lossless PNG screenshots required')
        if ref.width*ref.height>16_000_000:raise ValueError('Screenshot exceeds 16M pixel bound')
        if ref.size!=current.size:raise ValueError('BLOCKED: screenshot dimensions differ; map viewport/DPR first')
        if not regions:raise ValueError('Explicit fixture-only regions required')
        metrics=[]
        for box in regions:
            if len(box)!=4 or any(type(v) is not int for v in box):raise ValueError('Integer image-pixel bounds required')
            l,t,r,b=box
            if not 0<=l<r<=ref.width or not 0<=t<b<=ref.height:raise ValueError('BLOCKED: crop outside screenshot')
            diff=ImageChops.difference(ref.crop(box).convert('RGB'),current.crop(box).convert('RGB'))
            red,green,blue=diff.split()
            maxima=ImageChops.lighter(ImageChops.lighter(red,green),blue)
            histogram=maxima.histogram()
            fraction=sum(histogram[tolerance+1:])/sum(histogram)
            largest=next(i for i in range(255,-1,-1) if histogram[i])
            metrics.append(dict(region=box,changed_fraction=fraction,max_channel_delta=largest))
        return dict(status='PIXEL_MISMATCH' if any(m['changed_fraction']>max_changed_fraction for m in metrics) else 'PIXEL_MATCH',
            scope='SUPPLIED_FIXTURE_REGIONS_ONLY_NOT_ANDROID_OR_PRODUCT_PASS',regions=metrics,
            reference_sha256=hashlib.sha256(Path(reference).read_bytes()).hexdigest(),
            candidate_sha256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest())


def validate_capture(serial,samples,interval):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}',serial):raise ValueError('Explicit authorized ADB serial required')
    if not 1<=samples<=5 or not 0.5<=interval<=5 or samples*interval>25:raise ValueError('Capture exceeds sample/time bounds')


def collect(serial,output,event,samples=3,interval=1):
    validate_capture(serial,samples,interval)
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',event):raise ValueError('Use a synthetic incident label; no page/user text')
    if output.exists():raise ValueError('Use a fresh output directory; never overwrite evidence')
    output.mkdir(parents=True,mode=0o700)
    deadline=time.monotonic()+30
    def adb(*args):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('Capture reached 30-second wall limit')
        r=subprocess.run(['adb','-s',serial,*args],capture_output=True,text=True,timeout=min(5,remaining))
        if r.returncode:raise RuntimeError('ADB command unavailable: '+args[0])
        if len(r.stdout)>4_000_000:raise RuntimeError('Metadata response exceeds bound')
        return r.stdout
    if adb('get-state').strip()!='device':raise ValueError('Authorized device unavailable')
    processes=adb('shell','ps','-A','-o','PID,NAME')
    pids=[]
    for line in processes.splitlines():
        fields=line.split()
        if len(fields)==2 and fields[0].isdigit() and (fields[1]==PACKAGE or fields[1].startswith(PACKAGE+':')):pids.append(fields[0])
    if not pids:raise ValueError('Archium is not running; collector will not launch it')
    records=[]
    for index in range(samples):
        started=time.monotonic()
        row=dict(sample=index,event=event,utc=datetime.now(timezone.utc).isoformat(),
            monotonic_ns=time.monotonic_ns(),pid_count=len(pids))
        views=parse_views(adb('shell','dumpsys','activity',PACKAGE))
        row.update(views=views,dialog=dialog_observation(views),
            windows=window_metadata(adb('shell','dumpsys','window','windows')))
        layers=adb('shell','dumpsys','SurfaceFlinger','--list')
        row['surfaces']=[dict(layer_id=m.group(1),kind='ChromeChildSurface' if 'ChromeChildSurface' in line else 'ARCHIUM_LAYER')
            for line in layers.splitlines() if PACKAGE in line for m in [re.search(r'#(\d+)',line)] if m][:40]
        row['gpu_events']=[]
        for pid in pids[:6]:row['gpu_events'].extend(gpu_events(adb('logcat','--pid='+pid,'-d','-t','120','-v','threadtime')))
        row['limitations']=['No cross-process atomic snapshot','No SurfaceControl z/elevation proof',
            'No browser-controls provider/animation state without in-process trace',
            'Logcat is retrospective; absence of matched errors does not clear GPU']
        records.append(row)
        (output/('sample-'+str(index)+'.json')).write_text(json.dumps(row,indent=2)+'\n')
        if index+1<samples:time.sleep(max(0,interval-(time.monotonic()-started)))
    summary=dict(event=event,samples=len(records),android_execution='DIAGNOSTIC_CAPTURE_ONLY_NO_PASS',
        raw_logcat_saved=False,raw_view_text_saved=False,trace_executed=False)
    (output/'capture.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    c=sub.add_parser('collect');c.add_argument('--serial',required=True);c.add_argument('--output',type=Path,required=True)
    c.add_argument('--event',required=True);c.add_argument('--samples',type=int,default=3);c.add_argument('--interval',type=float,default=1)
    c=sub.add_parser('compare');c.add_argument('--reference',type=Path,required=True);c.add_argument('--candidate',type=Path,required=True)
    c.add_argument('--regions',type=Path,required=True,help='JSON image-pixel rectangle array; same viewport, DPR and fixture phase')
    c.add_argument('--tolerance',type=int,default=3);c.add_argument('--max-changed-fraction',type=float,default=0.001)
    a=p.parse_args()
    if a.mode=='collect':result=collect(a.serial,a.output,a.event,a.samples,a.interval)
    else:result=compare_pixels(a.reference,a.candidate,json.loads(a.regions.read_text()),a.tolerance,a.max_changed_fraction)
    print(json.dumps(result,indent=2));return 1 if result.get('status')=='PIXEL_MISMATCH' else 0


if __name__=='__main__':raise SystemExit(main())
