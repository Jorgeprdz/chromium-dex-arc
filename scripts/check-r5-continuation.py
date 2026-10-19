#!/usr/bin/env python3
"""Require a same-source, verified controlled checkpoint before reusing preflight."""
import argparse
import json
from pathlib import Path


def validate(r, sha, checkpoint, run):
    expected = dict(schema=1,outcome='BUILD_INCOMPLETE',expected_sha=sha,run_id=run,
        new_checkpoint=checkpoint,new_checkpoint_commit=sha,exit_code=0,
        recoverable=True,checkpoint_verified=True,pack_verified=True)
    for key,value in expected.items():
        if r.get(key) != value or type(r.get(key)) is not type(value):
            raise ValueError('Continuation receipt mismatch: ' + key)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--expected-sha',required=True)
    p.add_argument('--source-checkpoint',required=True)
    p.add_argument('--source-run-id',required=True)
    a=p.parse_args();validate(json.loads(a.receipt.read_text()),a.expected_sha,a.source_checkpoint,a.source_run_id)
    print('PREFLIGHT_REUSE=PASS source=' + a.expected_sha)
