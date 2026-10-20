# Archium — TODO pendiente para Codex (2026-10-17)

**Estado:** IMPLEMENTACIÓN LOCAL + PENDIENTES DE VALIDACIÓN. Una casilla completada indica únicamente el alcance descrito; pruebas host/Robolectric no equivalen a aceptación visual de una APK.

**Repositorio:** `Jorgeprdz/chromium-dex-arc`  
**Rama de trabajo de este TODO:** `assistant/archium-r5-arc-experience`  
**Rama candidata de correcciones:** `assistant/archium-r5-2-ui-fixes`; integración en la rama de build autorizada el 19-oct-2026 por «compila e instala».
**Entorno observado:** Samsung Galaxy S25, Android, Archium; validar tanto modo teléfono como Samsung DeX.  
**Motor de referencia documentado:** Chromium 157.0.8086.0 (confirmar pin y HEAD efectivos antes de trabajar).  

> **Orden:** estabilidad/renderizado primero; después pulido estético. Evitar un build pesado antes de aislar causas y probar cambios pequeños. No modificar `main` ni `feat/arc-desktop` durante el diagnóstico sin autorización.

**Alcance vigente autorizado:** correcciones de diálogos e interfaz fuera de Amazon.
Amazon conserva su bloqueo y no se reabre su investigación. El usuario autorizó después una compilación incremental de los fixes de diálogos/sidebar y su instalación, sujeta a los gates existentes.

## P0 — R5.1: estabilidad del contenido, compositor y ventanas

### [ ] P0-01 — Scroll corrupto / imágenes y texto «barridos»

**Reproducción reportada (17-oct-2026):** al desplazarse en `amazon.com.mx`, tarjetas de productos, fotografías y tipografías aparecen arrastradas/deformadas, superpuestas o como bloques negros. Hay captura aportada en la conversación del reporte; **no está anexada a este repositorio**.

**Investigar:** ruta Blink → Viz → Skia → GPU/Surface, invalidación/rasterización de tiles, buffers, overlays, `SurfaceView`, clipping y transformaciones del contenedor web; evaluar interacciones con `ArcDesktopCoordinator`. No atribuirlo de entrada al CSS de Amazon.

**Aceptación:** scroll repetido sin artefactos, imágenes ni glifos negros/duplicados; sin regresiones de FPS, foco o consumo en teléfono/DeX. Comparar en el mismo equipo con Chrome Android y, de ser posible, Samsung Internet.

### [ ] P0-02 — Fondo oscurecido sin diálogo visible

**Reproducción reportada:** un mensaje emergente activa el oscurecimiento del fondo (`scrim`), pero el cuadro con el mensaje no aparece.

**Investigar:** distinguir `alert/confirm/prompt` JavaScript, `<dialog>` web y diálogos nativos Chromium/Android; revisar jerarquía de ventanas, tokens, elevación/z-order, overlay, coordenadas, insets, reparenting y foco (también con DeX).

**Aceptación:** mensaje y acciones visibles y operables, restauración del foco y retiro del oscurecimiento tras cerrar. Verificar móvil y escritorio, con teclado/mouse y toque.

- [x] ~~Corregir el gate del presenter cuando el stack activo de browser controls está ausente~~ — fix `5184755`, 18 pruebas locales PASS; incluido en la rama candidata y su parche.
- [x] ~~Integrar el fix en APK mediante build incremental~~ — run `39338037898`, SHA `5b8694a07f328128e1267262780e6996b0ba4509`; artefacto y firma verificados.
- [x] ~~Confirmar que los diálogos vuelven a ser visibles en Galaxy~~ — confirmación directa del usuario el 20-oct-2026 tras instalación manual. PASS de visibilidad reportado por el usuario; no equivale a ejecutar toda la matriz.
- [ ] Verificar por separado alert/confirm/prompt, aceptar/cancelar, valores devueltos, secuencias, retiro del scrim y recuperación del foco; escritorio/móvil pendientes según escenario. **P0-02 conserva abierta la aceptación funcional completa.**

### [ ] P0-03 — Desaparece el contenido web y solo queda la title bar

**Reproducción reportada:** ocasionalmente desaparece toda la zona del sitio y permanece únicamente la barra superior/título de Archium.

