# R5.2 — GPU y diálogos: investigación aislada

Fecha: 2026-10-19. Rama local `assistant/archium-r5-2-forensic`, basada en
`3db367adff50d423b8c4475d10165d2790f6065a`. **No hay fix de producto demostrado.**
Se entrega evidencia nueva, instrumentación y la reproducción real del diálogo
invisible; no se justifica otra compilación antes de cerrar el diagnóstico.

## Aislamiento de la compilación

Run protegido: [39296066030](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39296066030).
Última consulta: 2026-10-19, aproximadamente 18:17 UTC, **in_progress**, SHA esperado
`3db367adff50d423b8c4475d10165d2790f6065a`. Supervisor existente PID 29810,
SID independiente 29711, proceso Python activo, registro FOLLOWING y stage 3.
Checkpoint origen registrado: `archium-checkpoint-38511423805-1`, run 38511423805.
No se despachó build, no se cambió su entrada, checkpoint ni estado del supervisor.
No se canceló run, limpió output, cambió GN args/pin/toolchain ni abrió monitor.
La verificación de checkpoint para una futura etapa sigue siendo responsabilidad
de sus gates: esta investigación no restaura ni certifica nuevamente sus bytes.

El trabajo está en `/workspace/Archium-R5.2-forensic`; la rama/canonical
`/workspace/Archium-R5` permanece intacta. La reparación parcial de reorder que
compila conserva su commit; se ejecutó su regresión host sin modificarla.

## P0-01 — corrupción de Amazon

**FAIL del usuario conservado; causa NOT_PROVEN; GREEN visual NOT_TESTED.**
Se revisaron captura, información GPU y los dumps/traza anteriores. Adreno 830,
ANGLE Vulkan 1.3.284, driver 512.800.64 y Skia GraphiteDawnVulkan son datos de la
consulta DevTools del instalado. La ausencia de crashes GPU en esa consulta no
prueba que sus recursos, fences o repintado fueran correctos durante el incidente.
La captura corrupta fue en teléfono: un recorte exclusivo del frame Arc de DeX no
explica por sí solo el conjunto. No se reprodujo Amazon en una cuenta personal.

