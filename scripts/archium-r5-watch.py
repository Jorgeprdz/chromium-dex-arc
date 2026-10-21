#!/usr/bin/env python3
"""Watch a single authenticated run. No builds, QEMU or Codex resume. Optional explicitly authorized ADB update.

The terminal remains open after completion or blockage until Ctrl+C. Active
queries start immediately then on 600-second slots; completed screens make no
further GitHub requests. State and JSONL evidence survive terminal restarts.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap
import time

spec=importlib.util.spec_from_file_location('r5_monitor',Path(__file__).with_name('archium-r5-monitor.py'))
monitor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
INTERVAL=600


def clean(value):
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', str(value))


def render(state, output=None, color=None, clear=None, width=None):
    output=output or sys.stdout
    tty=output.isatty()
    color=tty if color is None else color
    clear=tty if clear is None else clear
    width=max(38,min(112,width or shutil.get_terminal_size((96,30)).columns))-2
    reset='\x1b[0;40;37m' if color else ''
    cyan='\x1b[36m' if color else ''
    dim='\x1b[90m' if color else ''
    status=str(state.get('status','WATCHING'))
    tone=32 if status=='BUILD_SUCCESS' else 31 if any(x in status for x in ('FAIL','BLOCK','MISSING','LIMIT')) else 33
    accent=f'\x1b[{tone}m' if color else ''
    lines=[]
    def border():lines.append(cyan+'+'+'-'*width+'+'+reset)
    def row(text='',paint=''):
        for line in textwrap.wrap(clean(text),width-4,replace_whitespace=False) or ['']:
            lines.append(cyan+'|'+reset+'  '+paint+line.ljust(width-4)+reset+'  '+cyan+'|'+reset)
    border();row('ARCHIUM R5  /  PROGRESSIVE BUILD',cyan)
    row(('RUN MONITOR + VERIFIED ADB' if state.get('auto_install')=='ADB_VERIFIED_UPDATE' else 'WATCH ONLY')+'  |  CHECKPOINT REUSE  |  ARM64',dim);border()
    fields=[('RUN ACTUAL',state['run_id']),('SHA',state['expected_sha']),('WORKFLOW',monitor.WORKFLOW),
            ('STAGE',state['stage']),('CHECKPOINT ORIGEN',state['source_checkpoint']),
            ('RESTAURACION',state.get('restore_status','PENDING_CI')),
            ('CHECKPOINT NUEVO',state.get('new_checkpoint','--')),
            ('ESTADO GITHUB',state.get('github_status','PENDING')),
            ('JOB / STEP',state.get('job_step','--')),('TRANSCURRIDO',state.get('elapsed','--')),
            ('ULTIMA CONSULTA',state.get('last_poll','--')),
            ('SIGUIENTE CONSULTA','FINAL - sin mas consultas' if state.get('terminal') else state.get('next_poll','--')),
            ('APK STATUS',state.get('apk_status','PENDING_BUILD')),('INSTALACION',state.get('installation',{}).get('status','PENDING_BUILD')),('QEMU','DISABLED BY USER')]
    for label,value in fields:row(f'{label:<19}: {value}')
    border();row('[ '+status+' ]',accent)
    if state.get('last_error'):row(state['last_error'],accent)
    row('Refresco: 600s  |  Ctrl+C: cerrar monitor',dim)
    row('Sin relanzamientos ni reparaciones automaticas.',dim)
    row('ADB: actualizar solo APK verificada.' if state.get('auto_install')=='ADB_VERIFIED_UPDATE' else 'Instalacion manual.',dim)
    if state.get('terminal'):row('Run finalizado. Esta ventana permanece abierta.',accent)
    border()
    output.write(('\x1b[2J\x1b[H' if clear else '')+('\x1b[40;37m' if color else '')+'\n'.join(lines)+('\x1b[0m' if color else '')+'\n');output.flush()


def load_receipt(state):
    folder=Path(state['state_directory'])/'watch-artifacts'
    return monitor.unique_json(monitor.download(folder,state['run_id'],'Archium-R5-stage-receipt'),'stage-receipt.json')


def refresh(state,call=None,read_receipt=None):
    call=call or monitor.api
    run=call('actions/runs/'+str(state['run_id']))
    if (str(run.get('id'))!=str(state['run_id']) or run.get('head_sha')!=state['expected_sha']
            or run.get('head_branch')!=monitor.BRANCH
            or run.get('path')!='.github/workflows/'+monitor.WORKFLOW):
        raise ValueError('Run identity differs; observation stopped')
    state['github_status']=run['status']+'/'+str(run.get('conclusion'))
    if run.get('run_started_at'):
        start=datetime.fromisoformat(run['run_started_at'].replace('Z','+00:00'))
        state['elapsed']=str(datetime.now(timezone.utc)-start).split('.')[0]
    jobs=call(f'actions/runs/{state["run_id"]}/jobs?per_page=100')['jobs']
    state['job_gates']={j['name']:j.get('conclusion') or j['status'] for j in jobs}
    running=[j for j in jobs if j['status']=='in_progress']
    failed=[j for j in jobs if j.get('conclusion') in ('failure','cancelled','timed_out')]
    relevant=running or failed
    state['job_step']='; '.join(j['name']+' / '+', '.join(s['name'] for s in j.get('steps',[])
        if s.get('status')=='in_progress' or s.get('conclusion') in ('failure','cancelled','timed_out')) for j in relevant) or '--'
    restored=any(s['name']=='S1 restore once and transition patches' and s.get('conclusion')=='success'
                 for j in jobs for s in j.get('steps',[]))
    state['restore_status']='VERIFIED_BY_CI' if restored else 'PENDING_CI'
    state.update(status='WATCHING',qemu_result='DISABLED_BY_USER',qemu_enabled=False)
    if run['status']!='completed':return
    items=call(f'actions/runs/{state["run_id"]}/artifacts?per_page=100')['artifacts']
    apk=[a for a in items if a['name']=='Archium-for-Android-arm64' and not a.get('expired') and a.get('size_in_bytes',0)>0]
    groups=[a for a in items if re.fullmatch(r'archium-checkpoint-'+re.escape(str(state['run_id']))+r'-\d+-\d+',a['name']) and not a.get('expired')]
    if groups:
        tags={a['name'].rsplit('-',1)[0] for a in groups}
        state['new_checkpoint']=', '.join(sorted(tags))+' (published; bytes not verified here)'
    success=run.get('conclusion')=='success' and not failed
    state.update(status=('BUILD_SUCCESS' if len(apk)==1 else 'BUILD_SUCCESS_APK_MISSING') if success else 'BUILD_FAILED',
                 apk_status='ARTIFACT_AVAILABLE_NOT_DOWNLOADED' if success and len(apk)==1 else 'NO_APK',
                 installation={'status':'MANUAL_INSTALL_ONLY'},completed_at=run.get('updated_at'))
    success_receipt=False
    if any(a['name']=='Archium-R5-stage-receipt' and not a.get('expired') for a in items):
        receipt=(read_receipt or load_receipt)(state)
        if receipt.get('schema')!=1 or any(str(receipt.get(k))!=str(state[k]) for k in
                ('expected_sha','run_id','source_checkpoint','source_commit','source_run_id')):
            raise ValueError('Stage receipt identity differs')
        if receipt.get('outcome')=='BUILD_INCOMPLETE':
            monitor.validate_receipt(receipt,state)
            state.update(status='BUILD_INCOMPLETE_CHECKPOINT_SAVED',new_checkpoint=receipt['new_checkpoint'],
                         checkpoint_publication='CI_PACK_VERIFIED_NO_LOCAL_RESTORE')
        elif receipt.get('outcome')!='BUILD_FAILED':
            monitor.validate_receipt(receipt,state)
            success_receipt=receipt.get('outcome')=='BUILD_SUCCESS'
    if success and len(apk)==1 and state.get('auto_install')=='ADB_VERIFIED_UPDATE':
        if not success_receipt:raise ValueError('Successful stage receipt required before ADB update')
        install_success(state,jobs)
    state.update(terminal=True,next_poll='NONE_RUN_COMPLETED')


def install_success(state,jobs):
    gates={j['name']:j.get('conclusion') for j in jobs}
    if any(gates.get(n)!='success' for n in ('authorize','preflight / preflight','build / build')):
        raise ValueError('Mandatory GitHub jobs not all successful; ADB update blocked')
    folder=Path(state['state_directory'])
    cfg=state['adb_update']
    apk_folder=monitor.download(folder/'watch-artifacts',state['run_id'],'Archium-for-Android-arm64')
    apk,digest=monitor.verify_apk(apk_folder,state,cfg['apksigner'],cfg['aapt2'])
    state.update(apk_path=str(apk),apk_sha256=digest,apk_status='APK_VERIFIED',installation={'status':'VERIFYING_DEVICE'})
    monitor.save_state(folder,state)
    module_spec=importlib.util.spec_from_file_location('adb_update',Path(__file__).with_name('archium-r5-adb-update.py'))
    installer=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(installer)
    try:state['installation']=installer.update(state,folder/('adb-update-'+str(state['run_id'])))
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        state['installation']={'status':'INSTALL_VERIFICATION_BLOCKED','reason':clean(error)}
    monitor.save_state(folder,state)



def run_loop(state,folder,query=None,draw=None,sleep=time.sleep,monotonic=time.monotonic,wall=time.time):
    query=query or refresh;draw=draw or render
    state.setdefault('status','WATCHING')
    deadline=monotonic()
    try:
        while True:
            sleep(max(0.,deadline-monotonic()))
            started=deadline
            if not state.get('terminal'):
                now=wall()
                state['last_poll']=datetime.fromtimestamp(now,timezone.utc).isoformat()
                state['next_poll']=datetime.fromtimestamp(now+max(0.,monitor.next_deadline(started,monotonic())-monotonic()),timezone.utc).isoformat()
                try:
                    if 'night_started_epoch' in state and now-float(state['night_started_epoch'])>=float(state.get('night_budget_hours',10))*3600:
                        state.update(terminal=True,status='PAUSED_LIMIT_REACHED',last_error='Authorized monitoring budget exhausted; terminal remains open.')
                    else:
                        query(state)
                        state.update(heartbeat=state['last_poll'],network_error_count=0)
                        state.setdefault('initial_heartbeat',state['last_poll']);state.pop('last_error',None)
                except (ValueError,KeyError) as error:
                    state.update(terminal=True,status='BLOCKED',last_error=clean(error))
                except (RuntimeError,OSError,subprocess.SubprocessError) as error:
                    state['network_error_count']=state.get('network_error_count',0)+1
                    state['last_error']=clean(error)
                    state['status']='RETRYING_NETWORK'
                    if state['network_error_count']>=3:state.update(terminal=True,status='BLOCKED_NETWORK')
                state['ui_status']='OPEN'
                monitor.save_state(folder,state)
                with (folder/'watch-events.jsonl').open('a') as log:
                    log.write(json.dumps(dict(time=state['last_poll'],run_id=state['run_id'],sha=state['expected_sha'],status=state['status'],github=state.get('github_status'),error=state.get('last_error')))+'\n')
            draw(state)
            deadline=monitor.next_deadline(started,monotonic())
    except KeyboardInterrupt:
        state['ui_status']='CLOSED_BY_USER';monitor.save_state(folder,state)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--state-dir',type=Path,required=True)
    args=parser.parse_args();folder=args.state_dir
    lock=monitor.acquire_lock(folder);global_lock=monitor.acquire_lock(Path.home()/'.cache/archium-r5-monitor')
    try:
        state=json.loads((folder/'state.json').read_text());monitor.validate_state(state,int(state.get('max_new_runs',6)))
        state.update(monitor_pid=os.getpid(),monitor_ppid=os.getppid(),refresh_interval_seconds=600,
                     state_directory=str(folder.resolve()),monitoring_mode='WATCH_ONLY',terminal_output_tty=sys.stdout.isatty(),auto_repair='DISABLED_BY_USER',auto_continuation='DISABLED_BY_USER',
                     auto_install=state.get('auto_install','MANUAL_ONLY'),codex_status='IDLE',ui_status='OPEN')
        monitor.save_state(folder,state);run_loop(state,folder)
    finally:
        lock.close();global_lock.close()
        if sys.stdout.isatty():print('\x1b[0m',end='',flush=True)

if __name__=='__main__':main()
