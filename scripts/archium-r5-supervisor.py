#!/usr/bin/env python3
"""Event-driven owner of R5; Codex wakes only for bounded repair or installed audit."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r5monitor',ROOT/'scripts/archium-r5-monitor.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)


def classify(text):
    blocked=r'Checkpoint (groups|part|source|artifact)|Incompatible checkpoint|checkpoint.*(missing|truncated|mismatch|corrupt|expired|differs)|STALLED|SHA256SUMS|BLOCKED_CHECKPOINT|QEMU_ABI_BLOCKED|No space left|Insufficient (disk|free inodes)|quota|billing|HTTP (401|403)|Bad credentials|expired|signature|certificate|authorization|permission denied'
    technical=r'FAILURES!!!|FAILED \(|FAIL:|java\.lang\.\w+(Exception|Error)|error:|undefined reference|unresolved.*JNI|AssertionError|FAILED:|Robolectric.*fail|javac.*fail|test.*FAIL|RESOURCE.*FAIL|PRODUCT_REGRESSION|crash.*reproduc'
    if re.search(blocked,text,re.I): return 'BLOCKED','INFRASTRUCTURE_OR_AUTHORIZATION'
    lines=[line for line in text.splitlines() if re.search(technical,line,re.I)]
    if not lines: return 'BLOCKED','UNCLASSIFIED_FAILURE'
    key=re.sub(r'\b[0-9a-f]{8,40}\b|\d+','N',lines[0])
    return 'REPAIR',hashlib.sha256(key.encode()).hexdigest()[:20]


def verify_thread_events(events, session):
    ids=[e.get('thread_id') for e in events if e.get('type')=='thread.started']
    if not ids or any(i!=session for i in ids) or not any(e.get('type')=='turn.completed' for e in events) or any(e.get('type')=='turn.failed' for e in events):
        raise ValueError('CODEX_RESUME_BLOCKED: wrong thread or incomplete worker turn')
    return True


def limit_reason(state,now,budget,max_runs,cause,repair_limit):
    if now-float(state['night_started_epoch'])>=budget:return 'NIGHT_BUDGET'
    if int(state['stage'])>=max_runs:return 'RUN_LIMIT'
    if state.get('repairs_by_cause',{}).get(cause,0)>=repair_limit:return 'REPAIR_LIMIT'
    return None


def find_session(folder,session):
    files=list(folder.rglob('*'+session+'.jsonl'))
    exact=[]
    for p in files:
        with p.open() as f:
            meta=json.loads(f.readline())
        if meta.get('type')=='session_meta' and meta.get('payload',{}).get('id')==session:exact.append(p)
    if len(exact)!=1:raise ValueError('CODEX_RESUME_BLOCKED: exact session not found')
    return exact[0]


def session_idle(path):
    # Read only the bounded end, never infer that a live interactive CLI is active reasoning.
    with path.open('rb') as f:
        f.seek(max(0,path.stat().st_size-2*1024*1024));lines=f.read().decode(errors='replace').splitlines()
    status=None
    for line in lines:
        try:event=json.loads(line)
        except ValueError:continue
        kind=event.get('payload',{}).get('type') if event.get('type')=='event_msg' else None
        if kind=='task_started':status=False
        elif kind in ('task_complete','turn_aborted'):status=True
    return status is True


def save(folder,state):
    state['updated_at']=datetime.now(timezone.utc).isoformat();monitor.save_state(folder,state)


def journal(folder,state,event,**data):
    entry=dict(event=event,time=datetime.now(timezone.utc).isoformat(),run_id=state.get('run_id'),sha=state.get('expected_sha'),**data)
    with (folder/'events.jsonl').open('a') as f:
        f.write(json.dumps(entry)+'\n');f.flush();os.fsync(f.fileno())
    state['last_event_processed']=entry;save(folder,state)


def failure_evidence(folder,state,message):
    target=folder/('event-'+str(state['run_id']));target.mkdir(exist_ok=True)
    jobs=monitor.api(f'actions/runs/{state["run_id"]}/jobs?per_page=100')['jobs']
    (target/'jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
    evidence=[message]
    for job in jobs:
        if job.get('conclusion')!='failure':continue
        result=subprocess.run(['gh','api',f'repos/{monitor.REPO}/actions/jobs/{job["id"]}/logs'],text=True,capture_output=True,timeout=120)
        if result.returncode:
            evidence.append(result.stderr[-1000:]);continue
        log=result.stdout
        (target/f'job-{job["id"]}.log').write_text(log)
        # Prefer real error diagnostics, excluding routine negative-test output unless the
        # actual compile/gate step failed. The worker must establish the root cause.
        lines=[line for line in log.splitlines() if re.search(r'FAILURES!!!|FAILED \(|FAIL:|java\.lang\.\w+(Exception|Error)|error:|FAILED:|AssertionError|undefined reference|BUILD_INCOMPLETE|BLOCKED_|No space|quota|HTTP (401|403)|QEMU_ABI',line,re.I)]
        evidence.extend(lines[-100:])
    text='\n'.join(evidence)
    (target/'failure-report.md').write_text('# R5 event\n\n'+message+'\n\n```text\n'+text[-18000:]+'\n```\n')
    state['evidence_path']=str(target);state['failure_jobs']=[dict(id=j['id'],name=j['name'],steps=[s['name'] for s in j.get('steps',[]) if s.get('conclusion')=='failure']) for j in jobs if j.get('conclusion')=='failure']
    return target,text


def preserve_checkpoint(folder,state):
    # A genuine failure may still publish a fully packed, quiescent checkpoint.
    # It can seed a repair, but never qualifies for normal incomplete continuation.
    try:
        r=monitor.unique_json(monitor.download(folder,state['run_id'],'Archium-R5-stage-receipt'),'stage-receipt.json')
        if r.get('pack_verified') is not True or r.get('checkpoint_verified') is not True or r.get('expected_sha')!=state['expected_sha']:return
        tag=r['new_checkpoint'];sha=r['new_checkpoint_commit']
        items=monitor.artifacts(state['run_id']);checker=monitor.load_module('check-recovery-checkpoint')
        groups=checker.validate_inventory(items,tag,sha,10**18,10**18)
        token=subprocess.check_output(['gh','auth','token'],text=True,timeout=30).strip()
        payload,_=checker.remote_manifest(groups[0]['id'],monitor.REPO,token)
        monitor.validate_checkpoint(items,json.loads(payload),tag,sha)
        state['last_valid_checkpoint']=dict(source_checkpoint=tag,source_commit=sha,source_run_id=str(state['run_id']))
    except (ValueError,KeyError,RuntimeError,OSError,subprocess.SubprocessError):
        pass  # Existing last verified source remains authorized and untouched.


def run_worker(args,state,folder,event,report):
    session=state['codex_session_id'];session_file=find_session(args.sessions,session)
    if not session_idle(session_file):
        raise RuntimeError('CODEX_BUSY: original session has an active turn; defer event')
    lock=monitor.acquire_lock(folder/'codex-worker')
    work=report/('codex-'+event);work.mkdir(exist_ok=True)
    result_path=work/'worker-result.json'
    if (work/'started.json').exists():
        # Replay a durably completed worker after supervisor restart; never execute it twice.
        finished=work/'exit-code.json';events_file=work/'events.jsonl'
        if finished.is_file() and result_path.is_file() and events_file.is_file():
            record=json.loads(finished.read_text())
            replay=[json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]
            verify_thread_events(replay,session)
            if record.get('exit_code')==0 and record.get('thread_id')==session and record.get('mismatch') is False:
                lock.close();return json.loads(result_path.read_text())
        lock.close()
        raise ValueError('CODEX_RESUME_BLOCKED: prior worker lacks verified completion; no duplicate resume')
    checkpoint=state['last_valid_checkpoint']
    if event=='repair':
        scope=f'''Repair only this technical event. Read {report/'failure-report.md'} and relevant logs.
Identify root cause, reproduce RED, apply minimal fix, verify GREEN and required preflight gates.
Preserve the existing checkpoint and config/toolchain compatibility. No clean builds or deletes.
Commit and push only {monitor.BRANCH}. Do NOT dispatch Actions, launch a supervisor, use hardware
Android tests, start subagents, or wait for builds. Supervisor owns all dispatch and continuation.
Authorized source checkpoint: {json.dumps(checkpoint)}. Keep Chromium pin {monitor.PIN}.
If blocked, record BLOCKED; do not improvise. Write {result_path} as JSON with status REPAIR_READY
or BLOCKED, new_sha, previous_sha={state['expected_sha']}, source_checkpoint/source_commit/source_run_id
exactly as authorized above, gates=PASS only after execution, gate_evidence_file pointing to a
real repo-contained evidence file, and gate_evidence_sha256. Ensure clean git status and exact
remote branch SHA. Finish this one turn and return control; no installation or extra work.'''
    else:
        scope=f'''POST-INSTALL AUDIT ONLY. Read {report/'failure-report.md'} and state/evidence {folder}.
Compare actual Android system package, versionCode, signature and installer evidence to exact
artifact/run {state['run_id']}/{state['expected_sha']}. No device access means device runtime PENDING.
Use QEMU evidence for executed virtual tests; hardware/DeX remain PENDING_DEVICE_VALIDATION.
Update project final report against TODO.md. No development, code changes, builds, subagents,
or unverified PASS. If reproducible product regression found, report it rather than dispatch.
Write {result_path} JSON with status AUDIT_PASS/AUDIT_PARTIAL/PRODUCT_REGRESSION/BLOCKED,
source_sha and evidence_file. Finish this one turn and return control.'''
    prompt='ARCHIUM R5 SUPERVISOR EVENT — exact original session only.\n'+scope
    (work/'prompt.txt').write_text(prompt)
    command=[args.codex,'exec','-C',str(ROOT),'-s','danger-full-access','-c','approval_policy="never"',
             'resume',session,'-','--json','--output-last-message',str(work/'last-message.txt')]
    # These match this session's existing danger-full-access/never policy. No bypass flags.
    (work/'started.json').write_text(json.dumps(dict(session_id=session,command=command,started=time.time()))+'\n')
    state['codex_status']='ACTIVE';journal(folder,state,'CODEX_START',kind=event,evidence=str(work))
    events=[];deadline=min(time.time()+1800,state['night_started_epoch']+args.budget_hours*3600)
    with (work/'stderr.log').open('w') as err,(work/'events.jsonl').open('w') as out:
        proc=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,
                              text=True,bufsize=1,start_new_session=True)
        state['codex_worker_pid']=proc.pid;save(folder,state)
        proc.stdin.write(prompt);proc.stdin.close()
        mismatch=False
        try:
            while proc.poll() is None or select.select([proc.stdout],[],[],0)[0]:
                if time.time()>=deadline:
                    os.killpg(proc.pid,signal.SIGTERM);raise ValueError('PAUSED_LIMIT_REACHED: Codex worker budget')
                ready=select.select([proc.stdout],[],[],1)[0]
                if not ready:continue
                line=proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:break
                    continue
                out.write(line);out.flush()
                try:item=json.loads(line)
                except ValueError:continue
                events.append(item)
                if item.get('type')=='thread.started' and item.get('thread_id')!=session:
                    mismatch=True;os.killpg(proc.pid,signal.SIGTERM);break
            code=proc.wait(timeout=30)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=30)
            proc.stdout.close()
            state['codex_status']='IDLE';state.pop('codex_worker_pid',None)
            save(folder,state);lock.close()
    (work/'stdout.log').write_bytes((work/'events.jsonl').read_bytes())
    (work/'exit-code.json').write_text(json.dumps(dict(exit_code=code,thread_id=session,mismatch=mismatch))+'\n')
    verify_thread_events(events,session)
    if code!=0:raise ValueError('CODEX_RESUME_BLOCKED: worker exit '+str(code))
    if not result_path.is_file():raise ValueError('CODEX_RESUME_BLOCKED: no machine worker result')
    return json.loads(result_path.read_text())


def validate_repair(result,state):
    if result.get('status')!='REPAIR_READY' or result.get('gates')!='PASS' or result.get('previous_sha')!=state['expected_sha']:
        raise ValueError('Repair result/gates not approved')
    for k,v in state['last_valid_checkpoint'].items():
        if str(result.get(k))!=str(v):raise ValueError('Repair changed checkpoint authorization')
    sha=result.get('new_sha','')
    if not re.fullmatch('[0-9a-f]{40}',sha) or sha==state['expected_sha']:raise ValueError('Repair requires a new exact SHA')
    evidence=Path(result['gate_evidence_file']).resolve()
    if not evidence.is_relative_to(ROOT) or not evidence.is_file() or hashlib.sha256(evidence.read_bytes()).hexdigest()!=result.get('gate_evidence_sha256'):
        raise ValueError('Repair gate evidence missing or altered')
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!=monitor.BRANCH:
        raise ValueError('Repair branch differs')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('Repair worktree is dirty')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=sha:raise ValueError('Repair HEAD differs')
    subprocess.run(['git','merge-base','--is-ancestor',state['expected_sha'],sha],cwd=ROOT,check=True)
    if monitor.api('git/ref/heads/'+monitor.BRANCH)['object']['sha']!=sha:raise ValueError('Repair remote SHA differs')
    old=subprocess.check_output(['git','show',state['last_valid_checkpoint']['source_commit']+':config/archium-args.gn'],cwd=ROOT)
    if old!=(ROOT/'config/archium-args.gn').read_bytes():raise ValueError('BLOCKED_CHECKPOINT_INCOMPATIBLE: repair changed GN args')
    if json.loads((ROOT/'patches/upstream-files.json').read_text()).get('revision')!=monitor.PIN:
        raise ValueError('BLOCKED_CHECKPOINT_INCOMPATIBLE: repair changed Chromium pin')
    return sha



def validate_installation(receipt,state,folder,aapt2,apksigner):
    expected=dict(status='INSTALL_SUCCESS',source_sha=state['expected_sha'],run_id=str(state['run_id']),
        apk_sha256=state['apk_sha256'],installed_apk_sha256=state['apk_sha256'],package='app.archium.android')
    for key,value in expected.items():
        if str(receipt.get(key))!=value:raise ValueError('Installation identity mismatch: '+key)
    proof=Path(receipt['system_evidence_file']).resolve()
    if not proof.is_relative_to(folder.resolve()) or not proof.is_file() or hashlib.sha256(proof.read_bytes()).hexdigest()!=receipt.get('system_evidence_sha256'):
        raise ValueError('Installation requires preserved Android system evidence')
    observed=json.loads(proof.read_text())
    if observed.get('schema')!=1 or observed.get('collector')!='android-package-inspection' or observed.get('authorization')!='AUTHORIZED' or not observed.get('device_serial'):
        raise ValueError('Installed identity requires authorized Android collection')
    if not re.fullmatch(r'package:/data/app/[^\s]+/base\.apk\s*',observed.get('package_path_output','')):
        raise ValueError('Installed base APK path was not observed on Android')
    installed=Path(observed['installed_apk_file']).resolve()
    if not installed.is_relative_to(folder.resolve()) or not installed.is_file() or installed==Path(state['apk_path']).resolve():
        raise ValueError('Separate APK copied from Android is required')
    if hashlib.sha256(installed.read_bytes()).hexdigest()!=state['apk_sha256']:
        raise ValueError('Android-installed APK bytes differ from expected artifact')
    system_version=re.search(r'\bversionCode=([0-9]+)\b',observed.get('package_dump',''))
    if not system_version or system_version[1]!=receipt.get('version_code'):
        raise ValueError('Android package dump does not confirm installed version')
    badging=subprocess.check_output([aapt2,'dump','badging',state['apk_path']],text=True,timeout=120)
    version=re.search(r"versionCode='([0-9]+)'",badging)
    installed_badging=subprocess.check_output([aapt2,'dump','badging',str(installed)],text=True,timeout=120)
    if not re.search(r"package: name='app\.archium\.android'",installed_badging) or not re.search(r"versionCode='"+re.escape(receipt['version_code'])+r"'",installed_badging):
        raise ValueError('Copied installed package identity differs')
    signature=subprocess.check_output([apksigner,'verify','--print-certs',state['apk_path']],text=True,timeout=120)
    certs=re.findall(r'certificate SHA-256 digest: ([0-9a-f]{64})',signature)
    installed_signature=subprocess.check_output([apksigner,'verify','--print-certs',str(installed)],text=True,timeout=120)
    if re.findall(r'certificate SHA-256 digest: ([0-9a-f]{64})',installed_signature)!=certs:
        raise ValueError('Android-installed certificate differs from artifact')
    if not version or receipt.get('version_code')!=version[1] or certs!=[receipt.get('certificate_sha256')]:
        raise ValueError('Installed version/certificate differs from verified artifact')
    return True


def finish_build(args,state,folder):
    state['qemu_result']='QEMU_ABI_BLOCKED' if 'QEMU_ABI_BLOCKED' in state['status'] else 'QEMU_TESTS_PASS'
    state['gate_results']={'APK_VERIFIED':'PASS','ROBOLECTRIC_PASS':'PASS','JNI_LINK_PASS':'PASS'}
    if state['qemu_result']=='QEMU_ABI_BLOCKED':
        state.update(status='BLOCKED',blocking_reason='QEMU_ABI_BLOCKED',terminal=True,
            installation={'status':'INSTALL_PENDING_DEVICE','reason':'QEMU mandatory runtime gate blocked; no installation attempted'})
        journal(folder,state,'BLOCKED',reason='QEMU_ABI_BLOCKED');return
    receipt_path=folder/'install-receipt.json'
    if not receipt_path.is_file():
        state.update(status='INSTALL_PENDING_DEVICE',terminal=True,
            installation={'status':'INSTALL_PENDING_DEVICE','reason':'No authorized unattended system verification mechanism; APK preserved'})
        journal(folder,state,'INSTALL_PENDING_DEVICE');return
    receipt=json.loads(receipt_path.read_text())
    validate_installation(receipt,state,folder,args.aapt2,args.apksigner)
    state['installation']=receipt
    event=state['apk_sha256']
    if event in state.get('audited_installations',[]) and state.get('post_install_audit'):
        state.update(status='COMPLETE_SCOPED',terminal=True);save(folder,state);return
    if not session_idle(find_session(args.sessions,state['codex_session_id'])):
        state.update(status='WAITING_CODEX_IDLE');save(folder,state);return
    state['pending_audit_event']=event;save(folder,state)
    report=folder/('post-install-'+event[:16]);report.mkdir(exist_ok=True)
    (report/'failure-report.md').write_text(json.dumps(state,indent=2)+'\n')
    result=run_worker(args,state,folder,'audit',report)
    if result.get('source_sha')!=state['expected_sha']:
        raise ValueError('Post-install audit source SHA differs')
    if result.get('status')=='PRODUCT_REGRESSION':
        state['terminal']=False
        handle_failure(args,state,folder,ValueError('PRODUCT_REGRESSION: '+str(result)))
        return
    if result.get('status') not in ('AUDIT_PASS','AUDIT_PARTIAL'):
        raise ValueError('Post-install audit blocked; no complete claim')
    evidence=Path(result['evidence_file']).resolve()
    if not evidence.is_relative_to(ROOT) or not evidence.is_file():
        raise ValueError('Post-install audit lacks project report')
    if event not in state.setdefault('audited_installations',[]):state['audited_installations'].append(event)
    state.pop('pending_audit_event',None)
    state.update(post_install_audit=result,status='COMPLETE_SCOPED',terminal=True,
        device_dex_validation='PENDING_DEVICE_VALIDATION')
    journal(folder,state,'COMPLETE_SCOPED',scope=result['status'])


def handle_failure(args,state,folder,error):
    if 'MAX_STAGES' in str(error) or 'PAUSED_LIMIT_REACHED' in str(error):
        state.update(status='PAUSED_LIMIT_REACHED',blocking_reason=str(error),terminal=True);save(folder,state);return
    report,text=failure_evidence(folder,state,str(error));kind,cause=classify(text)
    state.update(blocking_reason=str(error),failure_class=kind,root_cause_key=cause)
    if kind!='REPAIR':
        state.update(status='BLOCKED',terminal=True,codex_status='IDLE');journal(folder,state,'BLOCKED',reason=str(error));return
    event_id=f'{state["run_id"]}:{state["expected_sha"]}:{cause}'
    claimed=event_id in state.get('claimed_events',[])
    reason=limit_reason(state,time.time(),args.budget_hours*3600,args.max_stages,cause,10**9 if claimed else args.max_repairs)
    if reason:state.update(status='PAUSED_LIMIT_REACHED',blocking_reason=reason,terminal=True);save(folder,state);return
    if not session_idle(find_session(args.sessions,state['codex_session_id'])):
        state.update(status='WAITING_CODEX_IDLE');save(folder,state);return
    preserve_checkpoint(folder,state)
    if not claimed:
        state.setdefault('claimed_events',[]).append(event_id)
        state.setdefault('repairs_by_cause',{})[cause]=state.get('repairs_by_cause',{}).get(cause,0)+1
    state['repair_count']=sum(state['repairs_by_cause'].values());state['status']='REPAIRING';save(folder,state)
    result=run_worker(args,state,folder,'repair',report)
    sha=validate_repair(result,state)
    if any(r['status']!='completed' for r in monitor.all_runs()):raise ValueError('Concurrent workflow prevents repaired dispatch')
    state.update(expected_sha=sha,status='REPAIR_APPROVED',**{'next_'+k:v for k,v in state['last_valid_checkpoint'].items()})
    state.pop('progress_fingerprint',None);journal(folder,state,'REPAIR_APPROVED',new_sha=sha)
    monitor.dispatch(state,folder)



def poll_owned_phase(state,folder,args):
    # The approved repair SHA is durable before dispatch. Recover this phase before
    # ever comparing the previous run's SHA against the new implementation SHA.
    if state.get('status')=='REPAIR_APPROVED':
        if monitor.api('git/ref/heads/'+monitor.BRANCH)['object']['sha']!=state['expected_sha']:
            raise ValueError('Repair remote SHA moved before dispatch')
        if any(r['status']!='completed' for r in monitor.all_runs()):
            raise ValueError('Concurrent workflow prevents repaired dispatch')
        monitor.dispatch(state,folder)
        return False
    return monitor.poll(state,folder,args)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-dir',type=Path,required=True)
    p.add_argument('--max-stages',type=int,default=6)
    p.add_argument('--max-repairs',type=int,default=2)
    p.add_argument('--budget-hours',type=float,default=10)
    p.add_argument('--codex',default='/root/.local/bin/codex')
    p.add_argument('--sessions',type=Path,default=Path('/root/.codex/sessions'))
    p.add_argument('--aapt2',required=True);p.add_argument('--apksigner',required=True)
    p.add_argument('--once',action='store_true');p.add_argument('--check-session',action='store_true')
    args=p.parse_args();args.installer=None
    folder=args.state_dir;state=json.loads((folder/'state.json').read_text())
    monitor.validate_state(state,args.max_stages)
    if not 0<args.budget_hours<=10 or not 1<=args.max_stages<=6 or not 0<=args.max_repairs<=2:raise ValueError('Supervisor bounds rejected')
    try:
        session=find_session(args.sessions,state['codex_session_id'])
        help_text=subprocess.check_output([args.codex,'exec','resume','--help'],text=True,timeout=30)
        if '[SESSION_ID]' not in help_text or '--json' not in help_text:raise ValueError('Installed CLI lacks exact resume/JSON')
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        state.update(status='CODEX_RESUME_BLOCKED',blocking_reason=str(error),terminal=True);save(folder,state)
        raise ValueError('CODEX_RESUME_BLOCKED: '+str(error)) from error
    if args.check_session:
        print(json.dumps(dict(session_id=state['codex_session_id'],session_file=str(session),cli_support='PASS',actual_resume='NOT_RUN_ACTIVE_ORIGINAL_TURN')));return
    lock=monitor.acquire_lock(folder);global_lock=monitor.acquire_lock(Path.home()/'.cache/archium-r5-monitor')
    state.update(supervisor_pid=os.getpid(),monitor_pid=os.getpid(),refresh_interval_seconds=600,codex_status='IDLE')
    state.setdefault('night_started_epoch',time.time())
    state.setdefault('last_valid_checkpoint',{k:state[k] for k in ['source_checkpoint','source_commit','source_run_id']})
    state.setdefault('repair_count',0);state.setdefault('repairs_by_cause',{})
    deadline=time.monotonic()
    while not state.get('terminal'):
        time.sleep(max(0,deadline-time.monotonic()));started=deadline
        state['last_poll']=datetime.now(timezone.utc).isoformat()
        state['next_poll']=datetime.fromtimestamp(time.time()+600,timezone.utc).isoformat()
        try:
            if time.time()-state['night_started_epoch']>=args.budget_hours*3600:
                state.update(status='PAUSED_LIMIT_REACHED',blocking_reason='NIGHT_BUDGET',terminal=True)
            else:
                prior_run=state['run_id'];done=poll_owned_phase(state,folder,args)
                if prior_run!=state['run_id']:
                    state['last_valid_checkpoint']={k:state[k] for k in ['source_checkpoint','source_commit','source_run_id']}
                    state['attempts']=state['stage']
                    journal(folder,state,'RUN_DISPATCHED')
                state.setdefault('initial_heartbeat',state['last_poll']);state['heartbeat']=state['last_poll'];state['network_error_count']=0
                if done:finish_build(args,state,folder)
        except ValueError as error:
            try:handle_failure(args,state,folder,error)
            except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as failure:
                state.update(status='CODEX_RESUME_BLOCKED' if 'CODEX_RESUME_BLOCKED' in str(failure) else 'BLOCKED',blocking_reason=str(failure),terminal=True)
        except (RuntimeError,subprocess.SubprocessError,OSError) as error:
            # Preflight/authorization failure can precede any native receipt. Inspect the
            # failed job instead of retrying a receipt download as if it were a network issue.
            if state.get('github_status')=='completed/failure':
                try:handle_failure(args,state,folder,error)
                except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as failure:
                    state.update(status='CODEX_RESUME_BLOCKED' if 'CODEX_RESUME_BLOCKED' in str(failure) else 'BLOCKED',blocking_reason=str(failure),terminal=True)
            else:
                state['last_network_error']=str(error)
                state['network_error_count']=state.get('network_error_count',0)+1
                if state['network_error_count']>=3:state.update(status='BLOCKED',blocking_reason='Repeated network/authorization failure',terminal=True)
        save(folder,state);monitor.render(state)
        print('SUPERVISOR='+state.get('status','FOLLOWING')+' CODEX='+state.get('codex_status','IDLE'),flush=True)
        if args.once:break
        deadline=monitor.next_deadline(started,time.monotonic())
    lock.close();global_lock.close()


if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as error:
        print('SUPERVISOR_BLOCKED: '+str(error),flush=True);raise SystemExit(2)
