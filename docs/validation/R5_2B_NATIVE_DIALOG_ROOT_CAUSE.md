# R5.2B — bloqueo de presentación con browser controls ausentes

Fecha: 2026-10-19. Worktree `Archium-R5.2-forensic`, rama
`assistant/archium-r5-2-forensic`, investigación previa `b4e0883`.

**Resultado: defecto del presenter reproducido y corregido a nivel de código,
con RED/GREEN local. P0-02 del APK instalado continúa abierto hasta GREEN real.**
La condición concreta del provider durante el incidente físico no pudo observarse
sin instrumentar otra APK. No se presenta esa vinculación como un hecho medido.
No hubo build, instalación, merge, cherry-pick ni modificación del supervisor.

## Primera transición incorrecta demostrada

En la reproducción del código fijado:

`SHOW solicitado → espera por hiddenRatio=0 → ATTACH nunca ocurre`,
aunque no existe la barra activa cuya animación se espera.

`BrowserControlsManager.getTopControlHiddenRatio()` devuelve **1.0** si la altura
superior es cero. Lo mismo sucede para la barra inferior. Es una semántica válida
para una barra ausente: se considera totalmente oculta. El provider también
expone esa convención. No debe cambiarse globalmente para arreglar un consumidor.

`BrowserControlsUtils.areBrowserControlsFullyVisible()` exige ratio exactamente
cero. `ChromeTabModalPresenter.showDialogContainer()` espera esa condición para
invocar `runEnterAnimation()`, pero muestra el scrim y oscurece el tab igualmente.
`TabModalPresenter.runEnterAnimation()` es donde se agrega ModalDialogView al
contenedor y se aplica VISIBLE. Con altura cero, ningún offset puede producir un
ratio cero: un nuevo callback de offsets por sí solo tampoco resuelve la espera.

Hay una segunda variante del mismo contrato: el diálogo espera con barra existente
parcialmente oculta y después la barra desaparece. Los callbacks de altura sólo
actualizaban márgenes; no reexaminaban la entrada pendiente. Se reproduce sin
suponer que un callback de offsets adicional vaya a llegar.

Arc aporta una ruta legítima hacia controles ausentes:
`ArcDesktopCoordinator.applyAddressBarPosition()` selecciona la supresión según
el modo escritorio/posición de la omnibox; `TabbedRootUiCoordinator.
setArcToolbarSuppressed()` oculta la toolbar, retira su capa de TopControlsStacker
y solicita actualización síncrona. El stacker recalcula la altura según las capas
restantes. **No se presupone que todas las configuraciones Arc tengan altura cero.**
La configuración efectiva del incidente debe confirmarse con la nueva traza.

## Qué está probado en Galaxy y qué no

Se conserva íntegra la evidencia de los doce mosaicos y el original del teléfono,
SHA-256 `ea568bda931099858fc8d24336507d194bb60a6a0ef0e07ef7843fec87427dac`.
No se repitió la matriz ni se navegó por cuentas personales durante R5.2B.

Durante los incidentes DeX anteriores: evento JS abierto, scrim visible,
`tab_modal_dialog_container` GONE/0×0 y sin ModalDialogView en la jerarquía.
HTML modal/no modal, overlay, nueva ventana y selector Android eran visibles.
Un alert válido en pantalla del teléfono sí mostró el cuadro. Estos hechos son
compatibles con el bloqueo reproducido; no miden por sí mismos el hiddenRatio.

**DEVICE_CAUSE_LINK=PENDING**: faltan ratio, alturas/posición efectiva y flag
pendiente del presenter durante esa misma apertura física. La APK instalada no
contiene las nuevas trazas. No se intentó inyectar agentes en un APK release,
obtener root ni evadir restricciones para leer sus campos Java. Sin otro build
no se pueden atribuir logs nuevos de esta instrumentación al Galaxy.

Evidencia física y hashes: [informe original](R5_2_PHONE_HTML_DIAGNOSTICS.md) e
[índice por caso](r52/phone-cases.json). No se inventó un Logcat posterior al fix.

## Ruta efectiva y fronteras de evidencia

No existe aquí una clase genérica que debamos modificar por llamarse
«ModalDialogPresenter»: la abstracción real es `ModalDialogManager.Presenter`.
La implementación TAB es ChromeTabModalPresenter, derivada de TabModalPresenter.