**Investigar:** pérdida/recreación de Surface, `surfaceCreated/surfaceDestroyed`, `WebContents` detach/attach, tamaño 0, recortes, occlusion, pestaña/renderer suspendido, cierre de renderer, GPU process loss, resize, minimizar/restaurar y cambios teléfono↔DeX. No confundir la UI nativa que permanece visible con un motor web sano.

**Aceptación:** superficie y pestaña recuperables en transiciones, resize y cambios de foco sin perder navegación/estado/formularios. Capturar logs del proceso y del compositor; no afirmar causa sin evidencia.

- [x] ~~Corregir el recorte vacío/obsoleto de Surface tras resize~~ — corrección parcial anterior con regresiones locales; no cierra todos los escenarios de P0-03.
- [ ] Completar aceptación física de minimizar/restaurar, resize y cambio teléfono↔DeX. Se conserva el PASS previo del usuario de recuperación entre apps/pestañas, sin presentarlo como una prueba nueva.

### [ ] P0-04 — Causa raíz, pruebas y entrega segura

- [x] ~~Registrar HEAD, APK/build instalado, versiones de Android y condiciones~~ — informes R5.2–R5.2E; cada ejecución nueva deberá confirmar de nuevo su binario.
- [x] ~~Preparar páginas deterministas y preservar el HTML original de diálogos~~ — fixtures y diagnósticos existentes; su disponibilidad no significa que todas las pruebas hayan pasado.
- [ ] Comparar teléfono / DeX, ventanas estrechas / maximizadas, pestañas normal / incógnito; realizar scroll, abrir/cerrar popup, resize, minimizar/restaurar y volver a foco.
- [x] ~~Recolectar logs/trazas y conservar evidencia privada con resúmenes depurados~~ — límites de atribución y capturas excluidas documentados; causa gráfica no demostrada.
- [ ] Mostrar RED antes del fix y GREEN después con pruebas relevantes; tests host no sustituyen validación visual de APK real.
- [ ] Arreglar mínimamente el componente responsable, sin workarounds globales ni cambios visuales ajenos.
- [ ] Usar build incremental **solo después** de diagnóstico, preflight, SHA exacto, gates y checkpoint compatible; solicitar aprobación antes de despachar el workflow.

**Prohibido como «solución» rápida:** desactivar GPU/aceleración global, forzar ANGLE/Vulkan indiscriminadamente, reemplazar Chromium por WebView, inyectar CSS/JS global para parchear sitios, ignorar crasheos o borrar cachés/checkpoints sin prueba.

## P1 — R5.2: pulido visual acordado el 16-oct-2026

- [ ] **Sidebar comprimida:** revisar ancho útil, aire entre pestañas, iconos y controles, especialmente en modo compacto y ventanas estrechas.
  - [x] ~~Evitar que la falta de altura de colecciones compacte la navegación de un rail ancho~~ — regresión local 216×500 y separación de presupuestos.
  - [x] ~~Centrar «+» según su fila real e insets, también durante colapso con bounds antiguos~~ — implementación local; falta aceptación con APK.
- [ ] **Jerarquía y consistencia visual:** homologar radios, espaciados, hover, foco, contraste y estado de pestaña seleccionada; evitar densidad excesiva.
  - [x] ~~Retirar hover/pressed/foco visual de controles Arc deshabilitados~~ — feedback preservado en controles habilitados; pruebas de drawables locales.
- [ ] **Contenido web aparentemente pequeño:** medir viewport CSS, device scale, zoom, RDS/UA Client Hints y `text autosizing` antes de cambiar escalas; respetar elección del usuario y evitar zoom forzado.
- [ ] **Controles de ventana:** mejorar visibilidad, contraste, hit targets y alineación sin tapar contenido ni interferir con controles nativos de Android/DeX.
- [ ] **Expandir/contraer sidebar:** pulir animación, reflow, controles y persistencia, sin saltos de viewport ni recreación de pestañas.
- [ ] **Zona inferior/footer:** alinear iconos/acciones, espacios, clipping y remanentes visuales del borde inferior (incluida la cuña previamente reportada cuando corresponda).
  - [x] ~~Asignar ancho de extensiones descontando el menú nativo medido y los insets~~ — no asumir menú de 44dp; actualización tras layout.
  - [x] ~~Redondear por separado los dos botones del footer con densidad fraccionaria~~ — reserva correcta de 232px a densidad 2.625, en lugar de 231px.
  - [ ] Validar footer, carga asíncrona de extensiones y cuña inferior en APK real; el arreglo de ancho no demuestra resuelto el recorte de Surface.

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

