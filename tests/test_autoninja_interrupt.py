"""Autoninja must wait for backend flushing when the whole group gets SIGINT."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AutoninjaInterruptTests(unittest.TestCase):
    def test_python_wrapper_waits_for_backend_flush(self):
        self.probe(delegate=False)

    def test_siso_can_delegate_to_the_original_callable_handler(self):
        self.probe(delegate=True)

    def probe(self, *, delegate):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child = root / 'backend.py'
            child.write_text('''import pathlib,signal,sys,time
def stop(signum,frame):
    time.sleep(0.25)
    pathlib.Path(sys.argv[1]).write_text("flushed")
    sys.exit(130)
signal.signal(signal.SIGINT,stop)
time.sleep(10)
''')
            wrapper = root / 'autoninja.py'
            wrapper.write_text('''import signal,subprocess,sys
if sys.argv[1] == "delegate":
    original = signal.getsignal(signal.SIGINT)
    def ignore(signum,frame):
        try: original(signum,frame)
        except KeyboardInterrupt: pass
    signal.signal(signal.SIGINT,ignore)
sys.exit(subprocess.call([sys.executable,sys.argv[2],sys.argv[3]]))
''')
            log = root / '.ninja_log'
            result = subprocess.run(
                ['timeout', '--signal=INT', '--kill-after=3s', '1s', sys.executable,
                 str(ROOT / 'scripts/archium-autoninja.py'), str(wrapper),
                 'delegate' if delegate else 'plain', str(child), str(log)],
                capture_output=True, text=True, timeout=8)
            self.assertEqual(result.returncode, 124, result.stderr)
            self.assertEqual(log.read_text(), 'flushed')
