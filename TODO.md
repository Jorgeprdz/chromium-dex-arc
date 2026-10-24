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

## R5.3 — validación real de uso (20-oct-2026)

- [x] ~~Verificar APK instalada del run 39379198808~~ — hash leído del sistema Android idéntico al artefacto `ade9b690…829f1fc`.
- [x] ~~Recorrer pestañas existentes y comprobar split básico en Galaxy~~ — pareja visible, foco por panel, scroll derecho, intercambio, separador, enlace público y Atrás ejecutados; PASS acotado a esta sesión.
- [x] ~~Comprobar sugerencias e historial desplegable~~ — sugerencias nativas al escribir y menú de historial hacia adelante visibles.
- [ ] **DEVICE-01 / omnibox: restaurar URL actual seleccionada.** El popup queda vacío al abrirlo desde la dirección lateral; reproducido en visor simple y split.
- [ ] **DEVICE-02 / split: navegar desde omnibox sobre el panel activo.** Enter crea otra pestaña y deja de mostrar la división, en vez de cambiar la dirección del panel seleccionado.
- [ ] **DEVICE-03 / sidebar compacta:** revisar fila activa que muestra X sin favicon; medir bounds de selección/cierre sin cerrar pestañas del usuario.
- [ ] Medir suavidad de intercambio por frames y validar cambio efectivo de UA móvil, creación desde selector, restauración y estabilidad prolongada; no cubiertos por esta revisión.

[Revisión real y evidencia](docs/validation/R5_3_DEVICE_USABILITY_REVIEW.md).


## R5.3 — fixes derivados de la revisión real (20-oct-2026)

- [x] ~~Corregir código DEVICE-01/02: diferenciar editar dirección actual de Ctrl+T~~ — el puente conserva URL y navegación actual; RED 4 fallos → GREEN 6/6 en ramas Java entregadas. Aceptación visual de nueva APK pendiente.
- [x] ~~Corregir política DEVICE-03 de fila compacta en ventana Arc~~ — no reemplazar favicon por X sin hover; conserva comportamiento móvil, expandido y pinned. Pendiente comprobar en Galaxy con nueva APK.
- [x] ~~Añadir regresiones en pruebas nativas Chromium y gate de Mediator~~ — no se salta ninguna suite existente.
- [ ] Completar build incremental y confirmar que el runner real pasa las regresiones nuevas.
- [ ] Instalar APK nueva y repetir casos DEVICE-01/02/03 en el Galaxy; mantener abiertos los defectos observados hasta GREEN visual.

[Corrección de dirección y compacta](docs/validation/R5_3_ADDRESS_AND_COMPACT_FIX.md).

- [x] ~~Superar gates locales del candidato~~ — 371/371 host PASS; 18 puente/Fusebox, 18 popup, 86 split y 50 helpers JVM PASS; preparación API37 y sintaxis PASS. No equivale a GREEN visual.


## R5.4 — acabado de split y PR de mejoras (20-oct-2026)

- [x] ~~Registrar confirmación del usuario: la pantalla dividida instalada ya funciona~~ — aceptación acotada a su confirmación; no implica validar este acabado nuevo.
- [x] ~~Añadir marco del tono de la ventana, separación central y esquinas suaves~~ — geometría compartida con ContentView/capas; contorno sutil del panel activo.
- [x] ~~Convertir la cápsula blanca en agarre y menú desplegable~~ — arrastre en estado compacto o expandido; intercambio con transición existente; X sale del split conservando ambas pestañas y la activa.
- [x] ~~Añadir cierre exterior/Escape/lifecycle y movimiento reducido~~ — casos JVM de controles, foco hijo, teardown y reducción de movimiento; aceptación WindowManager real pendiente.
- [x] ~~Ajustar mínimos y adaptación móvil al ancho interior del marco~~ — incluidos densidad fraccional, RTL y restauración de layout previo.
- [x] ~~Superar revisión y gates locales del acabado~~ — 106/106 JVM split, 24/24 parche, 17/17 host Arc, descubrimiento, preparación SDK37 y escena C++ con adaptadores host. No son GREEN visual.
- [ ] Mantener el PR en borrador y agrupar los siguientes fixes o implementaciones acordados antes de integrar y compilar.
- [ ] Validar el acabado con una APK futura: marco y color, cápsula, hover, teclado/Escape, resize, IME/insets, foco al salir, diálogos y restauración de superficie.
- [ ] Cuando se acuerde compilar el conjunto, verificar y reutilizar el último checkpoint compatible; no hay nuevo build despachado en esta tarea.

[Informe del acabado de split](docs/validation/R5_4_SPLIT_POLISH.md).

## R5.4 — enlaces y gestos aprobados (20-oct-2026)

- [x] ~~Implementar doble clic a 50/50 y ajuste magnético al centro~~ — transición rápida, histéresis de captura/liberación y límites reales del panel.
- [x] ~~Añadir hover y breve iluminación de encaje~~ — sin botones permanentes adicionales ni animaciones al desactivar movimiento.
- [x] ~~Ampliar temporalmente el panel y restaurar la pareja/proporción~~ — conserva Tabs/WebContents y acción de retorno visible.
- [x] ~~Añadir «Abrir en pestaña dividida» al menú nativo de enlaces~~ — clic alterno/long press; HTTP(S), contexto nativo y validación de origen/ventana/modelo.
- [x] ~~Conectar Ctrl+Alt+clic a NEW_SPLIT_VIEW~~ — Ctrl+clic y Alt+clic mantienen su tratamiento nativo; fallback fuera de ventanas Arc elegibles.
- [x] ~~Conservar metadata y propiedad de navegación nativa~~ — referrer/additional params del menú, headers/POST/renderer del atajo; la ruta renderer conserva el WebContents creado y deja viva la antigua pestaña vecina.
- [x] ~~Corregir hallazgos de revisión del conjunto~~ — agarre anclado al expandirse y animación detenida antes de cambiar de modelo; RED/GREEN.
- [x] ~~Superar gates locales de la tanda~~ — 124 JVM split PASS; 371 host verificados (dos fixtures AAPT2 reejecutados con SDK configurado); dos hooks host nuevos, preparación SDK37, sintaxis, actionlint y patch reproducible PASS.
- [x] ~~Despachar la tanda R5.4 y entregar el monitor~~ — run39486593880, SHA0eabba1; enlace nativo PASS, detenido por seis fallos de preparación JVM. Checkpoint39486593880-1 publicado; no se produjo APK validada.
- [ ] Validar las mejoras con APK instalada: enlaces generales, Ctrl+Alt, target=_blank, formularios, descargas, foco/restore y resize/móvil. No marcar PASS por gates host o por superar el build.

[Reporte de enlaces y gestos](docs/validation/R5_4_SPLIT_LINKS_AND_GESTURES.md).


## R5.4 — reparación del gate JVM y reutilización del último checkpoint

