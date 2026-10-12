# Archium R3: verificación contra el prompt protegido

Se contrasta el documento `ARCHIUM_VISUAL_PARITY_R3_CONSOLIDADO_2026-10-09.md`
con el código de `assistant/archium-r4-recovery` y la APK del run
[38210970891](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/38210970891).
Esta APK compila, está instalada y falla al abrir el navegador en DeX.
Una compilación exitosa no acredita la aceptación visual ni el funcionamiento.

Documento original conservado byte por byte respecto de `origin/feat/arc-desktop`
en `51e5ed429661727156ab2534caac99a82ee9264b`; SHA256:
`29aae34a6c849b361210782ca99cc9c471d8e9acc11433ab3fc051d04b907bc8`.
La rama de recuperación ya desciende de ese respaldo. No se mueve ni modifica
la rama protegida; tampoco `main`. El pin Chromium sigue siendo
`cfd94726b7b5fb48aedcc32662f2f3fbdbadec35`.

## Resultado de la revisión

**La paridad completa R3 no está verificada.** Se encuentran las implementaciones
y se reparan defectos reproducibles de captura, transición, sugerencias y color
de selección. Los requisitos que exigen el navegador completo en DeX quedan
pendientes de la nueva APK. No se sustituyen capturas por grep, mocks ni probes.

| ID | Estado del candidato | Evidencia actual y requisito pendiente |
|---|---|---|
| R3-01 Cuña inferior | PARTIAL | `ArcDesktopCoordinator` recorta holder y SurfaceView con radio inferior izquierdo cero en API >=33. `ArcDesktopPolicy` prueba la región táctil cuadrada. Falta captura ampliada y resize con fondos claros/oscuros. API <33 conserva el recorte simétrico: no se promete aceptación idéntica allí. |
| R3-02 Resize y preferencia | PARTIAL | `VerticalTabUtils.getUserResizedWidthDp/setUserResizedWidthDp` conserva la preferencia Chromium; la geometría consulta el ancho real reservado por Side UI. Este fix no cambia ese código ni introduce un ancho fijo. Faltan tres anchos, arrastre, maximizar/restaurar y reinicio de la nueva APK. |
| R3-03 Nueva pestaña | PARTIAL | `mNewTabRow` es una fila antes de las pestañas y delega a `mNativeNewTabButton.performClick`; no crea otro TabModel. Conserva etiqueta/accesibilidad y ahora tooltip también en compacto. Falta creación real con mouse, teclado y touch en los tres tamaños. |
| R3-04 Espacio y secciones | PARTIAL | `ArcCollectionsView` presenta favoritos, selector de espacio con flecha y menú, carpetas/fijados y controles reales. `ArcNativeTabSession` conserva la propiedad de TabModel. Hay pruebas de estado y foco. Faltan captura, menús cerca de bordes y navegación entre espacios en la nueva APK. |
| R3-05 Material | PARTIAL | **Fallback opaco de color configurable**, no blur, translucidez, vibrancy ni dynamic color del wallpaper. `ArcDesktopPolicy.surface` produce alpha 255; `mColumn.setBackgroundColor` aplica ese color. Observación del teléfono tras desconectar DeX: WindowManager `mBlurEnabled=false`. Esto no demuestra incapacidad permanente de DeX. Faltan capacidad OEM en display externo y matriz de wallpapers azul/naranja/claro/oscuro. |
| R3-06 Pestañas | PARTIAL | Defecto reproducido: la cápsula activa normal usaba tinte `ffcacccf` en vez de blanco. Reparado en el binder real, con texto negro y pruebas JVM de cinco semillas. Incógnito, multi-selección y móvil conservan sus ramas. Hover, cierre contextual y elipsis siguen en binders nativos. Falta render y títulos largos en DeX; nueva regresión Chromium bloqueante en CI. |
| R3-07 Header/omnibox | BLOCKED | La APK instalada falla en el cálculo de captura del toolbar y en transición a vertical tabs. Se recuperan correcciones omitidas de `1255da5` y la posición de sugerencias de `a1f3f2b`, manteniendo la LocationBar real dentro de la sidebar. Probes Android/JVM pasan; falta ChromeJUnit completo, abrir en DeX, Ctrl+L, autocompletado, favoritos y navegación real. |
| R3-08 Mosaicos | PARTIAL | Las tres acciones del header son bookmarks, menú de servicios Google y apariencia; el último no es un bookmark. Los favoritos reales tienen favicon y menú/contexto propios en `ArcCollectionsView`. No hay acciones sustituidas por decoración. Falta responsive y comprobación de cada acción en DeX. |
| R3-09 Footer | PARTIAL | Se conservan menú Chromium y host nativo de extensiones, con restauración al salir de Arc. El acceso Autofill sigue la ruta estándar; el backend propio de contraseñas permanece DEPRECATED por orden posterior del usuario. Faltan alineación, tooltips y acciones en la nueva APK. |
| R3-10 Viewport | PARTIAL | Los márgenes se derivan del holder original, outer padding y gap; el clipping se aplica al holder y superficie activa, con restauración. No se inyecta CSS ni se cambia UA/zoom en esta reparación. Faltan páginas claras/oscuras, insets, mover/maximizar/resize sin recarga y ausencia de franjas. |
| R3-11 Estado | BLOCKED | Los modelos/perfiles, store y pruebas host se conservan; las regresiones del callback sin strip horizontal pasan en JVM. La APK instalada tiene crash confirmado y no valida persistencia. Faltan ejecución completa de la nueva APK, normal/incógnito, historial, bookmarks, reinicio y tabs durante resize. |
| R3-12 DeX nativo | PARTIAL | La reparación no añade decoraciones/traffic lights, modifica taskbar ni introduce un WebView paralelo. Se mantiene el spacer de caption nativo. Falta comprobar mover, minimizar, maximizar y restaurar con la nueva APK en el display DeX. |

