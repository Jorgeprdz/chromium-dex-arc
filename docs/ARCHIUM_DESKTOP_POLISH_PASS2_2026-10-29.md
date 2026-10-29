# Archium Desktop polish pass 2 — 29 October 2026

Baseline: current remote R5 HEAD `7e91ec944f0297be67d7faa3893dcfe05aa6354b`.
Independent work branch: `assistant/archium-r5-desktop-polish-pass2-pending`.
The baseline build40936843775 completed successfully and its existing verified
installer reports INSTALL_SUCCESS. No baseline/Mobile pending history was rewritten.

## Visual audit and changes

The latest available owner capture is `Screenshot_20261029_161312_Archium for Android.jpg`
(2048×1152), SHA256 `cb551fb86442cbf4ea6298f1469f38db20756739777457f728fb5bdf3d1cd7c7`.
It was read privately from DCIM/Screenshots; neither owner tabs nor Calendar data
are included here. This is an actual owner screenshot, not a reconstructed render.
It does not establish physical acceptance of this patch or a pixel comparison
against a newly built APK.

| Component | Before | After |
|---|---|---|
| Tab titles | Pinned TextMedium14sp + existing2sp =16sp | **16sp retained**, single line/END ellipsis; no extra increase. Android14+ inverse conversion uses deriveDimension to respect nonlinear font scale and restore native14sp correctly. |
| Tab favicons | Normal22×22dp; pair45×22dp; compact pair32×22dp | **Retained**, including owning container sizing, colors/density and mobile restoration. No extra bitmap enlargement. |
| Favorite mosaic |50dp tiles/26dp optical box | **Unchanged**. Whole-row budget still reserves tab access. |
| Active row | Minimum11dp radius, native elevation | Minimum12dp radius; selected enabled row1dp elevation, ambient24/255 and spot36/255 black shadow. Existing native active/hover/focus/pressed cues retained. |
| Footer | Browser actions and native extensions share one row | Browser menu/camera/info/appearance in row1; same native extension host in row2 using full usable rail width.44dp targets,4dp gap only if row2 visible. |
| Empty/compact footer | Expanded host forcibly made visible; width subtracts browser buttons | Native host visibility remains coordinator-owned; row hidden when empty/compact. Narrow layout accounts for actual menu width; short window keeps native menu and returns secondary height to tabs. |
| Collection budget | Single footer assumption | Visible extension row reserves separately rounded44dp+4dp; stacked compact actions are counted. Collections yield first. Frame/viewports stay unchanged. |
| Space selector |14sp regular, inline font triangle, no section margins |14sp medium, shared16dp vector chevron at trailing edge,8dp compound gap,10dp inner sides,4dp top/2dp bottom margin; same44dp target and menu/selection/persistence. |
| Omnibar | Native URL owner, approved radius/position/geometry | Same geometry/editor/URL spans; desktop-only placeholder color blended78% foreground/22% surface, with4.5:1 contrast floor. Native hint lists restore on exit, including native theme updates. Command-owned hints are not modified. |

Default/user lavender material, frame24/8/16dp relationship, four viewport corners,
52dp collapsed rail, SurfaceView, hit testing, native navigation, sessions, split,
bookmarks/Ctrl+D, tab commands, camera handlers/media permissions, PiP/share and
Mobile pull-to-reveal/aura/status/glass sources remain outside this change.

## Native ownership

Constructor, repeated attachment, late extension discovery, global-layout availability,
desktop/mobile transition and destroy use the same extension view and native menu.
Original parents, indices, layout parameters and menu minimum size restore; handlers
are never rebuilt. A native RecyclerView can have populated adapter models before
layout creates children: extension availability must inspect that adapter rather
than requiring a materialized leaf in a hidden row.

Original row foreground, tint, radius, elevation and shadow colors restore; no
second outline or clip is installed. TranslationZ and drag/reorder remain native.
The subtle shadow's actual DeX clipping/optical appearance remains unverified.

## Local verification

- Complete host suite: **517/517 passed**, 1159.825s; configured Android36 jar, AAPT2 and genuine GN.
- Footer **24/24**, including real AndroidX RecyclerView initially-hidden first-item regression (RED2/24 before fix); geometry **18/18**.
- Sidebar appearance/font scale **34/34**; split favicon bindings **14/14**.
- Collections/Space **44/44**; desktop hint contrast/native restore **4/4**.
- Final SDK preparation **6/6**, including current adapter API; affected host consumers **19/19** after the review fix.
- Installer/updater guard suite **16/16** (private local harness; no install invoked).
- Generated patch/manifest reproduce identically twice. Diff-check, Python compilation, shell syntax and actionlint pass.
- The complete host run began before the final adapter availability fix; that narrow fix received fresh footer/geometry/SDK/consumer checks on the final source. No physical or native-build PASS is inferred.

Real-view probes use Robolectric SDK30/36. Chromium coordinator/resource boundaries
are explicit test adapters; these tests do not establish pixel rendering on DeX.
An initial SDK preparation ran concurrently with patch generation and rejected a
hash mismatch; it is superseded by the final sequential generation/preparation
check. This was a validation scheduling error, not a product build failure.

## Physical acceptance and delivery

**PENDING_DEVICE**: 2400×1350,903×779 and smaller windows; repeated resize;
expanded/collapsed rail; all four corners; omnibox sidebar/top; active/hover/focus;
font scales; actual installed extensions empty/one/many/late-first-item; native menus,
Ctrl+D/L/T, camera orientation, split/reorder, Desktop/Mobile and lifecycle.
No new APK or physical PASS is inferred from a static capture or host tests.
F06 pixelation remains observed with pending cause and is not claimed fixed here.

The user annex authorizes incremental build/install, superseding the earlier
NO BUILD/NO INSTALL delivery mode. The existing workflow, native stage and build
script accept only `assistant/archium-r5-desktop-native-mobile`; the pending branch
alone cannot dispatch an accepted build. Preserve the user's base-branch constraint
until integration authorization is unambiguous. No workflow changes, clean native
build, checkpoint deletion, profile reset, or automatic PR is part of this pass.


## Changed files

- `.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java`
- `.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarTablet.java`
- `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsView.java`
- `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java`
- `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopIcons.java`
- `chromium/chrome/android/junit/src/org/chromium/chrome/browser/arc/ArcCollectionsFocusTest.java`
- `chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopAppearance.java`
- `chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java`
- `docs/ARCHIUM_DESKTOP_POLISH_PASS2_2026-10-29.md`
- `docs/superpowers/plans/2026-10-29-desktop-pass2.md`
- `patches/archium-desktop.patch`
- `patches/upstream-files.json`
- `scripts/check-arc-preparation.py`
- `scripts/test-robolectric-desktop-footer.py`
- `scripts/test-robolectric-desktop-omnibox-contrast.py`
- `scripts/test-robolectric-sidebar-appearance.py`
- `scripts/test-robolectric-sidebar-geometry.py`
- `tests/footer_androidx.py`