## R5.2E — decisión final NO-GO

- [x] Ejecutar el intento final acotado en Galaxy. Amazon vuelve a mostrar
  corrupción en readback de Chromium y pantalla física. Traza Chromium recuperada
  con EOF y sin pérdida declarada; los eventos no incluyen píxeles de tiles GPU.
- [x] Obtener RED visual de la fixture existente sin contenido privado: distorsión
  en Archium; control Chrome sin errores en las muestras de color. Versiones y
  backends diferentes; no equivale a causa raíz ni GREEN de una corrección.
- [ ] **P0-01: UNRESOLVED_GRAPHICS_BLOCKER.** No se demostró la primera transición
  defectuosa ni el código responsable. Buffer Android identificado sólo por
  metadata; replay software no equivale a raster GPU vivo.
- [ ] P0-02: fix 5184755 preservado aislado; aceptación visual con APK corregida
  pendiente. Reordenamiento/sidebar preservados, sin nueva certificación visual.
- [x] Detener experimentos y no despachar build. Sin flags/workarounds gráficos,
  limpieza de outputs, cambios de supervisor ni integración automática.

[Decisión final y punto de cierre](docs/validation/R5_2_FINAL_GO_NO_GO.md).
**No continuar automáticamente ni abrir otra fase. Esperar decisión del usuario.**

## Correcciones autorizadas de interfaz — posteriores al NO-GO de Amazon

El usuario autorizó continuar con fixes fuera de Amazon y actualizar este TODO.
Implementación **0ab6204c9e785ef4d6ce1da456070f0a24f476fe**, en la rama candidata;
no se modificaron la rama base, el arreglo de identidad/reordenamiento de pestañas
ni los tres archivos del fix de diálogos 5184755.

- [x] ~~Implementar navegación responsive, presupuesto de footer y centrado de fila compacta~~ — cambios mínimos en ArcDesktopCoordinator.
- [x] ~~Añadir regresiones de colecciones sin altura, bounds antiguos y densidad fraccionaria~~ — RED observado y GREEN final: 18 casos nuevos en SDK30/36.
- [x] ~~Verificar las regresiones locales del lote~~ — 66 casos Robolectric y 37 comprobaciones Python enfocadas; alcance y adaptadores en el informe.
- [x] ~~Regenerar y comprobar el parche de 128 archivos y compilación aislada Android API37~~ — originales y pin intactos; no equivale a build Chromium/GN/JNI.
- [x] ~~Verificar estado/store/acciones/sesión en límites nativos sintéticos~~ — no acredita persistencia de perfiles reales tras reiniciar el navegador.

### Pendientes nuevos o precisados

- [ ] Compilación incremental del candidato, sólo tras autorización y validación del checkpoint real compatible. **No se despachó ningún run.**
- [ ] APK con fix nativo de diálogos: alert/confirm/prompt visibles, cancelación, retorno de valores, recuperación de foco y lifecycle de ventanas.
- [ ] Validar en Galaxy el footer tras medir/cargar el menú y extensiones, a distintas densidades; comprobar que los listeners no dejan trabajo tras destroy.
- [ ] Aceptación física de sidebar ancha/baja, compacta, hover y colapso repetido; preservar selección y WebContents.
- [ ] Completar el pulido visual restante de filas, espaciados y controles de ventana; las correcciones localizadas no cierran todo P1.
- [ ] Calibrar viewport/escalado con evidencia y respetando el zoom nativo elegido por el usuario; no se aplicó zoom forzado.
- [ ] Verificar marcadores y descargas reales, apertura del archivo y persistencia completa de sesiones tras cierre/reinicio; no sustituirlo por confirms del HTML.
- [ ] Cerrar P0-03 y la cuña inferior con evidencia del dispositivo; se conserva el arreglo parcial de clipping.
- [ ] QEMU_ABI_BLOCKED y aceptación GPU/DeX pendientes. Amazon continúa UNRESOLVED_GRAPHICS_BLOCKER y fuera de este lote.

[Implementación, RED/GREEN y límites de validación](docs/validation/R5_2_UI_FIXES.md).

## Compilación de fixes autorizada — 19-oct-2026

