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
        text = path.read_text()
        body = method_body(text, r'private void updateToolbarSceneLayerSuppression\(')
        guard = method_body(text, r'private void updateArcToolbarSceneGuard\(')
        source = '''public class SuppressionProbe {
            boolean mIsXrFsm, mIsVerticalTabsHiddenDueToNarrow, mIsArcToolbarSuppressed, mArcPhoneOverlayActive;
            static class Supplier { boolean value; void set(boolean v) { value=v; } boolean get() { return value; } }
            final Supplier mSuppressToolbarSceneLayerSupplier=new Supplier();
            final Supplier mArcToolbarSceneGuardSupplier=new Supplier();
            void updateArcToolbarSceneGuard() GUARD
            void updateToolbarSceneLayerSuppression() BODY
            public static void main(String[] args) {
                SuppressionProbe p=new SuppressionProbe();
                for(int mask=0;mask<16;mask++) {
                    p.mIsXrFsm=(mask&1)!=0;
                    p.mIsVerticalTabsHiddenDueToNarrow=(mask&2)!=0;
                    p.mIsArcToolbarSuppressed=(mask&4)!=0;
                    p.mArcPhoneOverlayActive=(mask&8)!=0;
                    p.updateToolbarSceneLayerSuppression();
                    if(p.mSuppressToolbarSceneLayerSupplier.value!=(mask!=0))
                        throw new AssertionError("texture suppression lost for mask="+mask);
                    if(p.mArcToolbarSceneGuardSupplier.value!=(mask!=0))
                        throw new AssertionError("scene guard lost for mask="+mask);
                    // Another native owner releasing suppression must preserve Arc's guard.
                    p.mSuppressToolbarSceneLayerSupplier.set(false);
                    p.updateArcToolbarSceneGuard();
                    if(p.mArcToolbarSceneGuardSupplier.value!=(mask!=0))
                        throw new AssertionError("native release lost guard for mask="+mask);
                }
            }
        }'''.replace('BODY', body).replace('GUARD', guard)
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/'SuppressionProbe.java'
            file.write_text(source)
            compiled = subprocess.run(['javac', '-d', directory, str(file)],
                                      text=True, capture_output=True)
            self.assertEqual(0, compiled.returncode, compiled.stdout+compiled.stderr)
            result = subprocess.run(['java', '-ea', '-cp', directory, 'SuppressionProbe'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