| Etapa | Código efectivo | Evidencia / límite |
| --- | --- | --- |
| REQUEST | TabModalDialogViewAndroid::Create/Show | Crea fábrica Java alert/confirm/prompt y usa WindowAndroid del WebContents; código fijado auditado |
| CREATE Java | JavascriptTabModalDialog.showDialog(WindowAndroid,long) → JavascriptModalDialog.show | Context/manager ausentes cancelan antes; si existen, infla custom view y construye PropertyModel; no se cambió esta lógica |
| ENQUEUE | ModalDialogManager.showDialog | Cola si tipo suspendido o prioridad bloqueada; no se midió cola interna en Galaxy |
| SHOW | ModalDialogManager.Presenter.setDialogModel → TabModalPresenter.addDialogView | Guarda modelo activo antes de crear vista y llamar showDialogContainer; el callback onDialogShown puede preceder ATTACH y no prueba visibilidad |
| ATTACH | ChromeTabModalPresenter gate → TabModalPresenter.runEnterAnimation | Primera transición defectuosa reproducida: altura cero/ratio uno difiere indefinidamente; scrim ya visible |
| MEASURE/LAYOUT | Android View traversal después de addView | En GREEN host, vista adjunta, contenedor VISIBLE y altura positiva; dimensiones inmediatas post-attach aún pueden ser cero |
| DRAW | Android/compositor | No ejecutado sobre APK corregido; no se deduce de un evento JS o de un test host |
| CLOSE | JavascriptModalDialog.onClick/onDismiss, manager y presenter.removeDialogView | Causas de aceptar/cancelar conservadas; entrada pendiente se cancela y se retiran vista/scrim en prueba local |

WindowAndroid determina el manager al entrar; ChromeTabModalPresenter conserva
Activity, tab activo y su contenedor. TabObscuringHandler administra el token de
oscuramiento; el fix no modifica su contrato, foco, window tokens ni reparenting.
TabModalLifetimeHandler mantiene sus reglas de suspensión/cierre por tab,
interactability y navegación; no se alteró.

## Comparación diferencial A–G

| Hipótesis | Resultado de esta investigación |
| --- | --- |
| A. No hay petición | No explica el mecanismo host ni la ejecución física de JS; la traza futura js_request lo distinguirá directamente |
| B. Cola bloqueada | No es necesaria para reproducir el fallo; no se afirma haber leído la cola del APK instalado |
| C. Presenter/ventana incorrectos | El mecanismo se reproduce con Activity/contenedor correctos; asociación exacta del Galaxy pendiente de handles correlacionados |
| D. Show sin adjunción | **Demostrado en host causal y observado como estado físico**; falta vincular el provider concreto del incidente |
| E. GONE incorrecto | En el mecanismo no es una ocultación posterior: queda en el estado inicial GONE porque nunca se ejecuta la entrada |
| F. Lifecycle elimina antes de draw | No necesario en reproducción estable; no observado cierre antes de las capturas previas; no se excluyen todas las carreras Android |
| G. Interferencia Arc | Supresión de toolbar puede producir la condición; no se atribuye a GPU, SurfaceView o z-order |

Los diálogos HTML usan Blink/top layer y el overlay usa DOM/CSS; no pasan por este
presenter. El selector de archivo usa una ruta Android distinta. Su visibilidad
no implica que todas las ventanas o permisos nativos estén validados.

## Corrección mínima y archivos

SHA de implementación: `51847556e761ca0600a4aa824531e40d200fdf17`.

1. ChromeTabModalPresenter calcula disponibilidad para el diálogo según la altura
   del stack **activo**, superior o inferior. Si es cero no existe una animación
   de esa barra que esperar; si existe, conserva la condición original de fully
   visible. El stack opuesto puede tener altura no nula.
2. La misma condición protege el callback pendiente. Los callbacks de altura
   vuelven a evaluar esa entrada tras actualizar layout; el flag se consume antes
   de adjuntar y el guard de modelo evita resucitar un diálogo cerrado.
