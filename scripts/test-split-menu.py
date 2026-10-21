#!/usr/bin/env python3
"""Compile/execute delivered native menu AnchorInfo, not a pointer/Android visibility test."""
from pathlib import Path
import argparse,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
source=(ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser/compositor/overlays/strip/TabContextMenuCoordinator.java').read_text()
body=method_body(source,r'public static class AnchorInfo').replace('@Nullable ','')
probe='''import java.util.List;
public class MenuProbe {
 public static class AnchorInfo BODY
 public static void main(String[]args){
  AnchorInfo info=new AnchorInfo(17,List.of(17));int[] calls={0};
  assert !info.hasArcSplitAction();info.setArcSplitAction(()->calls[0]++);
  assert info.hasArcSplitAction();info.runArcSplitAction();assert calls[0]==1;
  info.setArcSplitAction(null);info.runArcSplitAction();assert calls[0]==1;
  assert !info.hasArcSplitSeparateAction();
  info.setArcSplitSeparateAction(()->calls[0]+=10);
  assert info.hasArcSplitSeparateAction(); info.runArcSplitSeparateAction(); assert calls[0]==11;
  info.setArcSplitSeparateAction(null); info.runArcSplitSeparateAction(); assert calls[0]==11;
  assert info.getAnchorTabId()==17 && info.getAllTabIds().equals(List.of(17));
 }
}'''.replace('BODY',body)
f=a.work/'MenuProbe.java';f.write_text(probe)
subprocess.run(['javac','-d',str(a.work),str(f)],check=True);subprocess.run(['java','-ea','-cp',str(a.work),'MenuProbe'],check=True);print('PASS delivered AnchorInfo action lifecycle; Android context-menu presentation PENDING APK')
