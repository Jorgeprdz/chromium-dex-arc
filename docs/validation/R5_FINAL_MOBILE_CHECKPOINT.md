# R5 Desktop final + Mobile — checkpoint acotado

Base: a2ad646f4dabd96a1ba82dc246b8184a708d32b4, instalada por run 39562759522.
Rama: assistant/archium-r5-final-mobile, worktree /workspace/Archium-R5-final-mobile.
Chromium: cfd94726b7b5fb48aedcc32662f2f3fbdbadec35, sin cambios de motor, GN, toolchain, dependencias ni branding.

## Bloque A: implementación y límites

- D1: retirado el override transitorio de User-Agent de ArcSplitViewportPolicy. El hook se conserva sin efectos para no romper sus consumidores/gates. El tamaño físico continúa por CompositorViewHolder.updateWebContentsSize → WebContents.setSize y los ContentViews de cada panel. No se fuerza page scale, UA ni recarga; no se modifican ratios, identidad o selección de parejas. RED/GREEN del contrato UA y 140 pruebas del conjunto split pasan. **Esto no demuestra resuelto el zoom residual del renderer. D1 continúa abierto hasta evidencia 50→25→50 real.**
- D2: mosaicos GridLayout con slots de 64dp + márgenes de 4dp por lado; columnas según ancho útil. Nunca una columna: bajo dos slots, botón con menú de todos los favoritos en orden almacenado. Scroll sólo vertical para poblaciones grandes. Resize conserva las instancias de mosaicos/favicons y los datos. Se invalidan restricciones de columnas antes de reducirlas. El shell mantiene accesibles favoritos también en rail compacto, sin mostrar allí toda la UI de colecciones.
- D3: target invisible de 16dp en VerticalTabsSideUiCoordinator.getResizeHandleWidthPx, conservando límites, arrastre y persistencia nativos. Test upstream actualizado pero **suite nativa de este coordinador NOT RUN**. Cursor, hover, feedback y posibles interferencias requieren revisar el handler nativo y probar mouse/touch/stylus. `manual_resize` conserva su configuración previa; su default upstream es false. No afirmar que el agarre esté activo en toda configuración.
- D4: Fijar/Añadir favorito pasan a iconos con descripción y tooltip cuando sus mitades no admiten texto; la anchura elegida no cambia. El menú de favoritos compacto usa icono y descripción accesible.
- D10: matriz de vistas Android verificada para ancho amplio, dos columnas, menú y vuelta al ancho inicial, conservando objetos y almacenamiento. Menú abre todos los elementos en orden. **DeX/Galaxy reales y arrastre continuo NOT RUN. D10 no cerrado.**

## Pruebas

Evidencia privada: /workspace/archium-evidence/r5-final-mobile/.

- split.log: 140 PASS, Robolectric SDK30/36; adapters de Tab/WebContents/JNI explícitos, no aceptación de Blink/Viz.
- collections.log: 20 PASS, vistas/estado completos con R sintético y NativeTabs mock. Reflow, menú, identidad, foco y presupuestos. No prueba composición web.
- geometry.log: 18 PASS, vistas/drawables y expresiones reales del shell.
- grid-green.log: política real compilada; slots de distintas densidades, incluida fraccional, sin overflow ni columna única.
- projection.log: 17 regresiones PASS; drag.log: 3 PASS; gate-coverage.log: 2 PASS.
- patch.log: 24 PASS. preparation.log: parche de 159 archivos reproducible y compilación API SDK37.2 aislada PASS.
- Suite host completa, compilación nativa Chromium, APK nueva, rendimiento, memoria y pruebas físicas: NOT RUN.

El primer intento local con JDK17 no compiló jars Android para Java21; no se cuenta como RED del producto. Se usó el JDK21 ya instalado, sin descargas ni cambios al toolchain de producción. Dos expectativas anteriores del controlador que exigían cambiar UA fueron sustituidas por el contrato aprobado: resize no modifica el modo de sitio ni recarga. Se conservó RunWith/Config para descubrimiento nativo.

## Continuación implementada sobre 239750c

Desktop: foco de 2dp, prioridad de foco sobre hover en colecciones y encabezados accesibles. Se conserva el primer clic, las proporciones/selección de Split View y las dimensiones elegidas. El pulido visual completo D5–D9 sigue sujeto a aceptación.