- [x] ~~Identificar el fallo real del run39486593880~~ — falta de contexto nativo para GURL y mock de clase final ResourceRequestBody; tres casos × SDK30/36.
- [x] ~~Corregir la preparación de las pruebas~~ — BaseRobolectricTestRunner y fábrica real de ResourceRequestBody con interfaz JNI acotada y limpieza en finally; sin cambios de producción.
- [x] ~~Reproducir RED y obtener GREEN local pertinente~~ — 54 casos del controlador: seis fallos → 54 PASS; conjunto split 124 PASS. El probe declara sus límites y usa Mockito subclass y la clase final upstream real.
- [x] ~~Verificar metadata del checkpoint más reciente~~ — checkpoint39486593880-1, cuatro grupos y 25 partes; manifiesto/SHA de origen comprobados. Bytes completos y capacidad del runner deben verificarse antes de restaurar en CI.
- [x] ~~Completar controles host y de preparación~~ — 373 ejecutados:372 PASS, guard de descubrimiento ajustado y reejecutado1/1 PASS; SDK37, actionlint y patch reproducible PASS.
- [ ] Confirmar GREEN con el runner Chromium nativo completo y publicar APK verificable en la recompilación incremental.
- [x] ~~Validar marco, cápsula, gestos y enlaces divididos con la APK instalada~~ — PASS reportado por el usuario el 21-oct-2026; alcance detallado abajo. Amazon sigue UNRESOLVED_GRAPHICS_BLOCKER.

[Diagnóstico y corrección del gate JVM](docs/validation/R5_4_CI_JVM_REPAIR.md).


## Aceptación del usuario — R5.4, 21-oct-2026

Evidencia: confirmaciones en la conversación sobre el build del run [39503348021](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39503348021), SHA `cb9822aa0a4a0e4a5d5609bd80da470b0d4db325`. Son resultados de uso real reportados por el usuario, no una nueva ejecución automatizada ni una auditoría de instalación por ADB.

- [x] ~~Pantalla dividida, marco y botones/cápsula~~ — confirmación explícita del usuario.
- [x] ~~Ctrl+Alt+clic y abrir enlaces en pantalla dividida~~ — confirmación explícita del usuario.
- [x] ~~Arrastre del separador y adaptación a vista móvil~~ — confirmación explícita del usuario.
- [x] ~~Omnibox y diálogos nativos~~ — confirmación explícita del usuario.
- [x] ~~Encaje central y doble clic para volver a 50/50~~ — incluidos en la lista restante confirmada con «todo ok».
- [x] ~~Intercambiar, ampliar/restaurar conservando scroll y formularios~~ — incluidos en esa confirmación global de la lista revisada.
- [x] ~~Salir del split conservando ambas pestañas~~ — incluido en esa confirmación.
- [x] ~~Reordenar pestañas y volver desde otra aplicación sin perder contenido~~ — incluidos en esa confirmación.

### Pendientes fuera del alcance de esa aceptación

- [ ] Amazon: `UNRESOLVED_GRAPHICS_BLOCKER`; no se incluyó una corrección en este build.
- [ ] Verificaciones específicas no confirmadas: target=_blank/opener, descargas, marcadores y persistencia completa de sesiones.
- [ ] Validación detallada de teclado/Escape, IME/insets, recreación de superficie y estabilidad prolongada; la confirmación funcional no demuestra cobertura de todos esos casos.
- [ ] Pruebas específicas de GPU Samsung/DeX: `PENDING_DEVICE_VALIDATION`; QEMU sigue deshabilitado por decisión del usuario.


## Regresión reportada — pareja split al cambiar de pestaña (21-oct-2026)

La aceptación anterior queda acotada: el usuario detectó que seleccionar una pestaña externa y volver a una de las divididas deshace la pareja. Candidato de corrección implementado en la rama de parejas; GREEN host y validación de APK se registran por separado.

- [ ] Conservar la asociación, orden, proporción y panel activo al navegar a otra pestaña; suspender sólo la presentación y recuperarla al volver.
- [ ] Mostrar una entrada conjunta en la sidebar: títulos «Página 1 | Página 2» expandida y ambos favicons separables visualmente en compacto, conservando las identidades nativas.
- [ ] Regresión A/B → C → A/B repetida, incluyendo proporción modificada y foco; cierre y salida explícita deben conservar sus semánticas.
- [x] ~~Definir el alcance de parejas~~ — el usuario solicita varias parejas independientes por ventana.
- [ ] Revisar e implementar el [diseño de parejas persistentes](docs/superpowers/specs/2026-10-21-persistent-split-pairs-design.md), con regresiones y aceptación en APK nueva.

Causa reproducida: didSelectTab/refresh disolvían la asociación al seleccionar un ID ajeno. El registro de parejas ahora conserva asociaciones al suspender su presentación. RED/GREEN ejecutado en el controlador: 76 pruebas; la aceptación en APK nueva sigue pendiente. No se despacha build.


## Regresión reportada — primer clic de omnibox (21-oct-2026)

- [ ] **OMNI-CLICK-01:** con mouse, a veces el popup no abre hasta varios clics. La aceptación anterior de omnibox no cubría esta intermitencia.
- [x] ~~Reproducir un stream de entrada incompleto que consume el clic siguiente~~ — RED6/24 contra cb9822a; coincidencia causal con los eventos del Galaxy pendiente.
- [x] ~~Preparar corrección mínima del estado de gesto~~ — GREEN24/24 del probe Android,50/50 helpers,6/6 semántica y preparación SDK37 PASS; candidato aislado, no integrado en APK.
- [ ] Completar gates del conjunto y ejecutar las regresiones nuevas en el runner Chromium real antes del build incremental.
- [ ] Verificar primer clic con mouse, foco de ventana, copiar/editar, Ctrl+L/Ctrl+T y retorno desde otras apps con APK que contenga el cambio.

[Diagnóstico, RED/GREEN y límites](docs/validation/R5_5_OMNIBOX_POINTER_STREAM.md). No se declara resuelto por pruebas host.


## Próxima tanda única — parejas, entrada y jerarquía de sidebar

Estado: implementación autorizada el 21-oct-2026 y recuperada tras interrupción de Termux. El candidato vive en `assistant/archium-r5-persistent-split-pairs`; [recuperación y gates](docs/validation/R5_6_TERMUX_RECOVERY.md). La integración/compilación incremental y la aceptación de APK se mantienen como gates separados.

### Conjunto a integrar

Código recuperado y completado: registro de múltiples parejas; proyección por IDs nativos, fila conjunta y callbacks de iconos protegidos; candidato de omnibox; apariencia y microanimación cancelable. Los checks siguientes siguen abiertos porque incluyen integración final o aceptación en APK.

- [ ] Parejas divididas independientes: conservar A/B y D/E al visitar C; una fila por pareja, con ambos títulos o favicons según el rail. [Diseño para revisión](docs/superpowers/specs/2026-10-21-persistent-split-pairs-design.md).
- [ ] OMNI-CLICK-01: verificar e integrar el candidato aislado del primer clic con mouse; no marcar resuelto hasta GREEN en APK. [Diagnóstico y límites](docs/validation/R5_5_OMNIBOX_POINTER_STREAM.md).
- [ ] R4/SIDEBAR-HIERARCHY: aplicar únicamente el refinamiento visual y funcional detallado abajo, después de acordar el conjunto. No implica implementar otro navegador, sistema de pestañas ni gestor de Espacios.

### R4/SIDEBAR-HIERARCHY — viabilidad y alcance localizado

**Viable sobre la arquitectura existente.** TabVerticalViewBinder ya recibe IS_SELECTED, IS_MULTI_SELECTED, IS_PINNED, títulos y proveedor de favicons del modelo nativo. VerticalTabListCoordinator ya separa las listas fijadas/ordinarias y calcula un separador según las pestañas visibles del Espacio. VerticalTabItemHoverController ofrece hover cards y notificaciones de foco. ArcDesktopCoordinator ya dispone de cabecera, área de pestañas/Espacios y footer. Esos mecanismos deben reutilizarse; la inspección no demuestra que todas las carencias descritas sean defectos reproducidos.

