# Archium Portal — App Icon Assets

Archium's standalone brand identity for Android desktop environments (Samsung DeX, Android Desktop, Googlebook OS and other Android-based desktop systems). This is intentionally **not** a recolor of the Chromium icon.

## Variants

| Variant | Purpose | Sizes (px) |
|---|---|---|
| `archium-dark-N.png` | Default dark launcher/dock icon | 16, 32, 48, 64, 128, 192, 256, 512, 1024 |
| `archium-light-N.png` | Light appearance | 128, 256, 512, 1024 |
| `archium-monochrome-light-N.png` | White glyph on transparent canvas | 32, 64, 256, 512 |
| `archium-monochrome-dark-N.png` | Dark glyph on transparent canvas | 32, 64, 256, 512 |
| `archium-symbol-N.png` | Multicolor glyph, transparent canvas | 256, 512, 1024 |
| `archium-adaptive-foreground-N.png` | Padded foreground for Android adaptive icons | 432, 512, 1024 |
| `archium-adaptive-background-N.png` | Dark background for Android adaptive icons | 432, 512 |

Seven equivalent `archium-*.svg` vector masters accompany the PNGs.

The adaptive layers are **separate** because Android launchers supply their own icon masks. Do not bake a squircle background into the adaptive foreground. For Android's system-themed icon, use the solid monochrome glyph (or derive a `monochrome` vector drawable).

## Regenerate

```bash
python -m pip install cairosvg
python scripts/export-archium-icons.py
```

The exporter is deterministic. This commit **adds artwork**; it does not change the currently built APK icon, AndroidManifest, app ID, build configuration, or the protected `feat/arc-desktop` branch. Integrating the assets into Chromium's resource pipeline is a separate step.
