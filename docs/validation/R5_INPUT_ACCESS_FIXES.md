# R5 — safe input regions and readable menus

Branch: `assistant/archium-r5-desktop-native-mobile`. Installed/reviewed baseline: `b62ece7d4bc571a7bbdbb1c62107a0a4a993744a`, run40055660112. Candidate not yet built or physically accepted.

## Directed review and limitations

Phone: APKMirror/Google controls under system indicators did not respond to injected taps; compact navigation still overlapped ChatGPT's composer. First-focus omnibox/navigation and the installed alternative keyboard worked in the reviewed cases. Compact width became full width after native reattachment/theme recreation. NTP displayed a rectangular bottom scene. Expanded-pill design/material is approved and preserved.

DeX: Command Bar first click/Escape and Ctrl+T navigation worked in injected-input checks. A disposable Space/folder/pinned entry was created and removed without deleting its live tab; the test tab/Space/folder were then removed and original data preserved. Split layouts visibly adapted during 50→25→50 and25→75→25; CSS viewport/DPR/reload counters were NOT measured. Narrow Split's top search did not respond in two injected-tap attempts: exact input owner/root cause remains unproven. Menu text competed with sidebar text behind; dark header tile labels had weak contrast.

These are baseline observations, not acceptance of this candidate. The user's accidental workspace deletion removed the original screenshot/report files during this session. Do not treat filenames in older reports as retained new evidence. Repository and pinned originals were recovered; every recovered source hash matched the existing manifest before editing. Current recoverable test logs are under `/workspace/.local/state/archium-r5-input-fixes/`.

## Localized candidate changes

* `CompositorViewHolder.setArcPhoneContentInsets`: explicitly owned, idempotent minimum top/bottom margins (never sum an existing native safe reservation twice) move renderer and input host together. Top clears unconsumed status/cutout inset, including padding already consumed by the parent; compact navigation protects the existing native slot height below fixed web composers. IME visibility releases this extra bottom protection to Chromium's native IME layout. Original margins restore on native pages, pause/fullscreen, Desktop transition and teardown. No UA/DOM/JS/zoom changes.
* `ToolbarManager`: reuses existing phone activation and compact-state owner; global layout observes IME/root changes without a new insets consumer. Compact/full controls remain one native slot. On NTP, suppress the duplicate composited bottom scene while retaining native page layout/reservation. NTP redesign remains deferred.
* `ArcPhoneNavigation`: native reattachment obtains the current compact96dp width rather than MATCH_PARENT. Expanded dimensions/material/labels unchanged.
* `ArcPhoneGlass.Backdrop`: milky popup/suggestion surfaces paint their own opaque base before a partial web capture. A valid partial frame previously disabled fallback for uncovered sidebar regions. Omnibar/navigation glass is not milky and keeps its approved material. This removes competing unblurred labels without claiming native sidebar backdrop blur.
* `ArcDesktopCoordinator`/`ArcDesktopPolicy`: release phone-owned margins before Desktop captures its originals; include native caption safe area once in content top margin. This is a candidate for the top-edge input issue, not a proven device fix. Header tile idle labels select contrast against their actual pale tile surface; interaction labels retain the existing selection surface foreground. Sidebar widths, Split ratios and Space model untouched.

Expanded pills still intentionally overlay content. Safe bottom protection is active while compact, including web form focus; this does not claim that every expanded overlay can never intersect a site control. Device checks must confirm compact/expand transitions do not jump or oscillate during scroll.

## Tests and acceptance

RED retained for compact reattachment, partial-frame popup backing, missing safe-content APIs and failing tile AA contrast. GREEN:165 Android/Robolectric executions (original Chromium shadow policy82 methods),3 host geometry/actual tile contrast probes,2 adaptive controls probes; SDK37.2 isolated adapter compilation and197-file sparse application PASS. Actual source-checkpoint patch delta applied in hash-verified sparse fixture;187 unchanged timestamps retained; regeneration byte identical. Sparse fixture has a synthetic Git commit and is not checkpoint restoration or graphical acceptance.

Complete host suite:438 executions in872.353s,437 PASS/1 obsolete static contract FAIL (it required the former web-only bottom-scene flag). Updated that assertion and added an executed native-page/web/fullscreen ownership matrix; affected final suites17 PASS. Final geometry probes include pre-consumed native margins, exact negative-margin restoration and repeated calls. The initial full-suite run is NOT reported as green; CI must run the updated complete suite with preflight enabled. Source40049206996-1: metadata/manifest identity PASS (4 groups/25 parts); CI must verify capacity and every downloaded part hash before restore. No clean build, checkpoint deletion, retry or dispatch yet.

PENDING physical candidate: APKMirror/Google top controls; arbitrary fixed/sticky headers and composers; compact→expanded and theme reattachment; NTP pill; phone/DeX transition; dark/light menus; caption search on narrow Split; input after rotation/IME; fullscreen videos; subfolders/reordering/restart durability; actual mouse hover/right-click and sidebar grab. Small-window Space accessibility remains a known limitation of the existing compact policy and is not marked fixed. No performance measurements or device PASS inferred from JVM/static tests.

## Dispatched candidate — local follow-up record

Candidate63ea9314483288a729f226460c3d43256b7e8ef3 pushed; exactly one dispatch, run40068726423: https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/40068726423 . Authorize and complete CI preflight PASS; build is downloading the verified checkpoint inventory, restoration/integrated compilation/APK still pending. Native Termux monitor /dev/pts/1, watcher17643, CDMX600s and single-attempt verified installer active. State/intent/dispatch/source receipts: /workspace/.local/state/archium-r5-input-fixes/. No retry, clean build or checkpoint deletion. This follow-up updates local documentation only; remote build candidate remains63ea931.

## Installed result rejected — 24-oct-2026

Run40068726423 completed successfully and installed APK d4d1df3331e1c578f5957c80676663b1943f41a876209d2ad6dd1c4fd08bed34 with verified package/certificate/backup. User reports solid bands; own captures confirm the compositor margin regression. Visual acceptance FAIL. Follow-up code, local tests and the separate Android status-window touch constraint are documented in [R5_FULL_WINDOW_INPUT_REGRESSION.md](R5_FULL_WINDOW_INPUT_REGRESSION.md). Successful build/install did not establish visual acceptance.
