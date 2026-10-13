# Contributing to Archium

Help improve Android desktop browsing through device testing, documentation, translations or code.

[← README](README.md) · [Repository guide](docs/PROJECT_GUIDE.md) · [Known bugs](README.md#known-bugs)

## Before you start

Read the README's known bugs and to-do list. For a substantial change, open an issue describing the problem, expected behavior and a small scope first. The current preview comes from build 38322756782; its source and tools live on `assistant/archium-r4-recovery`.

## Report a bug

Include your Archium version, device model, Android version, desktop mode, reproducible steps, expected behavior and actual result. Screenshots or logs help, but remove accounts, conversations, tokens and other personal data. Mention whether the sidebar was expanded or collapsed.

## Submit code

1. Start from the [current source branch](https://github.com/Jorgeprdz/chromium-dex-arc/tree/assistant/archium-r4-recovery).
2. Keep the diff focused on a reproducible cause and add an appropriate regression test where needed.
3. When changing overlay or `.source-modified` sources, regenerate the patch with `scripts/generate-arc-patch.py` and verify reproducibility.
4. Explain what you tested, the exit codes and what remains unverified. Mocks and host tests do not establish native execution or device acceptance.
5. Target your PR at `assistant/archium-r4-recovery`. Do not change or merge into `feat/arc-desktop`, the protected backup branch.

Chromium builds consume substantial resources. Coordinate a SHA-pinned workflow dispatch and compatible checkpoint with the maintainer. Preserve valid outputs and caches; never turn a failed restore into a clean build or disable gates to get a PASS.

## Documentation and device testing

Installation guides, text reviews, translations and tests on DeX or other Android desktops are welcome. Use actual screenshots, identify the tested APK and distinguish observations from hypotheses. Choose example content that can be shared without exposing personal information.

## Current priorities

Lower-edge geometry, compact icons, omnibox and focus acceptance, real-device compatibility and Desktop Engine R1 measurements. Archium's custom password feature remains deprecated; this preview does not reactivate it.
