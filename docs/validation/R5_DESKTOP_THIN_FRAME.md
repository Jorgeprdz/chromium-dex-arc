# Desktop thin-frame regression — 24 Oct 2026

## Observed installed build

On the physical Galaxy RFCY203Q5TK, DeX display58, Archium task7990: screenshot and Activity view hierarchy collected in `/workspace/.local/state/archium-r5-desktop-thin-frame/`. Existing task brought forward without navigation or data changes. Screenshot shows the thick top strip. Native caption inset is40px at mdpi; coordinator bounds0,0–2400,1294 and compositor margins/bounds8,48–2392,1286. The tablet toolbar is GONE, so this is not an accidentally re-enabled toolbar.

Commit63ea931 changed content top spacing from original margin +8dp to max(original margin, caption height)+8dp. On this actual window that reserves48px instead of8px. The sidebar caption spacer is separate from this web-content margin. The former host test enforced this enlarged margin and therefore did not catch the visual regression.

## Local correction

Restore original native top margin + the existing8dp frame. Remove the additional caption-inset reservation from applyFrameGeometry. Preserve native window caption controls and sidebar caption-spacer ownership, original margins on teardown, frame material/colors, rail width, Split View and Mobile. No window flags, system caption heights, dependencies or rendering policies changed.

## Evidence and limits

- RED: executed production geometry returned48px for the observed caption40px; regression expects8px. Integration contract also failed. Log `red.log`.
- GREEN:3 geometry/actual idle-tile contrast/integration host probes;10 existing visual-contract tests. Logs `green.log`, `visual-contract.log`.
- SDK37.2 isolated preparation and pinned sparse patch application PASS, including6 related checks. Log `preparation.log`.
- Source checkpoint patch transition PASS:201 modified files verified,184 unchanged timestamps preserved, regeneration byte identical. This is a hash-verified sparse fixture, not restoration of the actual checkpoint. Log `transition.log`.
- Optional historical `test-robolectric-arc-frame.py` runner FAIL before execution: its fixture lacks existing ArcDesktopMaterial fields/updateMaterial. Six javac errors are retained in `android.log`; no Android/Robolectric PASS claimed for that runner. No production workaround or gate relaxation applied.

PENDING: integrated compilation and candidate APK, actual thin-frame screenshot, mouse/touch on web controls beside the native top-right caption buttons, window dragging/maximize/restore, expanded/collapsed rail, Split View and Desktop↔Phone transition. The native caption still owns its own control regions; this fix does not claim those regions become web input targets. No graphical acceptance inferred from host tests.

Run40116057788 remains on0f6c610 and does NOT contain this follow-up. At last monitor poll, authorization/preflight/checkpoint restoration passed and integrated build was running. No cancel, redispatch or extra build performed.
