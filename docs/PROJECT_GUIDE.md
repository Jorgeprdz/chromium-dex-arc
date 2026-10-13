# Repository guide

[← README](../README.md) · [Installation](INSTALL_ARCHIUM.md) · [Screenshots](SCREENSHOTS.md)

## Published build

Archium R4 preview `157.0.8086.0`, package `app.archium.android`, ARM64. The release preserves the signed APK from [run 38322756782](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782), with its original `SHA256SUMS` and `BUILD_REPORT.json`. The compiled source is `39b1bcbfa6cd8f51e0b66a7eccdb9e586d8d78b3`; the Chromium pin is `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Public download landing page and documentation; its previous browser/build code is preserved. |
| `assistant/archium-r4-recovery` | Current build sources and tools, plus this documentation. |
| `assistant/archium-r3-visual-fixes` | R3/R4 history before recovery. |
| `feat/arc-desktop` | Untouched protected backup: `51e5ed429661727156ab2534caac99a82ee9264b`. |

**[Browse current sources](https://github.com/Jorgeprdz/chromium-dex-arc/tree/assistant/archium-r4-recovery).** Earlier preparation documents describe historical states; they do not supersede this published download status.

## Source layout

These paths refer to the source branch. `main` does not contain a complete Chromium checkout.

| Path | Contents |
| --- | --- |
| `chromium/` | New Archium Java files, tests and resources. |
| `.source-reference/` | Pinned originals used to compare and apply the patch. |
| `.source-modified/` | Minimal edits to Chromium. |
| `patches/` | Generated patch and hash manifest. |
| `config/archium-args.gn` | Browser GN configuration. |
| `scripts/` | Generation, gates, transitions, checkpoints and APK verification. |
| `tests/` | Host suite and fixtures with explicit test scope. |
| `docs/` | Installation, screenshots, evidence, audits and plans. |
| `assets/branding/archium/` | Approved Portal identity. |

## Current build process

On the source branch, `baseline-build.yml` uses `workflow_dispatch` with an exact SHA and compatible checkpoint. It runs cheap preflight, capacity and integrity checks, one restore, an mtime-preserving transition, real gates, incremental links and APK generation. There is no clean-build fallback.

The published run restored `archium-checkpoint-38275213327-1` from `3c75be2c5fd0aff4a9616e218498886895f088ba`. The workflow retained 75-minute slices, at most two, and blocks publication when a gate fails. No new build was dispatched to prepare the documentation or release.

Regenerate the patch with `scripts/generate-arc-patch.py`; do not edit it manually. Python and synthetic contracts do not establish Robolectric, final resources or JNI results: the published build executed those real gates after restore.

## Evidence and follow-up

- [Build and installation evidence](evidence/2026-10-12-sidebar-fixes/build-38322756782-final.json).
- [Physical observations during capture](screenshots/r4-157.0.8086.0/capture-manifest.json).
- [R4 forensic repair log (Spanish)](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_R4_REPARACION_Y_BUILD_2026-10-11.md).
- [Desktop Engine R1 roadmap (Spanish)](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_DESKTOP_ENGINE_R1_PERFORMANCE_RENDERING_2026-10-12.md).

Navigation, color controls, About and sidebar toggling were observed on DeX. Lower-edge geometry, some compact icons and full acceptance remain pending. Archium's custom password feature remains deprecated.