- [x] ~~Preparar integración de diálogos `5184755` y controles/sidebar `0ab6204`~~ — preserva el arreglo de pestañas `3db367a`; sin cambios nuevos de pin, GN args ni toolchain.
- [x] ~~Verificar inventario y manifiesto remoto del último checkpoint disponible~~ — `archium-checkpoint-38511423805-1`, fuente `0abfc9f03e34c23762190365ccb0cf6f9e5c3260`, cuatro grupos/25 partes. Hashes de partes, árbol y outputs se verifican otra vez durante la restauración en CI.
- [x] ~~Completar build incremental del candidato integrado~~ — run `39338037898` SUCCESS; SHA `5b8694a07f328128e1267262780e6996b0ba4509`, APK SHA256 `9db795ddf861a008e0181a60c52bbdf96e91c070c3464ae2b85913f545e6dc37`.
- [x] ~~Verificar identidad de la nueva APK instalada~~ — `base.apk` leído por ADB y SHA256 idéntico al artefacto `9db795ddf861a008e0181a60c52bbdf96e91c070c3464ae2b85913f545e6dc37`; instalación manual confirmada por el usuario. Mantener los datos. QEMU continúa `QEMU_ABI_BLOCKED`: no es PASS y el gate existente impide instalación automática si se repite.
- [ ] Validar visualmente diálogos nativos, foco, footer y sidebar con la APK nueva; no cerrar estos defectos por el mero éxito del build.
- [ ] Amazon: `UNRESOLVED_GRAPHICS_BLOCKER`, ahora también congelamiento reportado por el usuario; sin corrección en este lote.

Preparación: [R5.2 build e instalación](docs/validation/R5_2_BUILD_INSTALL_PREPARATION.md).

### Confirmación del usuario — 20-oct-2026

Instalación manual reportada; los diálogos ya se ven. La identidad de la APK
instalada fue confirmada posteriormente por lectura del `base.apk` del sistema
y SHA256 idéntico al artefacto publicado. No se sustituye `QEMU_ABI_BLOCKED`
ni se afirma auditoría completa del dispositivo.
Se registra únicamente la visibilidad confirmada, sin atribuir resolución de Amazon.


## R5.3 — omnibox, historial y vista dividida (20-oct-2026)

- [x] ~~Preparar clic en la omnibox lateral → pop-up de Ctrl+T con URL seleccionada~~ — reutiliza foco nativo; Ctrl+T sigue vacío. RED baseline: 10/16 fallos; GREEN final: 18/18 en Robolectric, sin afirmar validación de APK nueva.
- [ ] Validar sugerencias, copiar/editar URL, teclado, foco y modo móvil con APK que contenga este cambio.
- [x] ~~Aprobar diseño de vista dividida y plan técnico~~ — ambas opciones de segunda pestaña; dos páginas reales, separador ajustable y cápsula blanca con flechas opuestas apiladas.
- [x] ~~Preparar estado puro de pareja~~ — seis tests JUnit: identidad, swap reversible, activo, cierre, salida y ratio finito. No presenta dos páginas por sí solo.
- [x] ~~Implementar presentación nativa de dos WebContents y conexión de lifecycle/input/selección~~ — código y contratos host probados; aceptación real en APK pendiente.
- [x] ~~Implementar intercambio de capas sin recarga con transición de 180 ms y cápsula blanca~~ — tests de controles/animación PASS; comprobar visualmente con APK nueva.
- [x] ~~Implementar conexión al historial nativo al mantener Atrás/Adelante~~ — preserva clic simple y descarta menú obsoleto por lifecycle/cambio de Tab; seis casos nuevos PASS host/Robolectric.
- [ ] Validar visualmente historial nativo y saltos a entradas con APK nueva.
- [ ] Gate Android de split: dos páginas vivas, scroll, diálogo por panel, cierre, foco, resize y recuperación de superficie. QEMU sigue bloqueado por ABI.

Diseño: `docs/superpowers/specs/2026-10-20-arc-split-view-design.md`.
Plan aprobado: `docs/superpowers/plans/2026-10-20-arc-split-view.md`.

