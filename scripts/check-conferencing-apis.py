#!/usr/bin/env python3
"""Compile delivered Java entrypoints against the genuine SDK; Chrome/JNI seams explicit.

This is not a Chromium link, an Android consent test, or WebRTC frame acceptance.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--android-jar', type=Path, required=True)
a = p.parse_args()
assert a.android_jar.is_file()
stubs = {
'org.jni_zero.CalledByNative': 'public @interface CalledByNative {}',
'org.jni_zero.JniType': 'public @interface JniType {String value();}',
'org.jni_zero.NativeMethods': 'public @interface NativeMethods {}',
'org.chromium.build.annotations.NullMarked': 'public @interface NullMarked {}',
'org.chromium.build.annotations.Nullable': '@java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE}) public @interface Nullable {}',
'org.chromium.build.NullUtil': 'public class NullUtil {public static <T>T assumeNonNull(T x){return x;}}',
'org.chromium.base.ContextUtils': 'public class ContextUtils {public static android.app.Activity activityFromContext(android.content.Context c){return null;}}',
'org.chromium.base.ServiceLoaderUtil': 'public class ServiceLoaderUtil {public static <T>T maybeCreate(Class<T> c){return null;}}',
'org.chromium.base.Log': 'public class Log {public static void e(String t,String s,Object... a){} public static void d(String t,String s,Object... a){}}',
'androidx.activity.result.ActivityResult': 'public class ActivityResult {public int getResultCode(){return 0;}public android.content.Intent getData(){return null;}}',
'androidx.fragment.app.FragmentActivity': 'public class FragmentActivity extends android.app.Activity {}',
'org.chromium.ui.base.WindowAndroid': 'public class WindowAndroid {public java.lang.ref.WeakReference<android.content.Context> getContext(){return null;}}',
'org.chromium.url.GURL': 'public class GURL {}',
'org.chromium.chrome.browser.profiles.Profile': 'public class Profile {public static Profile fromWebContents(org.chromium.content_public.browser.WebContents w){return null;}}',
'org.chromium.content_public.browser.WebContents': 'public class WebContents {public boolean isDestroyed(){return false;}public org.chromium.ui.base.WindowAndroid getTopLevelNativeWindow(){return null;}}',
'org.chromium.chrome.browser.desktop_site.DesktopSiteUtils': 'public class DesktopSiteUtils {public static boolean shouldOverrideDesktopSite(org.chromium.chrome.browser.profiles.Profile p,org.chromium.url.GURL u,android.content.Context c){return false;}public static boolean isArchiumDocumentPipEnabled(android.content.Context c){return false;}}',
'org.chromium.chrome.browser.content.ContentUtilsJni': 'class ContentUtilsJni {static ContentUtils.Natives get(){return null;}}',
'org.chromium.chrome.browser.tab.Tab': 'public class Tab {public int getId(){return 0;}public String getTitle(){return "";}public void loadIfNeeded(boolean forceBackingSize){}public org.chromium.content_public.browser.WebContents getWebContents(){return null;}}',
'org.chromium.content_public.browser.media.capture.ScreenCapture': 'public class ScreenCapture {public static void onPick(org.chromium.content_public.browser.WebContents w,androidx.activity.result.ActivityResult r){}}',
'org.chromium.chrome.browser.media.AllowedScreenCaptureLevel': 'public @interface AllowedScreenCaptureLevel {int DESKTOP=4;}',
'org.chromium.chrome.browser.media.MediaCapturePickerManager': '''public class MediaCapturePickerManager {
 public static class Params {public org.chromium.content_public.browser.WebContents webContents;public int allowedCaptureLevel;public boolean captureThisTab,excludeMonitorTypeSurfaces,excludeSelfBrowserSurface;}
 public interface Delegate {boolean isActive();void onCancel();void onPickWindow();void onPickScreen();void onPickTab(org.chromium.content_public.browser.WebContents w,boolean audio);}
 public static class Result {static final int CANCELLED=0,WINDOW_SELECTED=1,TAB_SELECTED=2,SCREEN_SELECTED=3;}
 static void recordResult(int r){}static void bringTabToFront(android.content.Context c,org.chromium.chrome.browser.tab.Tab t){}
}''',
'org.chromium.chrome.browser.media.MediaCapturePickerHeadlessFragment': '''public class MediaCapturePickerHeadlessFragment {
 @java.lang.annotation.Target({java.lang.annotation.ElementType.TYPE_USE}) @interface CaptureAction {int CAPTURE_CANCELLED=0,CAPTURE_WINDOW=1,CAPTURE_SCREEN=2;}
 interface Delegate {void onPicked(int action,androidx.activity.result.ActivityResult result);}
 static MediaCapturePickerHeadlessFragment getInstance(androidx.fragment.app.FragmentActivity a){return null;}
 void startAndroidCapturePrompt(Delegate d,android.content.Intent i){}
}''',
}
with tempfile.TemporaryDirectory(prefix='archium-conferencing-sdk-') as temporary:
    work = Path(temporary)
    sources = []
    for name, text in stubs.items():
        package, cls = name.rsplit('.', 1)
        f = work / (name.replace('.', '/') + '.java')
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text('package ' + package + ';\n' + text)
        sources.append(f)
    for name in ['chrome/browser/android/content/java/src/org/chromium/chrome/browser/content/ContentUtils.java',
                 'chrome/android/java/src/org/chromium/chrome/browser/media/MediaCapturePickerInvoker.java']:
        sources.append(ROOT / '.source-modified' / name)
    sources.append(ROOT / 'chromium/chrome/browser/android/content/java/src/org/chromium/chrome/browser/content/ArcDesktopPolicyBridge.java')
    sources.append(ROOT / '.source-reference/chrome/android/java/src/org/chromium/chrome/browser/media/MediaCapturePickerDelegate.java')
    subprocess.run(['javac', '-cp', str(a.android_jar), '-d', str(work/'classes'), *map(str, sources)], check=True)
print('CONFERENCING_ANDROID_SDK_API=PASS; CHROME_JNI_LINK=PENDING_CI; DEVICE_STREAM=PENDING')