Se verificaron las rutas reales al pin Chromium
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` / **157.0.8086.0**. Los hashes de fuentes
upstream obtenidas coinciden con el manifest del repo. El manifest de archivos
Archium no incluye parches directos en Blink, cc, Viz, GPU, Skia, Dawn ni ANGLE;
esto no excluye un defecto upstream o un efecto de integración Android.

| Tramo | Ruta auditada / hipótesis pendiente |
| --- | --- |
| Blink → Paint | HTMLDialogElement y top layer: HTML modal no usa el presenter Android |
| Raster → tiles | cc/tiles/tile_manager.cc: tareas de raster, readiness y redraw; faltan tiles/resource IDs del incidente |
| Viz → Skia | skia_renderer.cc: root damage y swap/skip; falta comparar daño con píxeles obsoletos |
| Skia → GPU | skia_output_surface_impl_on_gpu.cc: Graphite recording, shared images y semáforos; falta evidencia de fence/context/resource inválido |
| Android Surface | RenderWidgetHostViewAndroid, CompositorView y superficies; falta correlación frame/surface/resize durante corrupción |
| Shell Arc | Toolbar/TopControlsStacker, márgenes, clip y viewport; auditar transición con el estado nativo, no asumir causa |

Source DEPS: Skia `8643b1d64cff21b5e6f8d65ca98204c6eecb0098`,
ANGLE `756d31051f12e93630ae51fd5e0d03deb6958739`,
Dawn `32f77c02294310054a660c393feded4bcb3f203c`.
El default de kSkiaGraphite en este source no explica por sí solo su activación
instalada. Finch/feature configuration exacta queda pendiente. No se cambian flags
para reemplazar esa evidencia. `vulkan=disabled_off` de otra feature de Chromium
no implica que ANGLE/Dawn no utilicen Vulkan.

Próximo ensayo: fixture local de patrones con fase A/B, scroll y resize; comparar
ROIs de imágenes PNG con viewport/DPR idénticos. Capturar FrameTimeline, daños,
resource/tile IDs y fences para separar raster incompleto, buffer reutilizado,
frame duplicado, overlay promotion y lifecycle. Una imagen negra por sí sola no
identifica cuál. La fixture suplementaria no sustituye el HTML original.

## P0-02 — evidencia real nueva

**RED real reproducido en el Galaxy, DeX: alert/confirm/prompt invisibles.**
Los doce mosaicos originales se pulsaron individualmente con captura y dumps.
HTML modal/no modal, overlay CSS, ventana nueva y selector Android sí fueron
visibles. Tabla completa, URI, hash original, timestamps y límites:
[R5_2_PHONE_HTML_DIAGNOSTICS.md](R5_2_PHONE_HTML_DIAGNOSTICS.md).

Durante alert/confirm/prompt activos, container GONE, bounds cero y sin
ModalDialogView en la jerarquía. Categoría D (no adjunto/presentado) sustentada;
A (cuadro adjunto detrás de Surface) no explica la jerarquía observada por sí sola.
B/C/E no se evalúan como causas independientes sobre una vista que no aparece;
F no se observó: los eventos seguían abiertos al capturar. Estos resultados no
excluyen carreras no capturadas. Window tokens y SurfaceControl Z requieren
instrumentación; no se inventan a partir de Logcat o JavaScript.

Ruta nativa confirmada en el pin: TabModalDialogViewAndroid JNI →
JavascriptTabModalDialog → ModalDialogManager TAB → ChromeTabModalPresenter /
TabModalPresenter. LifetimeHandler puede suspender/cerrar por navegación,
interactability o tabs; no debe confundirse con Blink HTMLDialogElement.

Hallazgo causal de source: `ChromeTabModalPresenter.showDialogContainer()`
siempre puede mostrar scrim, pero difiere `runEnterAnimation()` mientras
`BrowserControlsUtils.areBrowserControlsFullyVisible()` no sea true. La condición
lee `getBrowserControlHiddenRatio()==0.f`; un callback posterior debe resolverla.
`TabModalPresenter.runEnterAnimation()` es donde se agrega ModalDialogView.
Archium suprime toolbar y la retira de TopControlsStacker. Durante el fallo se
observó toolbar GONE/control_container INVISIBLE. **La relación concreta entre
hiddenRatio, callback pendiente y ese contenedor aún no está demostrada dentro
del proceso.** Es una hipótesis prioritaria verificable, no licencia para saltarse
el gate ni forzar visibilidad global. Se necesita registrar ratio, alturas,
offsets, mRunEnterAnimationOnCallback, add/remove y lifecycle en el mismo incidente.
No se atribuye este fallo a Graphite sin esa evidencia; causa compartida con
Amazon sigue NOT_PROVEN.

## Instrumentación y pruebas entregadas

- `scripts/r52_forensics.py`: metadata Android depurada y acotada (serial explícito,
  máximo 5 muestras/30s); ventanas/handles, bounds/visibilidad, superficies y
  clasificación GPU sin mensajes personales. Dump secuencial no es snapshot
  atómico. Oracle PNG con ROI explícita y viewport idéntico detecta negro,
  duplicado y fase obsoleta; PIXEL_MATCH no es PASS general del producto.
- `scripts/r52_capture_trace.py`: plan por defecto; ejecución explícita sobre
  fixture, Perfetto 8s / 4 MiB / máximo archivo 8 MiB, sesión propia, logs crudos
  opcionales sólo privados. No detiene trazas ajenas. **Preparado, no ejecutado**
  en este incidente; no se afirma disponer de una nueva traza Perfetto.
- `ArcViewProbe.java`: helper opcional de UI thread, tokens/identidades sin texto,
  bounds, alpha, elevación/Z, SurfaceHolder y callbacks limitados a 64. **No está
  integrado en la APK instalada**. No observa SurfaceControl real ni el provider
  de browser controls sin un adaptador específico. No recrea Activity/superficies.
- `original-observer.js`: observador opcional limitado a clics/atributos/bounds del
  original, sin reemplazar handlers ni leer campos. Preparado, no inyectado.
- `r52-repaint.html`: fixture adicional determinista sin red ni diálogos; fases,
  imágenes de alta resolución, scroll y transformaciones. NOT_TESTED en GPU real.

Resultados locales realmente ejecutados:

| Prueba | RED | GREEN / alcance |
| --- | --- | --- |
| Oracle de píxeles | comparación inicial incorrecta falla con negro | detecta negro, duplicado y fase obsoleta; imágenes sintéticas |
| Metadata/privacidad/límites | casos añadidos antes de implementación | 14 tests Python PASS, 0.184s en repetición final |
| Recibo ante timeout | timeout perdía reporte | conserva CAPTURE_BLOCKED sin exponer error crudo |
| ArcViewProbe Robolectric | null Surface/frame y snapshot mutable | 6 PASS SDK30/36; no GPU Android real |
| HTML original host routing | mutación elimina alert y falla | 12 handlers PASS con DOM/native simulados; no prueba visibilidad |
| Reorder existente | sin modificación | 5 regresiones host PASS; no nuevo drag físico |
| Diálogos DeX | scrim sin cuadro, capturas reales | **GREEN de reparación NOT_TESTED** |

Logs RED/GREEN privados bajo `/workspace/macdesk-maintenance/archium-r52/`.
La suite completa de 325 tests pertenece al informe R5.1 anterior; no se presenta
como nueva ejecución R5.2. Los nuevos tests no sustituyen las pruebas gráficas.

## Regresiones, riesgos y siguiente build

No se modificó código de producto, manifest de patches, package name, identidad
Portal ni configuración de compilación. La instrumentación no tiene coste en la
APK actual. Integrarla en un futuro requiere revisar overhead, límites y retirada
de callbacks. Los PASS previos del usuario (restauración, omnibox/navegación,
ventanas/formularios) permanecen USER_REPORTED_PASS, sin reinterpretarlos como
nuevas regresiones ejecutadas. Bookmarks/descargas generales/sesiones: PENDING.
QEMU: **QEMU_ABI_BLOCKED**; los tests host/Robolectric y el Galaxy físico no son
QEMU. GPU Samsung/DeX completo sigue PENDING_DEVICE_VALIDATION; se añade solamente
la reproducción específica descrita, no aceptación total del dispositivo.

Ningún nuevo build despachado. Antes del siguiente: estado terminal del run actual,
checkpoint completo/compatible con hashes, args/toolchain/pin y budget; después,
sólo incremental sin limpieza. Primero medir el gate de browser controls y obtener
regresión causal, o una causa GPU reproducible. Esta rama entrega diagnóstico,
no un fix especulativo. El supervisor existente conserva la responsabilidad del
run; Codex finaliza el turno sin esperar compilación, QEMU ni instalación.

## Fuentes primarias fijadas

- [ChromeTabModalPresenter](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/chrome/android/java/src/org/chromium/chrome/browser/modaldialog/ChromeTabModalPresenter.java).
- [TabModalPresenter](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/browser_ui/modaldialog/android/java/src/org/chromium/components/browser_ui/modaldialog/TabModalPresenter.java).
- [TileManager](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/cc/tiles/tile_manager.cc).
- [SkiaRenderer](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/components/viz/service/display/skia_renderer.cc).

El SHA de esta entrega de investigación se obtiene del commit que introduce este
informe en la rama aislada; no es un SHA de implementación de un fix del APK.
