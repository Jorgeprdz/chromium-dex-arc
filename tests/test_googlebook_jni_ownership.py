"""JNI header ownership regression for the real stage-2 -Wunused-function failure.
Source contracts complement the real SDK probe; they do not claim native linking.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'.source-modified'
BASE='chrome/browser/android/content/'
JAVA=BASE+'java/src/org/chromium/chrome/browser/content/'

class GooglebookJniOwnershipTests(unittest.TestCase):
    def test_native_bearing_header_has_only_its_registering_owner(self):
        owner=MOD/BASE/'content_utils.cc'
        observer=MOD/'chrome/browser/content_settings/request_desktop_site_web_contents_observer_android.cc'
        for source in (owner,observer):
            text=source.read_text()
            if '#include "chrome/browser/android/content/jni_headers/ContentUtils_jni.h"' in text:
                self.assertIn('DEFINE_JNI(ContentUtils)',text,'Native-bearing generated header must stay with its registering owner')
        self.assertIn('DEFINE_JNI(ContentUtils)',owner.read_text())
        self.assertNotIn('DEFINE_JNI(ContentUtils)',observer.read_text())

    def test_observer_uses_called_by_native_only_bridge_and_gn_owns_it(self):
        source=ROOT/'chromium'/JAVA/'ArcDesktopPolicyBridge.java'
        text=source.read_text()
        self.assertNotIn('@NativeMethods',text)
        self.assertEqual(text.count('@CalledByNative'),3)
        for name in ('getArchiumUserAgentMode','isArchiumDocumentPipEnabled'):
            self.assertIn(name,text)
            observer=(MOD/'chrome/browser/content_settings/request_desktop_site_web_contents_observer_android.cc').read_text()
            self.assertIn('Java_ArcDesktopPolicyBridge_'+name,observer)
        build=(MOD/BASE/'BUILD.gn').read_text()
        self.assertEqual(build.count('java/src/org/chromium/chrome/browser/content/ArcDesktopPolicyBridge.java'),2)
        self.assertNotIn('@CalledByNative',(MOD/JAVA/'ContentUtils.java').read_text())

if __name__=='__main__':unittest.main()
