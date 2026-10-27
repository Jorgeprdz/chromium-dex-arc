#!/usr/bin/env python3
"""Qualify controlled native stages and aggregate one bounded, fixed-SHA CI chain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def qualify(r, sha, run, number, previous=None):
    if not 1 <= number <= 12:
        raise ValueError('Stage outside 1..12')
    for key, value in dict(schema=1,expected_sha=sha,run_id=run,exit_code=0).items():
        if r.get(key) != value or type(r.get(key)) is not type(value):
            raise ValueError('Stage identity/failure: '+key)
    if r.get('outcome') not in ('BUILD_SUCCESS','BUILD_INCOMPLETE'):
        raise ValueError('Genuine stage failure')
    p=r.get('progress',{})
    if not re.fullmatch('[a-f0-9]{64}',p.get('fingerprint','')):
        raise ValueError('Missing progress fingerprint')
    if any(type(p.get(k)) is not int or p[k]<0 for k in ('completed_outputs','completed_gates')):
        raise ValueError('Missing progress counters')
    if previous:
        before=previous['progress']
        if p['fingerprint']==before['fingerprint']:
            raise ValueError('STALLED: unchanged checkpoint progress')
        if any(p[k]<before[k] for k in ('completed_outputs','completed_gates')):
            raise ValueError('Progress counters regressed')
    if r['outcome']=='BUILD_INCOMPLETE':
        if any(r.get(k) is not True for k in ('recoverable','checkpoint_verified','pack_verified')):
            raise ValueError('Checkpoint not verified')
        if r.get('new_checkpoint')!=f'archium-checkpoint-{run}-{number}' or r.get('new_checkpoint_commit')!=sha:
            raise ValueError('Checkpoint identity differs')
    return r


def summarize(stages, sha, run, tag, source_sha, source_run, maximum):
    if not 1 <= maximum <= 12 or not 1 <= len(stages) <= maximum:
        raise ValueError('Invalid chain bound')
    previous=None
    for number,r in enumerate(stages,1):
        if previous and previous['outcome']!='BUILD_INCOMPLETE':
            raise ValueError('Stage ran after success')
        qualify(r,sha,run,number,previous)
        source=(tag,source_sha,source_run) if number==1 else (previous['new_checkpoint'],sha,run)
        if tuple(r.get(k) for k in ('source_checkpoint','source_commit','source_run_id')) != source:
            raise ValueError('Non-sequential checkpoint source')
        previous=r
    if previous['outcome']=='BUILD_INCOMPLETE' and len(stages)<maximum:
        raise ValueError('Chain stopped before authorized limit')
    result=dict(previous)
    # Root receipt describes the whole run. Per-stage receipts retain every actual source.
    result.update(source_checkpoint=tag,source_commit=source_sha,source_run_id=source_run,
        chain=dict(stages_completed=len(stages),maximum=maximum,work_minutes_per_stage=120,
                   final_source_checkpoint=previous['source_checkpoint'],stages=stages))
    return result


def prunable(items,run,number):
    if not run.isdigit() or not 1<=number<=12:raise ValueError('Prune identity rejected')
    sets={}
    for artifact in items:
        match=re.fullmatch(r'archium-checkpoint-'+re.escape(run)+r'-(\d+)-(\d{2})',artifact['name'])
        if match and 1<=int(match[1])<=number-3:
            sets.setdefault(int(match[1]),[]).append(artifact)
    result=[]
    for n,group in sorted(sets.items()):
        ordered=sorted(group,key=lambda a:a['name'])
        if [a['name'] for a in ordered]!=[f'archium-checkpoint-{run}-{n}-{i:02d}' for i in range(len(group))]:
            raise ValueError('Partial old checkpoint set; cleanup refused')
        result+=ordered
    return result


def prune(run,number,directory):
    # Called only AFTER the next source has been fully hashed and restored.
    # Retain the two newest chain sources; never touch external source/fallback,
    # APKs, manifests, receipts, logs, or artifacts from any other run.
    repository=os.environ['GITHUB_REPOSITORY'];items=[]
    for page in range(1,101):
        batch=json.loads(subprocess.check_output(['gh','api',f'repos/{repository}/actions/runs/{run}/artifacts?per_page=100&page={page}']))['artifacts']
        items+=batch
        if len(batch)<100:break
    else:raise ValueError('Artifact inventory bound exceeded')
    deleted=[];directory.mkdir(parents=True,exist_ok=True)
    path=directory/'checkpoint-cleanup.json'
    for artifact in prunable(items,run,number):
        subprocess.run(['gh','api','--method','DELETE',f'repos/{repository}/actions/artifacts/{artifact["id"]}'],check=True)
        deleted.append({k:artifact[k] for k in ('id','name','size_in_bytes')})
        path.write_text(json.dumps(dict(run_id=run,stage=number,deleted=deleted,bytes_freed=sum(a['size_in_bytes'] for a in deleted)),indent=2)+'\n')
    print('CHAIN_CLEANUP_DELETED='+str(len(deleted)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('qualify');q.add_argument('--receipt',type=Path,required=True)
    q.add_argument('--number',type=int,required=True);q.add_argument('--previous',type=Path)
    q.add_argument('--manifest',type=Path);q.add_argument('--output',type=Path,required=True)
    s=sub.add_parser('summarize');s.add_argument('--directory',type=Path,required=True)
    s.add_argument('--maximum',type=int,required=True);s.add_argument('--receipt',type=Path,required=True)
    c=sub.add_parser('prune');c.add_argument('--number',type=int,required=True);c.add_argument('--directory',type=Path,required=True)
    a=p.parse_args();sha=os.environ['GITHUB_SHA'];run=os.environ['GITHUB_RUN_ID']
    if a.command=='prune':
        prune(run,a.number,a.directory);return
    if a.command=='qualify':
        r=json.loads(a.receipt.read_text());prev=json.loads(a.previous.read_text()) if a.previous else None
        qualify(r,sha,run,a.number,prev)
        digest=''
        if r['outcome']=='BUILD_INCOMPLETE':
            if not a.manifest or not a.manifest.is_file():raise ValueError('Packed manifest absent')
            payload=a.manifest.read_bytes();m=json.loads(payload)
            if m['tag']!=r['new_checkpoint'] or m['commit']!=sha:raise ValueError('Packed manifest identity differs')
            digest=hashlib.sha256(payload).hexdigest()
        with a.output.open('a') as out:
            out.write('outcome='+r['outcome']+'\nnew_checkpoint='+str(r.get('new_checkpoint') or '')+'\nmanifest_sha256='+digest+'\n')
    else:
        try:
            # Job outputs are not sufficient evidence of successful uploads/qualification.
            needs=json.loads(os.environ['CHAIN_JOB_RESULTS'])
            for name,job in needs.items():
                if job['result'] not in ('success','skipped'):raise ValueError('Failed chain job: '+name)
            paths=sorted(a.directory.glob('Archium-R5-stage-receipt-*/stage-receipt.json'),
                         key=lambda x:int(x.parent.name.rsplit('-',1)[1]))
            stages=[json.loads(path.read_text()) for path in paths]
            result=summarize(stages,sha,run,os.environ['ARCHIUM_SOURCE_TAG'],
                             os.environ['ARCHIUM_SOURCE_COMMIT'],os.environ['ARCHIUM_SOURCE_RUN_ID'],a.maximum)
        except (ValueError,KeyError,OSError) as error:
            result=dict(schema=1,outcome='BUILD_FAILED',expected_sha=sha,run_id=run,
                source_checkpoint=os.environ['ARCHIUM_SOURCE_TAG'],source_commit=os.environ['ARCHIUM_SOURCE_COMMIT'],
                source_run_id=os.environ['ARCHIUM_SOURCE_RUN_ID'],exit_code=1,recoverable=False,
                checkpoint_verified=False,pack_verified=False,reason=str(error))
        a.receipt.write_text(json.dumps(result,indent=2)+'\n')
        print('CHAIN_OUTCOME='+result['outcome'])

if __name__=='__main__':main()
