# R5.2D — Amazon: límite de rasterización/composición

2026-10-19. **Amazon FAIL; ROOT_CAUSE=NOT_PROVEN; PRODUCT_FIX=NONE.**
Se obtuvo evidencia nueva en el Galaxy, sin compilar, cambiar flags ni modificar
el supervisor. El teléfono se devolvió al usuario al terminar la captura.
Amazon permanece abierto y P0-01 permanece pendiente.

## Procedencia e integridad

Worktree `/workspace/Archium-R5.2-forensic`, rama
`assistant/archium-r5-2-forensic`, base completa
`c753c0eee1f732092fc27315c8fb854d53f88c46`. Se leyeron íntegramente y se
compararon los bytes del worktree con `git show c753c0e:RUTA`:

| Documento | SHA-256 |
| --- | --- |
| R5_2C_AMAZON_NATIVE_DIALOGS.md | e91e4843737f9092fa13515b8b4f71cbc0a153b7f7e8765fd72a67d537754daf |
| R5_2_PHONE_HTML_DIAGNOSTICS.md | e9850b5473ecda20aa10ea6eea60fcc96fe0bde42a746ca7e0c1f142780bc9c5 |
| ARCHIUM_R5_2C_AMAZON_NATIVE_DIALOGS.md | 864146e69dd602796f016809c6d43c07278f872e41ef9a44a1fdcbbecdfe2a6f |

Se conserva la identificación de APK medida en R5.2C: run 39296066030,
commit 3db367adff50d423b8c4475d10165d2790f6065a, versionCode 808600074,
SHA-256 `08da74aa96c34d414d9f96324f65a8be1df69067288f4079531c6de73a802b31`.
No hubo instalación en esta intervención. Galaxy S25, Android 17, Adreno 830;
la consulta GPU previa registró ANGLE Vulkan 1.3.284 y GraphiteDawnVulkan.
Esto identifica el backend observado, no lo identifica como culpable.

## Captura nueva ejecutada realmente

Con disponibilidad confirmada por el usuario se abrió la homepage de Amazon MX
en Archium y se seleccionó su target CDP exacto. No se interactuó con cuentas,
compras ni formularios. Una sola ejecución coordinó Perfetto, metadata, capturas
web y un desplazamiento; no se repitió la matriz de popups ni se purgó caché.

| Estado | UTC | scrollY CSS | Imágenes DOM | Totalmente visibles / decodificadas |
| --- | --- | --- | --- | --- |
| Antes | 19:49:27.693 | 0 | 127 | 45 / 45 |
| Después | 19:49:30.080 | 649.53784 | 143 | 33 / 33 |

El criterio de esta tabla exige bounds totalmente dentro del viewport y tamaño
mayor de 20 CSS px; no es el mismo conteo de visibilidad parcial de R5.2C.
Viewport 2256×1330 CSS, DPR 0.9606830477714539. Hay imágenes ennegrecidas
**antes** de este scroll; después aparecen repeticiones verticales de imágenes y
texto en tarjetas. No se deduce que ambos síntomas tengan necesariamente una
misma causa. HTTP/complete/naturalWidth no son un oracle visual.

Se recuperaron 176 capas al terminar la primera toma. Las capas raíz 6 y 8
reportan RootScroller/OverflowScrolling; otras capas reportan Overlap o ninguna
razón adicional. Esas razones describen composición, no una condición de fallo.
La inspección posterior relacionó índices de imagen 42, 43 y 44 con backendNodeId
3023, 3048 y 3073 y capas 65, 67 y 69. Sus replays 155×173 muestran fotografías
normales, sin los barridos negros de la presentación compuesta. También se
recuperaron ocho replays pequeños y dos capas grandes; no se presentan como
una inspección exhaustiva de todas las capas.

La metadata de seis imágenes visibles y cinco niveles de ancestros no mostró
filter, text-shadow ni box-shadow; varias imágenes usan mix-blend-mode:multiply.
No se copiaron textos de productos ni URLs personalizadas al informe. Esto no
audita todo el CSS de Amazon ni descarta transformaciones en otros ancestros.

**Límite importante:** los replays de las imágenes se tomaron después de la
captura compuesta, no como readbacks atómicos del mismo frame. No se dispone de
una pareja de píxeles normalizada que demuestre cuál fue la primera operación
errónea. La captura física final muestra otra aplicación en ese display y queda
EXCLUDED_WRONG_FOREGROUND: no se compara con Amazon ni se publica. El foco que
reporta el DOM no garantiza por sí solo ausencia de oclusión Android.

## Qué significa el diferencial de capas

