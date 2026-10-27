#!/usr/bin/env python3
"""Persistent, fail-closed progressive R5 build monitor. Never uses device ADB."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import uuid
import zipfile

REPO = 'Jorgeprdz/chromium-dex-arc'
BRANCH = 'assistant/archium-r5-arc-experience'
WORKFLOW = 'baseline-build.yml'
PIN = 'cfd94726b7b5fb48aedcc32662f2f3fbdbadec35'
INTERVAL = 600
ROOT = Path(__file__).resolve().parent


def load_module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gh(args):
    result = subprocess.run(['gh', *args], text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError('GitHub command failed: ' + ' '.join(args[:2]) + ': ' + result.stderr.strip()[-800:])
    if args[0] == 'api':
        return json.loads(result.stdout) if result.stdout.strip() else None
    return None


def api(path, call=gh):
    return call(['api', f'repos/{REPO}/{path}'])


def all_runs(call=gh):
    runs = []
    for page in range(1, 101):
        batch = api(f'actions/runs?per_page=100&page={page}', call)['workflow_runs']
        runs.extend(batch)
        if len(batch) < 100:
            return runs
    raise ValueError('Run inventory exceeds bounded pagination')


def save_state(folder, state):
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / ('state.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('w') as handle:
        json.dump(state, handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, folder / 'state.json')
    descriptor = os.open(folder, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def acquire_lock(folder):
    folder.mkdir(parents=True, exist_ok=True)
    handle = (folder / 'monitor.lock').open('a+')
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise RuntimeError('Duplicate monitor refused') from None
    handle.seek(0); handle.truncate(); handle.write(str(os.getpid())); handle.flush()
    return handle


def validate_state(state, maximum):
    if not 1 <= maximum <= 12 or not 1 <= int(state['stage']) <= maximum:
        raise ValueError('Invalid stage bound (1..12)')
    for name in ['expected_sha', 'source_commit']:
        if not re.fullmatch('[a-f0-9]{40}', str(state.get(name, ''))):
            raise ValueError('Invalid ' + name)
    for name in ['run_id', 'source_run_id']:
        if not str(state.get(name, '')).isdigit(): raise ValueError('Invalid ' + name)
    if not re.fullmatch(r'archium-checkpoint-\d+-\d+',state.get('source_checkpoint','')):
        raise ValueError('Invalid source checkpoint')


def validate_receipt(receipt, state):
    if receipt.get('schema') != 1:
        raise ValueError('Receipt schema differs')
    for key in ['expected_sha','source_checkpoint','source_commit','source_run_id','run_id']:
        if str(receipt.get(key)) != str(state[key]): raise ValueError('Receipt identity differs: ' + key)
    outcome = receipt.get('outcome')
    if outcome not in ('BUILD_SUCCESS', 'BUILD_INCOMPLETE'):
        raise ValueError('Build failure: ' + str(outcome))
    if outcome == 'BUILD_INCOMPLETE':
        if receipt.get('exit_code') != 0 or any(receipt.get(k) is not True for k in (
                'recoverable','checkpoint_verified','pack_verified')):
            raise ValueError('Incomplete stage lacks verified recoverable receipt')
        if receipt.get('new_checkpoint_commit') != state['expected_sha'] or not re.fullmatch(
                rf'archium-checkpoint-{state["run_id"]}-\d+', receipt.get('new_checkpoint','')):
            raise ValueError('New checkpoint identity differs')
        fingerprint = receipt.get('progress',{}).get('fingerprint')
        if not isinstance(fingerprint,str) or not fingerprint:
            raise ValueError('Missing progress fingerprint')
        if fingerprint == state.get('progress_fingerprint'):
            raise ValueError('STALLED: unchanged checkpoint progress')
    return outcome


def validate_checkpoint(groups, manifest, tag, sha):
    checker = load_module('check-recovery-checkpoint')
    groups = checker.validate_inventory(groups,tag,sha,10**18,10**18)
    checkpoint = load_module('archium-checkpoint')
    workspace = manifest.get('workspace', '')
    # Runner locations are fixed by our build scripts; reject arbitrary manifest identities.
    if workspace not in ('/mnt/archium/chromium-archium','/home/runner/work/_temp/chromium-archium'):
        raise ValueError('Unexpected checkpoint workspace')
    checkpoint.validate_manifest(manifest, dict(schema=1,revision=PIN,commit=sha,tag=tag,workspace=workspace))
    if len(groups) != math.ceil(len(manifest['parts']) / checkpoint.GROUP_SIZE):
        raise ValueError('Checkpoint group count differs from manifest')
    return groups


def validate_incomplete_jobs(jobs, group_count, state):
    sentinel='Reject incomplete budget as a successful build'
    native=[job for job in jobs if any(step['name']=='S2-S4 blocking gates and incremental build'
                                       for step in job.get('steps',[]))]
    if len(native)!=1: raise ValueError('Missing or ambiguous native build job')
    native=native[0]
    required=['S0 source, capacity and bounded checkpoint manifest',
              'S1 download exactly the verified checkpoint groups',
              'S1 restore once and transition patches', 'S2-S4 blocking gates and incremental build']
    required += [f'Preserve checkpoint group {i:02d}' for i in range(group_count)]
    steps={step['name']:step.get('conclusion') for step in native['steps']}
    if any(steps.get(name)!='success' for name in required):
        raise ValueError('Native compiler/gate/checkpoint upload did not succeed')
    for job in jobs:
        conclusion=job.get('conclusion')
        if job.get('status')!='completed': raise ValueError('Incomplete job inventory')
        if job is native:
            if conclusion not in ('success','failure'): raise ValueError('Native stage interrupted')
        elif conclusion=='skipped':
            name=job['name'].lower()
            if 'qemu' not in name and not ('preflight' in name and int(state['stage'])>1):
                raise ValueError('Unexpected skipped prerequisite')
        elif conclusion!='success': raise ValueError('Prerequisite job failed')
        for step in job.get('steps',[]):
            if step.get('conclusion') in ('failure','cancelled','timed_out','action_required'):
                if job is not native or step['name']!=sentinel or step.get('conclusion')!='failure':
                    raise ValueError('Genuine failed compiler/test/infrastructure step')
    if native.get('conclusion')=='failure' and steps.get(sentinel)!='failure':
        raise ValueError('Native failure lacks controlled budget sentinel')


def find_dispatched(state, call=gh):
    nonce = state['dispatch_intent']['nonce']
    matches = [r for r in all_runs(call) if r.get('display_title') == 'Archium R5 ' + nonce
               and r.get('head_sha') == state['expected_sha'] and r.get('head_branch') == BRANCH
               and r.get('event') == 'workflow_dispatch'
               and r.get('path') == '.github/workflows/' + WORKFLOW]
    if len(matches)>1: raise ValueError('Ambiguous duplicate dispatch nonce')
    return str(matches[0]['id']) if matches else None


def dispatch(state, folder, call=gh):
    if 'dispatch_intent' not in state:
        state['dispatch_intent'] = dict(nonce=uuid.uuid4().hex,stage=int(state['stage'])+1,
            source_checkpoint=state.get('next_source_checkpoint',state.get('new_checkpoint')),
            source_commit=state.get('next_source_commit',state['expected_sha']),
            source_run_id=state.get('next_source_run_id',state['run_id']))
        state['status'] = 'DISPATCH_INTENT'
        save_state(folder,state)  # Durable intent MUST precede the potentially ambiguous network mutation.
        args = ['workflow','run',WORKFLOW,'--repo',REPO,'--ref',BRANCH]
        intent=state['dispatch_intent']
        fields = dict(expected_sha=state['expected_sha'],source_checkpoint=intent['source_checkpoint'],
                      source_commit=intent['source_commit'],source_run_id=intent['source_run_id'],
                      dispatch_id=intent['nonce'],skip_preflight=str(intent['source_commit']==state['expected_sha']).lower())
        fields['run_qemu'] = str(state.get('qemu_enabled', False)).lower()
        for key,value in fields.items(): args += ['-f',key+'='+str(value)]
        try: call(args)
        except (RuntimeError,subprocess.SubprocessError): pass
    found = find_dispatched(state,call)
    if found:
        old_run = state['run_id']
        state.update(run_id=found, stage=state['dispatch_intent']['stage'],
                     source_checkpoint=state['dispatch_intent'].get('source_checkpoint',state.get('new_checkpoint')),
                     source_commit=state['dispatch_intent'].get('source_commit',state['expected_sha']),
                     source_run_id=state['dispatch_intent'].get('source_run_id',old_run),status='FOLLOWING')
        for key in ('next_source_checkpoint','next_source_commit','next_source_run_id'):state.pop(key,None)
        del state['dispatch_intent']
    else:
        state['status']='DISPATCH_AMBIGUOUS'
    save_state(folder,state)


def artifacts(run_id):
    items=[]
    for page in range(1,101):
        data=api(f'actions/runs/{run_id}/artifacts?per_page=100&page={page}')['artifacts']
        items.extend(data)
        if len(data)<100: return items
    raise ValueError('Artifact inventory exceeds limit')


def download(folder, run_id, name):
    target=folder / ('run-'+str(run_id)) / name
    if target.exists():
        import shutil
        shutil.rmtree(target)
    target.mkdir(parents=True)
    gh(['run','download',str(run_id),'--repo',REPO,'--name',name,'--dir',str(target)])
    return target


def unique_json(folder, name):
    files=list(folder.rglob(name))
    if len(files)!=1: raise ValueError('Missing or ambiguous ' + name)
    return json.loads(files[0].read_text())


def validate_qemu(receipt,state,digest):
    for key,value in dict(source_sha=state['expected_sha'],run_id=str(state['run_id']),
                          apk_sha256=digest,device_validation='PENDING_DEVICE_VALIDATION').items():
        if str(receipt.get(key))!=value: raise ValueError('QEMU identity differs: '+key)
    if receipt.get('status') not in ('QEMU_TESTS_PASS','QEMU_ABI_BLOCKED'):
        raise ValueError('QEMU validation failed or not tested')
    return receipt['status']


def verify_apk(folder,state,apksigner,aapt2):
    apks=list(folder.rglob('*.apk'))
    if len(apks)!=1: raise ValueError('Missing or ambiguous APK')
    apk=apks[0]
    digest=hashlib.sha256(apk.read_bytes()).hexdigest()
    sums=list(folder.rglob('SHA256SUMS'))
    if len(sums)!=1 or sums[0].read_text().split()!=[digest,apk.name]:
        raise ValueError('SHA256SUMS mismatch')
    report=unique_json(folder,'BUILD_REPORT.json')
    expected=dict(source_sha=state['expected_sha'],run_id=str(state['run_id']),branch=BRANCH,chromium_pin=PIN,
                  APK_VERIFIED='PASS',ROBOLECTRIC_PASS='PASS',JNI_LINK_PASS='PASS',mandatory_gates='PASS')
    for key,value in expected.items():
        if str(report.get(key))!=value: raise ValueError('Build report gate/identity differs: '+key)
    try:
        subprocess.run([apksigner,'verify','--verbose','--print-certs',str(apk)],check=True,capture_output=True,timeout=120)
        badging=subprocess.check_output([aapt2,'dump','badging',str(apk)],text=True,timeout=120)
    except subprocess.SubprocessError:
        raise ValueError('APK signature/package verification command failed') from None
    if not re.search(r"package:\s+name='app\.archium\.android'",badging):
        raise ValueError('APK package differs')
    abis=re.search(r'^native-code:\s*(.*)$',badging,re.M)
    if not abis or re.findall(r"'([^']+)'",abis[1])!=['arm64-v8a']:
        raise ValueError('APK must exclusively target arm64-v8a')
    with zipfile.ZipFile(apk) as archive:
        lib_abis={n.split('/')[1] for n in archive.namelist() if n.startswith('lib/') and n.count('/')>=2}
        if lib_abis!={'arm64-v8a'}: raise ValueError('APK native libraries differ')
    return apk,digest


def next_deadline(start,now):
    return start + (max(1,math.floor((now-start)/INTERVAL)+1))*INTERVAL


def render(state):
    fields=[('ARCHIUM R5 — PROGRESSIVE BUILD',''),('RUN ACTUAL',state['run_id']),('SHA',state['expected_sha']),
            ('WORKFLOW',WORKFLOW),('STAGE',state['stage']),('CHECKPOINT RESTAURADO',state['source_checkpoint']),
            ('CHECKPOINT NUEVO',state.get('new_checkpoint','—')),('ESTADO GITHUB',state.get('github_status','—')),
            ('JOB / STEP',state.get('job_step','—')),('TIEMPO TRANSCURRIDO',state.get('elapsed','—')),
            ('ÚLTIMA CONSULTA',state.get('last_poll','—')),('SIGUIENTE CONSULTA',state.get('next_poll','—')),
            ('APK STATUS',state.get('apk_status','PENDING'))]
    print('\n'.join(k+(': '+str(v) if v!='' else '') for k,v in fields),flush=True)


def poll(state,folder,args):
    if 'dispatch_intent' in state:
        dispatch(state,folder)
        return False
    run=api('actions/runs/'+str(state['run_id']))
    if run['head_sha']!=state['expected_sha'] or run['head_branch']!=BRANCH or run.get('path')!='.github/workflows/'+WORKFLOW:
        raise ValueError('Run identity differs')
    state['github_status']=run['status']+'/'+str(run.get('conclusion'))
    if run.get('run_started_at'):
        started=datetime.fromisoformat(run['run_started_at'].replace('Z','+00:00'))
        state['elapsed']=str(datetime.now(timezone.utc)-started).split('.')[0]
    jobs=api(f'actions/runs/{state["run_id"]}/jobs?per_page=100')['jobs']
    state['job_gates']={j['name']:j.get('conclusion') or j['status'] for j in jobs}
    state['qemu_job']=[dict(name=j['name'],status=j['status'],conclusion=j.get('conclusion')) for j in jobs if 'qemu' in j['name'].lower()]
    state['job_step']='; '.join(j['name']+' / '+', '.join(s['name'] for s in j.get('steps',[]) if s['status']=='in_progress')
                              for j in jobs if j['status']=='in_progress') or '—'
    if run['status']!='completed': return False
    if run.get('conclusion') not in ('success','failure'): raise ValueError('GitHub run interrupted')
    receipt=unique_json(download(folder,state['run_id'],'Archium-R5-stage-receipt'),'stage-receipt.json')
    outcome=validate_receipt(receipt,state)
    if outcome=='BUILD_INCOMPLETE':
        if int(state['stage'])>=args.max_stages: raise ValueError('MAX_STAGES reached')
        tag=receipt['new_checkpoint']; sha=receipt['new_checkpoint_commit']
        items=artifacts(state['run_id'])
        checker=load_module('check-recovery-checkpoint')
        groups=checker.validate_inventory(items,tag,sha,10**18,10**18)
        token=subprocess.check_output(['gh','auth','token'],text=True,timeout=30).strip()
        payload,_=checker.remote_manifest(groups[0]['id'],REPO,token)
        validate_checkpoint(items,json.loads(payload),tag,sha)
        validate_incomplete_jobs(jobs,len(groups),state)
        # All groups are immutable digest-bearing GitHub artifacts. Runner receipt attests pack bytes.
        state.update(new_checkpoint=tag,progress_fingerprint=receipt['progress']['fingerprint'])
        active=[r for r in all_runs() if r['status']!='completed' and str(r['id'])!=str(state['run_id'])]
        if active: raise ValueError('Concurrent workflow active; continuation refused')
        head=api('git/ref/heads/'+BRANCH)['object']['sha']
        if head!=state['expected_sha']: raise ValueError('Branch moved; continuation refused')
        dispatch(state,folder)
        return False
    if run.get('conclusion')!='success': raise ValueError('Final APK requires successful GitHub run')
    apk,digest=verify_apk(download(folder,state['run_id'],'Archium-for-Android-arm64'),state,args.apksigner,args.aapt2)
    qemu=unique_json(download(folder,state['run_id'],'Archium-R5-QEMU'),'qemu-receipt.json')
    qstatus=validate_qemu(qemu,state,digest)
    state.update(apk_status='APK_VERIFIED',apk_sha256=digest,apk_path=str(apk),
                 status='BUILD_SUCCESS APK_VERIFIED '+qstatus+' DEVICE_VALIDATION_PENDING')
    if args.installer:
        # Installation is a handoff, never physical-device testing, uninstall, or data clearing.
        result=subprocess.run(shlex.split(args.installer)+[str(apk)],text=True,capture_output=True,timeout=180)
        if result.returncode: raise ValueError('Native installer failed')
        installed=json.loads(result.stdout)
        if installed.get('status') not in ('USER_CONFIRMATION_REQUIRED','INSTALL_SUCCESS'):
            raise ValueError('Unknown installer receipt')
        if installed['status']=='INSTALL_SUCCESS' and (installed.get('certificate_verified') is not True or installed.get('version_verified') is not True):
            raise ValueError('Installer lacks certificate/version verification')
        state['installation']=installed
    else:
        state['installation']={'status':'USER_CONFIRMATION_REQUIRED'}
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir',required=True,type=Path)
    parser.add_argument('--max-stages',type=int,default=4)
    parser.add_argument('--installer')
    parser.add_argument('--apksigner',default='apksigner')
    parser.add_argument('--aapt2',default='aapt2')
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    lock=acquire_lock(args.state_dir)
    # A second state directory must not bypass the single local monitor lock.
    global_lock=acquire_lock(Path.home()/'.cache'/'archium-r5-monitor')
    state=json.loads((args.state_dir/'state.json').read_text())
    validate_state(state,args.max_stages)
    state.update(monitor_pid=os.getpid(),monitor_ppid=os.getppid(),refresh_interval_seconds=INTERVAL)
    if state.get('terminal'): render(state); return
    deadline=time.monotonic()
    while True:
        time.sleep(max(0,deadline-time.monotonic()))
        started=deadline
        state['last_poll']=datetime.now(timezone.utc).isoformat()
        state['next_poll']=datetime.fromtimestamp(time.time()+max(0,next_deadline(started,time.monotonic())-time.monotonic()),timezone.utc).isoformat()
        try:
            done=poll(state,args.state_dir,args)
            state.setdefault('initial_heartbeat',state['last_poll'])
            state['heartbeat']=state['last_poll']
            state.pop('last_network_error',None)
            if done: state['terminal']=True
        except (subprocess.SubprocessError,RuntimeError) as error:
            state['last_network_error']=str(error)
        except (ValueError,KeyError,OSError) as error:
            state.update(status='STOPPED',error=str(error),terminal=True)
        save_state(args.state_dir,state)
        render(state)
        if state.get('terminal') or args.once: break
        deadline=next_deadline(started,time.monotonic())
    lock.close(); global_lock.close()


if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError) as error:
        print(str(error),file=sys.stderr)
        sys.exit(1)
