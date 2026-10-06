# SDD ledger — plan: docs/superpowers/plans/2026-10-06-adaptive-desktop.md

User-authored annex is the binding design/instruction; continuing previously authorized inline implementation without reopening approvals. Required pinned-source investigation done and saved on phone before product code for this annex.
Pre-flight Task 1→2: same current-window classifier/metrics shared by RDS and Arc; constants from real pinned AndroidX Window Core.
Pre-flight Task 2→3: native RDS/render policy and native zoom storage remain separate; no JS or new password/zoom database.
Pre-flight Task 4→build: final run waits for component preparation; monitors updated and agent paused immediately after dispatch by explicit user instruction.
Task 1: in progress; pinned AAR/JAR API inspected with javap, constants exist.
User explicitly approved the new written plan on 2026-10-06. Desktop/input annex plans are approved for inline execution. Pause-after-dispatch instruction remains binding.
Task 1 RED: missing shared class failed JVM behavioral tests; Arc width tests failed against old boolean vendor-policy signature; Android instrumentation failed before metrics implementation. Implemented shared AndroidX classifier/current usable WindowMetrics with Configuration fallback; removed Samsung/DeX/FEATURE_PC eligibility. GN/native gate remains pending.
Task 1 interim GREEN: real pinned AndroidX constants produce expected COMPACT/TABLET/DESKTOP boundaries and reversible resize; Arc width eligibility plus 4238 palette checks pass. Physical Android instrumentation verifies Configuration widths/rotation, rejects Application context and measures actual Activity window. GN, cross-display, split-screen runtime and UI mode integration still pending.
Task 1 Ruling: compile against the existing public AndroidX Window target exporting its Window Core dependency to avoid adding numeric constants or modifying generated AndroidX targets. Full GN/dependency verification still mandatory; cost if wrong: add explicit allowed direct Core dependency at native gate.
