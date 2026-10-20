"""Execute delivered Java hook bodies and pinned mouse policy/native forwarding conditions."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
class SplitLinkHooksTest(unittest.TestCase):
    def run_gate(self,name):
        with tempfile.TemporaryDirectory(prefix='archium-link-test-') as work:
            p=subprocess.run(['python3',str(ROOT/'scripts'/name),'--work',work],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_native_disposition_preserves_normal_mouse_modifiers(self):
        self.run_gate('test-split-link-disposition.py')
    def test_java_forwarding_and_context_navigation_metadata(self):
        self.run_gate('test-split-link-hooks.py')
