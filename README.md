<div align="center">

<img src="assets/branding/archium/archium-dark-128.png" width="96" alt="Logo Archium Portal">

# Archium

### Tu navegador. Tu espacio.

Una experiencia con sidebar y colores a tu medida, basada en Chromium y pensada para Android de escritorio.

![Preview R4](https://img.shields.io/badge/R4-preview-8B5CF6)
![Versión](https://img.shields.io/badge/versión-157.0.8086.0-5865F2)
![Android](https://img.shields.io/badge/Android-10%2B-3DDC84?logo=android&logoColor=white)
![Arquitectura](https://img.shields.io/badge/ABI-ARM64-475569)

**[⬇ Descargar Archium para Android](https://github.com/Jorgeprdz/chromium-dex-arc/releases/download/archium-r4-157.0.8086.0-preview/Archium-for-Android-arm64.apk)**

[Notas de la release](https://github.com/Jorgeprdz/chromium-dex-arc/releases/tag/archium-r4-157.0.8086.0-preview) · [Instalación](docs/INSTALL_ARCHIUM.md) · [Galería](docs/SCREENSHOTS.md) · [Reportar un problema](https://github.com/Jorgeprdz/chromium-dex-arc/issues/new)

</div>

![Archium en Samsung DeX con la sidebar abierta](docs/screenshots/r4-157.0.8086.0/sidebar-open.png)

**Captura real de Archium 157.0.8086.0 en Samsung DeX, Android 16.** Las imágenes muestran el APK publicado, sin recrear ni retocar la interfaz.

## Más espacio para navegar

| Tu navegación, a la izquierda | Tu estilo, en toda la ventana |
| --- | --- |
| Sidebar con pestañas, accesos favoritos, espacios y carpetas. La pestaña activa se distingue con una cápsula clara. | Ocho colores predefinidos, entrada HEX y controles RGB. Puedes previsualizar un tono, aplicarlo o cancelar. |
| Colapsa la sidebar para ampliar el visor; el botón **+** sigue a mano. | El marco y los fondos de la omnibox combinan con el color elegido. |

Archium conserva la navegación y los modelos de pestañas de Chromium. Su interfaz de escritorio está pensada para usar un monitor, teclado y ratón, con identidad visual **Archium Portal**.

## Míralo en acción

<table>
  <tr>
    <td width="50%"><strong>Sidebar compacta</strong><br><img src="docs/screenshots/r4-157.0.8086.0/sidebar-collapsed.png" alt="Sidebar colapsada con Nueva pestaña visible" width="100%"></td>
    <td width="50%"><strong>Colores a tu medida</strong><br><img src="docs/screenshots/r4-157.0.8086.0/color-picker.png" alt="Selector de ocho colores, HEX y RGB de Archium" width="100%"></td>
  </tr>
  <tr>
    <td><strong>Vista previa antes de aplicar</strong><br><img src="docs/screenshots/r4-157.0.8086.0/color-preview.png" alt="Vista previa coral en el marco y la omnibox" width="100%"></td>
    <td><strong>Acerca de Archium</strong><br><img src="docs/screenshots/r4-157.0.8086.0/about.png" alt="Diálogo Acerca de Archium con logo y versión instalada" width="100%"></td>
  </tr>
</table>

[Abrir la galería a tamaño completo →](docs/SCREENSHOTS.md)

## Descargar e instalar

1. Descarga el [APK ARM64](https://github.com/Jorgeprdz/chromium-dex-arc/releases/download/archium-r4-157.0.8086.0-preview/Archium-for-Android-arm64.apk).
2. Ábrelo desde **Archivos** y permite la instalación desde esa app si Android lo solicita.
3. Abre Archium. Para la experiencia mostrada, conecta Samsung DeX a un monitor.

**Requisitos del APK:** Android 10 o superior y procesador ARM64. Las capturas y la prueba de escritorio se hicieron en Samsung DeX con Android 16; otros entornos Android Desktop todavía necesitan validación.

| Descarga publicada | Valor |
| --- | --- |
| Versión | `157.0.8086.0` — preview R4 |
| Paquete | `app.archium.android` |
| ABI | `arm64-v8a` |
| APK | 366,979,888 bytes, aproximadamente 350 MiB |
| Build | [38322756782 — SUCCESS](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782) |

<details>
<summary><strong>Verificar la descarga</strong></summary>

La release incluye `SHA256SUMS` y el `BUILD_REPORT.json` original. El APK publicado conserva la firma y los bytes del build verificado e instalado.

```text
05a097adb97802d81bb97e65b46dbca2c60e559adcc53990d492d92c831eede6  Archium-for-Android-arm64.apk
```

```bash
sha256sum -c SHA256SUMS
```

Consulta la [guía de instalación y verificación](docs/INSTALL_ARCHIUM.md).

</details>

## Estado de esta preview

El build pasó los gates de recursos reales, iconos Portal, firma, Robolectric y enlace JNI. Después se observó navegación, colapso de sidebar, vista previa de colores y el diálogo Acerca de en el dispositivo.

Todavía hay detalles visuales por afinar en la unión inferior entre sidebar y visor y en algunos iconos del modo compacto. La aceptación completa en dispositivo sigue pendiente; esta versión se publica como **preview**. La función propia de contraseñas permanece **deprecated**.

[Estado y evidencia del build](docs/evidence/2026-10-12-sidebar-fixes/build-38322756782-final.json) · [Registro de capturas y observaciones](docs/screenshots/r4-157.0.8086.0/capture-manifest.json)

## Desarrollo y documentación

El [código de Archium está en assistant/archium-r4-recovery](https://github.com/Jorgeprdz/chromium-dex-arc/tree/assistant/archium-r4-recovery): parches, fuentes modificadas y herramientas. `main` publica esta portada y la documentación; no incorpora los cambios del navegador. El APK se compila incrementalmente desde un checkpoint compatible.

- [Guía del repositorio](docs/PROJECT_GUIDE.md): estructura, build y estado actual.
- [Reparación R4 y registro verificable](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_R4_REPARACION_Y_BUILD_2026-10-11.md).
- [Identidad y recursos Archium Portal](assets/branding/archium/README.md).
- [Desktop Engine R1](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_DESKTOP_ENGINE_R1_PERFORMANCE_RENDERING_2026-10-12.md): roadmap pendiente, sin promesas de rendimiento ya alcanzado.

La preview usa Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`; su código corresponde al commit `39b1bcbfa6cd8f51e0b66a7eccdb9e586d8d78b3`.

¿Encontraste algo? [Abre un issue](https://github.com/Jorgeprdz/chromium-dex-arc/issues/new) con tu modelo, versión de Android, modo de escritorio y pasos para reproducirlo. Las capturas sin datos personales ayudan a entender el problema.
