These three unmodified Apache-licensed sources come from Chromium revision
cfd94726b7b5fb48aedcc32662f2f3fbdbadec35, under
third_party/android_swipe_refresh/java/src/org/chromium/third_party/android/swiperefresh/.
manifest.json records their exact SHA256 values; the local Android runner checks them.

They exercise the actual native refresh threshold/state/callback with ArcPhonePullReveal.
The local runner supplies annotation declarations and a framework PathInterpolator for
AndroidX's easing dependency. Those boundaries do not replace the refresh widget,
its progress drawable, or its circle view. No application shadows are added.
Chromium's integrated JVM target uses its normal native library/dependencies instead
of these local fixture copies. These are local tests, not physical rendering acceptance.
