# Archium — TODO pendiente para Codex (2026-10-17)

**Estado:** PENDIENTE / BACKLOG. Documento de seguimiento, no equivale a reparación implementada ni a prueba superada.

**Repositorio:** `Jorgeprdz/chromium-dex-arc`  
**Rama de trabajo de este TODO:** `assistant/archium-r5-arc-experience`  
**Entorno observado:** Samsung Galaxy S25, Android, Archium; validar tanto modo teléfono como Samsung DeX.  
**Motor de referencia documentado:** Chromium 157.0.8086.0 (confirmar pin y HEAD efectivos antes de trabajar).  

> **Orden:** estabilidad/renderizado primero; después pulido estético. Evitar un build pesado antes de aislar causas y probar cambios pequeños. No modificar `main` ni `feat/arc-desktop` durante el diagnóstico sin autorización.

## P0 — R5.1: estabilidad del contenido, compositor y ventanas

### [ ] P0-01 — Scroll corrupto / imágenes y texto «barridos»

**Reproducción reportada (17-oct-2026):** al desplazarse en `amazon.com.mx`, tarjetas de productos, fotografías y tipografías aparecen arrastradas/deformadas, superpuestas o como bloques negros. Hay captura aportada en la conversación del reporte; **no está anexada a este repositorio**.

**Investigar:** ruta Blink → Viz → Skia → GPU/Surface, invalidación/rasterización de tiles, buffers, overlays, `SurfaceView`, clipping y transformaciones del contenedor web; evaluar interacciones con `ArcDesktopCoordinator`. No atribuirlo de entrada al CSS de Amazon.

**Aceptación:** scroll repetido sin artefactos, imágenes ni glifos negros/duplicados; sin regresiones de FPS, foco o consumo en teléfono/DeX. Comparar en el mismo equipo con Chrome Android y, de ser posible, Samsung Internet.

### [ ] P0-02 — Fondo oscurecido sin diálogo visible

**Reproducción reportada:** un mensaje emergente activa el oscurecimiento del fondo (`scrim`), pero el cuadro con el mensaje no aparece.

**Investigar:** distinguir `alert/confirm/prompt` JavaScript, `<dialog>` web y diálogos nativos Chromium/Android; revisar jerarquía de ventanas, tokens, elevación/z-order, overlay, coordenadas, insets, reparenting y foco (también con DeX).

**Aceptación:** mensaje y acciones visibles y operables, restauración del foco y retiro del oscurecimiento tras cerrar. Verificar móvil y escritorio, con teclado/mouse y toque.

### [ ] P0-03 — Desaparece el contenido web y solo queda la title bar

**Reproducción reportada:** ocasionalmente desaparece toda la zona del sitio y permanece únicamente la barra superior/título de Archium.

**Investigar:** pérdida/recreación de Surface, `surfaceCreated/surfaceDestroyed`, `WebContents` detach/attach, tamaño 0, recortes, occlusion, pestaña/renderer suspendido, cierre de renderer, GPU process loss, resize, minimizar/restaurar y cambios teléfono↔DeX. No confundir la UI nativa que permanece visible con un motor web sano.

**Aceptación:** superficie y pestaña recuperables en transiciones, resize y cambios de foco sin perder navegación/estado/formularios. Capturar logs del proceso y del compositor; no afirmar causa sin evidencia.

### [ ] P0-04 — Causa raíz, pruebas y entrega segura

- [ ] Registrar HEAD, APK/build instalado, versiones de Android, forma de ventana y condiciones de reproducción.
- [ ] Montar una página determinista con imágenes, tipografías, scroll, transform/sticky/fixed, canvas, `alert/confirm/prompt` y `<dialog>`.
- [ ] Comparar teléfono / DeX, ventanas estrechas / maximizadas, pestañas normal / incógnito; realizar scroll, abrir/cerrar popup, resize, minimizar/restaurar y volver a foco.
- [ ] Recolectar logs/trazas (GPU, renderer, compositor y Android WindowManager) eliminando tokens, cuentas y contenido privado.
- [ ] Mostrar RED antes del fix y GREEN después con pruebas relevantes; tests host no sustituyen validación visual de APK real.
- [ ] Arreglar mínimamente el componente responsable, sin workarounds globales ni cambios visuales ajenos.
- [ ] Usar build incremental **solo después** de diagnóstico, preflight, SHA exacto, gates y checkpoint compatible; solicitar aprobación antes de despachar el workflow.

**Prohibido como «solución» rápida:** desactivar GPU/aceleración global, forzar ANGLE/Vulkan indiscriminadamente, reemplazar Chromium por WebView, inyectar CSS/JS global para parchear sitios, ignorar crasheos o borrar cachés/checkpoints sin prueba.

## P1 — R5.2: pulido visual acordado el 16-oct-2026