- [ ] **Activa:** mantener un único tab activo según TabModel y su PropertyModel; conservar su resaltado al perder foco, recargar o navegar. Distinguir multiselección de actividad. Cuando se integren parejas, su fila conjunta representa el tab activo nativo sin marcar dos tabs activos independientes.
- [ ] **Estados:** separar normal, hover, activo, foco de teclado y deshabilitado; permitir activo+foco y activo+hover sin perder el resaltado principal. Usar los colores existentes y conservar radios, hit targets e iconos. Revisar el tratamiento actual de foco/hover antes de añadir listeners o indicadores.
- [ ] **Fijadas/temporales:** aprovechar las dos listas nativas y evaluar su separación en expandido/compacto cuando ambas estén presentes. Conservar orden/pinning nativos y el filtro por Espacio; no mover tabs por seleccionar ni crear etiquetas, filas de altura nueva o colores nuevos.
- [ ] **Tres regiones:** reforzar acciones, pestañas/Espacios y utilidades con los contenedores y separadores actuales. Mantener ancho, geometría general, disposición y dimensiones; no reconstruir el layout.
- [ ] **Identificación:** conservar favicon nativo y comprobar su fallback; título/tooltip o hover card y descripción accesible correctos al reciclar filas. Verificar también la pestaña activa, porque la hover card nativa puede omitirla. No cambiar ni teñir favicons del sitio.
- [ ] **Actualización:** actuar sobre propiedades/filas afectadas usando los IDs nativos actuales; no introducir una selección visual independiente ni refrescos completos en cada cambio de pestaña. Conservar ciclo de vida, cierre, movimiento, fijación y aislamiento por perfil/Espacio.

Componentes candidatos, sujetos a evidencia antes de modificar: TabVerticalViewBinder, VerticalTabItemHoverController, VerticalTabListCoordinator y el estilo de controles/regiones de ArcDesktopCoordinator. TabListMediator y ArcNativeTabSession conservan la autoridad del modelo y la proyección de Espacios. No añadir un store de selección ni reimplementar persistencia.

**Exclusiones del refinamiento R4:** omnibox (su bug se trata en el apartado independiente de esta tanda), desplazamiento horizontal, zoom/escala, viewport de Seguros Monterrey, renderizado/compositor, colores/branding y rediseño. No dependencias nuevas, animaciones costosas ni APIs exclusivas de Samsung. No declarar esos comportamientos web como fallos de Archium por la captura mencionada.

### R4 — refinamientos con GO incorporados al alcance (21-oct-2026)

Implementados en el candidato de la tanda conjunta y sujetos a validación de APK; los checks siguientes indican código y pruebas host, no aceptación de dispositivo. [Auditoría técnica y condiciones](docs/validation/R4_VISUAL_LINK_HOVER_FEASIBILITY.md). Conservar paleta, geometría, ancho compacto, iconografía y dimensiones actuales; reutilizar el alcance de jerarquía anterior sin duplicar sistemas.

- [x] **Selección activa refinada:** prioridad visual persistente desde el modelo nativo; distinguir hover, foco y multiselección, incluidas las futuras filas de parejas.
- [x] **Separadores sutiles:** aprovechar las regiones y listas existentes con espaciado disponible o trazos sin alterar dimensiones, orden ni hit targets.
- [x] **Tooltips/hover cards de pestañas:** reutilizar componentes nativos, comprobar títulos, accesibilidad, reciclado y cobertura de la pestaña seleccionada. No crear un overlay nuevo. Esto es identificación de pestañas, no Link Hover Preview.
- [x] **Normalización óptica de favicons:** centrado, ajuste y fallback consistentes dentro del tamaño actual; conservar el icono real sin teñirlo, recortarlo ni redibujarlo.
- [x] **Profundidad de sidebar:** borde interior de 1 píxel físico con la paleta actual, sin consumir espacio de layout. No incluir blur continuo ni sombras adicionales sin evaluación.
- [x] **Indicadores de Spaces:** proyectar el Espacio actual desde el modelo y selector persistentes existentes; no añadir otro store ni confundir Espacios con grupos.
- [x] **Microanimaciones acotadas:** transiciones de propiedades de UI cancelables, compatibles con animaciones desactivadas y reciclado. No animar dimensiones de WebContents/superficies; comprobar fluidez antes de ampliar efectos.

### Gates y aceptación del conjunto

- [ ] RED/GREEN relevante para los cambios realmente necesarios: selección, cierre de activa, pin/unpin, filas recicladas, hover/foco/deshabilitado y conservación del indicador sin foco de ventana.
- [ ] Verificar juntas las parejas persistentes, la entrada de omnibox y la jerarquía de filas; preservar reordenamiento y todos los PASS ya reportados por el usuario.
- [ ] Evidencia real de escritorio y DeX en ventana dividida, sin afirmar ejecución que no se haya realizado. Reinicio: verificar orden/pinning sólo con la persistencia nativa disponible. Confirmar ausencia de regresiones de scroll sin modificar su motor.
- [ ] Entregar lista de archivos realmente modificados, matriz visual, resultados y límites; distinguir PASS host, PASS de dispositivo y pendientes. QEMU sigue deshabilitado.
- [ ] Tras completar la implementación y gates autorizados, preparar una única integración y build progresivo desde el último checkpoint íntegro/compatible. No clean build, purge ni borrado de outputs/checkpoints; no alterar el monitor por definir este alcance.


## Future features — Link Hover Preview (pospuesto)

Se conserva la propuesta; **fuera de la próxima tanda y sin implementación por ahora**, por decisión del usuario. [Viabilidad y alternativas](docs/validation/R4_VISUAL_LINK_HOVER_FEASIBILITY.md).

- [ ] **Preview real de enlaces tras 3000 ms de hover con mouse/trackpad:** retomar mediante un SPIKE aislado cuando se autorice; una sola preview, compositor propio, sin cambiar foco ni pestaña principal. Antes de implementar, demostrar privacidad, política de cookies/storage/historial, cancelación, lifecycle y presupuesto de CPU/RAM/GPU/red con medidas reales.
- [ ] Evaluar conjuntamente tarjeta enriquecida y snapshot como alternativas explícitas, sin sustituir automáticamente la preview real. Las miniaturas existentes tienen GO técnico limitado, pero también quedan pospuestas junto con toda la funcionalidad Hover Preview. Un destino nuevo no debe cargarse silenciosamente por un cache miss.

No se descarta la preview real ni se altera su retardo acordado. Requiere autorización futura; no añade dependencias, builds ni cambios gráficos a la tanda actual.

## Desktop final + Mobile — checkpoint de Bloque A (21-oct-2026)

Alcance nuevo autorizado: D1–D10 y M1–M11 según especificación del usuario. Prioridad A→B→C→D, sin subagentes ni nuevas dependencias; máximo un workflow integrado, sin reintentos automáticos. **0/1 workflows consumidos.** Rama aislada `assistant/archium-r5-final-mobile`; base instalada a2ad646/run39562759522 conservada.

