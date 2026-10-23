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

## Fuente de blur vacía y owner real de insets — 23-oct-2026 CDMX

Run39926747580 / 2d2ba3a compiló e instaló (APK SHA256 `6c5958430be813bf3284d59c5dda6b9f1ab09b83987dd76b64f6420b92720168`). Aceptación visual **FAIL**. Capturas propias con patrón de contraste en claro y oscuro: ambas cápsulas dejan ver web real, pero sin desenfoque. Status bar conserva franja sólida y posición superior cambia tras configuración. Evidencia externa: `/workspace/archium-evidence/floating-v2-runtime-fix/review-*`. Pestaña temporal y tema automático restaurados.

El registro HWUI del PID de Archium dice `Surface doesn't have any previously queued frames, nothing to readback from`, coincidiendo con ambos resultados `copy success=false` y ausencia de `painted frame`. La fuente SurfaceView consultada carece de buffers. El CompositorView fijado documenta que SurfaceControl no permite leer esos buffers (su ruta de selección cambia temporalmente de superficie para la lupa). No se afirma haber leído directamente el flag SurfaceControl del APK.

Corrección candidata: sustituir PixelCopy por un puente JNI pequeño en CompositorView hacia **RenderWidgetHostView::CopyFromSurface**, API ya utilizada por TabContentManager en esta revisión. Copia sólo la región del control, máximo256×128, timeout250ms y una solicitud en vuelo; ningún capturer count, captura completa de página/ventana, cambio de superficie o configuración GPU. El callback vuelve a la secuencia original, el blur sigue en worker y los estados/generaciones existentes descartan resultados de otra pestaña o tras pausa. Error de superficie/protección mantiene el fallback translúcido; no se elude la política nativa de copia. No se crean dependencias ni se usa una API de testing en producción.

Segundo origen demostrado: **EdgeToEdgeLayoutCoordinator** aplica padding y pinta status/cutout antes del consumer Chrome; el opt-in añadido sólo al controlador posterior no puede eliminar una reserva ya aplicada. Opt-in móvil por defecto false en EdgeToEdgeBaseLayout y consumo en su coordinator real: elimina únicamente padding/pintura superior de status/cutout durante web Floating, conserva caption bar, laterales, IME y navegación, y restaura ruta nativa al salir. ToolbarManager activa ambos owners, sin cambiar dimensiones de omnibar.

No cambian archivos específicos Desktop, Spaces, Split View, colores o proporciones. Los métodos nuevos del compositor sólo se invocan desde el opt-in Phone. NTP continúa fuera de alcance. Revisadas declaraciones/API/targets GN contra fuentes fijadas; `NATIVE_API_AUDIT.md` guarda alcance y límites. Esa revisión no equivale a compilar C++ nativo.

Regresiones: probe del consumer real con dependencias sintéticas falla contra el owner fijado anterior (RED) y pasa con el fix: top0, laterales/caption conservados, IME600 y restauración nativa. Robolectric verifica región respecto de ContentView y rechazo de captura pendiente al cerrar la fuente; conserva pruebas de blur real sobre bitmap, foreground y estado. Los tests no prueban que el nuevo readback entregue frames en el Galaxy.

Gates ya ejecutados: Robolectric SDK30/36 **80 ejecuciones PASS**, política original40 métodos; host Phone específico y preparación SDK37.2 PASS; aplicación/transición24 PASS; parche/manifest178 archivos regenerados idénticos. Evidencia `/workspace/archium-evidence/floating-v2-readback-fix/`. Resultado de suite host completa y repeticiones de entorno se registra al terminar.

Fuente39829306775-1:4 grupos/25 partes, pin y manifest SHA256 `cf4cad1717bd041ad928bd8c102aecdbd027b707ec8e5c5494ff1dee342c8ce0` comprobados otra vez; artifacts no expirados. Todos los hashes de partes siguen siendo gate obligatorio de CI antes de restaurar. Sin limpieza ni borrados adicionales.

El usuario autorizó **un único build incremental** del SHA final nuevo, preflight completo y QEMU false; sin relanzamientos ni reparaciones. Monitor y actualización ADB sólo con recibos/SHA/paquete/ABI/firma/versión verificados, respaldo previo y misma identidad de Galaxy. **Aceptación gráfica del candidato PENDIENTE** hasta capturas instaladas comparadas con ambos renders, insets/scroll/IME, luz/oscuridad, fullscreen y transición Desktop↔Phone. No prometer rendimiento ni coincidencia visual por los gates locales.