- [ ] **Sidebar comprimida:** revisar ancho útil, aire entre pestañas, iconos y controles, especialmente en modo compacto y ventanas estrechas.
- [ ] **Jerarquía y consistencia visual:** homologar radios, espaciados, hover, foco, contraste y estado de pestaña seleccionada; evitar densidad excesiva.
- [ ] **Contenido web aparentemente pequeño:** medir viewport CSS, device scale, zoom, RDS/UA Client Hints y `text autosizing` antes de cambiar escalas; respetar elección del usuario y evitar zoom forzado.
- [ ] **Controles de ventana:** mejorar visibilidad, contraste, hit targets y alineación sin tapar contenido ni interferir con controles nativos de Android/DeX.
- [ ] **Expandir/contraer sidebar:** pulir animación, reflow, controles y persistencia, sin saltos de viewport ni recreación de pestañas.
- [ ] **Zona inferior/footer:** alinear iconos/acciones, espacios, clipping y remanentes visuales del borde inferior (incluida la cuña previamente reportada cuando corresponda).

**Decisiones visuales a preservar:** color durazno aprobado, identidad Arc/Archium Portal, pestañas verticales, estética ligera. No añadir sombras pesadas, bordes excesivos ni cristal/blur costoso sin soporte comprobado. Conservar navegación real de Chromium, bookmarks, perfiles y extensiones.

## Orden de ejecución cuando Codex esté disponible

1. **Auditar estado real del repo**, HEAD y de la APK que muestra el bug; no asumir que la rama de documentación coincide con los binarios instalados.
2. Reproducir, medir y aislar individualmente P0-01 / P0-02 / P0-03; determinar si comparten causa o requieren arreglos independientes.
3. Tests RED → fix mínimo → GREEN; revisión de diffs, memoria, energía y regresiones de interfaz móvil.
4. Hacer una sola solicitud de build incremental cuando haya evidencia suficiente y autorización explícita; validar APK en Galaxy S25 y DeX.
5. Cerrar P0; **solo entonces** trabajar P1 por lotes pequeños verificables.

**Documentos relacionados:** `docs/ARCHIUM_DESKTOP_ENGINE_R1_PERFORMANCE_RENDERING_2026-10-12.md` y verificaciones R3/R4 en `docs/` cuando existan en la rama. Sus planes no constituyen pruebas de que P0 ya esté arreglado.

## Avance de diagnóstico — 2026-10-19

Estado: **PREPARADO PARA BUILD INCREMENTAL SUPERVISADO**. Los anexos QEMU y
Autonomous Supervisor sustituyen la exigencia de pruebas físicas durante esta
ejecución; Galaxy/DeX quedan PENDING_DEVICE_VALIDATION. El estado vivo y los
RUN_ID se guardan en el registro privado del supervisor.
Se reprodujo y corrigió un recorte vacío/obsoleto de Surface al cambiar su tamaño
sin resize del holder (4 regresiones Robolectric SDK30/36 RED → GREEN y mutación
negativa RED). Esto no cierra P0-03 ni demuestra causa común con P0-01/P0-02.
Se añadió una página determinista de renderizado/diálogos y un bloqueo de GN args
incompatibles que conserva los outputs del checkpoint. R5.2 sigue pendiente.

Evidencia, checkpoint candidato y límites de validación:
[Auditoría R5 progresiva](docs/ARCHIUM_R5_PROGRESSIVE_2026-10-19.md).

El supervisor continúa únicamente checkpoints completos y compatibles, con seis
runs/10 horas y dos reparaciones por causa. Codex se reanuda por ID exacto solo ante
fallos técnicos reparables o instalación realmente confirmada. QEMU incompatible
se registra BLOCKED, sin PASS simulado, instalación ni builds limpios. No se cierran
las tareas P0/P1 por haber compilado o instalado una APK.

## R5.1 post-build — run 39259086848

- [ ] **FAIL 1 confirmado por usuario:** Amazon mantiene imágenes negras, texto
  duplicado y residuos incluso tras recuperación. Captura en teléfono recuperada;
  GPU observada Adreno 830 / ANGLE Vulkan / GraphiteDawnVulkan. Causa raíz y GREEN
  visual pendientes; no desactivar GPU ni atribuirlo al clip Arc anterior.
- [ ] **FAIL 2 confirmado por usuario:** scrim sin cuadro. Separar alert/confirm/prompt,
  HTML modal, HTML no modal, overlay CSS y Chromium/Android nativo. Se recuperó
  `archium-popup-log.txt` (JavaScript, no Logcat); retornos OK no prueban visibilidad.
  Jerarquía fuera del incidente no prueba bounds durante el fallo. Sin causa ni GREEN.
- [ ] **FAIL 3 confirmado por usuario:** títulos/filas se superponen tras reorder.
  Dump Android demuestra coexistencia de fila antigua 208px y compacta 44px en el
  mismo intervalo vertical. Candidato mínimo preserva modelos durante reorder de
  pestañas simples, con RED/GREEN JVM; validación visual y drag Android pendientes.
- [ ] Preservar PASS del usuario: restauración entre apps/pestañas, omnibox/navegación,
  ventanas y formularios. No equivale a nueva ejecución propia. Marcadores,
  descargas y persistencia completa de sesiones siguen PENDING.

