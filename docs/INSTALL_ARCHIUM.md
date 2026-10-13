# Instalar Archium

[← Portada](../README.md) · [Ver capturas](SCREENSHOTS.md)

## Descarga

La [preview R4 — 157.0.8086.0](https://github.com/Jorgeprdz/chromium-dex-arc/releases/tag/archium-r4-157.0.8086.0-preview) incluye el APK ARM64, su checksum y el reporte original del build.

**[Descargar Archium-for-Android-arm64.apk](https://github.com/Jorgeprdz/chromium-dex-arc/releases/download/archium-r4-157.0.8086.0-preview/Archium-for-Android-arm64.apk)**

Requiere Android 10 o superior y ARM64. El paquete es `app.archium.android`. Las capturas se hicieron en un Samsung SM-S931B con Android 16 y DeX; no acreditan compatibilidad ya probada con todos los modos de escritorio de otros fabricantes.

## Instalación y actualización

1. Descarga el APK y ábrelo desde Archivos o Descargas.
2. Si Android lo solicita, permite instalar aplicaciones desde esa app.
3. Instala y abre Archium. Si tienes esta misma línea de builds firmada, Android puede ofrecer actualizarla conservando sus datos.
4. Conecta DeX a un monitor para usar la interfaz de escritorio mostrada en la galería.

Si Android rechaza una actualización por firma, conserva la aplicación instalada y reporta el mensaje. No borres sus datos para intentar solucionarlo.

## Primera exploración

- Usa **Nueva pestaña**; con la sidebar compacta, usa **+**.
- El control superior de la sidebar alterna entre abierta y colapsada.
- La esfera multicolor abre **Color del navegador**: ocho presets, HEX y RGB. **Cancelar** descarta la vista previa; **Aceptar** guarda el color.
- El botón informativo del footer abre **Acerca de Archium**, con el logo Portal y la versión instalada.

## Comprobar el archivo

Descarga `SHA256SUMS` de la misma release junto al APK. En una terminal con `sha256sum`:

```bash
sha256sum -c SHA256SUMS
```

Resultado esperado: `Archium-for-Android-arm64.apk: OK`.

```text
05a097adb97802d81bb97e65b46dbca2c60e559adcc53990d492d92c831eede6
```

Datos de esta descarga: versión `157.0.8086.0`, versionCode `808600074`, ABI `arm64-v8a`, 366,979,888 bytes. Se publica el archivo original del [run 38322756782](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782), sin recompilar ni volver a firmar.

## Estado

Esta versión es una preview. Hay detalles visuales pendientes en el borde inferior y los iconos del modo compacto. La función propia de contraseñas está deprecated. Para reportar un problema, incluye modelo, Android, modo de escritorio, pasos y una captura sin datos personales.
