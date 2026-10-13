# Guía del repositorio

[← Portada](../README.md) · [Instalación](INSTALL_ARCHIUM.md) · [Galería](SCREENSHOTS.md)

## Qué se publica

Archium R4 preview `157.0.8086.0`, paquete `app.archium.android`, ARM64. La release conserva el APK firmado del [run 38322756782](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38322756782), con `SHA256SUMS` y `BUILD_REPORT.json` originales. El código compilado es `39b1bcbfa6cd8f51e0b66a7eccdb9e586d8d78b3` y el pin Chromium es `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.

## Ramas

| Rama | Uso |
| --- | --- |
| `main` | Portada y documentación pública de descarga; conserva su código previo. |
| `assistant/archium-r4-recovery` | Código y herramientas del build actual, más esta documentación. |
| `assistant/archium-r3-visual-fixes` | Historia R3/R4 anterior a la recuperación. |
| `feat/arc-desktop` | Respaldo protegido, sin modificar: `51e5ed429661727156ab2534caac99a82ee9264b`. |

**[Explorar las fuentes actuales](https://github.com/Jorgeprdz/chromium-dex-arc/tree/assistant/archium-r4-recovery).** Los documentos anteriores de preparación describen estados históricos; no reemplazan este estado de descarga.

## Estructura del código

Las rutas siguientes corresponden a la rama de código, no a una promesa de que `main` contiene un checkout completo de Chromium.

| Ruta | Contenido |
| --- | --- |
| `chromium/` | Nuevos archivos Java, tests y recursos de Archium. |
| `.source-reference/` | Originales del pin, para comparar y aplicar el patch. |
| `.source-modified/` | Ediciones mínimas sobre Chromium. |
| `patches/` | Patch generado y manifest de hashes. |
| `config/archium-args.gn` | Configuración GN del navegador. |
| `scripts/` | Generación, gates, transición, checkpoints y verificación del APK. |
| `tests/` | Suite host y fixtures con su alcance de prueba declarado. |
| `docs/` | Instalación, capturas, evidencia, auditorías y planes. |
| `assets/branding/archium/` | Identidad Portal aprobada. |

## Build actual

En la rama de código, `baseline-build.yml` se lanza por `workflow_dispatch` con un SHA exacto y un checkpoint compatible. Ejecuta preflight barato, capacidad e integridad, restore único, transición preservando mtimes, gates reales, enlaces incrementales y APK. No hay fallback a un build limpio.

El run publicado restauró `archium-checkpoint-38275213327-1`, de `3c75be2c5fd0aff4a9616e218498886895f088ba`. El workflow mantuvo slices de 75 minutos, máximo dos, y detiene la publicación si un gate falla. No se disparó otro build para preparar esta documentación ni la release.

El patch se regenera con `scripts/generate-arc-patch.py`; no se edita manualmente. Python y contratos sintéticos no acreditan Robolectric, recursos finales ni JNI: el build publicado ejecutó esos gates reales después del restore.

## Estado y seguimiento

- [Evidencia del build y de la instalación](evidence/2026-10-12-sidebar-fixes/build-38322756782-final.json).
- [Observaciones físicas al capturar](screenshots/r4-157.0.8086.0/capture-manifest.json).
- [Registro forense y reparación R4](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_R4_REPARACION_Y_BUILD_2026-10-11.md).
- [Desktop Engine R1: roadmap pendiente](https://github.com/Jorgeprdz/chromium-dex-arc/blob/assistant/archium-r4-recovery/docs/ARCHIUM_DESKTOP_ENGINE_R1_PERFORMANCE_RENDERING_2026-10-12.md).

La navegación, el selector, Acerca de y el colapso se observaron en DeX. La geometría inferior, algunos iconos compactos y la aceptación completa siguen pendientes. Contraseñas permanece deprecated; no se reactivó con la release.
