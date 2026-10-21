#!/usr/bin/env python3
"""Compile and execute delivered Java link hooks with explicit navigation/router adapters."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
from arc_toolbar_probe import method_body
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
base=ROOT/'.source-modified/chrome/android/java/src/org/chromium/chrome/browser'
impl=(base/'tab/TabWebContentsDelegateAndroidImpl.java').read_text();menu=(base/'contextmenu/ChromeContextMenuPopulator.java').read_text()
open_body=method_body(impl,r'public void openNewTab\(')
menu_body=method_body(menu,r'private void openArcSplitLink\(')
code='''
class GURL {String value;GURL(String s){value=s;}String getSpec(){return value;}}
class ResourceRequestBody {}
class Tab {}
class WindowOpenDisposition {static final int NEW_SPLIT_VIEW=12,NEW_FOREGROUND_TAB=3,NEW_BACKGROUND_TAB=4,SAVE_TO_DISK=7;}
class LoadUrlParams {String url;Object referrer,additional;LoadUrlParams(String s){url=s;}void setReferrer(Object o){referrer=o;}void setAdditionalNavigationParams(Object o){additional=o;}void setHasUserGesture(boolean b){}}
class ArcSplitLinkRouter {
 static boolean eligible=true,handled=true;static int calls;static Tab source;static LoadUrlParams params;
 static boolean canOpen(Tab t,GURL u){return eligible;}
 static boolean open(Tab t,LoadUrlParams p){calls++;source=t;params=p;return handled;}
 static boolean openNative(Tab t,GURL u,String h,ResourceRequestBody b,boolean r){calls++;source=t;return handled;}
}
class NativeDelegate {
 int calls,disposition;GURL url;String headers;ResourceRequestBody body;boolean renderer;
 void openNewTab(GURL u,String h,ResourceRequestBody b,int d,boolean r){calls++;url=u;headers=h;body=b;disposition=d;renderer=r;}
}
class DelegateProbe {
 Tab mTab=new Tab();NativeDelegate mDelegate=new NativeDelegate();
 public void openNewTab(GURL url,String extraHeaders,ResourceRequestBody postData,int disposition,boolean isRendererInitiated) OPEN
}
class Params {
 Object referrer=new Object(),additional=new Object();int taken;GURL url=new GURL("https://example.test/item");
 GURL getUrl(){return url;}Object getReferrer(){return referrer;}Object takeAdditionalNavigationParams(){taken++;return additional;}
}
class MenuProbe {
 Tab source=new Tab();Params mParams=new Params();Tab getTab(){return source;}
 private void openArcSplitLink() MENU
 void run(){openArcSplitLink();}
}
public class LinkHookProbe {
 public static void main(String[] args){
 DelegateProbe p=new DelegateProbe();GURL url=new GURL("https://example.test/");ResourceRequestBody body=new ResourceRequestBody();
 p.openNewTab(url,"X-Test: fixture",body,12,true);assert ArcSplitLinkRouter.calls==1;assert p.mDelegate.calls==0;
 ArcSplitLinkRouter.handled=false;p.openNewTab(url,"X-Test: fixture",body,12,true);
 assert p.mDelegate.calls==1 && p.mDelegate.disposition==3;assert p.mDelegate.body==body && p.mDelegate.url==url && p.mDelegate.renderer;
 ArcSplitLinkRouter.calls=0;p.openNewTab(url,"",null,4,false);assert ArcSplitLinkRouter.calls==0 && p.mDelegate.disposition==4;
 p.openNewTab(url,"",null,7,false);assert ArcSplitLinkRouter.calls==0 && p.mDelegate.disposition==7;
 MenuProbe m=new MenuProbe();ArcSplitLinkRouter.handled=true;m.run();assert m.mParams.taken==1;
 assert ArcSplitLinkRouter.source==m.source && ArcSplitLinkRouter.params.referrer==m.mParams.referrer && ArcSplitLinkRouter.params.additional==m.mParams.additional;
 ArcSplitLinkRouter.eligible=false;MenuProbe stale=new MenuProbe();stale.run();assert stale.mParams.taken==0;
 }
}'''.replace(' OPEN',' '+open_body).replace(' MENU',' '+menu_body)
f=a.work/'LinkHookProbe.java';f.write_text(code)
subprocess.run(['javac','-d',str(a.work),str(f)],check=True);subprocess.run(['java','-ea','-cp',str(a.work),'LinkHookProbe'],check=True)
print('PASS delivered Java shortcut/menu hook bodies; router/JNI/window execution is a separate gate')
