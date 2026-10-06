### Task 1: Verified old-to-new patch transition

**Files:**
- Modify: `scripts/archium-checkpoint.py` to separate explicit source checkpoint identity from current implementation identity.
- Create: `scripts/transition-archium-patches.py`.
- Test: `tests/test_checkpoint.py`, `tests/test_patch_transition.py`.

**Interfaces:**
- Existing strict restore remains strict by default.
- `transition(checkout, old_manifest, new_manifest, old_patch, new_patch, original_sources)` verifies revision, both patch hashes and all touched inputs before changing files.
- Old patch/manifest are loaded from their explicit committed revision, not assumed to equal current files.
- Persist transition receipt with old/new identities only after all mutations succeed; new checkpoint records the new implementation commit.

- [ ] Write RED tests: old checkpoint accepted only with its declared commit; wrong revision/path/hash rejected; old-only file restored; removed new source removed only when exact old hash matches; divergent user file/symlink rejects all writes; interrupted mutation restores pre-transition bytes.
- [ ] Run RED, then implement validation/staging/rollback. Preserve unchanged file bytes and mtimes.
- [ ] Run tests; expected full transition and tamper/interruption cases pass.
- [ ] Commit transition and tests.
