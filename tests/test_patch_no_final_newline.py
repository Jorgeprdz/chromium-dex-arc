"""Git patch must preserve pinned originals that do not have a final newline."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PatchNoFinalNewlineTests(unittest.TestCase):
 def test_resource_without_final_newline_remains_applicable(self):
  spec=importlib.util.spec_from_file_location('generator',ROOT/'scripts/generate-arc-patch.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);module.ROOT=root
   name='ui/android/java/res/values/ids.xml';old=b'<resources>\n</resources>';new=b'<resources>\n    <item type="id" name="example" />\n</resources>'
   for folder,data in [('.source-reference',old),('.source-modified',new),('src',old)]:
    p=root/folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
   module.main();subprocess.run(['git','init','-q',str(root/'src')],check=True)
   result=subprocess.run(['git','-C',str(root/'src'),'apply',str(root/'patches/archium-desktop.patch')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertEqual((root/'src'/name).read_bytes(),new)
