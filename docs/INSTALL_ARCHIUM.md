# Install Archium

[← README](../README.md) · [Screenshots](SCREENSHOTS.md)

## Download

The [R4 preview — 157.0.8086.0](https://github.com/Jorgeprdz/chromium-dex-arc/releases/tag/archium-r4-157.0.8086.0-preview) includes the ARM64 APK, checksum and original build report.

**[Download Archium-for-Android-arm64.apk](https://github.com/Jorgeprdz/chromium-dex-arc/releases/download/archium-r4-157.0.8086.0-preview/Archium-for-Android-arm64.apk)**

Requires Android 10 or later and ARM64. The package is `app.archium.android`. Screenshots were taken on a Samsung SM-S931B running Android 16 with DeX; they do not establish tested compatibility with every other manufacturer's desktop mode.

## Install or update

1. Download the APK and open it in Files or Downloads.
2. Allow installation from that app if Android asks.
3. Install and launch Archium. Android may offer to update an existing build from the same signing lineage while keeping its data.
4. Connect DeX to a monitor for the desktop interface shown in the gallery.

If Android rejects an update because of a signature mismatch, preserve the installed app and report the message. Do not erase its data to work around it.

## Explore the interface

- Use **New Tab**, or **+** when the sidebar is compact.
- The upper sidebar control switches between expanded and collapsed modes.
- The multicolor sphere opens the browser color picker: eight presets, HEX and RGB. **Cancel** discards the preview; **OK** saves your color.
- The information button in the footer opens **About Archium**, showing the Portal logo and installed version.

The captured interface is in Spanish: Nueva pestaña, Color del navegador, Cancelar, Aceptar and Acerca de Archium.

## Verify the file

Download `SHA256SUMS` from the same release alongside the APK. In a terminal with `sha256sum`:

```bash
sha256sum -c SHA256SUMS
```

Expected output: `Archium-for-Android-arm64.apk: OK`.

```text
05a097adb97802d81bb97e65b46dbca2c60e559adcc53990d492d92c831eede6
```

Download details: version `157.0.8086.0`, versionCode `808600074`, ABI `arm64-v8a`, 366,979,888 bytes. This is the original file from [run 38322756782](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782), without rebuilding or re-signing.

## Status

This is a preview. Lower-edge geometry and compact icons still need refinement. Archium's custom password feature is deprecated. When reporting an issue, include your device, Android version, desktop mode, reproduction steps and a screenshot without personal data.
