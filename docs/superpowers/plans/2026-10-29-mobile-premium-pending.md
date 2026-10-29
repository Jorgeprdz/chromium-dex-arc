# Mobile premium pending implementation plan

> Execute inline using superpowers:executing-plans and test-driven-development. One final logical commit as explicitly requested; no per-task commits, builds, installs, workflows or PRs.

**Goal:** Refine the existing mobile floating surfaces and contextual aura, pending the next authorized APK.
**Architecture:** Existing ArcPhoneGlass.Backdrop, four native action targets, native bottom sheet and status overlay. Add a small shared palette from the exact existing getArcPhonePageColor source. Preserve the approved pull implementation and all native geometry/input owners.
**Tech stack:** Pinned Chromium Android Java, existing drawable/property animation and local Robolectric fixtures.
**Spec:** User's MOBILE PREMIUM VISUAL POLISH prompt and mandatory DYNAMIC COLOR SYSTEM annex (annex overrides fixed blue).

## Global constraints
- Isolated worktree and branch assistant/archium-r5-mobile-polish-pending from 677c73fcebd14d37b52ec68e2dffba627282c0bf.
- Original branch/tree, run 40819836489 and installer monitor remain untouched.
- Exactly one commit: style(mobile): premium floating UI, adaptive status fade and contextual contextual aura.
- During implementation: NO BUILD / NO APK / NO INSTALL / NO WORKFLOW. The later user-authorized watchdog is the only deferred build/install path. No merge commit, history rewrite or automatic PR.
- No camera/UA/zoom logic/compositor/SurfaceView/insets/viewport changes.
- ArcPhonePullReveal.java and its color resolver and gesture bridge remain byte-identical.
- Existing sampling cadence and captures unchanged; colors use metadata events only.
- Native actions Inicio | Nueva | Pestañas | Menú remain in order with labels and hit targets.
- No exact render-match claim: no approved mobile render file was identified by name in this request; physical captures require a future authorized APK.

## Ownership audit before edits
| Area | Owner retained |
|---|---|
| Omnibar bounds/editor/paint | ToolbarPhone native location-bar rectangle and native editor |
| Glass composition / limited readback | ArcPhoneGlass; ToolbarManager attaches existing targets |
| Status indicators and visibility | StatusBarColorController + existing ArcPhoneStatusFade.StatusVisibility |
| Floating navigation/host switch | ArcPhoneNavigation + BottomControlsCoordinator/BottomBarHostManager |
| Scroll/autohide/reveal/IME/insets | Existing ToolbarManager, SwipeRefreshHandler, native bottom/edge coordinators |
| Menu, dismissal, scroll | Existing ArcPhoneNavigation.MenuSheet and BottomSheetController |
| Dynamic color | ToolbarThemeColorProvider.getArcPhonePageColor(tab), already used by pull-to-reveal |

## Review focus
- A custom external homepage must not falsely select Home; tab hub and menu must follow real native lifetime.
- Color metadata can change while neutral toolbar color stays unchanged; all new visual consumers must receive relevant changes without sampling.
- Animators must stop on destruction, respect disabled animations and avoid any layout change or stale view callback.
- Status tint transitions must preserve the native icon contrast authority and hidden/IME/fullscreen ownership.
- Original pull corners, gap fill and touch behavior must remain unchanged; no visual acceptance can be inferred from mocked compositor tests.

## Task 1: Cohesive mobile visual implementation and regressions
**Interfaces:** Page color -> shared palette -> aura/status; existing Backdrop -> floating finish; Host read-only state -> native-context selection/menu. No native action handler changes.
- [x] Baseline focused mobile Android suite; expect PASS or diagnose fixture/environment separately.
- [x] Add failing tests for contextual gradient aura, no permanent New selection, cancellation/disabled animations, dynamic palette and real Home semantics; expect behavior failures before implementation.
- [x] Implement palette and aura on existing pills; preserve navigation/actions/layout. Add metadata-only color propagation.
- [x] Add failing glass/status tests for translucent material, scoped dynamic tint and contrast; implement using existing drawables only.
- [x] Refine existing sheet's favicon/header/cards/zoom alignment and three-dot glyph; read native favorite state, preserve handlers and stale-page guard.
- [x] Run focused Android suite and relevant host ownership/insets/gesture contracts. Expect all PASS; record scope and counts.
- [x] Verify pull-to-reveal source/resolver/bridge unchanged, camera unchanged, patch generation reproducible, SDK API compilation and diff check.
- [x] One fresh final source review; fix substantive findings with regression tests. No implementer subagents.
- [x] Commit once, audit workflow triggers before optional pending-branch push. Never dispatch Actions.

## Handoff
IMPLEMENTED / COMMITTED / PENDING NEXT BUILD / NO BUILD / NO INSTALLATION / DEVICE VALIDATION PENDING.
Future integration: cherry-pick the single pending commit onto the next authorized source, rerun relevant preflight, then build only on explicit authorization. Pending Samsung matrix: scroll under both bars, all reveal frames/corners, IME/fullscreen/rotation/DeX transitions and native menu/tab lifecycle.

## Subsequent user authorization: deferred build watchdog
The user explicitly requested that a watchdog launch this implementation after run 40819836489 finishes. This authorizes one later incremental chain, after the mobile commit and tests are complete. It overrides NO BUILD only for that deferred dispatch. Installation was initially excluded; the subsequent explicit user authorization below permits the verified deferred installation. The existing run/installer stays untouched. Because the existing R5 workflow accepts only the build branch, the watchdog may fast-forward its remote ref from exact base 677c73f to the tested pending SHA only after successful completion; refuse a moved ref, concurrent workflow, invalid checkpoint or ambiguous prior dispatch. No merge commit, history rewriting, workflow changes or repair loops. Watchdog files/receipts remain private and separate from the visual commit.

Subsequent user message explicitly authorizes **build and install** through that watchdog. The later verified installer may therefore update this candidate, but only after the older installer has settled and after APK/package/ABI/source/hash/signature/device verification. Wait while media capture is active; no data clearing, force-stop or blind retries. This supersedes the earlier NO INSTALLATION handoff limit only for the authorized deferred candidate.
