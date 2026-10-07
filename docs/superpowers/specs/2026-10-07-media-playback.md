# Archium multimedia — initial scope

Approved execution context: user requested a separate media branch, accepted the initial scope (audit; MP4/H.264/AAC and web formats; Android decoding/streaming/fullscreen; ARM64 and Googlebook Intel preparation), then said “go”. Work inline without requesting phase-by-phase permission.

Base: 5d0a2f16a9828808a8d5a98a1adc0cdf5a45a33d on feat/media-playback. Chromium 157.0.8086.0 pinned at cfd94726b7b5fb48aedcc32662f2f3fbdbadec35; package app.archium.android.

Reuse Chromium's media pipeline and Android MediaCodec. Set the supported proprietary-codec and FFmpeg flavor arguments, preserving Chromium product branding, sandboxing, native controls and existing DRM policy. Check the effective GN values before compilation. Existing VPx/Opus/AV1 capabilities must remain enabled; HLS and platform HEVC follow pinned upstream defaults. HEVC decoding remains hardware dependent.

Provide local synthetic clear-media fixtures and a browser acceptance page for actual playback, seeking, MSE and HLS. Capability advertisements alone are not playback proof. Fullscreen, audible output and PiP require explicit device observations. EME availability is diagnostic; premium-service DRM is a separate unverified scope.

Prepare a validated x64 configuration from the common ARM64 settings; no Intel compatibility claim without building and testing it. Do not replace the browser pipeline with WebView/ExoPlayer, enable all vendor codecs, alter upstream media files or hardcode hardware support.

Keep the active Arc build and its monitor unchanged. Validate and publish this feature branch independently; serialize any later workflow dispatch behind the existing build. Report five phases: audit, implementation, local validation, publication, APK/device acceptance. Completion is not claimed until the last phase passes.
