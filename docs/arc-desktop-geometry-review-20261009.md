# Archium — geometría Arc Desktop y reauditoría R2

Fecha: 2026-10-09. Rama `feat/arc-media-only`; base `1255da5745e3cd1453ff17f3b237cd3f97a24b58`. Chromium pinned `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.

**READY FOR COMMIT y compilación CI.** No quedan bloqueantes conocidos de fuentes, preparación o preflight de R2. La aceptación integral de la APK, renderizado real y entrada en Android/DeX sigue pendiente. Este dictamen no convierte pruebas aisladas en aceptación visual.

La implementación inicial respetó la prohibición de publicar. El usuario autorizó después expresamente commit y lanzamiento del run; esa autorización permite staging, commit, push a la misma rama y workflow_dispatch. No autoriza instalación, ADB, merge ni borrar trabajo anterior.

**Geometría final.** La captura se normaliza con ancho medido/1382; el factor decorativo se limita a densidad×[0.5,1.5]. La densidad se usa para límites Android y objetivos táctiles, sin atribuir una densidad a la imagen. Sidebar expandido: objetivo334/1382 del ancho, limitado por el presupuesto Side UI, mínimo nativo92dp, mínimo de navegación210dp y máximo500dp. Sidebar colapsado52dp. La asignación nativa sigue gobernando desplazamiento del compositor y entrada; no se modifica el ancho del rail a espaldas de SideUiCoordinator.

Tabla para el fixture de ventana1382×863, densidad Android1 y sin caption adicional. La columna implementada describe política y parámetros ejercitados, no una captura de APK:

| Elemento | Referencia | Implementado | Evidencia |
|---|---|---|---|
| Sidebar |334×863;24.17%|334px; altura completa sin padding artificial|Política y asignador nativo ejecutados|
| Viewport |x334,y12;1037×840|x334,y12;1037×840|Fixture Java literal|
| Insets |superior12,derecho11,inferior11|12/11/11; separación lateral0|Métodos reales del coordinador|
| Radios |exterior13,interior11|13/11; outlines restaurables|Política y mutaciones; render real pendiente|
| Omnibox |x9,y57;316×49|host nativo316×49, márgenes9; navegación48+padding9|Parámetros; foco/entrada real pendiente|
| Favoritos |x9/117/225;y116;99/100/100×57|tres controles reales99/100/100×57; gaps9/8; separación tras URL10|Método real de ArcCollectionsView|
| Pestaña seleccionada |x9,y305;316×49|alto49, padding lateral9; Y dependiente de grupos/selección nativa|Binder real; no coordenada Y fija|
| Footer |centro aproximado833|fila48, inset inferior6; anclado al final del layout|Presupuesto flexible; posición real pendiente|

Con densidad2 y ventana2764×1726, las dimensiones de referencia se duplican. A igual cantidad de píxeles y distinta densidad, los límites táctiles pueden cambiar el ancho del sidebar; esto es deliberado. RTL conserva el anclaje físicoLEFT de Chromium; la política permite límites físicos reflejados sin forzar un cambio de lado solo por idioma.

**Responsive.** El header existente está dentro de un ScrollView. Su viewport se limita a257/863 del alto disponible, con mínimo táctil48dp y prioridad del presupuesto de pestañas; el contenido secundario completo continúa accesible mediante scroll. La cabecera no desplaza ilimitadamente la sección de tabs por colecciones largas. La lista nativa conserva el peso flexible. En ventanas cortas ceden utilidades, búsqueda secundaria y footer nativo; New Tab sigue disponible en el menú real. El menú nativo se recoloca en la cabecera cuando el footer no cabe. La navegación reducida está disponible manteniendo pulsado el toggle, con tooltip y acciones de Tab reales. En MOBILE se restauran toolbar, padres, márgenes, padding, outlines y controles; fullscreen libera reservas y decoración del frame.

**Reauditoría de R2 y revisión independiente.**

| Componente/gate | Estado | Resultado |
|---|---|---|
| Crash y geometría dropdown |PASS host / PARTIAL integral|Raíz de ventana compartida, dimensiones vacías0, traslación RTL/LTR, padding y recuperación detached→valid|
| Omnibox movido por scroll |PASS host|OnScrollChangedListener; no polling; posiciones cambian sin layout|
| Caption/bookmarks |PASS host / PARTIAL integral|TOOLBAR caption no desplazable; reserva neta;40+42=82,40−16=24, cambios de altura y fullscreen0|
| Sidebar y tabs cortos |PASS host|Ancho real, navegación separada de altura; se protege el listado al ocultar chrome|
| ARC→MOBILE→ARC / fullscreen |PASS límites / PARTIAL integral|Restauración y guardas probadas; flujo completo de actividad pendiente|
| Observers/destroy |PASS límites / PARTIAL integral|Scroll idempotente, detach/destroy, callbacks inactivos y restauración de superficies; fugas reales de Activity pendientes|
| Kit portátil R2 |PASS copia corregida|Validador apuntaba al nombreR1; corregido en copia de evidencia sin alterar el original. No forma parte del workflow de build|
| Preparación pinned |PASS|95 archivos aplicados y hashes correctos; pruebas Java y compilación aislada Android|
| Preflight completo |PASS|154/154, frente a137/137 inicialesR2|
| Diff y configuración |PASS|git diff --check; passwords localesfalse; scopearc-media; HEAD/index intactos antes de staging autorizado|
| Probe Android de la versión nueva |PENDIENTE|No se ejecutó ADB ni se instaló probe; evidencia previa no prueba estos cambios|
| APK integral / multimedia / DeX |PENDIENTE CI y dispositivo|El run autorizado producirá nueva evidencia de compilación; aceptación visual posterior|

La revisión independiente encontró3 Important y0Critical. Todos se reprodujeron y corrigieron con RED→GREEN:

- ControlesGONE conservaban getMeasuredHeight y consumían presupuesto de pestañas fijadas. onMeasure ahora descuenta solo controles visibles y nunca usa máximo0 como límite ilimitado.
- Scroll del nuevo header movía el omnibox sin relayout; dropdown conservaba Y anterior. Se añadieron eventos de scroll, registro simétrico, detach/destroy e idempotencia de attach. Las pruebas de extracción ahora seleccionan la declaración del método, evitando capturar una llamada a onGlobalLayout.
- Cambio de caption modificaba LayoutParams antes de la medición; el presupuesto usaba altura anterior. Lee altura solicitada y observa layout del spacer.

Otros ciclos RED→GREEN: ancho fijo240→334; hueco lateral8dp→0; callback que reactivaba Arc tras MOBILE; reserva fullscreen; spacer40→24; header que consumía excesivo alto; filas/favoritos de referencia. No se dejaron findings menores diferidos.

**Pruebas ejecutadas.** Python3.12.15 y OpenJDK17.0.20.1; Android SDK37.0. Los dos checks completos se repitieron tras la última modificación de producción:

```bash
ARCHIUM_BUILD_SCOPE=arc-media python3 scripts/check-arc-preparation.py --android-jar /opt/android-sdk/platforms/android-37.0/android.jar
ARCHIUM_BUILD_SCOPE=arc-media bash scripts/check-archium-repository.sh
```

Se fijaron PATH/JAVA_HOME/ARCHIUM_REPOSITORY_PYTHON al Python3.12 y JDK17 recuperados. Logs: `.sync-audit/arc-geometry-20261009/final-preparation-verified.log` y `final-repository-verified.log`. Las regresiones geométricas tienen16 tests Python; el caso adicional de scroll completa17 tests nuevos sobre la suite137 anterior. Antes del último ajuste de proporción también pasaron44 tests Arc. La compilación aislada usa contratos parciales de servicios; no compila una APK completa ni ejecuta Views Android reales.

**Riesgos residuales.** Hardware compositor/SurfaceView y capas multimedia deben verificar que el redondeo visible coincide con crop, outlines e hit testing. El SDK permite las APIs usadas, pero eso no prueba composición gráfica en DeX. El caption usa contratos pinned; la ausencia de llamadas que actualicen el stacker desde su getter evita recursión de actualización, pero cambios de todas las capas de una actividad real siguen pendientes. No se garantiza Y305 para la pestaña seleccionada: selección, pinned tabs, Spaces y recursos nativos determinan la posición. En ventanas físicamente menores que los targets táctiles, los controles requieren scroll o expansión/long-press. Estos puntos no se cuentan como aceptación integral.

**Decisiones de ejecución.** La especificación del usuario fue el diseño autorizado; ejecución inline y revisión independiente. Se preservaron13 archivos locales previos y el hash del index antes de integrar únicamente versionesR1 reconocidas. Densidad/proporciones se centralizaron; el lado físico nativo no cambia por idioma. Cabecera limitada para favorecer tabs; controles secundarios permanecen accesibles. No se borró ni reinicializó el worktree.

**Archivos modificados o nuevos (incluye R2 preservado/integrado).** El ViewUtils original auxiliar anterior se conserva fuera del commit porque no es una modificación de producción requerida.

- `.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/TabVerticalViewBinder.java`
- `.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabListCoordinator.java`
- `.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabRailLayout.java`
- `.source-modified/chrome/android/features/tab_ui/java/src/org/chromium/chrome/browser/tasks/tab_management/vertical_tabs/VerticalTabsSideUiCoordinator.java`
- `.source-modified/chrome/android/java/src/org/chromium/chrome/browser/tabbed_mode/TabbedRootUiCoordinator.java`
- `.source-modified/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/OmniboxSuggestionsDropdownEmbedderImpl.java`
- `.source-reference/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarEmbedder.java`
- `.source-reference/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarEmbedderUiOverrides.java`
- `.source-reference/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/LocationBarEmbedderUiOverridesUnitTest.java`
- `.source-reference/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/OmniboxSuggestionsDropdownEmbedderImpl.java`
- `.source-reference/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/OmniboxSuggestionsDropdownEmbedderImplUnitTest.java`
- `.source-reference/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/suggestions/OmniboxSuggestionsDropdownEmbedder.java`
- `.source-reference/ui/android/java/src/org/chromium/ui/base/ViewUtils.java`
- `chromium/chrome/android/java/res/values/arc_strings.xml`
- `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcCollectionsView.java`
- `chromium/chrome/android/java/src/org/chromium/chrome/browser/arc/ArcDesktopCoordinator.java`
- `chromium/chrome/browser/ui/vertical_tabs/android/java/src/org/chromium/chrome/browser/ui/vertical_tabs/ArcDesktopPolicy.java`
- `docs/superpowers/plans/2026-10-09-arc-desktop-geometry.md`
- `docs/superpowers/specs/2026-10-09-arc-desktop-geometry.md`
- `patches/archium-desktop.patch`
- `patches/upstream-files.json`
- `scripts/check-arc-preparation.py`
- `scripts/test-android-arc-toolbar.py`
- `tests/android/toolbar/ArcOmniboxResizeTest.java.in`
- `tests/arc_toolbar_probe.py`
- `tests/java/ArcDesktopGeometryTest.java`
- `tests/java/ArcDesktopPolicyTest.java`
- `tests/test_arc_geometry.py`
- `tests/test_arc_geometry_review.py`
- `tests/test_arc_geometry_runtime.py`
- `tests/test_arc_omnibox_resize.py`

Entrega generada: `patches/archium-desktop.patch` SHA256 `6d8067677a772431b5373cbd5c15f8a6779963330f8a5704ec576a8e57d9e3df`; `patches/upstream-files.json` SHA256 `bf11eeb9206a10a08ec4c9b0a901630f58a4772f5bdc9d4afc84155ccad909e9`. Diff completo antes de commit: `.sync-audit/arc-geometry-20261009/full.diff` (incluye nuevos archivos, sin git add indiscriminado).

Run previsto: `baseline-build.yml`, `feat/arc-media-only`, `ARCHIUM_BUILD_SCOPE=arc-media`, local passwordsfalse; checkpoint `archium-checkpoint-37807259506-1`, identidad verificada `33db26aa6fad2e8a9ac9ccf26774605edb9db771`, misma revisión Chromium. Se comprobó descarga del manifiesto mediante gh release download; no es una APK de la reparación nueva.
