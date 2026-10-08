#!/usr/bin/env python3
"""Run pinned autoninja while letting its native backend own SIGINT shutdown."""
import os
from pathlib import Path
import runpy
import signal
import sys


def defer_interrupt(_signum, _frame):
    # A callable is required: pinned siso.py delegates to its previous handler.
    # Do not raise KeyboardInterrupt: subprocess.call would kill its child.
    pass


if __name__ == '__main__':
    if os.environ.get('DEPOT_TOOLS_USE_VIRTUAL_BUILD_PATH') == '1':
        raise SystemExit('The checkpoint runner requires the ordinary pinned build path.')
    target = Path(sys.argv[1]).resolve()
    summarize = os.environ.get('NINJA_SUMMARIZE_BUILD') == '1'
    if summarize:
        os.environ['NINJA_STATUS'] = '[%r processes, %f/%t @ %o/s : %es ] '
    sys.path.insert(0, str(target.parent))
    sys.argv = [str(target), *sys.argv[2:]]
    signal.signal(signal.SIGINT, defer_interrupt)
    try:
        runpy.run_path(str(target), run_name='__main__')
    except SystemExit as result:
        if not result.code and summarize:
            runpy.run_path(str(target.parent / 'post_build_ninja_summary.py'),
                           run_name='__main__')
        raise
