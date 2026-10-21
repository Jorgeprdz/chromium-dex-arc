#!/usr/bin/env python3
"""Machine outcome and real Ninja-output progress; never infer recovery from failure."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def progress(out):
    outputs = {}
    log = out / '.ninja_log'
    if log.is_file():
        with log.open(errors='replace') as f:
            for line in f:
                fields = line.rstrip('\n').split('\t')
                if len(fields) == 5:
                    outputs[fields[3]] = [fields[2], fields[4]]
    gates = sorted(p.name for p in (out / '.archium-r5-gates').glob('*/*') if p.is_file())
    payload = json.dumps([sorted(outputs.items()), gates], separators=(',', ':')).encode()
    return {'fingerprint': hashlib.sha256(payload).hexdigest(),
            'completed_outputs': len(outputs), 'completed_gates': len(gates)}


def receipt(env, *, exit_code, packed, complete, progress):
    recoverable = exit_code == 0 and packed and not complete
    return {'schema': 1,
            'outcome': 'BUILD_SUCCESS' if complete and exit_code == 0 else
                       'BUILD_INCOMPLETE' if recoverable else 'BUILD_FAILED',
            'expected_sha': env['GITHUB_SHA'], 'run_id': env['GITHUB_RUN_ID'],
            'source_checkpoint': env['ARCHIUM_SOURCE_TAG'],
            'source_commit': env['ARCHIUM_SOURCE_COMMIT'],
            'source_run_id': env.get('ARCHIUM_SOURCE_RUN_ID', ''),
            'new_checkpoint': env['ARCHIUM_CHECKPOINT_TAG'] if packed else None,
            'new_checkpoint_commit': env['GITHUB_SHA'] if packed else None,
            'exit_code': exit_code, 'recoverable': recoverable,
            'checkpoint_verified': packed, 'pack_verified': packed,
            'progress': progress}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--receipt', type=Path)
    p.add_argument('--exit-code', type=int, default=1)
    p.add_argument('--packed', action='store_true')
    p.add_argument('--complete', action='store_true')
    p.add_argument('--only-if-absent', action='store_true')
    args = p.parse_args()
    data = progress(args.out)
    if args.receipt:
        if args.only_if_absent and args.receipt.exists():
            return
        data = receipt(os.environ, exit_code=args.exit_code, packed=args.packed,
                       complete=args.complete, progress=data)
        args.receipt.write_text(json.dumps(data, indent=2) + '\n')
    else:
        print(json.dumps(data, sort_keys=True))


if __name__ == '__main__':
    main()
