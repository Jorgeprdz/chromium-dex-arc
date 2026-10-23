# Floating V2 — candidato de implementación, 22-oct-2026 CDMX

Rama: `assistant/archium-r5-desktop-native-mobile`. Base: `c2e3773a604204676e4cec2296b650481e5b9632`, Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` (157.0.8086.0). Este documento sustituye la dirección visual anterior: el usuario aprobó los dos renders V2 con contenido detrás de ambas cápsulas. No se considera aceptada una APK del candidato.

Referencias inspeccionadas: `Archium_Floating_V2_01_Instagram.png` y `Archium_Floating_V2_02_LinkedIn.png`, también entregadas en Download del teléfono. Copia y evidencia local: `/workspace/archium-evidence/floating-glass-over-content-v2/`. No se modifica el contenido de Instagram, LinkedIn ni otras webs.

## Cambios y componentes reutilizados

- `BrowserControlsManager`: opt-in de reserva/offsets cero para contenido web durante navegación Mobile. Mantiene los campos nativos de altura y restaura la política nativa al desactivarse. `CompositorViewHolder` actualiza tamaño y viewport mediante su flujo existente. No cambia Blink, GPU, UA, escalas, proporciones ni algoritmos de Split View.
- `ToolbarPhone`: fondo de cristal dentro de la cápsula existente, tanto en dibujo legacy como en la ruta refactorizada. **No cambia ancho, alto, padding, editor, acciones de seguridad ni hit targets de la omnibar.** Reutiliza elevación y foco existentes.
- `ArcPhoneNavigation`: misma cápsula y mismo slot nativo inferior, con cuatro acciones, contador y bottom sheet existentes. Fondo del slot/delegate transparente sólo cuando se activa el cristal; contraste de etiquetas neutras en ambos temas. No se agrega una segunda barra ni otra omnibar.
- `ArcPhoneGlass`: captura con PixelCopy sólo las regiones de las cápsulas del SurfaceView del compositor, reducidas a un máximo de 256×128 por imagen; una copia en vuelo, doble buffer por región. Blur de píxeles en un HandlerThread; controles/texto nativos permanecen nítidos. No captura la ventana ni persiste imágenes. El Drawable recorta la imagen desenfocada y aplica tinte translúcido claro/oscuro.
- `ToolbarManager`: activa sólo en teléfono y página web interactiva; vuelve a fondos/geometría nativos con editor, NTP, Hub o fullscreen. Restaura los Drawables originales de los contenedores. Invalida muestras en cambio de pestaña/URL; pausa/destroy detienen el muestreo y liberan buffers/worker; movimiento ajusta la frecuencia. Resultados tardíos o de geometría anterior se descartan.
- Registros GN y filtro de tests existentes ampliados; parche y manifest regenerados. Sin dependencias nuevas. Manifest comparado con la base: ningún archivo Desktop/Spaces/colecciones/Split específico cambia. La integración compartida se mantiene detrás del opt-in móvil.

## Evidencia local

| Verificación | Resultado | Alcance |
|---|---|---|
| Reserva viewport, cuerpos reales de getters compilados | PASS, 2 tests | Alturas/offsets cero, estado nativo preservado y restauración; wiring de integración |
| Navegación + cristal Robolectric SDK30/36 | PASS, 76 ejecuciones | Vistas Android reales; acciones/controller y captura GPU como fronteras explícitas |
| Política original de descubrimiento Chromium | PASS, 38 métodos | TestListComputer/Allowlist fijados e íntegros; sin application shadows |
| Host phone | PASS, 9 tests | Incluye duplicados hairline, dimensiones y guards de tema/política |
| Ownership del slot inferior y anotaciones TYPE_USE | PASS, 5 tests | Misma barra, sin nuevo root overlay; campos entregados compilados |
| Cobertura de gates | PASS, 2 tests | Suites entregadas registradas |
| Owner de contraste status bar | PASS, 1 test | Restauración nativa y actualizaciones de insets/delegate |
| Aplicación / transición del parche | PASS, 7 / 17 tests | Hashes fijados, transición incremental |
| Preparación SDK37.2/JDK21 | PASS | Parche de 169 archivos; adaptadores nuevos compilados con fronteras Chromium stubbed; regresiones sintéticas Desktop/sesión existentes |
| Regeneración de parche/manifest | PASS | Segunda generación idéntica byte a byte |
| Compilación integrada Chromium / APK V2 | NOT RUN | Sin Actions, publicación ni instalación nueva |
| Aceptación gráfica/dispositivo/rendimiento | PENDIENTE | Ninguna captura de la APK anterior valida este candidato |

Evidencia RED: `viewport-red.log`, `integration-red.log`, `glass-red.log`. GREEN: `viewport-green.log`, `glass-final.log`, `phone-host-final.log`, `preparation-final.log`, `patch-application.log`, `patch-transition.log`, `delivery-delta.txt`. Los fallos intermedios del harness gráfico/SQLite se corrigieron como limitaciones del entorno local; no se cuentan como bugs gráficos del producto.

## Diferencias y límites pendientes

El cristal usa muestreo limitado, no blur nativo continuo del compositor: cada región se actualiza aproximadamente a 8 fps durante movimiento y 2 fps en reposo. Falta medir fluidez, memoria y consumo reales. No se promete equivalencia de rendimiento ni coincidencia visual con los renders.

Cuando PixelCopy no dispone de un SurfaceView válido, la región sale de sus límites o la superficie protege su contenido, se conserva el tinte translúcido sin muestra; no se usa captura de ventana ni se eluden protecciones. Esta degradación y la ruta compositor/texturas requieren validación en Galaxy/DeX.

La NTP y edición utilizan sus superficies y geometría nativas deliberadamente; el trabajo pendiente de New Tab previamente aceptado no se reabre. El teclado y las reservas de sistema siguen con sus owners nativos; la barra inferior nativa se oculta ante IME. No se afirma validado ese comportamiento en la APK nueva.

Antes de aceptar visualmente: comprobar contenido detrás y fuera de ambas cápsulas, ausencia de bandejas grises, sombras, status/gesture bars y recortes; páginas claras/oscuras, cambio dinámico de tema, teclado y formularios inferiores, scroll hasta el final, rotación, fullscreen, Hub, incógnito, cambio/restauración de pestañas, y Desktop→Phone→Desktop. Verificar también controles compositados durante scroll y fuente de PixelCopy. La transparencia de status bar reutiliza el owner previo; no se ha demostrado en dispositivo que toda la franja superior muestre web.

**Estado:** implementación guardada con gates locales PASS; aceptación visual e integración nativa PENDIENTES. No declarar DONE ni coincidencia visual. No se lanzó una compilación; se necesita autorización nueva para un único build incremental y posterior validación física.


## Auditoría automática Light/Dark — 22-oct-2026 CDMX

Revisión posterior a `fd4195c`. No se detectó un defecto reproducible en los límites locales comprobados, por lo que **no se cambia código de producción, geometría ni preferencias del usuario**. Se añaden tres pruebas Robolectric y una de integración estática.

La elección de tema sigue siendo la nativa de Chromium. Con **Seguir tema del sistema**, los cambios DayNight se propagan a los proveedores nativos; los callbacks de color/tint y de configuración actualizan las superficies Floating. Una selección explícita Claro/Oscuro dentro de Chromium conserva su significado. Esta auditoría no cambia ajustes del teléfono ni afirma haber probado la programación automática de Android.

Comprobaciones nuevas:

- Provider real `ToolbarThemeColorProvider` y `ThemeColorProvider` fijado: cuatro transiciones claro↔oscuro mediante eventos nativos simulados, en ambos órdenes (color/tint), sin reactivar manualmente la opción Floating ni reconstruir vistas. Los observers reciben la nueva superficie y tinta.
- El callback entregado de configuración actualiza Floating **antes** del retorno por orientación sin cambios; un cambio nocturno no queda bloqueado por seguir en vertical.
- Cristal: cambia el tinte de una muestra existente sin introducir un fondo blanco temporal, manteniendo la imagen y las dimensiones. Es una prueba de contratos de dibujo, no detección visual de flashes de GPU.
- Cápsula inferior y menú ya abiertos: cuatro transiciones conservando las vistas y layout; AA ≥4.5 para etiquetas, incluso con ripple presionado, y ≥3 para iconos sobre los fondos límite blanco/negro simulados. El menú no se cierra ni se crea de nuevo. El dominio conserva contraste AA.

| Componente | Claro | Oscuro |
|---|---|---|
| Status bar | PASS contrato estático/owner | PASS contrato estático/owner |
| Omnibar | PASS local de paleta/eventos; geometría estática | PASS local de paleta/eventos; geometría estática |
| Floating Pill inferior | PASS local, contraste calculado | PASS local, contraste calculado |
| Menú/bottom sheet propio | PASS local de cambio y estado | PASS local de cambio y estado |
| Selector nativo, sugerencias, diálogos y teclado | PENDIENTE | PENDIENTE |
| Cambios dinámicos | PASS eventos simulados/configuración estática | PASS eventos simulados/configuración estática |

**Toda aceptación real en dispositivo continúa PENDIENTE**, también para las filas PASS locales. En particular, no se ha comprobado visibilidad de iconos de status bar sobre páginas de color contrario al tema, raster del texto de omnibar, barras del sistema, teclado/menú durante un cambio real, reinicio conservando preferencia ni seguir el horario del sistema. No declarar WCAG AA global a partir de las pruebas de la cápsula inferior.

Evidencia nueva en el mismo directorio externo: `theme-audit.log` (76 ejecuciones SDK30/36, política original 38 métodos), `theme-host.log` (9 PASS), `theme-status-owner.log` (1 PASS), `theme-patch.log` (7 PASS), `theme-transition.log` (17 PASS). Patch/manifest regenerados y comprobados reproducibles. Sin nuevo build, instalación ni Actions. La preparación SDK previa continúa aplicando al código de producción sin cambios; los tests nuevos sí se compilaron/ejecutaron en el runner local.

## Fallo físico confirmado y corrección de composición — 22-oct-2026 CDMX

Run39898129497 / `2ef296770a2face3495166fe91933fcf2b4f24da`: compilación e instalación **PASS**, aceptación visual **FAIL**. Hash de APK instalada comprobado otra vez en el teléfono: `7371ebc49e7f0c756a78647c5f0516b191affd6bc3fd26ec70e688188ccd46bc`. Los estados NOT RUN anteriores describen el momento en que se escribieron; este resultado los actualiza.

Evidencia nueva: `/workspace/archium-evidence/floating-v2-runtime-fix/`. Se inspeccionaron ambos renders, las cuatro capturas del usuario y capturas propias con franjas de colores en una página de diagnóstico aislada. No se inyectó diseño en una web externa. Se utilizó la pestaña que estaba en blanco y se restituyó `about:blank`; modo nocturno restaurado a `auto`. El teléfono se devolvió al usuario y a Termux.

### Causa demostrada y alcance de la corrección

La jerarquía estable muestra `ToolbarControlContainer` **INVISIBLE**, su `SurfaceView` a 904×1880 y el contenido bajo controles. Los métodos entregados `getTopControlHiddenRatio()`/`getBottomControlHiddenRatio()` devolvían 1 al ser cero la altura expuesta por el modo overlay. El código Chromium fijado `BrowserControlsUtils.drawControlsAsTexture()` interpreta ese ratio positivo como dibujo mediante textura; `BrowserControlsManager.shouldShowAndroidControls()` oculta entonces la vista real. `ArcPhoneGlass` exige `view.isShown()` antes de copiar: para el target superior oculto nunca podía entregar una muestra. Esto explica una ruta fallida concreta que los tests anteriores de alturas/offsets no cubrían.

La captura de franjas confirma además que el padre de la superficie sigue empezando a y=86: hacer transparente el color de status bar no elimina su reserva de espacio. El owner fijado sólo permite top edge-to-edge para sus páginas nativas admitidas, sin opt-in para una web con Floating.

- Ratio de ocultamiento cero exclusivamente durante overlay móvil. Fuera del opt-in se conservan los cálculos originales, hiding tokens, animaciones y fullscreen.
- Se reutiliza `mSuppressToolbarSceneLayerSupplier` para retirar la textura superior duplicada, conservando motivos XR/vertical-tabs/Arc existentes. La escena inferior también se suprime durante el overlay, manteniendo el mismo slot Android. Así PixelCopy no vuelve a muestrear las propias cápsulas/textos compositados. La escena inferior original era visible incluso con el slot Android visible; identificar cada píxel blanco del run anterior no es posible con el dump de bounds y no se afirma haberlo demostrado.
- Opt-in reversible en el owner `EdgeToEdgeController` para que web llegue bajo status bar. En la ruta legacy sólo se desplazan los márgenes superiores de los controles y progress bar por el inset real/cutout; se guardan/restauran los originales. Ancho/alto de omnibar no cambian. La ruta moderna conserva su owner nativo de posición. IME, NTP, Hub, editor, fullscreen y Desktop salen del opt-in.
- Contraste de status bar: se pide enforcement nativo de Android mientras está transparente y se restaura el valor anterior al salir; queda pendiente comprobar su resultado sobre páginas reales y versiones del sistema.
- Diagnóstico acotado `ArchiumGlass`: cambios de activación, primer resultado de copia por target/generación y primer dibujo de muestra. Sólo metadatos/bounds, sin URL, píxeles o capturas persistidas. Permite verificar en el candidato que el frame llega a dibujarse.

RED/GREEN conservado: `hidden-ratio-red.log`, `composition-red.log`, `insets-red.log` contra implementación anterior; `overlay-green.log`. Se ejecutan cuerpos entregados de los getters, visibilidad de escena y políticas de insets con dependencias sintéticas: no son aceptación gráfica ni una compilación de todo Chromium.

Gates locales del candidato: 76 ejecuciones Robolectric SDK30/36 y política Chromium38 métodos; host phone13, ownership5, status-owner1, coverage2, aplicación7 y transición17 PASS. Preparación SDK37.2/JDK21 y parche/manifest de 173 archivos reproducibles PASS. Ningún archivo específico de Desktop/Spaces/Split cambia; se amplían únicamente integraciones móviles y owners compartidos detrás de opt-in.

### Limpieza autorizada

Inventario paginado completo: 12 artifacts de checkpoints, 1 release normal, sin releases de checkpoints ni runs activos al borrar. Se verificaron manifest/pin/grupos y se compararon IDs, digest y tamaños inmutables de los preservados con los consumidos por CI: fuente39829306775-1 restaurada por run39898129497; fallback39817793524-1 restaurado por run39829306775. Ambos pasos `S1 restore once and transition patches` PASS. No se hizo aquí una descarga completa de sus partes; CI debe volver a verificar los bytes antes de restaurar.

Eliminado el conjunto completo `archium-checkpoint-39729088298-1`: artifacts12407577182,12407357649,12406988634,12406883793. Total **26.530.254.497 bytes** (26,53 GB decimales). Fuente39829306775-1 y fallback39817793524-1 conservados y comprobados presentes después. APKs, respaldos, logs, release preview y outputs no se borraron. Recibo persistente: `cleanup-receipt.json` en la evidencia nueva.

### Build y aceptación pendientes del candidato

Autorizado por el prompt actual **un solo** build incremental después de los gates, preflight completo, QEMU false, sin reintentos ni reparaciones automáticas. Estado/dispatch/monitor se guardarán en un directorio nuevo bajo `/workspace/.local/state/archium-r5-floating-runtime-*`; el run anterior permanece intacto. La instalación exige recibo/artefacto del SHA exacto, verificación de paquete/ABI/firma/hash/versión y respaldo previo de la APK instalada.

No declarar visual PASS del candidato antes de instalar y comparar capturas. Pendientes: dibujo real y logs PixelCopy, ambos renders, modo claro/oscuro, status/gestos/cámara, scroll y acceso a controles inferiores, teclado, menú, selector, rotación y Desktop↔Phone. Las capturas propias del run39898129497 prueban el fallo y cambio de tema nativo, no la corrección nueva ni toda la matriz de aceptación.

## Run39907023931 — preflight bloqueado por probe desactualizado

SHA compilación solicitada: `2c78ab3dc3a08a0aa1663abd774e66f556d88f32`. Resultado: authorize PASS; preflight FAIL; build y QEMU SKIPPED; checkpoint no restaurado, sin nuevo checkpoint ni APK. No hubo instalación ni relanzamiento.

Primer error causal: `tests/test_r4_composited_toolbar.py` extrae el cuerpo real de `ToolbarManager.updateToolbarSceneLayerSuppression()` y lo compila en `SuppressionProbe`. La clase auxiliar declaraba sólo los tres motivos antiguos; faltaba `mArcPhoneOverlayActive`, agregado por Floating. Javac rechaza esa clase auxiliar con `cannot find symbol`, y el preflight se detiene. CI ejecutó 413 tests: 412 aprobados y un error. La preparación SDK/parche anterior a la suite sí pasó; eso no constituye compilación nativa integrada.

Corrección localizada, sin cambios de producción: declarar el cuarto campo en el probe, recorrer sus 16 combinaciones (antes8) y mostrar stderr de javac si vuelve a fallar. No se elimina ni relaja el gate. Prueba aislada RED/GREEN PASS; mutación que retira la condición móvil rechazada exactamente en `mask=8`, preservando los motivos Desktop/XR/narrow originales.

Evidencia: `run39907023931-preflight.log`, `suppression-probe-red-detail.log`, `suppression-probe-green.log`, `suppression-mutant.log`, en `/workspace/archium-evidence/floating-v2-runtime-fix/`. El monitor existente conserva el fallo real. La APK anterior y los checkpoints fuente/fallback siguen intactos. Se requiere nueva autorización para otro run; no se usó una segunda ejecución remota.

Validación local de la corrección, 23-oct-2026 CDMX:

- Probe corregido: PASS, 16 combinaciones. Mutante sin condición móvil: rechazado enmask8, PASS del control negativo.
- Suite host completa ejecutada: 413 tests; 411 PASS y2 ERROR del entorno local por seleccionar `/usr/bin/aapt2` de Debian2.19, que no lee `resources.arsc` del SDK37.2 (`entry offsets overlap actual entry data`). No se presenta esa invocación como PASS.
- Las dos pruebas de recursos se repitieron sin cambios con el AAPT2 37.0 existente y SDK37.0: ambas PASS; fixture real18 recursos PASS. Logs `host-complete-after-fix.log` y `aapt37-resource-rerun.log`. Las pruebas restantes, incluida la regresión que bloqueó CI, pasaron en la suite completa.
- Herramientas locales de esa ejecución: JDK21, GN genuino1000 (no el pin de GN usado por CI); la repetición de recursos usó AAPT2 2.20-15087165 del SDK. No se instalaron ni actualizaron dependencias, no se relajaron gates y no se modificó producción.
- Regeneración: patch/manifest idénticos a2c78ab3; diff limpio. La integración nativa y aceptación visual siguen pendientes de otro run autorizado.

Para futuras comprobaciones locales usar explícitamente `ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2` y un SDK compatible; no seleccionar el AAPT2 de Debian por PATH. El CI existente ya usa el AAPT2 del SDK.
