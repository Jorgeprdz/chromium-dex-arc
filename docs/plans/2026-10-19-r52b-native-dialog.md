# R5.2B directed native-dialog diagnosis

Work only in the existing forensic worktree, based on b4e0883. The user approved
minimal fixes supported by causal tests, instrumentation and a report, with no
build, merge, cherry-pick, supervisor change or active-branch mutation.

Hypothesis: an absent active browser-controls stack reports hiddenRatio=1, so
ChromeTabModalPresenter defers attachment indefinitely while already showing the
scrim. Prove this with pinned manager/provider and presenter methods plus real
Android views under Robolectric. This proves a source-level failure mechanism;
installed-device provider values remain a separate evidentiary requirement.

1. Preserve the existing twelve-case evidence; trace request/model/presenter.
2. RED: absent active controls must permit dialog attachment and layout; visible
   controls still wait for their normal visibility condition.
3. If reproduced, fix readiness locally in the presenter only, including pending
   state when controls disappear. Do not change shared hidden-ratio semantics.
4. Add bounded opt-in metadata at the deferred/attach/remove boundary, correlate
   by model identity, record no title, origin, message or input.
5. GREEN and dismissal/value/cleanup regressions; patch reconstruction/checkpoint
   compatibility audit. Keep native GPU and installed-APK acceptance pending.
6. Commit isolated change and report; no build dispatch.
