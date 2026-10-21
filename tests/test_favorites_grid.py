"""Compile the delivered column policy; Android layout acceptance remains separate."""
from pathlib import Path
import subprocess, tempfile, unittest
from test_group_projection import method
ROOT=Path(__file__).resolve().parents[1]
class FavoritesGridPolicyTest(unittest.TestCase):
    def test_columns_and_menu_threshold_across_densities(self):
        source=(ROOT/'chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsView.java').read_text()
        code='public class GridProbe {'+method(source,'static int favoriteColumns(')+'''
 public static void main(String[] args) {
  for(int slot:new int[]{72,94,144,189,216}) {
   if(favoriteColumns(4*slot,slot)!=4)throw new AssertionError("four wide");
   if(favoriteColumns(2*slot,slot)!=2)throw new AssertionError("two narrow");
   if(favoriteColumns(2*slot-1,slot)!=0)throw new AssertionError("menu fallback");
   for(int width=0;width<14*slot;width++) {
    int columns=favoriteColumns(width,slot);
    if(columns==1 || columns<0 || columns*slot>width)throw new AssertionError("overflow or single column");
   }
  }
 }
}'''
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'GridProbe.java';path.write_text(code)
            subprocess.run(['javac',str(path)],check=True)
            subprocess.run(['java','-cp',tmp,'GridProbe'],check=True)
