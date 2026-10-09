# Archium Arc parity correction plan

**Goal:** Correct the reported DeX geometry and navigation failures while preserving native Chromium behavior and Android window decorations.

**Architecture:** Extend the existing Arc composition and policy. Keep Chromium responsible for tab models, URL editing, bookmark persistence, compositor sizing and the native search overlay; keep Android responsible for the caption and window controls.

**Spec:** User's original ARC geometry specification and subsequent “ARC ORIGINAL vs. ARCHIUM ANDROID” annex, supplied in this conversation.

**Constraints:** Same worktree and branch; retain unrelated pending work, `ARCHIUM_BUILD_SCOPE=arc-media` and disabled local passwords. The user subsequently explicitly authorizedcommit/run/monitor/automaticverifiedinstallation and asked root to pauseaftermonitorlaunch. No merge. LinkedIn diagnosticsremovedfromscope.

**Review focus:** Final SideUi animation commit, nullable native caption state, incognito model transitions, caller gesture exclusion restoration, and narrow/short windows must preserve working native controls.

- [x] Reproduce stale web clipping on sidebar collapse; execute the actual SideUi producer/consumer boundary in regression probes.
- [x] Refresh Arc clipping on committed native specs, and unregister its observer on destruction.
- [x] Test native compact-origin display, focused editing and full URL copy before adapting `UrlBarMediator` and `LocationBarTablet`.
- [x] Test and implement the shared native bookmark bridge and three-column tile layout, including observer lifetime, folders, private navigation and scrolling.
- [x] Test and implement native caption gesture ownership release while its toolbar is suppressed; preserve caller rectangles and MOBILE restoration.
- [x] Test and implement gradient, regular-tab contrast/typography and restrained native New Tab styling, with exact MOBILE restoration.
- [x] Integrate bookmark bridge, caption suppression API, native desktop search initialization/routing and continuous frame appearance in existing coordinators.
- [x] Gate the horizontal bookmark surface through the existing stacker contract; retain native provider width notifications and preferences.
- [x] Review the expanded-width allocator against measured density/window bounds and preserve intentional user resizing. Actual 206/393 discrepancy remains BLOCKED pending device inputs.
- [x] Investigate LinkedIn and sidebar-window disappearance independently; preserve private device evidence outside tracked files and report unproven causes explicitly. Windowdisappearance runtimevalidation remains pending; LinkedInremovedfromscope byuser.
- [x] Regenerate the pinned Chromium patch and run both mandatory full checks with Python 3.12 and JDK 17; repair every failure. Repository262/262(final), preparation101files PASS.
- [x] Review sources and deliver geometry comparisons, UI acceptance matrix, regressions, residual blockers and commit readiness in docs/arc-parity-review-20261009.md. Sourceverdict READY for authorizedcommit/buildafterfinalchecks; visualAndroidacceptance remains PARTIAL untildevicevalidation.
