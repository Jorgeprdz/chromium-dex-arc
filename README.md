<div align="center">

<img src="assets/branding/archium/archium-dark-128.png" width="96" alt="Archium Portal logo">

# Archium

### Your browser. Your space.

A Chromium-based browser with a collapsible sidebar and customizable colors, built for Android desktop environments.

![R4 Preview](https://img.shields.io/badge/R4-preview-8B5CF6)
![Version](https://img.shields.io/badge/version-157.0.8086.0-5865F2)
![Android](https://img.shields.io/badge/Android-10%2B-3DDC84?logo=android&logoColor=white)
![Architecture](https://img.shields.io/badge/ABI-ARM64-475569)

**[⬇ Download Archium for Android](https://github.com/Jorgeprdz/chromium-dex-arc/releases/download/archium-r4-157.0.8086.0-preview/Archium-for-Android-arm64.apk)**

[Release notes](https://github.com/Jorgeprdz/chromium-dex-arc/releases/tag/archium-r4-157.0.8086.0-preview) · [Installation](docs/INSTALL_ARCHIUM.md) · [Screenshots](docs/SCREENSHOTS.md) · [Contribute](CONTRIBUTING.md)

</div>

![Archium running on Samsung DeX with the sidebar expanded](docs/screenshots/r4-157.0.8086.0/sidebar-open.png)

**An actual screenshot of Archium 157.0.8086.0 on Samsung DeX, Android 16.** Screenshots show the published APK without retouching or recreating its interface. The captured UI is in Spanish.

## More room for the web

| Navigation at your side | Make it yours |
| --- | --- |
| A sidebar for tabs, favorite shortcuts, spaces and folders. A light capsule highlights the active tab. | Eight color presets, HEX input and RGB controls. Preview a color before applying it, or cancel to keep your current theme. |
| Collapse the sidebar to expand the page while keeping the **+** button within reach. | The window frame and native omnibox backgrounds respond to your chosen color. |

Archium retains Chromium's navigation and tab models. Its desktop interface is designed for a monitor, keyboard and mouse, with the **Archium Portal** visual identity.

## See it in action

<table>
  <tr>
    <td width="50%"><strong>Compact sidebar</strong><br><img src="docs/screenshots/r4-157.0.8086.0/sidebar-collapsed.png" alt="Collapsed sidebar with the New Tab button visible" width="100%"></td>
    <td width="50%"><strong>Your colors</strong><br><img src="docs/screenshots/r4-157.0.8086.0/color-picker.png" alt="Archium color picker with eight presets, HEX and RGB" width="100%"></td>
  </tr>
  <tr>
    <td><strong>Preview before applying</strong><br><img src="docs/screenshots/r4-157.0.8086.0/color-preview.png" alt="Coral live preview on the frame and omnibox" width="100%"></td>
    <td><strong>About Archium</strong><br><img src="docs/screenshots/r4-157.0.8086.0/about.png" alt="About dialog with the Portal logo and installed version" width="100%"></td>
  </tr>
</table>

[Open the full-size gallery →](docs/SCREENSHOTS.md)

## Download and install

1. Download the [ARM64 APK](https://github.com/Jorgeprdz/chromium-dex-arc/releases/download/archium-r4-157.0.8086.0-preview/Archium-for-Android-arm64.apk).
2. Open it in **Files** and allow installation from that app if Android asks.
3. Launch Archium. Connect Samsung DeX to a monitor for the desktop experience shown above.

**APK requirements:** Android 10 or later and an ARM64 processor. Desktop checks and screenshots were performed on Samsung DeX with Android 16. Other Android desktop environments still require device validation.

| Published download | Value |
| --- | --- |
| Version | `157.0.8086.0` — R4 preview |
| Package | `app.archium.android` |
| ABI | `arm64-v8a` |
| APK size | 366,979,888 bytes, approximately 350 MiB |
| Build | [38322756782 — SUCCESS](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782) |

<details>
<summary><strong>Verify your download</strong></summary>

The release includes `SHA256SUMS` and the original `BUILD_REPORT.json`. The published APK retains the signature and bytes of the verified, installed build.

```text
05a097adb97802d81bb97e65b46dbca2c60e559adcc53990d492d92c831eede6  Archium-for-Android-arm64.apk
```

```bash
sha256sum -c SHA256SUMS
```

See the [installation and verification guide](docs/INSTALL_ARCHIUM.md).

</details>

## Preview status

The build passed real resource, Portal icon, signature, Robolectric and JNI link gates. Navigation, sidebar toggling, color preview and the About dialog were subsequently observed on the device.

Full device acceptance remains pending. This version is published as a **preview**. Archium's custom password feature remains **deprecated**.

[Build and installation evidence](docs/evidence/2026-10-12-sidebar-fixes/build-38322756782-final.json) · [Capture manifest and observations](docs/screenshots/r4-157.0.8086.0/capture-manifest.json)

## Known Bugs

These visual issues were observed in the published APK on Samsung DeX and remain visible in the screenshots.

| Area | Observed behavior |
| --- | --- |
| Lower edge | A small light wedge remains at the junction between the sidebar and page viewport. |
| Compact mode | Some tab and omnibox icons still need presentation refinements. The **+** button remains visible. |

No crash was observed during this capture session while navigating, opening the color picker, toggling the sidebar or viewing About. This does not replace complete stability testing. [Report a reproducible issue](https://github.com/Jorgeprdz/chromium-dex-arc/issues/new).

## To-do

- [ ] Fix the lower-edge wedge and refine compact-mode icons.
- [ ] Complete device acceptance: startup, omnibox suggestions, navigation, resizing and focus changes.
- [ ] Validate additional Android desktop environments on real devices.
- [ ] Measure performance, memory and rendering against the Desktop Engine R1 roadmap before claiming improvements.
- [ ] Expand tests, translations and documentation with community contributions.

## Contributors Required

Interested in building a browser for Android desktops? These contributions would help most right now:

| Background | Where you can help |
| --- | --- |
| Android / Java / Chromium | Window geometry, sidebar, omnibox and accessibility. |
| DeX and desktop QA | Reproductions, keyboard/mouse testing and device coverage. |
| GN / Ninja / GitHub Actions | Reproducible gates and incremental checkpoint recovery. |
| Performance and rendering | Measurements and diagnosis for the Desktop Engine R1 roadmap. |
| Documentation and translation | Installation guides, screenshots and clear user-facing text. |

**[How to contribute →](CONTRIBUTING.md)** · [Suggest an improvement or report a bug](https://github.com/Jorgeprdz/chromium-dex-arc/issues/new)

## Development and documentation

The [current source branch is assistant/archium-r4-recovery](https://github.com/Jorgeprdz/chromium-dex-arc/tree/assistant/archium-r4-recovery), containing patches, modified sources and tools. `main` publishes this landing page and documentation while retaining its previous browser/build code. The APK is built incrementally from a compatible checkpoint.

- [Repository guide](docs/PROJECT_GUIDE.md): layout, build process and current status.
- [R4 forensic repair log (Spanish)](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_R4_REPARACION_Y_BUILD_2026-10-11.md).
- [Archium Portal identity and resources](assets/branding/archium/README.md).
- [Desktop Engine R1 roadmap (Spanish)](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_DESKTOP_ENGINE_R1_PERFORMANCE_RENDERING_2026-10-12.md): planned work, not achieved performance claims.

This preview uses Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`; the APK source commit is `39b1bcbfa6cd8f51e0b66a7eccdb9e586d8d78b3`.
