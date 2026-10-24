# Phone full-window / floating input regression

Reviewed installed candidate:63ea9314483288a729f226460c3d43256b7e8ef3, run40068726423. Installation receipt identifies package app.archium.android and APK SHA256 d4d1df3331e1c578f5957c80676663b1943f41a876209d2ad6dd1c4fd08bed34. User rejects its solid bands; previous visual acceptance is FAIL.

## Device evidence

Own captures before/down/up and UIAutomator dumps: `/workspace/.local/state/archium-r5-fullscreen-regression/`. Expanded compositor/WebView bounds [0,86][904,1966]; compact bounds [0,86][904,1766]. The added phone top86/bottom200 margins remove real page area and expose the solid Activity background. This is the demonstrated cause of the compact bottom band; the candidate removes that margin owner and its layout/IME callbacks entirely. Compacting must move controls, never resize the web surface.

A second input owner was overlooked: pinned Chromium ToolbarControlContainer consumes ACTION_DOWN across its rectangular native bounds, even where the floating toolbar is transparent. New phone-only dispatch opt-in declines DOWN outside the actual translated/visible address capsule, including rounded transparent corners. Android then performs ordinary sibling hit testing; there is no manual event forwarding, synthetic click or transparent interception layer. Existing gesture sequences, focused editing, native pages/Desktop and visible find-in-page controls retain native routing. The opt-in resets at teardown.

The device InputDispatcher also delivered a probe at(680,53) to the separate Android StatusBar window (system-touch-dispatch.txt). Returning false in an Activity cannot forward that system-owned touch to web content. App-area passthrough and system-bar touch ownership are separate. A choice was presented for web controls placed beneath system indicators: temporarily hide indicators when compact, or retain only a system-height safe region. No such visibility change has been made without the user's choice; native status gestures remain available. This unresolved case is not reported as fixed.

## Transparent, diffused status surface

Reuse ArcPhoneGlass's bounded web-content sampler for a status-height target, not window capture. Its sample-only backdrop paints the blurred web frame without the pill tint/opaque popup fallback. A Drawable-only mask fades blur into the live page; native icons belong to Android above it. Existing theme palette/hysteresis selects a lighter translucent contrast gradient. No touch View, DOM changes or new dependencies. Expanded omnibar/navigation material and dimensions unchanged. Protected/unavailable samples retain the contrast fade; no fake claim of successful sampling.

Desktop's frame/colors/ratios/Spaces untouched; only the obsolete call releasing the removed phone margin owner is removed. Existing popup readability, compact width reattachment and NTP scene fixes preserved. NTP redesign stays deferred.

## Local evidence and pending acceptance

RED: full-window contract catches the margin call; native floating-dispatch opt-in absent; status sample/backdrop API absent. Added gradient-density/AA regression checks. GREEN:440 complete host tests PASS (703.385s); final5 input/adaptive tests PASS including translated/hidden/corner hit masks.167 Robolectric executions PASS with original Chromium shadow policy. SDK37.2 isolated preparation PASS; extracted delivered native touch-filter field/setter/dispatch compile against genuine SDK37.2 (resource ID boundary only). Host/native boundaries are explicit; none of these is candidate graphical acceptance.

198-file patch application, real checkpoint-source delta in hash-verified sparse fixture,187 unchanged timestamps and byte-identical regeneration PASS. Sparse fixture is not a real checkpoint restore. Source40049206996-1 still valid metadata/identity,4 groups25 parts; CI must check capacity and every part hash before restoration. Last successful40068726423 has APK/receipt only, no newer checkpoint.

No new build dispatched yet. One incremental build is authorized; system-indicator interaction choice remains pending. Physical candidate acceptance still requires: full-height page during scroll/compact/expand; no solid bands; tap web controls above/around the pill; exact system-indicator case per chosen behavior; real blur without rectangular cutoff; light/dark; editor/IME/find/menu; fullscreen; rotation; Desktop transition. The phone was returned to Termux after baseline probes.
