# Bounded incremental build chain

Approved: user requested up to 12 automatically chained two-hour stages, preserving outputs.
Reuse baseline-build.yml and archium-r5-stage.yml, one dispatch, fixed SHA; no phone supervisor.

- [x] Test stage qualification and chain aggregation: success, incomplete, failure, stall, wrong source, 12-stage cap.
- [x] Add optional bounded chain inputs/outputs and unique artifacts to existing reusable workflow.
- [x] Give each stage 120 minutes of useful work, separate from restore/pack/upload; retain hard runner cap/reserves.
- [x] Publish small manifest artifacts; bind their SHA to prior stage outputs and verify all checkpoint part hashes on restore.
- [x] Chain up to twelve jobs; stop on APK, genuine failure, missing uploads or unchanged progress. Preflight once for fixed SHA.
- [x] Test affected gates/workflow syntax; preserve product patch byte-for-byte; commit/push exact SHA.
- [ ] Validate latest checkpoint and active-run inventory, dispatch once with max_stages=12, restore native observer/verified installer and notifications.
