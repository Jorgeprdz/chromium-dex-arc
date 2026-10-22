#!/usr/bin/env python3
"""Validate read-only CDP resize traces; does not resize, emulate or navigate a page."""
import argparse
import json
from pathlib import Path


def errors(trace):
    failures = []
    identities = {}
    for row in trace:
        for page in row['pages']:
            state = json.loads(page['state']['result']['result']['value'])
            ident = page['id']
            prefix = f"{row['stage']} / {ident}: "
            if abs(state['rootWidth'] - state['width']) > 2:
                failures.append(prefix + 'layout viewport differs from innerWidth')
            if state['narrow'] != (state['width'] <= 700):
                failures.append(prefix + '700px media query differs from pane width')
            if abs(state['visual'] - state['width']) > 2:
                failures.append(prefix + 'visual viewport differs from innerWidth')
            if abs(state['scale'] - 1) > .02:
                failures.append(prefix + 'unexpected visual scale')
            invariant = (state['dpr'], state['timeOrigin'])
            if ident in identities and identities[ident] != invariant:
                failures.append(prefix + 'DPR changed or document reloaded')
            identities[ident] = invariant
    return failures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    args = parser.parse_args()
    problems = errors(json.loads(args.trace.read_text()))
    print('\n'.join(problems) if problems else 'PASS: viewport trace')
    raise SystemExit(bool(problems))