- [x] ~~Conectar menú de pestaña a selector existente/nueva y salida~~ — usa TabModel/TabCreator reales; pruebas del controlador en adaptadores nativos PASS.
- [x] ~~Implementar viewport por panel y preferencia móvil temporal al estrechar~~ — umbrales 600/640 dp, sin recarga ni cambio de zoom/preferencia global. Variantes de servidor pueden requerir navegación explícita.
- [x] ~~Regresiones de recuperación de ContentView, restauración de IDs e incógnito~~ — 68 casos split/controlador/puente Java con límites nativos explícitos; no son GREEN gráfico.
- [ ] Verificar en APK: adaptación móvil por panel, sugerencias, ambos contenidos vivos, IME, diálogos, cierre, TalkBack, persistencia y transición suave.
- [x] ~~Terminar el conjunto diseñado, revisión y gates locales~~ — 340/340 host, 68/68 split, 44/44 helpers y 18/18 omnibox; preparación PASS.
- [ ] Completar compilación incremental y validar la nueva APK; RUN_ID/SHA/checkpoint se registran en el supervisor, sin build limpio.

Informe de implementación y límites: [R5.3](docs/validation/R5_3_SPLIT_VIEW.md).

- [x] ~~Corregir los cinco hallazgos importantes de revisión del split~~ — recuperación, foco, teclado activo, arranque diferido y mínimos por panel con RED/GREEN; se incluye rollback de entrada fallida.
- [ ] Medir coste de mantener dos pestañas visibles y ejecutar la matriz de IME, TalkBack, permisos y Surface con la nueva APK; no cerrado por tests host.

## R5.3 — reparación de build y monitor (20-oct-2026)

- [x] ~~Reproducir y corregir los cuatro errores Java TYPE_USE `@Nullable` del run 39362104801~~ — imports de Consumer/IntConsumer, sin cambiar comportamiento; regresión compilada RED/GREEN.
- [x] ~~Preparar reintento desde el checkpoint más reciente del run fallido~~ — `archium-checkpoint-39362104801-1`, 733 outputs conservados; manifiesto/inventario verificados. Hashes completos/restauración se exigen en CI.
- [x] ~~Desactivar QEMU para este despacho por petición expresa~~ — `run_qemu=false`; no declarar PASS de QEMU ni aceptación Android.
- [x] ~~Implementar monitor de sólo observación con panel ASCII, colores y limpieza antes del refresco~~ — consulta inmediata y cada 600s; mantiene ventana abierta al finalizar, sin reparaciones/relanzamientos automáticos. La solicitud posterior autoriza actualización ADB verificada al finalizar.
- [ ] Completar el nuevo build incremental y verificar la nueva APK. RUN_ID/SHA se guardan en el registro persistente.
- [ ] Confirmar actualización ADB de la nueva APK y validar split, omnibox, foco, diálogos y adaptación móvil; sin GREEN visual por tests host.

[Reparación y monitor](docs/validation/R5_3_BUILD_REPAIR_MONITOR.md).

- [x] ~~Superar gates locales de la reparación y monitor~~ — 352/352 host, 13/13 dirigidas, preparación API37, actionlint y sintaxis shell/Python PASS. El build Chromium real se valida en CI.


## R5.3 — runner y actualización ADB (20-oct-2026)

- [x] ~~Identificar el fallo del run 39370769321~~ — Chromium no descubre clases sin `@RunWith`; no fue un fallo de asserts ni motivo para eliminar el gate.
- [x] ~~Corregir registro de ArcSplitStateTest y ArcSplitViewportPolicyTest~~ — RED en ambas; GREEN de descubrimiento y 86 tests JVM split.
- [x] ~~Validar metadatos del checkpoint más reciente~~ — `archium-checkpoint-39370769321-1`, cuatro grupos/25 partes; restauración y hashes completos pendientes de CI.
- [x] ~~Implementar actualización ADB autorizada y verificada en el monitor~~ — firma, versión, gates y hash del APK instalado; mantiene los datos y respeta confirmaciones Android.
- [ ] Confirmar descubrimiento real de ambas suites y completar el reintento incremental en CI.
- [ ] Confirmar INSTALL_SUCCESS con evidencia Android de la nueva APK; no confundir armado con instalación realizada.
- [ ] Ejecutar aceptación visual de split, cápsula, transición, omnibox y viewport móvil en la nueva APK.

[Diagnóstico, límites y actualización](docs/validation/R5_3_TEST_DISCOVERY_ADB_UPDATE.md).
