"""Execute the production spinner method on JVM; sparse fixture, NOT Chromium integration."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/TabListMediator.java"

def probe(source, assertions):
    method = source.split('    void setThumbnailSpinnerVisibility(', 1)[1]
    method = '    void setThumbnailSpinnerVisibility(' + method.split('    void updateThumbnailFetcher(', 1)[0]
    java = '''public class SpinnerProbe {
      static class Tab { int getId() { return 1; } }
      static class TabListLayoutType { static final int FLAT=0; }
      static class TabModel { static final int INVALID_TAB_INDEX=-1; }
      static class TabProperties { static final int SHOW_THUMBNAIL_SPINNER=1; }
      static class PropertyModel { void set(int key, boolean value) {} }
      static class Item { PropertyModel model=new PropertyModel(); }
      static class Models { Item get(int index) { return new Item(); } }
      int mLayoutType=1;
      Models mModelList=new Models();
      int getIndexFromTabId(int id) { return TabModel.INVALID_TAB_INDEX; }
      void updateThumbnailFetcher(PropertyModel model, int id) {}
    ''' + method + '''
      public static void main(String[] args) {
        boolean expected=Boolean.parseBoolean(args[0]);
        if (SpinnerProbe.class.desiredAssertionStatus()!=expected) throw new IllegalStateException("JVM assertion mode");
        SpinnerProbe probe=new SpinnerProbe();
        boolean threw=false;
        try { probe.setThumbnailSpinnerVisibility(new Tab(),true); }
        catch(AssertionError error) { threw=true; }
        if(threw!=expected) throw new IllegalStateException("Release must not throw; debug must assert");
        probe.mLayoutType=0;
        probe.setThumbnailSpinnerVisibility(new Tab(),true);
      }
    }'''
    with tempfile.TemporaryDirectory(prefix='archium-spinner-') as d:
        path = Path(d) / 'SpinnerProbe.java'
        path.write_text(java)
        subprocess.run(['javac', '-d', d, str(path)], check=True, capture_output=True, text=True)
        return subprocess.run(['java', '-ea' if assertions else '-da', '-cp', d,
                               'SpinnerProbe', str(assertions).lower()], capture_output=True, text=True)


class ThumbnailSpinnerLayoutGateTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(shutil.which('javac') and shutil.which('java'), 'Real JVM is required')

    def test_release_nonflat_has_no_artificial_crash(self):
        result = probe(SOURCE.read_text(), False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_debug_nonflat_asserts_with_ea(self):
        result = probe(SOURCE.read_text(), True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unconditional_throw_mutant_is_rejected_in_release(self):
        source = SOURCE.read_text().replace('assert mLayoutType == TabListLayoutType.FLAT;',
            'if (mLayoutType != TabListLayoutType.FLAT) { throw new AssertionError(); }')
        self.assertNotEqual(probe(source, False).returncode, 0)

    def test_removed_assert_mutant_is_rejected_in_debug(self):
        source = SOURCE.read_text().replace('assert mLayoutType == TabListLayoutType.FLAT;', '')
        self.assertNotEqual(probe(source, True).returncode, 0)

if __name__ == "__main__":
    unittest.main()
