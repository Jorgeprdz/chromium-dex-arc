# Mobile Floating V2 Implementation Plan

> For agentic workers: execute inline with superpowers:executing-plans. No subagents (user constraint).

**Goal:** Implement the approved V2 overlays: real web content behind both glass capsules, existing omnibar dimensions and four native lower actions.

**Architecture:** Phone-only opt-in in BrowserControlsManager exposes zero web-content reservation while retaining raw control dimensions for restoration. Native ToolbarPhone and the existing bottom delegate retain their views/actions. A bounded PixelCopy sampler reads only the two capsule regions of the compositor SurfaceView; small bitmaps are blurred on a worker and painted by background Drawables, leaving native editors/icons sharp. Clear buffers on tab/mode/focus/lifecycle transitions; no saved captures, JS, engine changes or new dependencies.

**Tech Stack:** pinned Chromium Android, Java, Android Bitmap/PixelCopy/HandlerThread, existing host and native JUnit gates.

- [x] A. RED/GREEN viewport policy: zero content insets/offsets only during phone browsing, raw dimensions preserved, native paths restored for Desktop/editor/NTP/Hub. Test delivered getter bodies, transitions and duplicate declarations. Preserve fullscreen/IME owners.
- [x] B. RED/GREEN glass: source crops bounded to SurfaceView, limited buffers/in-flight copies, worker blur, generation checks and clear on source change/destroy. Native view tests with explicit source boundaries; no application shadows.
- [x] C. Integrate backgrounds into ToolbarPhone and ArcPhoneNavigation, remove opaque trays, preserve existing bounds/actions. Wire current tab, configuration, focus, Hub and destroy events via ToolbarManager.
- [x] D. Run SDK preparation, original Chromium shadow policy, affected JUnit, patch application/transition/reproducibility; inspect native method/API declarations before commit. Update TODO and validation with real results and device/build limitations.

No Actions, clean build, heavy checkpoint or APK publication without fresh authorization. Real visual/performance acceptance remains pending a candidate APK, including both themes, keyboard, secure surfaces, scrolling and Desktop regression.

Local verification completed; results and device/integrated limitations: [R5_FLOATING_V2.md](../../validation/R5_FLOATING_V2.md). These checked implementation steps do not mean device acceptance.