Cierre de gates locales del candidato: suite host completa416 tests,410 PASS,4 FAIL y2 ERROR causados exclusivamente por mi variable `ARCHIUM_TEST_ANDROID_JAR` apuntando a `android-37` (directorio inexistente). No se registra esa invocación como PASS. Repetidos los mismos seis casos sin cambiar sus tests, con `/opt/android-sdk/platforms/android-37.0/android.jar`: native API4 PASS y recursos2 PASS (fixture real18 recursos). Logs `host-complete.log`, `native-api-correct-sdk.log`, `resource-correct-sdk.log`. Los otros410 casos, incluidos los nuevos probes y gates de rollback/estado/patch, pasaron en la suite completa. Robolectric final80 PASS/política40; preparación SDK y patch24 PASS. No se omite preflight remoto.


## Cristal, edición y menús — candidato posterior a 76e7934, 23-oct-2026 CDMX

Run39961783403 compiló e instaló, pero la aceptación visual continúa FAIL. La APK instalada sí entrega y pinta muestras del compositor (`runtime-glass.txt`); el defecto actual no es ausencia de readback. Capturas propias `before.png` y `omnibar-edit.png`, jerarquías y logs en `/workspace/archium-evidence/floating-v2-optics-review/`. La sombra legacy usaba el rectángulo completo del editor en lugar de la cápsula; el blur anterior retenía trazos de texto y las superficies de edición/menús permanecían opacas.

Cambios candidatos:
- ArcPhoneGlass: tres pases de blur lineal con buffers/capturas limitados, tinte neutral nativo claro/oscuro, borde de 0,5dp oscuro/claro sólo en la pill inferior, selección de targets visibles sin perder turnos y descarte de resultados de menús cerrados. Coordenadas de pantalla para muestrear correctamente ventanas PopupWindow/Dialog separadas; nunca captura recursiva de ventana.
- ToolbarPhone: sombra exterior suave limitada al rectángulo real de la omnibar, sin cambiar tamaño. Indicador fino de carga en su perímetro con progreso/fade nativos y colores neutros del tema; ToolbarProgressBar suprime exclusivamente su línea Android/compositada durante el opt-in y restaura el estado nativo al salir.
- ToolbarManager y contenedor/dropdown nativos de sugerencias: el foco ya no desactiva la presentación flotante. Fondo de cristal y fondos de filas atenuados sin alterar editor, navegación, selección, teclado ni acciones. Restauración del fondo/color/alpha nativo al desactivar.
- Menú inferior: reutiliza la captura compartida, con fallback nativo. `hasSolidBackgroundColor()` desactiva explícitamente la superficie opaca del owner; destruir el sheet libera su target. Sin otra barra ni menú ficticio.
- ViewUtils y un tag de recursos UI permiten al Activity registrar un decorador opcional, sin dependencias nuevas. AppMenu principal/submenús («Más opciones»), PageInfoDialog («Configuración del sitio») y ContextMenuDialog (enlaces/imágenes) se conectan a ese owner. El decorador guarda fondos/padding y los restaura al desactivarse o cerrar; sólo despeja las capas de superficie suministradas por el owner, sin borrar botones ni advertencias de seguridad. Ausencia de registro conserva el comportamiento nativo/Desktop. Menús del sistema Android y pantallas completas de Ajustes no se convierten en cristal.
- InsetObserver y EdgeToEdgeControllerImpl propagan el área segura superior por observers nativos, manteniendo transparencia. Ayuda a webs que respetan safe areas; no garantiza corregir encabezados de sitios que las ignoran. El contraste de iconos de status bar sobre páginas arbitrarias sigue pendiente de comprobación física.
- El generador de parches ahora conserva el marcador Git de falta de salto final de línea: el `ids.xml` fijado no termina en newline. RED: parche corrupto; GREEN: aplicación y bytes exactos. No se modificó el original fijado para ocultarlo.

Verificación actual: 92 ejecuciones Robolectric SDK30/36 y política original Chromium46 métodos PASS; host phone23, ownership5 y parche25 PASS. Preparación SDK37.2/JDK21 PASS con fronteras sintéticas Chromium; no compila íntegramente los widgets nativos nuevos. Regeneración del parche/manifest (187 archivos) idéntica. Transición sparse real desde los patches del commit fuente198fe8a PASS,158 timestamps de entradas idénticas preservados; HEAD sintético sólo en el fixture, originales verificados contra sus hashes fijados. No se restauró aquí el archivo completo del checkpoint. Suite host completa final424 PASS (`host-delivery-final.log`); suite anterior421 PASS. RED/GREEN y logs por etapa conservados en la evidencia citada. Ningún PASS local equivale a apariencia validada de APK.