Mobile: ArcMobileControls conserva la omnibox superior nativa y observa su foco sin sustituir listeners. Añade cuatro acciones inferiores, + con contraste por luminancia, contador real, haptic, visibilidad según modo/fullscreen/IME e insets. La reserva inferior se libera conservando cambios de margen ajenos. Su controlador persiste al cambiar de tamaño de ventana.

El menú inferior usa Dialog nativo, cierre Back/exterior y swipe de cabecera; sólo despacha acciones reales Chromium (información del sitio, buscar, compartir, traducir, sitio desktop, zoom cuando existe el ID, menú completo), fijar y Spaces reales. No hay IA falsa ni métricas de bloqueo. La cabecera de seguridad/favicon, agrupación premium y controles zoom +/- quedan pendientes.

Las pestañas abren el Hub/switcher nativo con sus snapshots, sin duplicar bitmaps. Spaces usa ArcNativeTabSession y el store existente, accesible en menú y long press del contador. Se conserva la pestaña seleccionada al adjuntar/restaurar Mobile; una selección explícita pendiente se aplica al terminar restore. Selector dentro del Hub, filtrado visual del switcher y tarjetas específicas pendientes.

ArcMobileHomeView se inserta exclusivamente dentro del FrameLayout de la NTP regular. Se ocultan/restauran sus hijos conservando cambios posteriores de Chromium; no existe overlay sobre webs ni inyección. Usa icono oficial, Space actual, búsqueda nativa, favoritos reales, cinco entradas HTTP(S) del historial de esta pestaña y configuración. Historial nulo se tolera. Otros contenedores o perfil no disponible conservan la NTP Chromium. Colores individuales por Space y personalización propia pendientes; el modelo actual no guarda colores por Space.

## Evidencia adicional

Directorio: /workspace/archium-evidence/r5-final-mobile/continuation/.
- mobile.log: 18 PASS, SDK30/36; callbacks del Host son frontera sintética, no prueba de integración Activity/Blink.
- collections.log: 22 PASS, incluida prioridad de foco sobre hover.
- geometry.log: 18 PASS; transitions.log: 12 PASS (rail no split; split cubierto por su suite previa).
- native-session.log: 12 escenarios PASS del adapter real con contratos nativos sintéticos; incluye selección conservada y petición explícita durante restore.
- gate.log: 2 PASS; patch.log: 24 PASS. Preparación SDK37.2 PASS (162 archivos); routing y guards del runner PASS (ver routing.log y dispatch.log).
- Las firmas NavigationController/NavigationHistory/NavigationEntry y el contenedor FrameLayout de FeedSurfaceCoordinator se contrastaron con el pin exacto. Esto no sustituye el compilador nativo.

## Build y continuación exacta

Único intento integrado autorizado; utilizar checkpoint archium-checkpoint-39551668868-1, SHA35747e28fec81d80c6b97f82f366fc97809aa339, run39551668868. El run exitoso39562759522 conserva APK/receipt pero no publicó checkpoint nuevo. Se comprobaron cuatro grupos no expirados del checkpoint anterior; integridad de bytes se verifica durante restauración en CI. Sin clean fallback, cambios de GN/toolchain/dependencias ni QEMU.

El runner queda restringido a assistant/archium-r5-final-mobile y SHA exacto; no se modifica el monitor histórico de la APK instalada. Registrar ID/SHA/URL del único dispatch tras lanzarlo. No repetir automáticamente si falla: primer error causal, fix localizado y nueva autorización para otro run.

Pendientes físicos: viewport/zoom 50→25→50; favoritos durante drag, target de sidebar y menú estrecho; primer clic omnibox, navegación, diálogos, teclado/IME/gestos y adaptación; seguridad Chromium, memoria y rendimiento. Todos NOT RUN en este candidato. No instalar/publicar APK sin sus verificaciones. Tras el build, completar los pendientes visuales del TODO y actualizar esta evidencia sin declarar aceptación por inspección.

## Dispatch integrado autorizado

- Run: [39628600358](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39628600358).
- Código enviado: `1e15e84a6738a8cdd1719305d870635c6541c85b`. Rama: `assistant/archium-r5-final-mobile`.
- Intentos consumidos: **1/1**. Sin relanzamientos automáticos; QEMU desactivado.
- Origen incremental: `archium-checkpoint-39551668868-1`; integridad de bytes pendiente del gate de restauración CI.
- Estado al registrar: in_progress. APK nueva: pendiente; no instalada. Refinamientos y aceptación física pendientes según TODO.
