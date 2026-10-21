#!/usr/bin/env python3
"""Compile delivered C++ scene with explicit host adapters, NOT a GPU/Android test."""
import argparse, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True)
common=r'''
#pragma once
#include <memory>
#include <vector>
#include <map>
#include <cstdint>
#include <iostream>
#include <algorithm>
#include <cmath>
using jobject=void*;struct JNIEnv {};using SkColor=unsigned;constexpr SkColor SK_ColorWHITE=0xffffffff;
#define DEFINE_JNI(x)
#define DCHECK(x) std::cerr
#define CHECK(x) std::cerr
#define JNIEXPORT
#define JNICALL
namespace base {namespace android {template<class T> struct JavaRef {};}}
template<class T> using scoped_refptr=std::shared_ptr<T>;
template<class T> using raw_ptr=T*;
namespace gfx {
struct Size {int w=0,h=0;Size()=default;Size(int x,int y):w(x),h(y){}int width()const{return w;}int height()const{return h;}bool operator!=(const Size&o)const{return w!=o.w||h!=o.h;}};
struct PointF {float xx=0,yy=0;PointF()=default;PointF(float x,float y):xx(x),yy(y){}float x()const{return xx;}float y()const{return yy;}};
struct Rect {int xx=0,yy=0,w=0,h=0;Rect()=default;Rect(int x,int y,int width,int height):xx(x),yy(y),w(width),h(height){}Size size()const{return {w,h};}int width()const{return w;}int height()const{return h;}};
struct RectF {float xx=0,yy=0,w=0,h=0;RectF()=default;RectF(float x,float y,float width,float height):xx(x),yy(y),w(width),h(height){}float x()const{return xx;}float y()const{return yy;}float width()const{return w;}float height()const{return h;}bool IsEmpty()const{return w<=0||h<=0;}};
}
namespace viz {struct OffsetTag {};}
namespace cc {namespace slim {
class Layer:public std::enable_shared_from_this<Layer> {
 public: int tab_id=-1,clip_width=0;bool live=false,hidden=false;gfx::PointF pos;std::vector<std::shared_ptr<Layer>> kids;
 static std::shared_ptr<Layer>Create(){return std::make_shared<Layer>();}
 void AddChild(std::shared_ptr<Layer> l){kids.push_back(l);} const auto&children()const{return kids;}
 float opacity()const{return 1;}bool hide_layer_and_subtree()const{return hidden;}bool draws_content()const{return true;}
 void SetHideLayerAndSubtree(bool x){hidden=x;}void SetPosition(gfx::PointF x){pos=x;}gfx::PointF position()const{return pos;}
 void SetIsDrawable(bool){}void SetOffsetTag(viz::OffsetTag){}auto RootLayer(){return shared_from_this();}gfx::Size bounds()const{return {};}
};
}namespace android {inline viz::OffsetTag FromJavaOffsetTag(JNIEnv*,const base::android::JavaRef<jobject>&){return {};}}}
namespace ui {struct ViewAndroid{void set_content_offset_x(float){}};}
namespace content {struct WebContents {ui::ViewAndroid view;ui::ViewAndroid*GetNativeView(){return &view;}};}
class TabAndroid {content::WebContents wc;public:content::WebContents*web_contents(){return &wc;}};
namespace android {
class SceneLayer {protected:std::shared_ptr<cc::slim::Layer>layer_=cc::slim::Layer::Create();public:SceneLayer(JNIEnv*,const base::android::JavaRef<jobject>&){}virtual~SceneLayer()=default;virtual bool ShouldShowBackground(){return false;}virtual SkColor GetBackgroundColor(){return 0;}auto layer(){return layer_;}};
class TabContentManager;inline TabContentManager*g_probe_manager=nullptr;
class TabContentManager {std::map<int,TabAndroid>tabs;public:int primary=-1;std::vector<int>visible;
 static TabContentManager*FromJavaObject(const base::android::JavaRef<jobject>&){return g_probe_manager;}
 auto GetLiveLayer(int){return cc::slim::Layer::Create();}TabAndroid*GetTab(int id){return &tabs[id];}
 void UpdateVisibleIds(const std::vector<int>&ids,int p){visible=ids;primary=p;}
};
class ContentLayer{std::shared_ptr<cc::slim::Layer>l=cc::slim::Layer::Create();public:
 static std::shared_ptr<ContentLayer>Create(TabContentManager*){return std::make_shared<ContentLayer>();}auto layer(){return l;}
 void SetProperties(int id,bool live,float,bool,float,float,bool clip,const gfx::Rect&r){l->tab_id=id;l->live=live;l->clip_width=clip?r.width():0;}
};
}
'''
headers=['jni.h','base/android/jni_weak_ref.h','base/android/scoped_java_ref.h','base/memory/raw_ptr.h','base/memory/scoped_refptr.h','chrome/browser/ui/android/layouts/scene_layer.h','cc/input/android/offset_tag_android.h','cc/slim/filter.h','cc/slim/layer.h','chrome/browser/android/compositor/layer/content_layer.h','chrome/browser/android/compositor/layer_title_cache.h','chrome/browser/android/compositor/tab_content_manager.h','chrome/browser/android/tab_android.h','content/public/browser/web_contents.h','ui/android/view_android.h','ui/gfx/geometry/rect_f.h','chrome/android/chrome_jni_headers/StaticTabSceneLayer_jni.h']
(a.work/'common.h').write_text(common)
for name in headers:
 f=a.work/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('#include "common.h"\n')
source=ROOT/'.source-modified/chrome/browser/android/compositor/scene_layer/static_tab_scene_layer.cc'
exe=a.work/'scene-probe'
r=subprocess.run(['g++','-std=c++17','-I',str(a.work),'-I',str(ROOT/'.source-modified'),str(source),str(ROOT/'tests/native/arc_split_scene_probe.cc'),'-o',str(exe)])
if r.returncode:raise SystemExit(r.returncode)
subprocess.run([str(exe)],check=True);print('PASS actual scene C++ at layer/Tab/JNI ADAPTER boundaries; NOT GPU/Android/Pixels')
