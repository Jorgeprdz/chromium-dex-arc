R5 compositor probe uses only local synthetic content; no accounts or external assets.

Serve this directory on loopback and use an authorized `adb reverse` for that port.
Open `r5-compositor.html` in a new Archium tab. Record the exact APK hash/version,
Chromium pin, Android release, display/window size, density and selected UI mode.

Compare Archium, Chrome and Samsung Internet on the same device. For each browser:

1. Run Scroll cycle at least five times; inspect all image/text/canvas tiles.
2. Open/close alert, confirm, prompt and HTML dialog separately. Check keyboard,
   mouse/touch, scrim removal and focus restoration.
3. Resize narrow/maximized windows, collapse/expand sidebar, minimize/restore,
   switch tabs, lock/unlock and repeat phone ↔ DeX transitions without reloading.
4. Repeat in incognito; record viewport measurements before/after each transition.
5. Capture narrowly scoped compositor/renderer/WindowManager diagnostics and
   synthetic screenshots. Keep unrelated user tabs/notifications out of reports.

PASS requires observed visual results on the target device. The probe itself,
Robolectric, compilation and a successful installation do not imply visual PASS.