- [x] D1 parcial: retirar overrides de UA por ancho. Contrato sin navegación/recarga y conjunto split: 140 PASS locales. **Zoom/viewport Blink 50→25→50 pendiente; D1 no cerrado.**
- [x] D2 implementación local: grid según ancho útil, mínimo dos columnas o menú; conservación de orden, objetos y datos. Colecciones Android: 20 PASS. Política de columnas con densidades fraccionales PASS. Aceptación APK pendiente.
- [x] D3 código: target invisible 16dp; sin cambiar límites ni persistencia. **Suite nativa del coordinador, habilitación manual_resize, mouse/hover/cursor/touch/stylus pendientes.**
- [x] D4 implementación local: acciones Fijar/Favorito compactas con descripción/tooltip; sin forzar ancho. Compilación SDK aislada PASS; aceptación física pendiente.
- [ ] D10: cerrar matriz completa en Galaxy/DeX; geometría Android del shell 18 PASS no equivale a validación manual.
- [ ] Bloque B D5–D9: revisar deltas y aceptación sobre base instalada, preservando primer clic y parejas.
- [ ] Bloque C M1–M5: candidato implementado parcialmente; ver continuación abajo. Aceptación nativa y refinamientos visuales pendientes.
- [ ] Bloque D M6–M11: inicio nativo implementado como candidato; adaptación, rendimiento y aceptación física pendientes.
- [ ] Build/APK nueva: NOT RUN; no se consume el intento remoto con la tanda incompleta. No hay PASS gráfico, de memoria ni rendimiento nuevo.

[Estado, límites y continuación exacta](docs/validation/R5_FINAL_MOBILE_CHECKPOINT.md). Evidencia local en `/workspace/archium-evidence/r5-final-mobile/`. Parche/preparación y pruebas adicionales: ver resultados finales del checkpoint; no usar casillas de implementación como aceptación visual.

Verificación final de este checkpoint: parche reproducible de 159 archivos y preparación SDK37.2 PASS; aplicación/transición de parche 24 PASS; proyección 17 PASS; drag 3 PASS; cobertura del orquestador 2 PASS. No se ejecutó la suite host completa ni el compilador Chromium nativo de este candidato.

## Continuación Desktop/Mobile — candidato incremental (21-oct-2026)

- [x] B: foco estructural de 2dp en controles, prioridad de foco sobre hover y encabezados accesibles en colecciones. Se conservan geometría, anchos, parejas y candidato previo de primer clic. No equivale a aceptación visual D5–D9.
- [x] C, código local: cuatro acciones inferiores con + destacado, contador, haptic e insets/teclado; omnibox nativa superior con alineación según foco sin sustituir listeners. Menú inferior con acciones Chromium, Back/exterior/deslizamiento de cabecera. Switcher nativo con sus snapshots; selector de Spaces reutiliza store y acciones existentes.
- [x] D, código local: inicio Archium dentro de la NTP nativa, branding oficial, búsqueda real, favoritos del Space, historial de esta pestaña y configuración. No inyección en webs externas. Contraste de botones según luminancia; se restauran las vistas nativas al salir.
- [x] Regresión Mobile: cambiar UI no cambia UA/recarga; adjuntar Spaces no sustituye la pestaña actual; una selección explícita de Space pendiente espera al restore. Barra inferior conserva otros cambios de margen.
- [ ] Pendientes: geometría grande/estados completos de omnibox; cabecera con favicon/seguridad y agrupación visual del menú; zoom +/- dedicado; selector visible y filtrado por Space dentro del Hub; rediseño específico de tarjetas, colores por Space y personalización. No existen datos de color por Space en el modelo actual. Resumir sin backend se omite; no se inventan métricas de bloqueador.
- [ ] Dispositivo: todos los puntos 50→25→50, drag de sidebar, dropdown estrecho, mouse/touch/stylus, insets/IME/orientación, restauración, contraseñas/passkeys, rendimiento/memoria siguen NOT RUN.

Pruebas locales: Mobile 18 PASS; colecciones 22 PASS; geometría 18 PASS; transición 12 PASS; adapter nativo 12 escenarios PASS con frontera sintética; gates 2 PASS. Parche de 162 archivos regenerado. La compilación Chromium nativa y una APK de este candidato requieren el único intento integrado autorizado. Se actualizan exclusivamente los guards del runner a esta rama; se conserva SHA exacto y checkpoint obligatorio, sin fallback limpio.

## Dispatch integrado autorizado

- Run: [39628600358](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39628600358).
- Código enviado: `1e15e84a6738a8cdd1719305d870635c6541c85b`. Rama: `assistant/archium-r5-final-mobile`.
- Intentos consumidos: **1/1**. Sin relanzamientos automáticos; QEMU desactivado.
- Origen incremental: `archium-checkpoint-39551668868-1`; integridad de bytes pendiente del gate de restauración CI.
- Estado al registrar: in_progress. APK nueva: pendiente; no instalada. Refinamientos y aceptación física pendientes según TODO.

## Fallo de preflight 39628600358 y corrección localizada

El run terminó failure antes de restaurar el checkpoint o compilar Chromium: `test_r53_test_discovery.SplitDiscoveryTest.test_every_split_gate_has_explicit_robolectric_runner` exigía anotaciones cortas con imports en `ArcSplitViewportPolicyTest.java`; el test entregado usaba nombres totalmente cualificados. CI ejecutó 384 pruebas host y reportó un fallo. No hubo APK nueva ni instalación; el checkpoint remoto original permanece disponible.

Corrección: imports explícitos de RunWith/Robolectric/Config/GraphicsMode/SQLiteMode y anotaciones cortas. Se conserva el runner, SDK30/36 y la lógica de la prueba. El gate existente no se modifica. Parche/manifest regenerados (162 archivos).

Verificación local de esta corrección: gate de discovery RED antes y GREEN después; viewport Robolectric 4 PASS; aplicación/transición de parche 24 PASS; preparación SDK37.2 PASS. Evidencia: `/workspace/archium-evidence/r5-final-mobile/continuation/`, archivos `run-39628600358-preflight.log`, `discovery-{red,green}.log`, `viewport-annotation-green.log`, `patch-fix.log`, `preparation-fix.log`. No se repite la suite completa local ni se atribuye aceptación gráfica a estos resultados.

Intentos remotos consumidos: **1/1**. Otro intento incremental requiere autorización nueva del usuario; no se despacha ni relanza automáticamente. Si se autoriza, utilizar el mismo checkpoint `archium-checkpoint-39551668868-1`/SHA35747e28fec81d80c6b97f82f366fc97809aa339/run39551668868 con el nuevo SHA corregido, y actualizar la sesión de monitor/instalador al nuevo run sin borrar evidencia anterior. QEMU desactivado; APK sólo tras gates y validación de firma/versión/dispositivo.

## Nuevo intento autorizado — 39634608887

El usuario autorizó otro único intento con «go». Run [39634608887](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39634608887), código `b51d9b0494a379a58b808d3b4fbf5b3566890fb0`, rama `assistant/archium-r5-final-mobile`. Estado al registrar: in_progress; resultado/APK pendientes. Se reutiliza `archium-checkpoint-39551668868-1`; preflight completo habilitado y QEMU desactivado. Autorización nueva: **1/1 intento consumido**, sin relanzamientos automáticos.