[Informe forense y límites de validación](docs/validation/R5_1_FORENSIC_REPORT.md).
QEMU del build evaluado: **QEMU_ABI_BLOCKED**, 32 casos BLOCKED; GPU/DeX siguen
PENDING_DEVICE_VALIDATION. No cerrar estos fallos por superar build o tests host.

## R5.2 — investigación aislada y ensayo original (2026-10-19)

- [ ] P0-01 Amazon: causa NOT_PROVEN; fixture/oracle y captura acotada preparados,
  sin GREEN visual ni cambio arbitrario de GPU.
- [ ] P0-02: RED real en DeX con alert/confirm/prompt, incluidos seis mosaicos de
  ruta nativa. Scrim visible, contenedor GONE/0×0 y sin ModalDialogView durante
  evento abierto. Hipótesis prioritaria: espera del gate de browser controls;
  falta observar hiddenRatio/callback interno antes de una corrección.
- [x] Ejecutar individualmente los doce mosaicos del HTML original intacto en
  Galaxy con capturas/dumps correlacionados: HTML modal/no modal/overlay,
  window.open y selector Android visibles. Este check sólo certifica el ensayo,
  no cierra P0-02 ni valida marcadores reales o descargas generales.
- [ ] GREEN posterior a reparación y validación GPU/DeX completa pendientes.
  QEMU_ABI_BLOCKED permanece; no hubo ejecución Android QEMU.

[Informe GPU/diálogos](docs/validation/R5_2_GPU_DIALOG_FORENSIC.md) y
[matriz del HTML original](docs/validation/R5_2_PHONE_HTML_DIAGNOSTICS.md).
Rama activa/run 39296066030 preservados; ningún build nuevo desde investigación.

## R5.2B — presenter nativo con barra ausente

- [x] Reproducir en código el bloqueo: altura del stack activo cero → hiddenRatio
  uno → scrim visible sin adjuntar ModalDialogView; RED/GREEN Robolectric de
  métodos fijados y vistas Android. Se conserva la semántica global del provider.
- [x] Preparar fix local del gate y de callbacks de altura, más trazas optativas
  correlacionadas por modelo; no se modificaron JNI, respuestas ni identidades
  de pestañas. No hubo build ni integración en la rama activa.
- [ ] Confirmar los valores internos del provider durante el incidente del Galaxy
  y obtener GREEN visual de alert/confirm/prompt con APK posterior autorizada.
  El fix de código no cierra P0-02 del instalado. Foco, permisos, draw y fugas de
  ventanas reales siguen pendientes. QEMU_ABI_BLOCKED no cambia.

[Diagnóstico, RED/GREEN y límites R5.2B](docs/validation/R5_2B_NATIVE_DIALOG_ROOT_CAUSE.md).

## R5.2C — Amazon directo sobre APK 3db367a

- [x] Confirmar por hash que la APK instalada es la publicada en 39296066030;
  todavía no incluye el fix nativo 5184755. No se declara autoinstalación.
- [x] Reproducir en Amazon corrupción de imágenes/texto con imágenes DOM
  decodificadas y sin fallos HTTP/transporte de imagen en la ventana registrada.
- [x] Diferencial de imágenes: PNG local tras scroll sin diferencias; tres
  muestras AVIF reales y sus PNG visibles en composición simple normal/multiply.
- [x] Corregir path de output de Perfetto con RED/GREEN; captura real recuperada.
- [ ] Amazon: causa gráfica y fix de producto pendientes. La traza recuperada
  no se sincronizó con el scroll y no es prueba causal. Se detuvieron acciones
  al cambiar el usuario de aplicación. No introducir flags GPU por tanteo.

[Informe R5.2C](docs/validation/R5_2C_AMAZON_NATIVE_DIALOGS.md). Sin nuevo build.

## R5.2D — frontera paint/raster/composición, sin build

- [x] Captura sincronizada real de Amazon y scroll: imágenes negras antes del
  desplazamiento y repeticiones de texto/imágenes después. P0-01 continúa FAIL.
- [x] Relacionar tres imágenes DOM con capas y recuperar replays software
  visualmente normales. No son readbacks de tiles GPU ni una pareja atómica.
- [x] Analizar traza: 97 frames con layer_name de Archium en la ventana de scroll;
  pérdidas/import errors y ausencia de eventos de tiles impiden causa concluyente.
- [x] Preparar fixture de reciclaje/capas y sonda privada acotada; 7 tests Node y
  15 Python PASS locales. No equivalen a GREEN gráfico.
- [ ] Ejecutar nueva fixture en Galaxy/Chrome Android y enlazar raster/resources
  con composición. Referencia Chromium Linux bloqueada al conectar a CDP.
- [ ] Causa raíz, fix mínimo y GREEN visual de Amazon siguen pendientes.
  QEMU_ABI_BLOCKED y aceptación GPU/DeX pendientes; fix 5184755 preservado aislado.

[Informe R5.2D y evidencia](docs/validation/R5_2D_AMAZON_COMPOSITOR_ROOT_CAUSE.md).
Sin nuevos runs, integración del fix nativo ni cambios de flags/checkpoints.
