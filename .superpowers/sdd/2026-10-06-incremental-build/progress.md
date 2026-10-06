# SDD ledger — plan: docs/superpowers/plans/2026-10-06-incremental-build.md

Approved three-plan scope. Baseline Python suite 9/9.
Pre-flight Task 1→2: explicit checkpoint commit identity feeds strict restore and transition before GN regeneration; subsequent stages must restore only current identity.
Pre-flight Task 2→3: build artifact consumed only after signature and E2E checks.
Ruling: build transition infrastructure precedes finishing the password component native gate because that gate needs a restored full Chromium checkout. Final APK build remains deferred until both components are implemented. Cost if wrong: early infrastructure change reviewed before component compilation, not a claim of feature completion.
Task 1: in progress.
Task 1 RED: transition tests failed because transition module did not exist; checkpoint identity test failed because explicit source_commit was unsupported.
Task 1 GREEN: 10 real-git transition scenarios and 3 checkpoint cases pass; whole Python suite 20/20. Verified old-only source restoration, removed overlay deletion, unchanged mtimes, parent/leaf symlink and divergent-input rejection, manifest/patch checksums, pinned-git originals, and exception/KeyboardInterrupt rollback of bytes/modes/mtimes.
Task 1 Ruling: rollback covers handled exceptions and KeyboardInterrupt; SIGKILL cannot run cleanup. CI must fail without publishing a checkpoint after any incomplete transition, and next run starts again from the verified old checkpoint. Cost if wrong: partially changed transient runner workspace, never accepted as a continuation checkpoint.
Scope steering 2026-10-06: user added adaptive window desktop policy and keyboard/mouse layer, with mandatory pinned-source investigation before those product changes. Original password/Arc and build plans remain active.
Task 1: complete (commits adb9601..12776ea, tests: python3 -m unittest discover -s tests -p test_*.py → OK)
User steering: after dispatching the final build run, update the monitoring script for that run and pause work. Do not continue installation/E2E automatically after that handoff; user must resume. Continue authorized preparation until dispatch.
Task 2 RED: 7 routing tests showed missing old-source inputs/transition, stale-args GN omission, absent validation gate and unchecked source inputs. Added branch routing, mandatory GN on transition/args changes and one shared 120-minute Ninja budget. CI/native execution remains pending.
Task 2 local GREEN: all 27 Python tests and bash -n passed; actionlint v1.7.12 reports no workflow errors. Source transition precedes GN/Ninja, continuation preserves strict current commit, changed args regenerate GN, validation compiles first, failure stops and timeout publishes only current state. Real CI/GN/native execution pending; Task 2 not marked complete.
