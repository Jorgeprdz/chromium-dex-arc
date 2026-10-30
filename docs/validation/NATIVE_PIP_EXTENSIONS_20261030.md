# Native PiP and extensions source validation — 2026-10-30

Pinned source: `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.
This records source/host results. Candidate APK behavior is pending physical acceptance.
No active meeting, device lifecycle, camera processing, capture lifecycle, native
build, installation, or workflow dispatch was changed by this work.

## Automatic Document PiP

The supplied physical Meet summary establishes: switching an existing tab opens
native Document PiP; directly minimizing does not; an already opened PiP survives
minimization. The pinned Android `AutoPictureInPictureTabModelObserverHelper`
observes tab selection only. Its selected tab remains active when its activity
is hidden. The Android window-occlusion helper is a stub.

The helper now observes native `WebContents::OnVisibilityWillChange` while auto-PiP
is available. On desktop Android 17+ (the existing per-window Document PiP policy),
a selected but hidden/occluded opener is effectively inactive. This enters the
same native media-session path used by tab switching, before hiding, and retains
that state for asynchronous PiP acknowledgement. Showing the selected opener
again follows the existing native exit path. The existing eligibility,
permissions, dismissal, user-media and media-session policies are unchanged.
Phones and older Android retain selection-only activation. Closing and dragging
are suppressed. The observer is detached when auto-PiP observation stops.

The actual transition methods compile and execute in
`tests/test_auto_pip_background.py`. RED: missing native visibility callback.
GREEN: direct hide, duplicate hide, pending acknowledgement state, restore,
occlusion, inactive tabs, closing individual/batched tabs, dragging, unsupported
policy and stopped observation. The existing Document PiP viewport host test
also passes. Four Chromium lifecycle tests were added to the already registered
`auto_picture_in_picture_tab_model_observer_helper_unittest.cc`; they have not
been executed in a Chromium native test binary. Native filter:
`AutoPictureInPictureTabModelObserverHelperTest.*`.

### Zoom investigation — native site route exists, acceptance pending

The physical Zoom summary reports no PiP for minimizing or switching tabs.
Further investigation establishes that this is not evidence of missing Zoom
support. [Zoom Web App release notes](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0066432)
announce automatic tab-switch PiP on August 25, 2025. The deployed public
`web_client/7.2.0.3.12902/js/chunks/loginview.min.js` registers a Media Session
PiP action in its same-origin meeting child and calls the top document's native
Document PiP API. The associated `main-client.min.js` initializes that action
when the site's feature, rendering and meeting-state gates permit it.

Read-only runtime probes coordinated by the root agent establish that the
actual meeting child exposes Document PiP, can access the same-origin top,
has its Zoom PiP feature enabled and is not configured as mobile or PiP-disabled.
Its existing PiP singleton is initialized with 480x270 defaults and event
subscriptions, remains idle and has zero failed window requests. This narrows
the unresolved issue to native entry eligibility/routing; it does not prove a
missing handler. No site handlers or call controls were invoked by those probes.

The Android feature's BASE_FEATURE default is disabled, but this build sets
`is_desktop_android=true` and the pinned `chrome_browser_field_trials.cc`
enables that feature for desktop Android. A proposed additional factory policy
was therefore withdrawn; no factory, feature-default or eligibility override is
included. Native automatic entry also intentionally refuses to replace any
existing PiP. The earlier Meet evidence ends with Meet PiP still open, so that
exclusive-window condition must be excluded when physically accepting Zoom.

The browser-initiated video fallback remains unsuitable: pinned native policy
rejects active camera/microphone sessions, requires one normal player and
requires the primary main frame. This does not block Zoom's separate site-owned
Document PiP route. No native restriction was weakened, no arbitrary video was
selected, and no camera/capture path was changed. Zoom automatic PiP remains
pending a controlled physical test and native route evidence after reconnecting.

## Native extensions menu

`ExtensionsToolbarCoordinatorImpl::showExtensionsMenu` previously set the puzzle
button visible then used `View.post(performClick)` as if posting waited for layout.
Archium moves the native toolbar into a separate containing row. That row can
still be hidden until its global-layout update, or intentionally stay hidden in
a compact rail. Native popup creation could therefore run without valid anchor
bounds.

Programmatic opening now waits for pre-draw and checks visible, measured native
anchor bounds after layout. It uses the native puzzle button where available,
or the existing native app-menu button if the extensions row is hidden. Only the
native `ExtensionsMenuCoordinator` RectProvider is changed for that request;
the real ListMenuButton, native mediator, extension bridge and dismissal owner
remain in place. Dismissal resets the anchor to the puzzle button. Requests are
coalesced and pending pre-draw observation is removed when the owner is destroyed.
The native touch-up dismissal debounce can ignore a programmatic click: pending
state is retained only when the native mediator is initializing or the menu is
open. An ignored click clears pending state so a later request can retry. The
host regression demonstrated RED for this latch before the outcome check and
GREEN for ignored-click recovery while preserving asynchronous initialization.

`tests/test_extensions_menu_anchor.py` executes the actual programmatic-show,
RectProvider, anchor setter and native dismissal methods on a host JVM. RED:
premature click before layout; then missing compact-row fallback. GREEN: hidden,
zero-size and pending-layout anchors wait; ready anchors click once; compact
layouts use the visible app-menu anchor; already-open/destroyed owners ignore
requests; dismissal restores the default anchor.

Pinned native API inspection confirmed: `ListMenuHost` requires its owning view
to be attached; `AnchoredPopupWindow` uses that view's root for its window token
and uses the delegate RectProvider for popup positioning. A visible alternate
native toolbar anchor therefore needs no copied menu or replacement popup.

Physical acceptance still needs Meet direct minimize/app switch, restoration,
dismissal preferences and existing PiP persistence; Zoom registration/site
behavior; and opening the native extensions menu from expanded and compact rails.
