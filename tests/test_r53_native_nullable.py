"""Compile the delivered native callback declarations with Chromium TYPE_USE Nullable."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from arc_toolbar_probe import method_body

ROOT=Path(__file__).resolve().parents[1]

class NativeCallbackNullableTest(unittest.TestCase):
    def test_delivered_native_callback_declarations_compile(self):
        paths=[('HolderCallbacks','chrome/android/java/src/org/chromium/chrome/browser/compositor/CompositorViewHolder.java','setArcSplitActivation',['mArcSplitActivation']),
               ('VerticalCallbacks','chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListCoordinator.java','setArcSplitRequest',['mArcSplitRequest','mArcSplitEnabled'])]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);annotation=root/'Nullable.java'
            annotation.write_text('package org.chromium.build.annotations; @java.lang.annotation.Target(java.lang.annotation.ElementType.TYPE_USE) public @interface Nullable {}')
            files=[annotation]
            for name,path,method,fields in paths:
                text=(ROOT/'.source-modified'/path).read_text()
                imports='\n'.join(re.findall(r'^import java\.util\.function\.[^;]+;',text,re.M))
                declarations='\n'.join(re.search(r'^\s*private[^\n]+\b'+field+r'\s*(?:=[^\n]+)?;',text,re.M).group().strip() for field in fields)
                signature=re.search(r'public void '+method+r'\([^)]*\)',text,re.S).group()
                source=imports+'\nimport org.chromium.build.annotations.Nullable;\nclass '+name+' {\nstatic class Tab {}\n'+declarations+'\n'+signature+method_body(text,r'public void '+method+r'\(')+'\n}'
                p=root/(name+'.java');p.write_text(source);files.append(p)
            result=subprocess.run(['javac','-d',str(root),*map(str,files)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
