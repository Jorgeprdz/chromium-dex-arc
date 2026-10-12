"""Execute the shipped suppression expression; no Chromium compositor PASS claim."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from arc_toolbar_probe import method_body

ROOT = Path(__file__).resolve().parents[1]


class CompositedToolbarTest(unittest.TestCase):
    def test_arc_suppresses_texture_and_preserves_xr_and_narrow_reasons(self):
        path = ROOT / '.source-modified/chrome/android/java/src/org/chromium/chrome/browser/toolbar/ToolbarManager.java'
        body = method_body(path.read_text(), r'private void updateToolbarSceneLayerSuppression\(')
        source = '''public class SuppressionProbe {
            boolean mIsXrFsm, mIsVerticalTabsHiddenDueToNarrow, mIsArcToolbarSuppressed;
            static class Supplier { boolean value; void set(boolean v) { value=v; } }
            final Supplier mSuppressToolbarSceneLayerSupplier=new Supplier();
            void updateToolbarSceneLayerSuppression() BODY
            public static void main(String[] args) {
                SuppressionProbe p=new SuppressionProbe();
                for(int mask=0;mask<8;mask++) {
                    p.mIsXrFsm=(mask&1)!=0;
                    p.mIsVerticalTabsHiddenDueToNarrow=(mask&2)!=0;
                    p.mIsArcToolbarSuppressed=(mask&4)!=0;
                    p.updateToolbarSceneLayerSuppression();
                    if(p.mSuppressToolbarSceneLayerSupplier.value!=(mask!=0))
                        throw new AssertionError("texture suppression lost for mask="+mask);
                }
            }
        }'''.replace('BODY', body)
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/'SuppressionProbe.java'
            file.write_text(source)
            subprocess.run(['javac', '-d', directory, str(file)], check=True, capture_output=True)
            result = subprocess.run(['java', '-ea', '-cp', directory, 'SuppressionProbe'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