Monitor e instalador: sesión Termux independiente, estado `/workspace/.local/state/archium-r5-final-mobile-39634608887/`. Refresco 600s; instalación únicamente después de gates, identidad del run, checksum, firma, package/ABI, versión y dispositivo, con comprobación posterior de bytes instalados. Evidencia del fallo anterior conservada. No se declara APK ni aceptación física por lanzar este run.

## Desktop fixes + rollback Mobile — 22-oct-2026

Nueva rama `assistant/archium-r5-desktop-native-mobile`, base verificada33e79a5. No Actions en esta tarea; el build requiere autorización nueva.

- [x] P0 candidato local: sincronizar los dos WebContents al terminar el layout; RED/GREEN de callback y secuencias, sin UA/zoom/recargas. Aceptación de Blink aún abierta.
- [x] P1: mismo ArcCommandBar desde primer clic lateral/superior; preservar editor, navegación y atajos.
- [x] P2: clic derecho/long press, quitar de Space y cerrar nativo separados, tooltip y guard para filas borradas; prueba de ausencia de pins espontáneos por restore/Space.
- [x] P3: retirar ArcMobileControls/HomeView, integraciones Activity/Root UI, recursos/gates/tests huérfanos y opciones exclusivas del adapter; fuente propia sólo en Desktop. Native Activity coincide con la versión previa a Mobile.
- [ ] P4 aceptación física: viewport/escala/media queries/scroll/formulario/reloads; primer clic y atajos; quitar/cerrar/reiniciar; toolbar/NTP/teclado/insets Phone y Desktop↔Phone.
- [ ] P5: autorizar un único build incremental tras entregar auditoría local. Checkpoint39551668868-1 conserva cuatro grupos compatibles; bytes/capacidad se verifican durante restauración CI.

Evidencia y resultados exactos: [auditoría Desktop + Mobile nativo](docs/validation/R5_DESKTOP_NATIVE_MOBILE.md). Los PASS locales no cierran las casillas de dispositivo.

Gates finales de esta tanda: host389 PASS; split144 PASS; entrada omnibox26 PASS; Command Bar18 PASS; colecciones28 PASS; transiciones12 PASS; adapter12 escenarios PASS; rollback5 PASS; preparación SDK37.2 y reproducibilidad PASS. Estado del candidato: **READY FOR BUILD**, con aceptación física P4 pendiente y sin Actions lanzadas.


## Split View — seguimiento físico22-oct-2026

- [x] Run39705469954 SUCCESS e instalación verificada del SHA78b370b. Autorización1/1 consumida; ningún intento adicional.
- [ ] P0 **FAIL EN APK**: separador funcional; viewport visible cambia1058→527→1058px, pero layout/media query conserva ancho superior al panel estrecho. La sincronización Java anterior no cierra este problema.
- [x] Candidato local: política nativa de layout por WebContents de Split View, limitada a páginas donde Chromium ignora meta viewport; limpieza por pertenencia/WeakPtr y recomputación al salir. Sin UA/zoom forzado/GN/GPU.
- [x] Pruebas interpretadas:5 PASS del validador/contratos fuente y5 PASS de invariantes de Mobile nativo. RED de traza física conservado. No son ejecución C++ ni aceptación de Blink.
- [ ] Compilar/probar C++ y verificar el candidato físicamente. **NO COMPILAR TODAVÍA**, instrucción vigente del usuario; no solicitar ni disparar Actions en esta tanda.

Punto exacto de continuación, evidencia y limitaciones: [R5_SPLIT_LAYOUT_VIEWPORT_FOLLOWUP.md](docs/validation/R5_SPLIT_LAYOUT_VIEWPORT_FOLLOWUP.md).


## Mobile — navegación y menú aprobados, 22-oct-2026

- [x] Implementación local: reemplazar el contenido de la barra inferior nativa por cuatro acciones; conservar omnibar y título superiores. Un solo slot y una sola vista compartida con Hub.
- [x] Menú nativo bottom sheet sin editor inferior; acciones reales Chromium, zoom, pin, descargas y acceso al menú completo. Superficies suaves sin contornos gruesos.
- [x] Robolectric30 PASS, ownership4 PASS, gates2 PASS, legacy5 PASS, split5 PASS y preparación aislada SDK37.2 PASS. Alcance y fronteras simuladas documentados.
- [ ] Compilación completa Java/C++ y aceptación física Mobile/desktop/transiciones: NOT RUN. El candidato Split View anterior permanece pendiente de aceptación Blink/dispositivo.
- [ ] APK y Actions: NO LANZADOS; se mantiene «no compiles todavía». No eliminar checkpoints ni hacer clean.

Checkpoint y continuación: [R5_MOBILE_APPROVED_REDESIGN.md](docs/validation/R5_MOBILE_APPROVED_REDESIGN.md). Esta aprobación reemplaza únicamente la decisión anterior sobre presentación inferior móvil; los overlays Mobile antiguos siguen eliminados.


## Fallo39721663072 — corrección de integración Java

- [x] Diagnóstico: preflight/restauración y host398 PASS; falla compilación Java por TYPE_USE Nullable mal ubicado en el tipo anidado ArcPhoneNavigation.Host.
- [x] Corrección de una línea en ToolbarManager y nueva prueba compilada RED/GREEN de la declaración real; ownership5 PASS.
- [ ] Compilación nativa/APK del fix: pendiente de autorización para otro único intento. No se relanzó Actions; APK anterior intacta.
- Checkpoint publicado39721663072-1, SHA82b37ed; pack verificado por CI, futura restauración requiere gates de integridad/compatibilidad. Receipt BUILD_FAILED/recoverable=false, sin continuación automática.

