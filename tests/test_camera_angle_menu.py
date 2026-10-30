"""Compile the delivered browser orientation storage without Android host dependencies."""
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

class CameraAngleMenuTests(unittest.TestCase):
    def test_browser_default_and_stored_angles_are_owned_per_tab(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for path, source in {
                'base/supports_user_data.h': '#pragma once\n#include <memory>\n#include <unordered_map>\n#include <string>\nnamespace base {struct SupportsUserData {struct Data {virtual ~Data()=default;}; std::unordered_map<std::string,std::unique_ptr<Data>> data;Data* GetUserData(const char* key){auto i=data.find(key);return i==data.end()?nullptr:i->second.get();}void SetUserData(const char* key,std::unique_ptr<Data> value){data[key]=std::move(value);}};}\n',
                'content/public/browser/web_contents.h': '#pragma once\n#include "base/supports_user_data.h"\nnamespace content {struct WebContents:base::SupportsUserData {int changes=0;void OnWebPreferencesChanged(){++changes;}};}\n',
            }.items():
                p=work/path
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(source)
            source = work/'case.cc'
            source.write_text('#include "'+str(ROOT/'chromium/chrome/browser/android/content/arc_camera_orientation.h')+'"\n#include <cassert>\nint main(){content::WebContents a,b;assert(arc_camera::Get(nullptr)==-1);assert(arc_camera::Get(&a)==1);assert(arc_camera::Get(&b)==1);for(int turns=0;turns<=3;++turns){arc_camera::Set(&a,turns);assert(arc_camera::Get(&a)==turns);assert(arc_camera::Get(&b)==1);}assert(a.changes==4);arc_camera::Set(&a,-1);assert(arc_camera::Get(&a)==1);arc_camera::Set(&a,99);assert(arc_camera::Get(&a)==1);arc_camera::Set(&b,2);assert(arc_camera::Get(&a)==1);assert(arc_camera::Get(&b)==2);}')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(work),str(source),'-o',str(work/'case')],check=True)
            subprocess.run([str(work/'case')],check=True)


if __name__=='__main__':
    unittest.main()