Conteo: **0 PASS, 10 PARTIAL, 0 FAIL del candidato, 2 BLOCKED**.
La APK instalada tiene **ANDROID_RUNTIME=FAIL**. La clasificación del candidato
no convierte ese fallo observado en PASS ni declara corregido todo el navegador.

## Defectos confirmados y reparación acotada

1. `ToolbarLayout.getLocationBarContentRect` asumía que el toolbar era ancestro
   de la LocationBar. La sidebar ya la reubica legítimamente. El walk llegaba a
   `ViewRootImpl` y el cast fallaba. Se conserva la ruta de descendientes y se
   usan coordenadas de la misma ventana para la sidebar; detach/otra ventana
   devuelven rect vacío. Historial: commit `1255da5745e3cd1453ff17f3b237cd3f97a24b58`.
2. `TabbedRootUiCoordinator.onVerticalTabsActiveChanged` asumía que existía
   `TabStripTransitionCoordinator`. ToolbarPhone no lo tiene. Se conserva cleanup
   de observadores y el estado, evitando esperar una transición horizontal
   inexistente. La preferencia muestra la sidebar directamente en ese caso.
3. El cálculo de sugerencias tenía el mismo contrato de ancestro incorrecto.
   Se recupera el hunk de `a1f3f2bb5d2e50437aca5b47c63014e38fa998a8`, contrastado
   con el upstream exacto. Se mantiene autocompletado Chromium, no una barra nueva.
4. La selección normal usa blanco, como exige R3, y el texto/iconos contrastan
   con esa superficie. La selección de incógnito y multi-selección se conserva.
5. Nueva pestaña compacta y botones de navegación obtienen tooltip con el mismo
   texto de accesibilidad. No se cambia geometría ni se duplican controles.

## Pruebas observadas

- `python3 -m unittest discover -s tests -p test_arc_toolbar_runtime.py -v`:
  RED exit 1; GREEN exit 0, **6 tests**, 12 escenarios de métodos reales con
  límites de servicios explícitos. No es integración Chromium.
- `scripts/test-android-arc-toolbar.py ... --display-id 17 --original`:
  RED exit 1, `ViewRootImpl` real; fix de captura GREEN exit 0 en el Samsung/DeX.
- Probe de coordenadas de sugerencias original: RED exit 1 en display 17.
  Se desconectó ese display antes de la última repetición; ese intento produjo
  `SecurityException` al lanzar en display ausente, exit 1, no PASS oculto.
- Probe final de captura y sugerencias en el mismo Samsung, display **0**:
  GREEN exit 0; reparent, descendiente, detach y otra ventana. Son métodos reales
  trasplantados a instrumentación acotada, **no la actividad Archium completa**.
- Color de selección: RED exit 1 (`ffffffff != ffcacccf`); GREEN exit 0.
  Compila/ejecuta los métodos reales del binder con límites de servicios y policy
  real; verifica selección normal, incógnito, multi-select y móvil.
- Suite host integral: exit 0, **242 passed / 0 failed / 0 skipped**, 481.682 s.
  GN real en tres perfiles y AAPT2 real acotado; no equivalen a render Chromium.
- Preparación de patch y API SDK: exit 0. Generación doble de 109 archivos:
  hashes idénticos. Patch `455f96daed8a222c1769253bc8886feb95e36f5d816c91ce8d5bda9c0129dd8b`;
  manifest `034955d92e9f5ec6d69de2b3da1e0ff12fd5f9e11b30b06afa36878d1408f276`.
- Nuevas regresiones registradas en ChromeJUnit: `ArcToolbarReparentingTest`,
  `ArcTabSelectionTest`, y ampliaciones de `TabbedRootUiCoordinatorUnitTest` y
  `OmniboxSuggestionsDropdownEmbedderImplUnitTest`. Se ejecutan como gates
  bloqueantes **antes de libchrome**, además de S3. Estado: PENDING_POST_RESTORE.

Excepciones filtradas y hashes de logs/comandos:
[evidencia](evidence/2026-10-12-dex-runtime/results.json),
[stack traces de Archium](evidence/2026-10-12-dex-runtime/archium-exception-excerpts.txt).
No se publica el crash buffer completo ni datos de otras aplicaciones.

## Aceptación posterior a la APK

Con el monitor autorizado se entrega la compilación incremental y se detiene
el trabajo automático para seguimiento manual. Al volver a conectar DeX:
abrir sin crash; comprobar Ctrl+L/URL/sugerencias/back/forward/reload, incluida
la posición vertical del dropdown debajo de la omnibox de la sidebar; tres anchos
con preferencia intacta; nueva pestaña por mouse/teclado/touch; cápsula blanca y
hover; espacios/bookmarks/extensiones; esquinas/insets; normal/incógnito; mover,
maximizar/restaurar y reiniciar sin pérdida de estado. Capturar la unión inferior
y repetir wallpapers para aceptar visual/material. Hasta observar esa evidencia
no se marca R3 completo ni ANDROID_RUNTIME=PASS.