Evidencia y alcance: [checkpoint Mobile](docs/validation/R5_MOBILE_APPROVED_REDESIGN.md#run39721663072--fallo-java-y-corrección-localizada).


## Fallo39729088298 — corrección de buffer C++

- [x] Java integrado supera el defecto Nullable anterior; host399 PASS. Primer fallo posterior: Clang rechaza ids[i] sobre arreglo C en StaticTabSceneLayer.
- [x] Sustituido por std::array, sin cambios de algoritmo ni supresiones. Clang local RED/GREEN con unsafe-buffer-usage/Werror y ensayo de pertenencia/swap/detach PASS (fronteras simuladas). Split5 y Mobile ownership5 PASS.
- [ ] APK/build integrado del cambio: pendiente de autorización nueva. No se relanzó Actions ni se instaló nada.
- Checkpoint publicado39729088298-1, fuente7c4ece8; gates de integridad/compatibilidad obligatorios antes de una futura restauración.

Detalle y evidencia: [registro del fallo C++](docs/validation/R5_MOBILE_APPROVED_REDESIGN.md#run39729088298--corrección-de-buffer-nativo).


## Floating Mobile aprobado + auditoría Light/Dark — 22-oct-2026

- [x] PNG de Pictures inspeccionados y hasheados; segunda imagen blanca como referencia principal. Mantener ancho/alto actuales de omnibar, según instrucción posterior.
- [x] Candidato local: superficie de omnibar nativa y status bar; una cápsula inferior en el slot existente, reserva/insets nativos, cuatro acciones y azul activo adaptado al tema. Sin modificar Desktop/engine/páginas.
- [x] Auditoría local: sincronizar tint/fondo de incógnito y contexto DayNight, recolorear sheet abierto conservando scroll, fondo inicial oscuro, estado de zoom deshabilitado, contraste al presionar y contraste de iconos de status bar conservado por el owner al actualizar insets/delegate. Sin cambios de geometría durante esta auditoría.
- [x] Pruebas locales y evidencia RED/GREEN documentadas. No equivalen a aceptación gráfica de dispositivo.
- [ ] Compilación integrada de componentes nativos y APK del candidato: NOT RUN; sin Actions ni checkpoints pesados.
- [ ] Matriz visual real completa: PENDIENTE en claro/oscuro (status, omnibar, pill, menús, Hub, IME/foco, fullscreen, insets, seguir sistema, reinicio y transiciones Desktop↔Phone). No declarar READY FOR BUILD todavía.

Checkpoint recuperable y diferencias respecto al render: [R5_FLOATING_MOBILE_LIGHT_DARK.md](docs/validation/R5_FLOATING_MOBILE_LIGHT_DARK.md). Base instalada92c24df/run39781720300; ese éxito no valida los cambios nuevos.


## Run39817793524 — fallo de compilación corregido localmente

- [x] Identificado primer error causal: override `ToolbarPhone.shouldDrawHairline()` duplicado por Floating. No fue un timeout; fallo11:26 CDMX y checkpoint/publicación hasta~11:50.
- [x] Unificado en el método nativo existente, sin cambiar dimensiones ni filtros originales. Nueva prueba javac/Java RED/GREEN; superficie4, aplicación7 y transición17 PASS.
- [x] Patch/manifest regenerados de forma reproducible; único código de producción distinto de a3841bc: ToolbarPhone.
- [ ] Build integrado del fix y APK: pendientes. Sin relanzar Actions. La APK anterior permanece instalada y respaldada.
- [ ] Validar íntegramente checkpoint39817793524-1 antes de una restauración futura; su publicación no equivale a verificar aquí todos sus bytes.

Preferencia de horas: Ciudad de México (`America/Mexico_City`, UTC−6). Detalle: [auditoría Floating y fallo del run](docs/validation/R5_FLOATING_MOBILE_LIGHT_DARK.md#run39817793524--fallo-y-corrección-localizada).


## Run39829306775 — incompatibilidad de tests corregida localmente

- [x] Causa raíz: descubrimiento Robolectric de Chromium rechaza tres shadows de clases propias en ArcPhoneNavigationTest; el runner local previo no aplicaba esa política.
- [x] Sin ampliar excepciones: retirar shadows, inyectar únicamente fronteras de recursos/flags por constructor de pruebas y conservar28 tests. Constructor normal conserva helpers nativos.
- [x] Reproducción RED con TestListComputer/Allowlist originales fijados; GREEN en política y56 ejecuciones locales. Guard del preflight2, superficie4, aplicación7 y transición17 PASS. Parche reproducible.
- [ ] Gate integrado y APK del fix: NOT RUN. No relanzar sin autorización nueva. Desktop, geometría, motor y respaldo conservados.
- [ ] Verificar todos los bytes del checkpoint39829306775-1 antes de usarlo en un próximo build incremental.

Evidencia y límites: [run39829306775](docs/validation/R5_FLOATING_MOBILE_LIGHT_DARK.md#run39829306775--rechazo-de-shadows-y-corrección-de-la-validación). Horas CDMX.


## Floating V2 aprobado — 22-oct-2026 CDMX

- [x] Implementación candidata: contenido bajo controles mediante opt-in móvil; fondos nativos transparentes y cristal con muestreo limitado de SurfaceView, conservando el tamaño actual de omnibar y el único slot inferior existente.
- [x] Cuatro acciones y menú reales conservados; Desktop/Spaces/Split específicos sin cambios. Pestañas/URL/foco/modo/lifecycle gestionan buffers y restauración.
- [x] Gates locales: 70 ejecuciones Robolectric, política Chromium35 métodos, host phone8, ownership5, coverage2, status1, patch7+17, preparación SDK y regeneración reproducible PASS. Alcances y evidencia en el checkpoint V2.
- [ ] Compilación nativa integrada y APK V2: NOT RUN. Sin nuevo Actions ni checkpoints pesados.
- [ ] Aceptación con los renders en dispositivo: PENDIENTE, ambos temas, scroll/blur, insets, teclado, menús, fullscreen y transición Desktop↔Phone. No declarar coincidencia visual por estas pruebas locales.

Checkpoint vigente: [R5_FLOATING_V2.md](docs/validation/R5_FLOATING_V2.md). Sustituye la referencia anterior de barras con bandejas opacas. Muestreo limitado y fallback sin blur documentados; falta medir rendimiento real.


## Auditoría Floating V2 Light/Dark automática — 22-oct-2026 CDMX

- [x] Revisado seguimiento del tema nativo: actualización de configuración aun sin rotación y observers color/tint. Sin cambiar preferencias de tema, diseño ni producción.
- [x] 76 ejecuciones Robolectric y política Chromium38 métodos PASS; contraste de pill presionada/seleccionada, cristal y menú abierto durante claro↔oscuro. Host phone9 y status owner1 PASS; parche reproducible, aplicación7 y transición17 PASS.
- [ ] Prueba física de seguir sistema, legibilidad status/omnibar sobre páginas opuestas, sugerencias, Hub, teclado, cambios dinámicos y persistencia al reiniciar: PENDIENTE. No se compiló una APK nueva.

Matriz y límites: [auditoría en R5_FLOATING_V2.md](docs/validation/R5_FLOATING_V2.md#auditoría-automática-lightdark--22-oct-2026-cdmx).

## Corrección Floating tras fallo físico — 22-oct-2026 CDMX

- [x] Run39898129497 compiló e instaló; aceptación visual FAIL confirmado con capturas del usuario y propias. Actualiza los NOT RUN históricos anteriores.
- [x] Causa concreta: alturas overlay cero se interpretaban como controles totalmente ocultos; la vista superior invisible impedía el muestreo. Corregidos ratios y retiradas texturas duplicadas sólo durante overlay.
- [x] Top edge-to-edge reversible en owner nativo, márgenes legacy por inset/cutout sin redimensionar omnibar, restauración y diagnóstico acotado de copia/dibujo.
- [x] RED/GREEN y gates locales documentados en R5_FLOATING_V2.md. No equivalen a aceptación de APK.
- [x] Limpieza autorizada: checkpoint39729088298-1 eliminado completo; 26.530.254.497 bytes liberados. Preservados fuente39829306775-1, fallback39817793524-1, APKs y respaldos.
- [ ] Único build incremental del candidato, monitor Termux CDMX e instalación verificada: seguir recibo/estado nuevo en `.local/state/archium-r5-floating-runtime-*`.
- [ ] Aceptación visual real del candidato en ambos temas y regresiones: PENDIENTE; no declarar DONE.

## Run39907023931 — preflight y corrección del probe

- [x] Causa identificada y reproducida: SuppressionProbe no declaraba `mArcPhoneOverlayActive`; único error entre413 tests remotos. Sin restauración, compilación Chromium ni APK nueva.
- [x] Actualizado sólo el test: cuatro flags y16 combinaciones; stderr de javac visible. RED/GREEN y mutante sin condición móvil rechazado PASS; producción intacta.
- [ ] Validación integrada y APK del fix: PENDIENTE; requiere autorización nueva. No se relanzó Actions. Ver R5_FLOATING_V2.md.
- [x] Revisión host completa tras el fix: 411 PASS;2 pruebas de recursos fallaron con AAPT2 Debian/SDK37.2 y ambas pasaron al repetir con AAPT2 SDK37.0, sin cambiar tests. No declarar PASS de la primera invocación completa. Patch de producción idéntico; detalles y logs en el checkpoint.

## Floating: fuente de blur e insets reales — 23-oct-2026 CDMX

- [x] Run39926747580 instalado, diseño físico FAIL documentado con patrón propio claro/oscuro: transparencia funciona, blur falla; fuente SurfaceView sin buffers según HWUI.
- [x] Candidato: readback acotado por API Chromium existente, sin PixelCopy ni cambiar GPU; owner raíz móvil de insets corregido, Desktop y tamaño de omnibar conservados.
- [x] Regresión RED/GREEN del owner real y ciclo de captura;80 ejecuciones Robolectric/política original40 métodos, preparación SDK y aplicación/transición24 PASS; patch178 archivos reproducible. Alcances en R5_FLOATING_V2.md.
- [x] Suite host416:410 PASS y6 fallos de ruta SDK local, los seis repetidos sin cambios de tests y PASS con SDK37.0 existente; primera invocación no PASS. Logs y límites registrados.
- [ ] Único build incremental autorizado, monitor Termux CDMX600s e instalación verificada; no relanzamientos.
- [ ] Aceptación gráfica de la nueva APK frente a renders y regresiones reales: PENDIENTE.


## Cristal y menús posteriores a 76e7934 — 23-oct-2026 CDMX

- [x] Evidencia propia: readback funciona; sombra legacy fuera de cápsula, blur insuficiente y fondos nativos opacos demostrados/documentados.
- [x] Candidato local: blur/tinte, borde discreto claro/oscuro inferior, sombra ajustada, edición con pill flotante, cristal compartido en menú inferior, Más opciones/submenús, Configuración del sitio y menú de enlaces/imágenes; restauración de capas nativas y lifecycle.
- [x] Progreso nativo presentado en el perímetro con color temático; área segura superior propagada sin tocar sitios/engine ni tamaño de omnibar.
- [x] Robolectric92/política46, host phone23, ownership5, preparación SDK y parche25 PASS; marcador de ausencia de newline corregido con RED/GREEN. Alcance sintético/nativo parcial documentado.
- [x] Checkpoints inventariados: sólo fuente39829306775-1 y fallback39817793524-1, conservados completos; no redundantes seguros,0 bytes eliminados. Hashes de partes/capacidad pendientes del gate CI.
- [x] Suite host completa final424 PASS.
- [x] Único build autorizado lanzado: run39982605276, código052c55ab39e97ea267d0eb0f5a3eecc77484e70a; authorize/preflight PASS, restauración incremental en curso al registrar.
- [x] Monitor nativo Termux /dev/pts/2, PID18267/worker18481, CDMX600s, sin reintentos.
- [ ] APK nueva e instalación: PENDING_BUILD; sólo actualizar si todos los gates de identidad/firma/hash/version/ABI pasan.
- [x] Limpieza posterior al monitor: 73 entradas, cuatro worktrees y dos clones obsoletos; espacio libre observado +26.053.664.768 bytes (76.052.656.128 libres). Historial/local changes recuperados, JARs compartidos preservados y respaldo APK verificado. Fuente activa/Git común, datos Android, credenciales y referencias visuales conservados.
- [ ] Aceptación visual real del candidato y todos sus menús, ambos temas, teclado, insets, carga y Desktop↔Phone: PENDIENTE; no declarar DONE.


## Desktop liquid lechoso + corrección móvil — 23-oct-2026 CDMX

- [x] Extensión Desktop autorizada: marco interior/rail/pestañas, omnibox nativa, Command Bar y sugerencias, decorador de AppMenu/PageInfo/ContextMenu; paleta del Space conservada, sin cambiar geometría ni Split View. Barra exterior DeX nativa.
- [x] Captura de paneles recortada al contenido realmente visible, destino proporcional y fallback lechoso legible. Pill exterior transparente en NTP sin activar captura web.
- [x] Android local:122 pruebas sampler/navegación/Command Bar,8 drawables nativos,18 foco Tablet y12 transiciones PASS. Contraste probado en4.096 colores y páginas opuestas. No equivale a aceptación de APK.
- [ ] Flecha/título anterior junto a status bar: pendiente de reproducción/evidencia; no se afirma corregido.
- [ ] Validación física del nuevo candidato en Claro/Oscuro, menús, NTP, teclado, fullscreen y Desktop↔Phone; PopupMenu del framework/diálogos de Ajustes conservan presentación nativa.
- [ ] Nuevo build/instalación: NO LANZADOS. Requiere nueva autorización de compilación.

Detalle: `docs/validation/R5_DESKTOP_MILKY.md`. Se conserva el trabajo móvil en curso y no se volvió a controlar el teléfono después de liberarlo.

Verificación del checkpoint Desktop: suite host424 PASS; política Chromium61 métodos PASS; preparación SDK37.2/JDK21 PASS con fronteras declaradas; parche/manifest187 archivos reproducibles y transición sparse desde198fe8a PASS (153 timestamps conservados). Evidencia y límites en `docs/validation/R5_DESKTOP_MILKY.md`.


## Revisión instalada1298b31 — 23-oct-2026 CDMX

- [x] Run40004797899/APK1298b31 instalados; hash de bytes instalado confirmado por ADB.
- [x] Blur móvil observado sobre prueba de colores. El usuario decide conservarlo como está: no modificar su material.
- [x] Desktop Command Bar/sugerencias: capturas y dibujo observados; no confundir con aceptación de toda la interfaz.
- [ ] Marco/sidebar Desktop: efecto liquid esperado no conseguido. Relleno opaco sin fuente de captura y brillo casi imperceptible; causa y muestras documentadas en `docs/validation/R5_DESKTOP_MILKY.md`.
- [x] Diagnóstico temporal retirado, pestañas originales preservadas; teléfono y DeX liberados. Sin cambios de producción ni nueva compilación en esta revisión.


## Desktop: relieve visible y ajuste guardado — 23-oct-2026 CDMX

- [x] Fix de fondos Desktop casi planos: material de tres tonos, paleta del Space, coordenadas alineadas, contraste AA y clip original. No se presenta como blur del escritorio (el dispositivo informa soporte entre ventanas desactivado/no soportado).
- [x] Apariencia → intensidad Desktop0–100, vista previa local, Aceptar/Cancelar/Restablecer y persistencia. Selector de color y atajo de posición preservados.
- [x]134 ejecuciones Android PASS; política Chromium67 métodos;8 drawables/foco nativos y12 transiciones PASS. Host específico25 parche+8 recursos+2 cobertura PASS; SDK aislado y reproducibilidad/transición comprobados. Fronteras y límites en `docs/validation/R5_DESKTOP_MILKY.md`.
- [x] Producción móvil preservada como aprobó el usuario; sin cambios de motor, GPU, dependencias, layout ni Split View.
- [ ] Único build incremental autorizado: registrar SHA y run en estado `archium-r5-material-control`.
- [ ] Validación física Claro/Oscuro y del nuevo control tras instalar: PENDIENTE.

## Mobile UI polish — status fade e insets, 23-oct-2026 CDMX

- [x] Rama/base verificadas: assistant/archium-r5-desktop-native-mobile, a4d9bf7; se conserva Desktop preparado y UI móvil aceptada. Referencia física más reciente150306 inspeccionada.
- [x] Fade nativo visual detrás de indicadores, ligado al inset real; no toca píldoras, sombras, fondo web, viewport ni input. Paleta Chromium/tema nativo y fallback con histéresis; no captura adicional.
- [x] Contraste conservado al enfocar editor y tras refresh de delegates; sin escritura opaca/transparente doble, sin scrim de plataforma superpuesto; retiro en pause/fullscreen/Desktop/destroy.
- [x] 153 ejecuciones Robolectric PASS, SDK29/30/36 según caso; política original76 métodos PASS. RED/GREEN de overlay ausente, backing en foco y scrim duplicado; preparación SDK37.2/JDK21 PASS. No equivalen a aceptación gráfica.
- [x] Baseline físico: primer toque/teclado/sugerencias y Back observados; se recuperó la pestaña sin navegar y se devolvió Termux al usuario. Contraste en foco falla en la APK anterior; candidato nuevo pendiente de instalar. Flecha/dirección tenue pendiente, no declarada corregida.
- [x] Host426:425 PASS/1 contrato estático obsoleto FAIL; suite afectada actualizada y repetida6 PASS; probes nuevos4 PASS. Recibos finales y parche192 reproducible/transición151 timestamps PASS; no presentar primera suite como verde.
- [ ] Único dispatch incremental autorizado tras commit; fuente39829306775-1 conservada, sin clean/reintentos. Estado nuevo archium-r5-mobile-status-polish; build/APK pendientes, aceptación física pendiente.
- [ ] Validación física del candidato: fade e indicadores claro/oscuro, cambio automático, teclados, YouTube/HTML5 fullscreen/orientación/resume, gestos, Desktop↔Phone. Ver docs/validation/R5_MOBILE_STATUS_POLISH.md.


## Fixes de revisiones móvil y DeX — 23-oct-2026 CDMX

- [x] Candidato sobre cd84ed4: fijar en carpeta abierta (incluida conversión desde favorito), títulos/contraste de fijadas en rail expandido, detach antes de callbacks de teardown del tab strip y solicitud de escritura inmediata de metadata mediante PrefService nativo.
- [x] Compactación móvil aprobada: scroll/foco nativos, un control Archium de la misma pill, restauración, movimiento lateral y salida manual para páginas sin scroll; sin reglas por sitio ni cambios de tamaño/material de la omnibar expandida.
- [x] Guard de textura de toolbar frente a releases de owners nativos; inset estable al salir de fullscreen; lookup de decorador por ventana real para menús con ContentView no-Activity.
- [x] RED/GREEN de lógica y Android local; suites y límites en docs/validation/R5_REVIEW_FIXES.md. No equivalen a aceptación física.
- [ ] Compilación Chromium/JUnit integrados y APK del candidato: NO LANZADOS. No se borraron checkpoints ni se hizo clean.
- [ ] Aceptación física en móvil/DeX, temas, subcarpetas tras reinicio, controles de webs arbitrarias, teclado/foco, fullscreen y menús: PENDIENTE. No declarar DONE ni paridad de rendimiento/seguridad.

### Preflight recovery — 23-oct-2026 CDMX

- [x] Run40046612155/f6a998a: authorize PASS, preflight FAIL; restore/build skipped, NO_APK. First causal error: missing extracted updateArcToolbarSceneGuard dependency in the host Java probe.
- [x] Probe repaired with the real guard body,16 state combinations and native-owner release assertions; local RED/GREEN retained. Related adaptive/scene ownership tests2 PASS. Production patch unchanged.
- [ ] New single incremental attempt explicitly authorized by user; dispatch only after available local checks. Candidate APK/device validation remains pending.

### Java TYPE_USE fix — run40049206996

- [x] Remote preflight PASS and checkpoint restoration VERIFIED_BY_CI; native Java compilation FAIL at ToolbarManager438, invalid placement of @Nullable on a fully qualified ValueAnimator type. NO_APK / no installation.
- [x] Localized declaration fix with SDK-based RED/GREEN; adaptive2 and scene/suppression1 PASS. Patch regenerated and reproducibility checked. Previous candidate's full local434-test suite finished PASS; not claimed as a full rerun after this fix.
- [ ] New integrated native build requires fresh user authorization; no automatic retry. Published checkpoint40049206996-1 remains unverified locally. Device/UI acceptance pending.

## R5 input access / menu readability — 24-oct-2026 UTC

- [x] Recovered deleted repository/pinned sources with matching manifest hashes; preserved installed baseline b62ece7 and hidden evidence/backups. Current branch unchanged.
- [x] Candidate code: phone content safe regions with owned/restored margins, compact-width reattachment, NTP duplicate-bottom scene suppression, popup partial-frame backing, Desktop caption top clearance and readable idle tile labels. Expanded pills/material, sidebar widths, Split ratios and Spaces model preserved.
- [x] Local RED/GREEN:165 Android executions (82 original shadow-policy methods),3 host geometry/contrast and2 adaptive probes; isolated SDK37.2 compilation PASS;197-file patch application/delta and identical regeneration PASS,187 unchanged timestamps preserved. Not graphical/device acceptance.
- [x] Complete local suite438:437 PASS/1 obsolete NTP static contract FAIL; corrected assertion plus native-page matrix and final affected suites17 PASS. Full-suite run is not presented as green.
- [x] One incremental build dispatched: run40068726423, exact candidate63ea9314483288a729f226460c3d43256b7e8ef3; authorize/preflight PASS, checkpoint download/build pending. Native Termux monitor + verified installer open on /dev/pts/1, CDMX/600s; no additional dispatch. Details and honest pending device cases: [R5_INPUT_ACCESS_FIXES.md](docs/validation/R5_INPUT_ACCESS_FIXES.md).
- [ ] Small-window Spaces access, narrow Split top-search root cause and broad physical regressions remain pending. Old inspection screenshots were accidentally deleted; do not claim retained visual evidence.
- [x] After run/monitor launch: MacDesk hidden-root startup and Panel/Docklike readiness PASS; GNOME Nautilus is default, actual native X11 folder open/close PASS; related9 tests PASS. Physical DeX appearance pending (disconnected). Separate MacDesk commitca67e88.

## Phone full-window regression — 24-oct-2026

- [x] Visual acceptance of installed63ea931: FAIL. Own capture/dump proves added margins reduce the page to [0,86][904,1766] while compact, exposing a200px solid bottom region.
- [x] Candidate removes the phone compositor-margin owner; restores full-window overlay policy. Adds native phone-only DOWN passthrough outside the translated/visible capsule; preserves native find, editing, gesture sequence and Desktop routing.
- [x] Status diffused surface reuses bounded web sampler, sample-only material, noninteractive Drawable fade and native contrast/theme owner; approved pill dimensions/material retained.
- [x] Local440 host PASS, final5 input/adaptive PASS,167 Android executions PASS, genuine SDK37.2 input API check/preparation PASS,198-file reproducible patch and187 unchanged timestamps verified. Not physical acceptance.
- [ ] System clock-region web touches: InputDispatcher delivers them to Android StatusBar. User was asked to choose temporary hiding while compact versus only system-height safe region. No visibility change or claim of web click-through here.
- [ ] One incremental build authorized, not dispatched yet; physical candidate acceptance pending. See [R5_FULL_WINDOW_INPUT_REGRESSION.md](docs/validation/R5_FULL_WINDOW_INPUT_REGRESSION.md).
