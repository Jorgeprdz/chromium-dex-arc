"""Execute delivered identity policy and picker fallback with explicit Java boundaries.

These probes do not simulate a MediaStream or assert device/meeting acceptance.
"""
import unittest
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from test_phone_overlay_insets import method, run_probe

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / '.source-modified'

class GooglebookCaptureTests(unittest.TestCase):
    def test_delivered_entrypoints_compile_against_real_android_sdk(self):
        sdk = os.environ.get('ARCHIUM_TEST_ANDROID_JAR', '/opt/android-sdk/platforms/android-37.2/android.jar')
        self.assertTrue(Path(sdk).is_file(), 'Genuine Android SDK required')
        result = subprocess.run([sys.executable, str(ROOT/'scripts/check-conferencing-apis.py'),
                                 '--android-jar', sdk], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_document_pip_is_per_document_desktop_and_android17_only(self):
        source = (MOD / 'chrome/browser/ui/android/desktop_site/java/src/org/chromium/chrome/browser/desktop_site/DesktopSiteUtils.java').read_text()
        self.assertIn('public static boolean isArchiumDocumentPipEnabled(', source)
        body = method(source, 'public static boolean isArchiumDocumentPipEnabled(')
        code = '''class Context {} public class PipProbe {
 static boolean desktop; static class Build {static class VERSION {static int SDK_INT;}}
 static class ArcDesktopAppearance {static boolean isDesktopWindow(Context c){return desktop;}}
''' + body + '''
 static void check(boolean b){if(!b)throw new AssertionError("Document PiP capability isolation");}
 public static void main(String[] args){Context c=new Context();Build.VERSION.SDK_INT=37;check(!isArchiumDocumentPipEnabled(c));desktop=true;check(isArchiumDocumentPipEnabled(c));Build.VERSION.SDK_INT=36;check(!isArchiumDocumentPipEnabled(c));}}
'''
        run_probe(self, {'PipProbe.java': code}, 'PipProbe')
        native = (MOD / 'chrome/browser/content_settings/request_desktop_site_web_contents_observer_android.cc').read_text()
        self.assertIn('ReadyToCommitNavigation(', native)
        self.assertIn('SetDocumentPictureInPictureAPIEnabled(', native)

    def test_native_googlebook_builder_preserves_actual_version_and_arm_hints(self):
        source = (MOD / 'chrome/browser/android/content/content_utils.cc').read_text()
        body = method(source, 'static void JNI_ContentUtils_SetUserAgentOverride(')
        code = r'''
#include <string>
#include <vector>
#include <optional>
#include <cassert>
#define ARCH_CPU_ARM_FAMILY 1
using JNIEnv=int;using jobject=int;
namespace base::android {template<class T>using JavaRef=T;}
namespace blink {struct UserAgentMetadata {std::string platform="Android",platform_version="17.0.0",architecture="",bitness="",model="SM-S931B",full_version="157.0.8086.0";bool mobile=true,wow64=false;std::vector<std::string>form_factors;};struct UserAgentOverride {std::string ua_string_override;std::optional<UserAgentMetadata>ua_metadata_override;};}
namespace version_info {std::string major="157";std::string GetMajorVersionNumber(){return major;}}
namespace embedder_support {blink::UserAgentMetadata GetUserAgentMetadata(){return{};}std::string BuildUserAgentFromOSAndProduct(std::string os,std::string p){return os+" "+p;}std::vector<std::string>GetFormFactorsClientHint(blink::UserAgentMetadata,bool mobile){return {mobile?"Mobile":"Desktop"};}}
namespace content {struct WebContents {static WebContents instance;blink::UserAgentOverride ua;bool inherit;static WebContents*FromJavaWebContents(int){return &instance;}void SetUserAgentOverride(blink::UserAgentOverride value,bool i){ua=value;inherit=i;}};WebContents WebContents::instance;}
''' + body + r'''
int main(){JNI_ContentUtils_SetUserAgentOverride(nullptr,0,false);auto&wc=content::WebContents::instance;auto m=*wc.ua.ua_metadata_override;
assert(wc.ua.ua_string_override=="X11; CrOS x86_64 14541.0.0 Chrome/157.0.0.0");assert(m.platform=="Android"&&!m.mobile&&m.architecture=="arm"&&m.bitness=="64"&&m.platform_version=="17.0.0"&&m.full_version=="157.0.8086.0"&&m.model.empty());assert(!wc.inherit&&m.form_factors[0]=="Desktop");
version_info::major="158";JNI_ContentUtils_SetUserAgentOverride(nullptr,0,false);assert(wc.ua.ua_string_override.ends_with("Chrome/158.0.0.0"));}
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'profile.cc'; path.write_text(code)
            result = subprocess.run(['g++', '-std=c++23', '-Wall', '-Wextra', str(path), '-o', tmp+'/profile'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            subprocess.run([tmp+'/profile'], check=True)

    def test_environment_default_and_explicit_preference_precedence(self):
        source = (MOD / 'chrome/browser/ui/android/desktop_site/java/src/org/chromium/chrome/browser/desktop_site/DesktopSiteUtils.java').read_text()
        body = method(source, 'public static boolean shouldOverrideDesktopSite(')
        code = '''@interface Nullable {} class Context {} class Profile {} class GURL {}
public class IdentityProbe {
 static boolean desktop, explicit, setting, command, custom;
 static class CommandLine {static CommandLine getInstance(){return new CommandLine();}boolean hasSwitch(String s){return s.equals("user-agent")?custom:command;}}
 static class ChromeSwitches {static String REQUEST_DESKTOP_SITES="request-desktop-sites";}
 static class ArcDesktopAppearance {static boolean isDesktopWindow(Context c){return desktop;}}
 static boolean hasUserUpdatedContentSettings(GURL u,Profile p){return explicit;}
 static boolean readRequestDesktopSiteContentSettings(Profile p,GURL u){return setting;}
 static boolean shouldApplyWindowSetting(Profile p,GURL u,Context c){return false;}
 static boolean isOnEligibleExternalDisplayForDesktopUA(Context c){return false;}
''' + body + '''
 static boolean result(){return shouldOverrideDesktopSite(new Profile(),new GURL(),new Context());}
 static void check(boolean b){if(!b)throw new AssertionError("environment default / explicit preference isolation");}
 public static void main(String[] a){
 check(!result()); desktop=true;check(result());
 explicit=true;setting=false;check(!result()); setting=true;check(result());
 desktop=false;check(result()); explicit=false;check(!result());
 desktop=true;check(result());desktop=false;check(!result());
 command=true;check(result());command=false;custom=true;desktop=true;check(!result());
 }}'''
        run_probe(self, {'IdentityProbe.java': code}, 'IdentityProbe')

    def test_public_picker_requires_unrestricted_source_choice(self):
        source = (MOD / 'chrome/android/java/src/org/chromium/chrome/browser/media/MediaCapturePickerInvoker.java').read_text()
        self.assertIn('static boolean canUseSystemPicker(', source,
                      'unbranded picker still cancels without a public consent path')
        body = method(source, 'static boolean canUseSystemPicker(')
        code = '''public class PickerPolicyProbe {
 static class AllowedScreenCaptureLevel {static final int DESKTOP=4;}
 static class MediaCapturePickerManager {static class Params {int allowedCaptureLevel=4;boolean captureThisTab,excludeMonitorTypeSurfaces,excludeSelfBrowserSurface;}}
''' + body + '''
 static void check(boolean b){if(!b)throw new AssertionError("capture policy must fail closed");}
 public static void main(String[] a){var p=new MediaCapturePickerManager.Params();check(canUseSystemPicker(p));
 for(int i=0;i<4;i++){p.allowedCaptureLevel=i;check(!canUseSystemPicker(p));}p.allowedCaptureLevel=4;
 p.captureThisTab=true;check(!canUseSystemPicker(p));p.captureThisTab=false;
 p.excludeMonitorTypeSurfaces=true;check(!canUseSystemPicker(p));p.excludeMonitorTypeSurfaces=false;
 p.excludeSelfBrowserSurface=true;check(canUseSystemPicker(p));}}
'''
        run_probe(self, {'PickerPolicyProbe.java': code}, 'PickerPolicyProbe')

    def test_system_result_delivers_single_use_consent_before_start_and_cancels_safely(self):
        source = (MOD / 'chrome/android/java/src/org/chromium/chrome/browser/media/MediaCapturePickerInvoker.java').read_text()
        body = method(source, 'private static void showSystemPicker(')
        policy = method(source, 'static boolean canUseSystemPicker(')
        code = '''public class CaptureResultProbe {
 static final String TAG="test";
 static class Intent {} static class Activity {boolean isFinishing(){return false;}boolean isDestroyed(){return false;}}
 static class FragmentActivity extends Activity {}
 static class Context {static String MEDIA_PROJECTION_SERVICE="projection";MediaProjectionManager manager=new MediaProjectionManager();Activity activity=new FragmentActivity();Object getSystemService(String s){return manager;}}
 static class ContextUtils {static Activity activityFromContext(Context c){return c.activity;}}
 static class MediaProjectionManager {int asks;Intent createScreenCaptureIntent(){asks++;return new Intent();}}
 static class Log {static void e(String tag,String message,Throwable e){}}
 static class WebContents {boolean destroyed;boolean isDestroyed(){return destroyed;}}
 static class CaptureAction {static final int CAPTURE_CANCELLED=0,CAPTURE_WINDOW=1;}
 interface Callback {void picked(int action,Object result);}
 static class MediaCapturePickerHeadlessFragment {static Callback callback;static MediaCapturePickerHeadlessFragment getInstance(FragmentActivity a){return new MediaCapturePickerHeadlessFragment();}void startAndroidCapturePrompt(Callback c,Intent intent){callback=c;}}
 static int tokens;static Object consent;
 static class ScreenCapture {static void onPick(WebContents w,Object r){tokens++;consent=r;}}
 static class AllowedScreenCaptureLevel {static final int DESKTOP=4;}
 static class MediaCapturePickerManager {
  static class Params {int allowedCaptureLevel=4;boolean captureThisTab,excludeMonitorTypeSurfaces,excludeSelfBrowserSurface;WebContents webContents=new WebContents();}
  static class Delegate {boolean active=true;int picked,cancelled;boolean isActive(){return active;}void onCancel(){cancelled++;}void onPickWindow(){if(consent==null)throw new AssertionError("started without consent");picked++;}}
  static class Result {static int CANCELLED=0,WINDOW_SELECTED=1;}static void recordResult(int r){}
 }
''' + policy + body + '''
 static void check(boolean b){if(!b)throw new AssertionError("Android consent / native request lifecycle");}
 public static void main(String[] args){
  Context c=new Context();var p=new MediaCapturePickerManager.Params();var d=new MediaCapturePickerManager.Delegate();Object token=new Object();
  showSystemPicker(c,p,d);check(c.manager.asks==1&&tokens==0&&d.picked==0);MediaCapturePickerHeadlessFragment.callback.picked(1,token);check(consent==token&&tokens==1&&d.picked==1&&d.cancelled==0);
  showSystemPicker(c,p,d);MediaCapturePickerHeadlessFragment.callback.picked(0,null);check(tokens==1&&d.cancelled==1);
  showSystemPicker(c,p,d);d.active=false;MediaCapturePickerHeadlessFragment.callback.picked(1,new Object());check(tokens==1&&d.picked==1);
  d.active=true;showSystemPicker(c,p,d);p.webContents.destroyed=true;MediaCapturePickerHeadlessFragment.callback.picked(1,new Object());check(tokens==1&&d.cancelled==2);
  p.webContents.destroyed=false;p.allowedCaptureLevel=2;int prompts=c.manager.asks;showSystemPicker(c,p,d);check(c.manager.asks==prompts&&d.cancelled==3);
  p.allowedCaptureLevel=4;c.activity=new Activity();showSystemPicker(c,p,d);check(c.manager.asks==prompts&&d.cancelled==4);
 }}'''
        files = {'CaptureResultProbe.java': code,
                 'android/content/ActivityNotFoundException.java': 'package android.content;public class ActivityNotFoundException extends RuntimeException {}'}
        run_probe(self, files, 'CaptureResultProbe')

    def test_googlebook_override_keeps_android_hints_and_real_architecture(self):
        source = (MOD / 'chrome/browser/android/content/content_utils.cc').read_text()
        self.assertIn('"Chrome/" + version_info::GetMajorVersionNumber() + ".0.0.0"', source)
        self.assertIn('spoofed_ua.ua_metadata_override->platform = "Android";', source)
        self.assertNotIn('GetAndroidDesktopCpuArchitecture()', source,
                         'Finch-disabled helper hardcodes x86 on ARM devices')

    def test_native_consent_reaches_existing_backend_without_default_display(self):
        source = (MOD / 'chrome/android/java/src/org/chromium/chrome/browser/media/MediaCapturePickerInvoker.java').read_text()
        self.assertIn('showSystemPicker(context, params, delegate)', source)
        body = method(source, 'private static void showSystemPicker(')
        self.assertIn('createScreenCaptureIntent()', body)
        self.assertIn('ScreenCapture.onPick(params.webContents, result)', body)
        self.assertIn('delegate.onPickWindow()', body)
        self.assertNotIn('createConfigForDefaultDisplay', body)
        self.assertNotIn('DEFAULT_DISPLAY', body)
        self.assertIn('delegate.onCancel()', body)

    def test_both_upstream_capture_features_are_enabled(self):
        for file, feature in [('content/public/common/content_features.cc','kUserMediaScreenCapturing'),
                              ('chrome/browser/media/webrtc/desktop_media_picker.cc','kAndroidMediaPicker')]:
            source = (MOD / file).read_text()
            self.assertIn('BASE_FEATURE(' + feature + ', base::FEATURE_ENABLED_BY_DEFAULT)', source)

    def test_profile_platform_is_normalized_per_effective_user_agent(self):
        source = (MOD / 'third_party/blink/renderer/core/frame/navigator_id.cc').read_text()
        body = method(source, 'String NavigatorID::platform() const')
        self.assertIn('userAgent().contains("X11; CrOS x86_64 14541.0.0")', body)
        self.assertIn('return "Linux x86_64"', body)

if __name__ == '__main__':
    unittest.main()
