# Archium — revisión de paridad visual R2, 2026-10-09

Repositorio verificado: `Jorgeprdz/chromium-dex-arc`; rama `feat/arc-media-only`; base de esta corrección `bacd31c8286c677f24e55e3a46b12d9161664abc`; Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`. Se conserva el mismo worktree, `ARCHIUM_BUILD_SCOPE=arc-media`, passwords locales deshabilitados y archivos previos sin relación. El usuario autorizó expresamente commit, siguiente run e instalación verificada al terminar. No se realiza merge. LinkedIn queda excluido.

## Comparativa comprobable

El build instalado, run37936080454, ya tiene navegación real, omnibox lateral, resize manual, gradiente configurable, espacios, pestañas nativas, footer y viewport redondeado. Esta revisión conserva esos avances. Las imágenes nombradas `92061.jpg` y `91725.webp` no están disponibles en el entorno: los valores de Arc proceden de las medidas suministradas por el usuario. La evidencia propia procede de capturas y grabación del APK instalado en DeX, no de un montaje del APK nuevo.

| Aspecto | Arc, referencia del usuario | APK instalado antes de R2 | Implementación R2 y límite de evidencia |
|---|---|---|---|
| Sidebar | Aproximadamente24.17%; ancho adaptable | Ancho321px elegido manualmente en captura | Se mantiene el ancho manual y su persistencia. El cálculo proporcional solo corresponde al estado sin resize manual. |
| Navegación | Región integrada y controles discretos | Back/Forward/Reload funcionan; fondos permanentes fragmentan header | Se conserva el controlador y se añaden superficies transparentes en reposo, hover/pressed/focus y tinta disabled. Visual posterior pendiente. |
| Omnibox | Campo protagonista | LocationBar nativo; foco puede desbordar cabecera | Misma UrlBar, texto14sp y clipping acotado al ScrollView lateral; dropdown independiente conserva anclaje. |
| Pestaña activa | Cápsula iluminada | Selección gris con protagonismo moderado | Selección clara según tema, texto legible, radio proporcional; multiselección mantiene su apariencia nativa diferenciada. |
| Favoritos | Mosaicos reales con favicon | Placeholder de ojo cuando no llega bitmap | FaviconUtils nativo usa bitmap, fallback de dominio/color o globo genérico. Sin tintar logos. |
| Espacio | Encabezado interactivo discreto | Personal sobre bloque sólido | Personal semibold14sp, acción conservada, superficie de interacción sin bloque sólido en reposo. |
| Material | Profundidad y gradiente | Gris-lavanda suave | Gradiente nativo afinado; color guardado y variante cálida existentes conservados. Sin blur ni overlays nuevos. |
| Página | Panel redondeado y sin toolbar duplicado | Banda blanca29px bajo caption; márgenes azules del sitio | Supresión ARC en supplier del toolbar gráfico; reservas reales de caption siguen en stacker. El CSS y los márgenes del sitio no se alteran. |
| Cierre sidebar | Contenido acompaña cierre | En91frames el borde permanece318–322px y salta a52px al final | Nueva transición comparte duración/interpolación nativas y actualiza borde, compositor e input en posiciones intermedias. Fluidez real posterior pendiente. |

## Diagnóstico y correcciones

La banda clara es chrome interno residual: `ToolbarTablet` estaba GONE, pero `TopToolbarSceneLayer` dibujaba su recurso mediante un supplier distinto. ARC añade un motivo independiente de supresión al `ToolbarManager`, compuesto con XR y condiciones nativas de ancho estrecho. No se quitan el caption de Android ni las reservas contractuales de `TopControlsStacker`.

La superposición de cabecera se reproduce con el foco nativo: el ScrollView visible mide243px y sus hijos464px. `LocationBarTablet` desactivaba el clipping de todos sus ancestros al expandir Fusebox. R2 limita ese cambio al interior del host lateral y mantiene el clip del ScrollView; popover y MOBILE conservan su camino original.

El cierre en dos pasos procede de actualizar la geometría del panel solo al finalizar el cambio de SideUi. `ArcViewportTransition` se incorpora a la transición nativa. Durante el cierre Blink prepara una vez el canvas objetivo más ancho al comenzar. Durante la apertura se conserva el canvas amplio existente y el resize nativo lo estrecha al finalizar; esto evita una zona vacía a la derecha por llegada temprana de un frame ya estrechado. Durante la animación solo cambian el offset de compositor/input y el recorte. La geometría vuelve a los specs publicados al finalizar; una generación invalida callbacks antiguos al interrumpir, cambiar de modo, fullscreen o destruir. El holder también invalida settlements nativos ya encolados al comenzar una nueva animación, recibir un resize más reciente o ejecutar shutDown; así un cierre interrumpido no aplica su offset obsoleto durante la reapertura. No hay polling permanente ni layout de Blink en cada frame.

El ojo no representa una funcionalidad especial de favoritos: era `android.R.drawable.ic_menu_view`, placeholder. El callback solo aceptaba bitmaps y descartaba el fallback nativo. Se usan los resultados reales de `LargeIconBridge` y `FaviconUtils`, manteniendo perfil, sesión y guards de destrucción. La ausencia del bitmap de un sitio concreto no demuestra un fallo de red o del sitio.

## Geometría y tokens

Estas cifras prueban la política con ventana1382×863, densidad1 y sidebar334; no convierten píxeles de la captura en dp universales. El holder real incluye el contrato de caption del sistema y el clipping de superficie. Redondeo: cada token se redondea al píxel más próximo; error máximo0.5px por token antes de sumar límites. No hay tolerancias adicionales para esconder diferencias.

| Parámetro | Referencia | Política implementada en caso de referencia |
|---|---:|---:|
| Ventana disponible |1382×863px|1382×863px|
| Sidebar expandida sin ancho manual |334px|334px|
| Viewport local |x334,y12|x334,y12|
| Viewport visible |1037×840px|1037×840px|
| Inset superior/derecho/inferior |12/11/11px|12/11/11px|
| Radio exterior/interior |13/11px|13/11px|
| Insets laterales header |9px|9px|
| Omnibox |49px alto|máximo entre49px escalados y48dp de hit target|
| Accesos rápidos |57px alto; gaps9/8px|57px; gaps9/8px en referencia|
| Sidebar colapsada |Contrato Android52dp|52dp; no se sustituye por proporción expandida|
| Texto principal/tab/omnibox/espacio |Referencia visual, no dp|14sp; respeta fontScale|
| Texto secundario |Jerarquía menor|12sp|
| Fila/touch navegación y footer |Adaptación Android|48dp; controles secundarios se ocultan según espacio útil|
| Radio pestaña seleccionada |12–15px visuales|14px proporcional en referencia|
| Radios controles/mosaicos |Coherentes y redondeados|8dp navegación;12dp colecciones|
| Separación de secciones |Adaptable|8dp|
| Fondo por defecto |Gris-lavanda del build actual|seed0xff706b86; color de usuario conservado|
| Transición |Sin salto en borde del viewport|Duración350ms e interpolador0.45/0/0.12/1 del SideUi nativo|

El estado expandido sigue sujeto a límites nativos92–500dp, al mínimo útil de navegación y al espacio reservado al contenido web. Esos límites no se modifican en R2. El resize manual tiene precedencia. Ventanas cortas conservan lista flexible y scroll de cabecera; MOBILE restaura medidas/tintas/tamaño de texto original. El footer permanece anclado. No se rellenan los espacios vacíos con elementos decorativos.

## Archivos y reutilización

| Archivo | Propósito |
|---|---|
| `ArcDesktopCoordinator.java` | Transición/clip/input, favicon fallback, presentación de header y UrlBar existente. |
| `ArcViewportTransition.java` (nuevo) | Único componente nuevo de producción: transición del borde visible dentro del TransitionSet existente. |
| `ArcCollectionsView.java` | Favicons nativos y estados discretos; Personal semibold; acciones/IDs/modelos existentes. |
| `ArcDesktopPolicy.java` | Tokens tipográficos y colores/contraste centralizados; conserva medidas y allocator. |
| `ArcDesktopAppearance.java` | Drawables nativos de hover/focus/press y superficies derivadas del tema. |
| `TabVerticalViewBinder.java` | Cápsula activa e inactivos; cierre contextual para mouse; conserva eventos e interacción táctil. |
| `LocationBarTablet.java` | Clipping de foco limitado al host lateral; camino nativo MOBILE/popover intacto. |
| `TabbedRootUiCoordinator.java` | Conecta supresión ARC al manager gráfico real. |
| `ToolbarManager.java` | Compone supresión ARC/XR/narrow y libera estado durante destroy. Se añade par de referencia/modified en su ruta real. |
| `CompositorViewHolder.java` | Puentes mínimos para mantener el canvas amplio durante ambas direcciones y actualizar offset visual/input. |
| `chrome_java_sources.gni` | Registra la nueva transición en GN. |
| `check-arc-preparation.py` | Probes SDK37 actualizados con firmas nativas exactas y nuevas APIs. |
| `tests/test_arc_{native_overlay,collection_presentation,content_animation,header_presentation,tab_interaction,viewport_transition}.py` | Nuevas regresiones sobre código real y límites Android/nativos simulados. |
| `tests/test_arc_{appearance,content_resize,geometry_runtime}.py` | Amplían pruebas anteriores, sin eliminarlas. |
| `tests/fixtures/arc-caption/TopControlLayer.java` | Contrato pinneado de capa nativa para compilación SDK; nullability TYPE_USE conservada. |
| `patches/archium-desktop.patch`, `patches/upstream-files.json` | Patch y hashes regenerados contra el pin;104 archivos totales. |
| `docs/superpowers/plans/2026-10-09-arc-r2-installed-polish.md` | Plan y alcance autorizado. |

Se reutilizan LocationBar, TabModel, native bookmarks/pinned models, SideUi, SurfaceView/outline, DesktopWindowStateManager, stacker y theme preferences. No hay un segundo omnibox, motor web, almacenamiento ni controles ficticios. Los iconos coloreados de extensiones del footer son accesos reales: se conserva su identidad y el feedback nativo. Tampoco se eliminan las dos pestañas legítimas del mismo portal.

## Pruebas y revisión

Comandos ejecutados sobre la versión final del código, con Python3.12.15 y JDK17.0.20.1:

- `ARCHIUM_BUILD_SCOPE=arc-media bash scripts/check-archium-repository.sh`, configurando `ARCHIUM_REPOSITORY_PYTHON=/tmp/archium-ci-stability-20261008/python312/bin/python3` y `JAVA_HOME_17_X64=/usr/lib/jvm/java-17-openjdk-arm64`: **PASS,294/294 tests**,167.100s, `ARCHIUM_REPOSITORY_PREFLIGHT=PASS`.
- `ARCHIUM_BUILD_SCOPE=arc-media python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-37.0/android.jar`, mismo Python/JDK: **PASS**,104 archivos aplicados/hash exacto, geometría y contratos Java, adapters/probes SDK37,5 casos de la suite específica nativa.
- `git diff --check` y `git diff --cached --check`: **PASS**. GN pinneado2589; registro único de transición y patch regenerado.
- Revisión independiente integral y dos rereviews: **sin hallazgos critical/important pendientes**. El reviewer ejecutó además el caso de settlement encolado:1/1 PASS.

Se preserva la suite anterior265/265, que incluye los arreglos R2/R2.1 anteriores. El primer retest detectó dos fixtures antiguos incompletos: faltaba extraer el nuevo helper de clipping y faltaba el sink de favicon. Se corrigieron conservando las16 y8 verificaciones anteriores, y añadiendo clipping observable/fallback nulo. La suite final contiene29 pruebas adicionales respecto a265. Logs privados: `r2-repository-release.log`, `r2-preparation-release.log`, `native-sizing-queue-{red,green}.log`, `expansion-canvas-{red,green}.log` y `mobile-hover-{red,green}.log` bajo `.sync-audit/arc-next-polish-20261009/`.

Estos resultados usan límites Android/JNI/event-scheduler simulados donde corresponde; los probes SDK validan firmas, tipos y anotaciones reales, pero no compilación Chromium integral. El run y la validación visual del APK nuevo siguen separados de esas pruebas locales.

Regresiones RED→GREEN: supresión gráfica ARC y clipping de foco; placeholders/fallback/tint de favoritos; cabecera discreta; borde de cierre/input intermedios y callbacks invalidados; texto Personal14sp; cierre contextual con evento nativo y listener de foco sin acumulación. Un mutante de transición que solo emite el ancho final provoca fallo del test intermedio. Los escenarios anteriores de geometry/caption/dropdown/resize/ARC–MOBILE se conservan.

## Matriz de aceptación

`PARTIAL` significa cambios implementados y contrato local comprobado, con aceptación visual/dispositivo todavía pendiente. `BLOCKED` significa que la verificación requerida necesita el APK nuevo y el display desconectado. No hay PASS integral por compilación aislada.

| ID | Área | Estado integral | Evidencia local y limitación |
|---|---|---|---|
|R2-01|Header/navigation alignment|PARTIAL|Header presentation y supplier ARC; alineación/estados en APK nuevo pendientes.|
|R2-02|Active tab styling|PARTIAL|Contraste y texto sobre fuente real; cápsula nueva pendiente de captura.|
|R2-03|Sidebar resize preservation|PARTIAL|Allocator nativo/manual y preferencias sin cambio; drag y reconstrucción en nuevo APK pendientes.|
|R2-04|Inactive tab styling|PARTIAL|Binder preserva estados nativos y feedback ARC; hover visual pendiente.|
|R2-05|Space selector|PARTIAL|Constructor/acción real y14sp semibold; captura posterior pendiente.|
|R2-06|Pinned/quick controls|PARTIAL|Bitmap/fallback/globo y guards de perfil/sesión comprobados; favicon real pendiente de dispositivo.|
|R2-07|Typography|PARTIAL|SP/fontScale y restore MOBILE; clipping real con títulos largos pendiente.|
|R2-08|Color and material|PARTIAL|Contraste de paletas y gradiente único; parpadeos/scroll real pendientes.|
|R2-09|Section hierarchy|PARTIAL|Acciones y espacios conservados, scroll acotado; muchas pestañas/carpeta en APK nuevo pendientes.|
|R2-10|Bottom controls|PARTIAL|Footer nativo anclado y accesos genuinos conservados; hit targets/hover en DeX pendientes.|
|R2-11|Web viewport geometry|PARTIAL|Referencia exacta, clip/superficie/input, suppression y lifecycle; franja real posterior pendiente.|
|R2-12|Mouse hover/focus states|PARTIAL|Evento nativo reenviado una vez, rebind/focus sin acumulación; mouse real pendiente.|
|R2-13|Responsive layout|PARTIAL|Resize continuo, altura corta, LTR/RTL, modes y epochs en probes; maximizar/resolución DeX pendientes.|
|R2-14|Existing functionality regression|PARTIAL|Suite completa y probes al finalizar; navegación/persistencia reales y build integral pendientes.|
|DEX-AFTER|Capturas y rendimiento del APK nuevo|BLOCKED|Display externo desconectado por el usuario; aún no existe APK R2 para medir FPS y capturar.|

## Rendimiento, evidencia y pendientes

La revisión independiente detectó y se corrigieron dos regresiones: el canvas final estrecho preparado antes de abrir podía dejar una franja derecha vacía; la contribución del foco al cierre contextual debía limitarse a ARC para restaurar el hover MOBILE exacto. También se detectó un settlement nativo encolado de la transición anterior que podía estrechar el canvas y rebobinar el offset durante una reapertura rápida. Se corrigió con generaciones por petición/preparación/shutdown; la prueba drena ese callback antiguo y verifica que solo la última petición aplica su tamaño. Los tres hallazgos tienen regresiones RED→GREEN.

La nueva animación no introduce un timer permanente ni `WebContents.setSize` por frame. Comparte la transición nativa y actualiza solo offsets/outline/surface clip durante su vida. Los gradientes y estados utilizan drawables Android; los mapas de presentación son débiles y los callbacks invalidables. Esto acredita límites de trabajo en fuente/probes, no una medición de FPS/GPU del APK nuevo.

Evidencia privada, fuera de git: `.sync-audit/arc-next-polish-20261009/current-dex.png`, `sidebar-overlap-current.png`, `archium-focus-before.png`, `omnibox-focused.png`, `omnibox-blurred.png`, `archium-focus-toggle-review.mp4` y dumps de la jerarquía. La grabación útil contiene91frames; el primer vídeo parcialmente tapado por Termux no se usa para aceptación. En la captura inicial el DecorView/área Android mide1591×856px, el sidebar321px y el holder1578×829px; son medidas del dump de esa captura, no del tamaño completo de otra ventana. La banda29px se midió en captura con caption nativo40px. Escape retira sugerencias pero no demuestra blur completo.

No hay capturas posteriores del APK R2: se requieren compilación, instalación verificada y reconexión del display. Pendientes precisos: confirmar banda eliminada sin perder caption; foco/dropdown sin overflow; animación cierre/abertura sin doble fase; favicons del sitio; cierre mouse/touch; drag continuo/maximizar/restaurar/resolución; fonts y títulos largos; recreación de SurfaceView/tab switch/fullscreen; persistencia y navegación reales. La minimización al clicar reportada anteriormente requiere retest real; no se declara corregida únicamente por limitar el clipping.

La compilación y el instalador se activarán para el commit exacto después de la verificación local. El monitor conserva600s de actualización y líneas continuas; el worker independiente solo instala un run exitoso con SHA esperado, hash del artifact/firma/paquete y hash del `base.apk` instalado. Si falta el dispositivo, espera. La confirmación de instalación no se inventa mientras el build está en curso. Después de lanzar monitor y worker, el agente queda en pausa por orden del usuario.

Dictamen de fuentes: **READY FOR COMMIT**, suite294/294 y preparación SDK/patch PASS, revisión sin blockers de código pendientes. Esto autoriza producir el APK para validación y no representa aceptación visual integral. Paridad visual integral: **PARTIAL**, con aceptación posterior de DeX **BLOCKED** por display desconectado. Instalación y build nuevos: pendientes del run explícito posterior al commit.
