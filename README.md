# Archium

**A Chromium-based Android browser experiment focused on tablet and desktop-class use, with an Arc for Mac-inspired interface and a local-first password system.**

> [!IMPORTANT]
> Archium is **under active development**. The current repository contains implementation work, build tooling, tests and design documentation, but the new integrated APK described below is not yet considered functionally accepted.

## What is Archium?

Archium starts from **Chromium 157** and explores what a serious desktop-style browser can look like on Android when the browser adapts to the **current window**, not to a specific manufacturer, display ID or desktop mode.

The project has two immediate goals:

1. Build a real **Arc for Mac-inspired browser interface** on top of Chromium's existing tab, omnibox, navigation and profile models.
2. Provide a **local password vault** for Android using Chromium's PasswordManager/PasswordStore architecture, with encryption backed by Android Keystore and CSV import/export.

The intention is not to paint a desktop skin over a mobile browser. Archium aims to reuse Chromium's native browser behavior wherever possible and only replace or extend the layers that need to be different.

## Contributors wanted

Archium is looking for collaborators who want to help build a **Chrome + Arc experience designed for Android desktop environments**.

The goal is a browser that feels at home when Android is used like a computer: **Samsung DeX, Android Desktop Mode, Googlebook-style environments, tablets, freeform windows and external displays**—while still remaining a real Chromium browser underneath.

Areas where contributions are especially welcome:

- Chromium Android / Android Desktop internals;
- Java, C++, JNI, GN and Ninja;
- browser UI, compositor and window-management work;
- Arc-inspired sidebar, tabs, Spaces and interaction design;
- keyboard and mouse behavior;
- extensions on Android Desktop;
- local password management and Android Keystore;
- tablet, DeX, Desktop Mode, Googlebook and external-display testing;
- build infrastructure, reproducible patches and CI.

We are not looking to make a WebView wrapper or a visual mock-up. The challenge is to make Chromium itself deliver a convincing desktop browsing experience on Android.

If that sounds interesting, **issues, testing, code review, implementation help and pull requests are welcome**.

## Base

- **Chromium:** 157.0.8086.0
- **Pinned revision:** `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`
- **Android package:** `app.archium.android`
- **Current implementation branch:** `feat/arc-desktop`
- **Target:** Android phones, tablets, Samsung DeX, Android Desktop Mode, Googlebook-style environments, freeform windows and external displays
- **Root / Shizuku / ADB at runtime:** not required

Archium preserves Chromium's underlying navigation, profiles, tabs, incognito model and extension infrastructure instead of recreating them in a WebView.

## Arc-inspired desktop interface

The desktop UI is designed around a left sidebar and a real browser viewport rather than a traditional mobile toolbar stretched across a large screen.

Planned and in-progress behavior includes:

- navigation controls and address/search integrated into the sidebar;
- Favorites backed by real browser actions;
- persistent pinned entries and folders;
- local Spaces;
- real open tabs connected to Chromium's `TabModel`;
- native tab creation, selection, closing and restoration;
- a collapsible and resizable sidebar;
- keyboard focus and mouse interaction;
- rounded web-content geometry implemented through the real viewport/compositor path rather than decorative masks;
- light, dark and customizable frame themes that do **not** tint webpages;
- explicit appearance modes: **Auto / Arc / Mobile**.

The interface is inspired by **Arc for Mac**, but Archium is an independent project and is not affiliated with The Browser Company.

## Local passwords

Archium's current password work is intentionally **local-first** and does not depend on Google Sync.

The design keeps Chromium's existing PasswordManager matching, save/update prompts and fill behavior while adding an Android-compatible local backend.

### Security model

- local `LoginDatabase`-based storage;
- random data-encryption key;
- key protected by **Android Keystore**;
- fail-closed behavior if encryption is unavailable;
- no hard-coded encryption key;
- no plaintext fallback;
- no personal password CSV in tests;
- incognito does not create normal-profile password records.

### Planned user features

- save and update passwords from real login flows;
- autofill using Chromium's origin matching;
- native password-management screen;
- search, edit and delete;
- authenticated reveal/copy where supported;
- CSV import with preview and duplicate handling;
- atomic import/rollback behavior;
- CSV export through Android's Storage Access Framework.

Google Sync, passkeys and Google Wallet are **not** dependencies of the local vault.

## Adaptive desktop behavior

Archium is being structured around the **current window width**, not the physical device category.

| Window width | Class | Intended behavior |
| --- | --- | --- |
| **< 600 dp** | Compact | Mobile UI/site by default |
| **600–839 dp** | Tablet | Arc-eligible UI and desktop-site behavior |
| **>= 840 dp** | Desktop | Desktop-class Archium behavior |

The thresholds reuse the AndroidX/Chromium window-size model where available.

The desktop policy is designed to respond to split screen, freeform resize, rotation and display changes without treating Samsung DeX—or any other OEM desktop mode—as a requirement.

