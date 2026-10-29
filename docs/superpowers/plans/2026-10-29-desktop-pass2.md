# Desktop polish pass 2 implementation plan

> For agentic workers: execute the independent footer and native-row tasks with scoped ownership, then integrate and review once.

**Goal:** refine the approved DeX UI without changing Chromium behavior or Mobile.
**Architecture:** keep native tab/menu/extension owners, existing frame and glass. Separate the existing footer into browser-controls and native-extension rows; reserve tab access before collections.
**Tech stack:** Android Java views/drawables, pinned upstream overlays, Robolectric/host probes.
**Spec:** user's ARCHIUM R5 DESKTOP POLISH PASS 2 plus explicit build/install annex.

## Constraints
One commit `style(desktop): refine tab typography, selection and two-row footer` on independent pending branch from current remote7e91ec9. No Mobile/command/frame geometry changes, no native handlers replaced, no checkpoint deletion, profiles untouched. One incremental build only after local gates and prior chain settled; verified install monitor.

## Review focus
- Native extension visibility changes and late attachment must not leave an empty row or stale parent.
- Collapsed/narrow/short rail keeps menu and native tabs reachable without undersized targets.
- Font scale/native size restoration remains idempotent; never stack +sp on recent increase.
- Selected/hover/focus/multiselect states preserve native semantics and restore shadows on Mobile.
- No favicon image outgrows native clipping container; no mosaic or raster changes.

## Tasks
- [x] Audit current tokens, upstream title dimensions, icon containers, footer lifecycle and latest owner screenshot. Record baseline and missing physical comparison.
- [x] Footer: regression for expanded two rows with native extension host, empty/hidden host, late attachment, compact/short windows, restore/destroy. Implement through existing coordinator and measured policy; retain listeners and original parents/layout params/visibility.
- [x] Native row appearance: test effective sp/font scale, containment and spacing; keep adequate recent sizes, tune only if justified. Slightly refine existing active radius to12dp and selected-only subdued1dp shadow, restoring original state and preserving pressed/focus.
- [x] Collections/omnibar: refine Space hierarchy using existing button and layout; improve desktop native URL contrast without changing positions/command behavior. Leave mosaic and frame geometry untouched.
- [x] Run scoped real-view regressions, native preparation and full host gates with configured SDK/AAPT2. Reproduce patch twice, diff-check and independent review. Verify no Mobile/command/frame-source delta.
- [x] Commit once and publish pending branch safely. Report exact values/tests and PENDING_DEVICE.
- [ ] Resolve explicit base-preservation instruction before fast-forward integration required by the authorized build/install; no workflow or checkpoint changes.