Inventario GitHub paginado antes del nuevo build: sólo fuente39829306775-1 y fallback39817793524-1 (cuatro grupos cada uno,25 partes), sin ejecuciones activas/queued. Identidad, expiración e inventario comprobados; manifests leídos mediante Range acotado y pin verificado. SHA manifest fuente `cf4cad1717bd041ad928bd8c102aecdbd027b707ec8e5c5494ff1dee342c8ce0`; fallback `393267e38590fe0c8dcead5a330dd7fda51e97a76286ef99d284a8997cf99548`. No hay redundantes seguros: **0 bytes liberados, ningún checkpoint eliminado**. CI debe verificar capacidad y todos los hashes antes de restaurar. Recibo `cleanup-receipt.json`.

Autorizado por el usuario un único build incremental del SHA final, con preflight completo y QEMU desactivado; monitor nativo Termux CDMX600s. Sin reintentos automáticos. Estado de despacho y resultado se registrarán en un directorio nuevo. Limpieza de almacenamiento del teléfono autorizada después de abrir el monitor: preservar fuente activa/soporte del monitor, credenciales y respaldo necesario para actualizar sin pérdida de datos.

Aceptación física del candidato: **PENDIENTE** en ambos temas, cambio automático, contraste sobre páginas opuestas, borde/sombra/blur, menú principal y submenús, información del sitio, enlaces/imágenes, editor/sugerencias/pill con IME, progreso perimetral, fullscreen, rotación y Desktop↔Phone. La NTP continúa pendiente según acuerdo. Desktop no se rediseña ni se modifican sus anchos, Spaces o Split View. No declarar DONE por compilar/instalar.


### Despacho e inventario posterior — run39982605276

Código de compilación `052c55ab39e97ea267d0eb0f5a3eecc77484e70a`, rama `assistant/archium-r5-desktop-native-mobile`. [Actions](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39982605276). Un único dispatch con nonce persistente, SHA verificado en remoto y sin ejecución equivalente/activa. `skip_preflight=false`, `run_qemu=false`; fuente39829306775-1/198fe8a/run39829306775. Authorize y preflight remoto PASS; `build / build` en `S1 restore once and transition patches` al consultar. No se afirma todavía éxito de restauración, compilación ni APK nueva.

Estado/intent/recibos y launcher: `/workspace/.local/state/archium-r5-optics-052c55a/`, `/workspace/.local/bin/archium-r5-optics-39982605276.sh`. Nueva sesión nativa Termux `/dev/pts/2`, shell18267, watcher18481; hora CDMX, refresco600s. Sin supervisor ni nuevos dispatch/reparaciones/reintentos. Wake lock reafirmado después de retirar sesiones viejas. Instalador verificado heredado habilitado; APK/instalación del nuevo run pendientes. Captura posterior a instalación no equivale a aceptación de ambos temas.

Limpieza autorizada del teléfono realizada DESPUÉS de abrir el monitor:73 entradas retiradas (35 APK locales antiguas,15 archivos públicos de Archium,4 worktrees,2 clones,1 alias roto,outputs de mantenimiento y15 launchers). Se preservaron historia Git independiente en bundles verificados, diferencias y archivos no seguidos de las copias con cambios locales: `recovered-local-changes/` dentro del estado nuevo. Worktrees retirados mediante Git, conservando `/workspace/Archium-R5/.git`, almacén común de la rama activa. Clones MacDesk-V6/macdesk-source retirados; no se realizó desarrollo en ellos. Dependencias JAR del runner copiadas con hash verificado a `/workspace/.local/share/archium-host-test-support/`; ruta compatible del classpath anterior conservada sin sus outputs viejos.

Espacio Android observado:49.998.991.360 →76.052.656.128 bytes libres, diferencia26.053.664.768 bytes; suma estimada de entradas eliminadas25.236.964.457 bytes (medidas distintas: espacio libre del volumen y tamaños de archivos/directorios). Recibo por ruta: `storage-cleanup-receipt.json`; validación posterior de Git activo, classpath, respaldo y monitor PASS. Documentos personales, perfiles/datos de apps, credenciales, renders aprobados y evidencia del defecto actual fuera del alcance de eliminación. Checkpoints GitHub:0 eliminados, fuente/fallback conservados como se documentó arriba.

APK anterior aún disponible en `/sdcard/Download/Archium_R5_76e7934_arm64.apk`, SHA256 `70e23546ecd290f26d3c89fa20ebde2b36e1a36e02a548c1e589162af60b10b1`. Respaldo previo protegido en `/workspace/.local/state/archium-r5-floating-readback-76e7934/adb-update-39961783403/installed-before.apk`, SHA256 `6c5958430be813bf3284d59c5dda6b9f1ab09b83987dd76b64f6420b92720168`. El instalador guardará también la APK instalada antes de cualquier reemplazo nuevo. Aceptación visual del candidato052c55a: PENDIENTE.