> The deeper automatic desktop-site/UA, zoom and additional keyboard/mouse layer are staged separately from the current Arc + local-password integration run.

## Keyboard and mouse

Archium prefers Chromium's existing input routes instead of duplicating them.

The project is designed to preserve or verify native behavior for shortcuts such as:

`Ctrl+L`, `Ctrl+T`, `Ctrl+W`, `Ctrl+Shift+T`, tab switching, navigation shortcuts, reload/hard reload and browser pages such as history/downloads.

Additional desktop integration includes:

- Arc sidebar toggle;
- middle-click tab closing through the real tab model;
- middle-click links opening background tabs;
- modifier-click dispositions;
- mouse Back/Forward buttons;
- `Ctrl+wheel` through Chromium's native zoom path.

Fake fullscreen, synthetic web events and JavaScript-based browser controls are deliberately avoided.

## Current implementation status

Archium distinguishes **code prepared**, **tests passed**, **compiled integration** and **accepted runtime behavior**. A green unit test is not treated as proof that the final browser feature works.

### Already validated in preparation

- Android Keystore behavior exercised on a physical Android device;
- persistence/durability regression coverage for the local key material;
- synthetic CSV parser/writer test coverage;
- window-classification and appearance-policy checks;
- reproducible sparse-patch/hash verification;
- preparation and incremental-build routing tests;
- persistent Arc sidebar data model work for Spaces/Favorites/pinned entries.

### Still pending before acceptance

- full native C++/JNI/GN compilation of the local password backend;
- real browser save/update/fill validation;
- visible password manager + authentication + SAF wiring;
- complete Arc sidebar integration with Chromium's live `TabModel`;
- compositor/viewport acceptance for the Arc frame;
- final integrated APK build;
- update-signature verification;
- end-to-end testing after install;
- final visual comparison against Arc for Mac references.

In short: **the architecture and a meaningful amount of implementation exist, but the integrated build still has to prove them together.**

## Build strategy

Chromium is expensive to build, so Archium uses a strict incremental-build strategy.

The workflow is designed to:

1. restore a known previous checkpoint only when its revision, commit, paths and hashes match;
2. transition from the old pinned patch to the new one;
3. regenerate GN when build inputs change;
4. let Ninja invalidate and rebuild only the affected targets;
5. preserve new checkpoints between stages;
6. build targeted native/Java tests before the final APK;
7. never call a pending build a successful delivery.

The existing app/profile is not deleted simply to work around an APK signing mismatch.

## Project principles

Archium follows a few rules that are intentionally boring—and important:

- **Use Chromium's real models.** Tabs, navigation, passwords, profiles and extensions should remain browser features, not simulations.
- **No fake controls.** If a button exists, it should operate a real browser action.
- **No WebView replacement.** Archium remains a Chromium browser fork.
- **No OEM lock-in.** Samsung DeX is a test environment, not a dependency.
- **No destructive shortcuts.** Build/install problems are not solved by wiping the user's browser profile.
- **No secret leakage.** Passwords, personal CSV contents and signing keys do not belong in logs, CI artifacts or the repository.
- **No success by implication.** A successful build does not automatically mean visual or functional acceptance.

## Roadmap

The current sequence is intentionally narrow:

**Now**

- finish Arc UI integration;
- finish local password/CSV integration;
- compile targeted native tests;
- produce and verify the integrated APK;
- run end-to-end validation.

**Next**

- adaptive Request Desktop Site behavior;
- desktop/mobile UA policy driven by current window;
- native page zoom persistence and Arc exposure;
- additional keyboard and mouse integration;
- broader tablet/freeform/external-display validation.

**Later / research**

- Google Sync feasibility as a separate experiment;
- additional desktop-browser capabilities only after the core build is stable.

## Why no Google Sync right now?

Chromium contains the Sync machinery, but a third-party Android Chromium fork does not automatically receive Chrome's Google authentication, authorization, password backend or encryption-key infrastructure.

Archium therefore treats Google Sync as a separate research problem rather than blocking the browser on a feature that cannot currently be guaranteed.

Local passwords are designed to work independently.

## Documentation

The repository's `docs/` directory contains the implementation notes, design decisions, validation results and build strategy used to keep the project reproducible.

The original visual direction is documented in [`docs/design.md`](docs/design.md). Newer implementation documents supersede older assumptions where the project has evolved.

## Development status disclaimer

Archium is experimental software. Until an integrated APK has completed compilation and runtime acceptance, screenshots, renders, tests and design documents should be treated as development evidence—not as proof that every described feature is available in a released build.

## Credits

Archium is built from the open-source **Chromium** project.

Its desktop interface takes visual and interaction inspiration from **Arc for Mac**. Arc and The Browser Company are trademarks/products of their respective owners. Archium is not affiliated with or endorsed by Google, Chromium, Arc or The Browser Company.