Se consultó código original del pin Chromium
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` (157.0.8086.0):

- [InspectorLayerTreeAgent::makeSnapshot](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/third_party/blink/renderer/core/inspector/inspector_layer_tree_agent.cc)
  actualiza el lifecycle y obtiene `layer->GetPicture()`.
- [PictureSnapshot::Replay](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/third_party/blink/renderer/platform/graphics/picture_snapshot.cc)
  asigna un SkBitmap limpio y reproduce la picture mediante ReplayingCanvas.
  **No lee la textura GPU viva del tile.**
- [PageHandler::CaptureScreenshot](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/content/browser/devtools/protocol/page_handler.cc)
  solicita screenshot desde surface en esta toma. La ruta de
  [RenderWidgetHostImpl](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/content/browser/renderer_host/render_widget_host_impl.cc)
  fuerza redraw y obtiene CopyFromSurface; no es una captura física Android.
  [RenderWidgetHostViewAndroid](https://chromium.googlesource.com/chromium/src/+/cfd94726b7b5fb48aedcc32662f2f3fbdbadec35/content/browser/renderer_host/render_widget_host_view_android.cc)
  delega la copia a la superficie de composición cuando usa browser compositor.

**Inferencia acotada:** hay contenido que puede reconstruirse correctamente desde
la picture, mientras el readback compuesto está alterado. Un fallo exclusivo de
z-order/oclusiones de WindowManager o de la presentación final de SurfaceFlinger
no explica por sí solo esos píxeles corruptos del readback de Chromium. No se
descarta interacción con recursos compartidos o con la integración de Surface.
La captura puede forzar repintado y makeSnapshot puede modificar el lifecycle;
esas perturbaciones impiden afirmar que el replay sea el tile anterior al fallo.

Primera observación incorrecta demostrada: **píxeles de la captura compuesta**.
Primera transición causal incorrecta entre paint, raster y composición:
**todavía no demostrada**. No hay prueba para elegir Skia, Viz, ANGLE o driver.

## Traza: correlación lograda, atribución incompleta

Perfetto CLI y pull: exit 0; archivo 33,550,953 bytes. Inicio del proceso
19:49:26.250Z; scroll 19:49:28.007–19:49:29.416Z. A diferencia de R5.2C, la
reproducción ocurrió durante la traza. Se analizó con Trace Processor oficial
v58.2, descargado por su launcher oficial con verificación de hash.

- 1,725 actual frames y 1,725 expected frames globales.
- 97 actual frames con layer_name asociado a Archium, entre
  19:49:27.718309Z y 19:49:30.204916Z, calculado con snapshots REALTIME/BOOTTIME.
- 382,810 slices globales, pero **cero** PrepareTiles/DrawAndSwap/RasterTask
  encontrados en la consulta dirigida. No hay correlación tile/resource/fence.
- `frame_timeline_event_parser_errors=1632`, `slice_max_depth_exceeded=111`,
  `traced_chunks_discarded=1`. La traza queda **PARTIAL_NOT_CAUSAL**.
- No hay nombre de proceso Archium en la tabla process de esta captura; la
  atribución anterior usa layer_name, no una asociación PID/upid inventada.

No se interpretan frames con jank o diferencias de rendimiento como corrupción.
El archivo binario y los logs auténticos quedan privados e intactos. El TXT
exportado por los popups sigue siendo registro JavaScript, no Logcat.

## Auditoría de código e hipótesis

| Hipótesis | Evidencia / alcance |
| --- | --- |
| Descarga fallida como explicación universal | Insuficiente: R5.2C registró respuestas y recuperó seis assets; tres se presentaron correctamente en contexto simple. No se repitió aquí toda la red. |
| AVIF o multiply por sí solos | No reproducidos en las 12 variantes simples de R5.2C. No descartados en interacción con capas complejas. |
| CSS shadow observado como origen de las copias | No respaldado en los seis samples y ancestros inspeccionados; no equivale a auditar todo el sitio. |
| Corrupción inherente en toda picture/imagen | No explica los replays normales recuperados; falta pareja atómica del mismo frame. |
| Error sólo de la composición Android final | Insuficiente para explicar readback Chromium ya corrupto; ver inferencia anterior. |
| Reutilización/clear de tiles o render targets, damage, sincronización | Abiertas: faltan IDs y readbacks de las fronteras relevantes. No se cambia ninguna de ellas por intuición. |
| Offset/clip de Arc | Abierta, sin transición errónea medida; no se declara culpable por la coincidencia con DeX. |

Se revisaron `cc/tiles/tile_manager.cc`, `GpuRasterBufferProvider` (content IDs,
dirty rects, Begin/EndRaster y sync tokens), `viz::Display::DrawAndSwap`,
SkiaRenderer y la ruta SkiaOutputSurface GPU. Son puntos para correlacionar, no
funciones a las que se haya demostrado llegar con estado incorrecto.
En Archium se revisaron `ArcDesktopCoordinator.applyFrameGeometry`, clipping de
la Surface activa y las adiciones beginArcRailViewportResize /
setArcContentOffsetForRail de CompositorViewHolder. Estas últimas propagan tamaño
y offset; no reescriben el algoritmo de tiles. No se midió una divergencia de
offset, tamaño o DPR que justifique un cambio de geometría.

## Instrumentación preparada y pruebas

Implementación diagnóstica local:
**043ee143e2d4a4c74c3e949d3050ffb32b40c305**. No es un fix del motor.

- `scripts/r52d-layer-probe.cjs`: toma antes/replay/después, relación DOM/capa,
  límites de 512 capas y tres replays, timeout, output privado. Sin navegar,
  recargar ni desplazar. Rechaza páginas ajenas, cambios de foco/viewport/scroll
  y diferencias de geometría de imágenes. Metadata estable nunca significa PASS
  visual ni identidad de recurso GPU. Esta nueva sonda no se ejecutó en Galaxy;
  las capturas reales anteriores fueron obtenidas por scripts privados cuyos
  hashes están en el recibo.
- `r52d-layer-reuse.html`: 96 tarjetas, dieciséis PNG 768² compartidos, scroll,
  sticky/fixed, transformaciones fraccionarias, multiply, contain:paint y doce
  pasos de reciclaje con retorno a fase/scroll iniciales. Permite resize externo.
  No usa Amazon, cuentas ni assets privados.
- `r52d-frame-timeline.pbtxt`: propuesta acotada gfx-only con process_stats para
  mejorar atribución y reducir volumen. **NOT_TESTED en Android**; no se afirma
  que arregle las pérdidas de la captura anterior.

Resultados locales reales: **7 PASS** Node (origen, privacidad y validez de pares),
**15 PASS** Python del recolector/oracle existente y sintaxis JavaScript válida de
la fixture. No son pruebas GPU ni un RED/GREEN de producto. Un intento de
Chromium Linux ARM64 headless de referencia y un retry acotado fallaron al
conectar a CDP. Se conservan ambos logs: **HOST_REFERENCE=BLOCKED**. No hubo
ejecución de la nueva fixture en Android ni comparación visual con Chrome Android.
No se cambiaron flags gráficos para sortear ese bloqueo.

| Aceptación | Estado |
| --- | --- |
| Amazon actual, antes/después del scroll | FAIL real |
| Regresión determinista del defecto en nueva fixture | NOT_TESTED |
| RED de una causa concreta de raster/composición | NOT_TESTED |
| Fix gráfico mínimo | NONE, causa no demostrada |
| GREEN visual Galaxy con APK corregida | NOT_TESTED |
| Invalidación/recreación de Surface controlada | NOT_TESTED; screenshot fuerza redraw, no prueba recreación |
| QEMU Android | QEMU_ABI_BLOCKED conservado |
| GPU Samsung / DeX aceptación final | PENDING_DEVICE_VALIDATION |

La siguiente sesión disponible debe ejecutar la nueva fixture y la sonda en
Galaxy y Chrome Android, en geometría idéntica; capturar pares estables y revisar
la presentación después del replay. Si reproduce, capturar una ventana corta
de tracing Chromium, consultando primero Tracing.getCategories, para enlazar
paint/raster IDs con render passes y damage. El config Perfetto Android por sí
solo no provee esos eventos. Si aún falta la frontera, se necesita instrumentación
dirigida de content IDs/dirty rects/sync tokens y readback de tiles/render passes;
no una desactivación de GPU. Nunca usar un asset privado como fixture pública.

## Preservación e integración

La rama activa sigue en 3db367adff50d423b8c4475d10165d2790f6065a y limpia.
No se cambia el arreglo de identidad/reordenamiento de pestañas. El fix de
diálogos **51847556e761ca0600a4aa824531e40d200fdf17** continúa aislado en este
historial; no se mergeó/cherry-pickeó ni se declara validado en una APK que no lo
contiene. Sus pruebas source-level de R5.2B mantienen el alcance documentado.

Esta entrega cambia sólo diagnósticos, fixture, tests y documentación. No hay
diff nuevo de Chromium/.source-modified/.source-reference, workflows, pin,
GN args, toolchain, JNI, package o Portal. No añade invalidación al grafo nativo.
No se restauró ni aprobó de nuevo un checkpoint: un futuro build deberá verificar
los bytes del último checkpoint compatible, no inferirlo de este informe.
No se inició GitHub Actions ni una compilación de Chromium, ni se limpiaron outputs/checkpoints.
No se tocó ni duplicó el supervisor. No hay siguiente build autorizado/despachado
por esta investigación; Amazon sigue abierto hasta GREEN real.

[Recibo depurado, hashes y límites](r52d/evidence.json). Originales privados en
`/workspace/macdesk-maintenance/archium-r52d/`; se conservan también íntegros los
directorios R5.2/R5.2B/R5.2C. No se publican capturas completas, Logcat bruto,
pictures personalizadas ni trazas con metadata de otras aplicaciones.
