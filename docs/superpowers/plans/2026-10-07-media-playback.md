# Archium Media Playback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Enable native Chromium clear-media formats and make configuration and playback failures observable.
**Architecture:** Two supported GN overrides restore proprietary formats and matching FFmpeg decoders; a fail-closed effective-GN gate protects builds. Synthetic files and browser tests exercise the existing pipeline. Architecture configuration is derived from one common file.
**Tech Stack:** Chromium 157, GN, Python, FFmpeg test-data generation, HTML/JavaScript.
**Spec:** docs/superpowers/specs/2026-10-07-media-playback.md

## Global Constraints
- Chromium 157.0.8086.0: cfd94726b7b5fb48aedcc32662f2f3fbdbadec35; FFmpeg dependency 9db86ce5b5b454dfc96c435f9f0723012980c37f.
- feat/media-playback; app.archium.android; preserve active feat/arc-desktop build/monitor.
- No upstream media rewrite, Google product branding, security disablement or DRM certification claim.
- Report progress per phase, tests and failures separately from runtime acceptance.

## Review Focus
- Missing or malformed effective GN args must fail before any compiler or APK operation.
- Codec override loss must be caught by actual pinned GN evaluation.
- x64 configuration must preserve package/security settings and reject unknown architectures.
- Browser capability support must not earn playback PASS without time advancement and decoded frames.
- Streaming and seeking must use valid synthetic media and Range-capable HTTP delivery.

### Task 1: Configuration and effective-GN gate
**Files:** config/archium-args.gn; scripts/archium-media-preflight.py; scripts/build-archium.sh; tests/test_media_config.py; tests/media_gn_probe.py; tests/fixtures/media-gn/.
**Interfaces:** preflight consumes gn args --list --short and emits JSON status plus effective values; nonzero exit prevents compilation.
- [x] Execute pinned GN baseline; preserve RED values.
- [x] Add tests for actual configuration behavior, malformed/missing values and failure routing.
- [x] Add two supported overrides and a pre-compile effective-GN gate.
- [x] Re-run tests GREEN and full repository suite.

### Task 2: Architecture preparation and browser acceptance
**Files:** scripts/archium-build-config.py; tests/test_media_config.py; scripts/generate-media-fixtures.py; scripts/serve-media-tests.py; tests/runtime/media/index.html; tests/runtime/media/media-tests.js; tests/runtime/media/data/; tests/test_media_server.py.
**Interfaces:** configuration writes args for arm64/x64; fixture recipe generates owned clear-content samples; HTTP server handles byte ranges; browser page records actual playback outcomes.
- [x] Write RED behavior tests for architecture validation and HTTP byte ranges.
- [x] Implement small configuration and serving tools; generate and inspect synthetic files with ffprobe.
- [x] Add playback, seek, MSE and HLS cases with error/timeouts and cleanup.
- [x] Run all local tests, preparation, syntax checks and verify unchanged patch parity.

### Task 3: Review, publication and device acceptance
**Files:** docs/media-playback.md; docs/media-progress.md.
- [x] Review all changes and report the exact local limits.
- [ ] Check expected remote media branch base; commit and normal fast-forward push.
- [ ] Keep current active run/monitor unchanged; hand off later serialized media build.
- [ ] After a media APK exists, run acceptance on Archium; verify clear media, audio, seek, fullscreen/PiP and hardware decoding. Intel requires its own APK/device checks.
