### Task 1: Appearance eligibility and persistence

**Files:**
- Modify: `chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java`, `ArcDesktopAppearance.java`.
- Modify: `chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopWindowObserver.java`.
- Modify: `chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/VerticalTabUtils.java`.
- Test: `tests/java/ArcDesktopPolicyTest.java`; Android configuration/lifecycle tests.

**Interfaces:**
- Pure `isArcWindow(int preference, boolean tabletWindow, boolean desktopWindow): boolean`.
- Preference values AUTO, ARC, MOBILE; persist separately from width/collapse state.
- `ArcDesktopAppearance.isDesktopWindow(Context)` remains a compatibility entry point during transition and delegates to the new policy.

- [ ] Replace old test expectations with new RED cases: AUTO tablet true, desktop true, phone false; ARC true independent of manufacturer; MOBILE false; phone orientation alone does not switch AUTO.
- [ ] Run pure Java tests and observe RED.
- [ ] Implement policy using current window/form-factor information, desktop/freeform hints and preference. Remove reliance on Samsung fields for eligibility; use width for geometry only.
- [ ] Add native appearance selector and observer cleanup; recreate/relayout using Chromium restoration where necessary.
- [ ] Run pure and runtime tests for tablet, phone, manual overrides, display move/reconnect and restored tabs. Expected policy and persistence pass.
- [ ] Commit policy and tests.