3. Se mantienen getBrowserControlHiddenRatio, BrowserControlsUtils, constraints,
   fullscreen, permisos, JNI, valores de prompt y acciones nativas. No se fuerza
   visibilidad global, GPU ni recreación de Activity/Tab/WebContents.

Archivos de producto:

- `.source-modified/chrome/android/java/src/org/chromium/chrome/browser/modaldialog/ChromeTabModalPresenter.java`: gate, callbacks y trazas optativas.
- `.source-modified/components/javascript_dialogs/android/java/src/org/chromium/components/javascript_dialogs/JavascriptModalDialog.java`: sólo trazas de request/close, sin modificar respuestas.
- `.source-modified/chrome/android/junit/src/org/chromium/chrome/browser/modaldialog/ChromeTabModalPresenterUnitTest.java`: cuatro regresiones del gate.
- Originales fijados correspondientes en `.source-reference/`; patch y manifest regenerados.
- `scripts/test-robolectric-native-dialog-gate.py`, fixture y catálogo de hashes: prueba local reproducible de métodos entregados.

## Instrumentación dirigida

Tag `ArchiumModal`, desactivado salvo que Android autorice nivel DEBUG para ese
tag. Clave de correlación: PID + identidad del modelo + intervalo monotónico de
request; los handles son locales al proceso, no identificadores globales durables.
La petición JavaScript y el presenter comparten el mismo modelo.

Eventos: `js_request`, `show_request`, `show_deferred`, `controls_offset`,
`controls_height`, `attach_before`, `attach_after`, `remove_before`, `remove_after`,
`js_close`. Incluyen tiempo monotónico ns, thread, tab, Activity, ventana/token,
presenter/modelo, altura y posición de controles, offsets/ratio, flag pendiente,
identidad/visibilidad/children/dimensiones/foco del contenedor. No incluyen título,
URL, mensaje, origen, contraseña ni texto introducido. Se conservan las últimas
transiciones de cierre aun tras alcanzar el límite de callbacks registrados.

Máximo por presentación: 24 registros del presenter más dos de cierre; la capa
JS añade request/close. No se retienen modelos ni se crean observadores, ventanas,
sesiones de monitor o callbacks de layout. Se registra estado inmediato de
adjunción, no una falsa garantía de DRAW; capturar traversal/píxeles por separado.

Procedimiento de un único ensayo futuro, sin repetir doce mosaicos:
[README del harness](../../tests/fixtures/rendering/r52b/README.md).
El procedimiento requiere una APK posterior autorizada, con actualización
incremental; los comandos de activar trazas no se ejecutaron aquí sobre la APK vieja.

## Pruebas RED/GREEN y regresiones

RED observado antes de modificar el producto: **16 ejecuciones, 12 fallos de
aserción esperados**, SDK30/36. Cuatro ejecuciones ya pasaban: ruta con controles
existentes y respuestas del controller. Los fallos no eran errores de compilación.
Se corrigieron previamente errores del adaptador antes de aceptar el RED.

Control negativo final con presenter upstream intacto: **18 ejecuciones, 12 fallos**
de aserción, incluidos los casos de cierre pendientes añadidos después del primer
RED. Log: `/workspace/macdesk-maintenance/archium-r52b/baseline-negative-final.log`.

GREEN final: **18 PASS**, SDK30/36, incluidos dos casos adicionales de cierre
pendiente sin resurrección por callback tardío. Log:
`/workspace/macdesk-maintenance/archium-r52b/green-final.log`.

Los cuerpos se extraen por definición de método desde los fuentes entregados y
los originales fijados; hashes externos verificados. No se copió la condición
esperada a un presenter inventado. Se ejecutan manager ratios, utils, show,
readiness, callbacks, enter/exit/remove y click/dismiss del controller. Vistas y
layout son Android real bajo Robolectric. JNI, inputs del provider, inflado de
recursos/modelos, scrim y selección son adaptadores explícitos. No se compila la
clase Chromium completa ni se ejecuta su target GN con este harness.

| Regresión | Alcance ejecutado |
| --- | --- |
| Stack superior ausente | ratio uno real del método; contenedor VISIBLE, un hijo adjunto y altura positiva |
| Stack inferior ausente | pasa aun con altura no nula del stack opuesto |
| Barra existente parcialmente oculta | espera y adjunta una sola vez al recibir fully visible |
| Barra desaparece durante espera | callbacks superior/inferior resuelven sin exigir offset adicional |
| Cierre antes de entrada | callback tardío no reabre ni vuelve a adjuntar |
| 25 aperturas/cierres por SDK | sin hijos residuales, parent viejo null; no sustituye análisis de heap/ventanas reales |
| Alert/confirm/prompt | accept de vacío/PRUEBA/Unicode, cancel de botón/back y cierre nativo conservan rutas de respuesta en controller; frontera JNI adaptada |
| Trazas | opt-in, límite por presentación y cierre final, sin texto privado |

Foco y retorno de IME en Galaxy: **NOT_TESTED después del fix**. Permisos Android
y HTML sobre la APK corregida: NOT_TESTED; se conserva su visibilidad previa,
no se convierte en regresión nueva aprobada. Fugas de WindowManager/heap reales:
PENDING. Cuatro casos añadidos al target Chromium: **preparados, ejecución completa
pendiente CI**; no se confunden con los 18 casos locales.

Suite host completa: **339 tests en 548.338s: 337 PASS y 2 FAIL por entorno**.
Los fallos fueron `test_portal_optimized_alias.OptimizedAliasTest.
test_pinned_upstream_config_reproduces_missing_themed_alias` y
`test_portal_optimized_alias.OptimizedAliasTest.
test_real_aapt2_shortened_alias_and_foreign_manifest_rejection`: faltaban las
variables del ejecutable AAPT2 y Android jar, no un error del presenter.
Reejecución de esos dos tests con `ARCHIUM_TEST_AAPT2=/opt/android-sdk/build-tools/37.0.0/aapt2`
y `ARCHIUM_TEST_ANDROID_JAR=/opt/android-sdk/platforms/android-37.0/android.jar`: **2 PASS,
243.709s**. La suite completa no se repitió: se conserva su resultado inicial y
la resolución dirigida. AAPT2 usa QEMU de usuario x86 en este host ARM64; esto no
es Android Emulator ni cambia QEMU_ABI_BLOCKED. Logs `full-suite.log` y
`resource-rerun.log` bajo el directorio privado R5.2B.

[Recibo depurado de verificación](r52b/verification.json).
Reconstrucción del patch sobre todos los originales declarados: PASS, 128 rutas.
Sólo tres entradas difieren frente a `3db367a`; el código de identidad/reorder de
pestañas permanece idéntico. No se repitió validación física de drag.

## Checkpoint y ejecución protegida

Pin Chromium `cfd94726b7b5fb48aedcc32662f2f3fbdbadec35` / 157.0.8086.0 intacto.
GN args, toolchain, ARM64, package app.archium.android, recursos Portal y workflow
sin cambios. No cambia firma JNI ni grafo nativo; la invalidación esperada se
limita a compilación Java, dex/empaquetado y tests dependientes. Ninja determinará
el conjunto real cuando se autorice una etapa incremental.

El patch/manifest se verificó reconstruyendo fuentes temporales; no se restauró
ni modificó el checkpoint real. Por tanto **compatibilidad estructural preparada,
compatibilidad de bytes/runner aún a verificar** con los gates originales antes
de la próxima etapa. No se hace fallback limpio. No se tocó out/Archium ni cachés.

Run reservado: [39296066030](https://github.com/Jorgeprdz/chromium-dex-arc/actions/runs/39296066030),
SHA `3db367adff50d423b8c4475d10165d2790f6065a`, in_progress en la consulta inicial
R5.2B. Supervisor existente PID 29810 / SID 29711 observado activo; no se cambió
su estado ni se despachó trabajo. El checkpoint origen previamente registrado
es archium-checkpoint-38511423805-1. El último checkpoint válido para un futuro
build se debe verificar después de que termine el run; este informe no lo aprueba
anticipadamente. No se mezclan artefactos de ambos SHAs.

QEMU permanece **QEMU_ABI_BLOCKED**. GPU Amazon sin cambios ni nueva conclusión.
Estado del fix: **SOURCE_REGRESSION_GREEN / DEVICE_ACCEPTANCE_PENDING**.
Estado de integración: **LOCAL_ONLY, NO_BUILD_DISPATCHED**.
