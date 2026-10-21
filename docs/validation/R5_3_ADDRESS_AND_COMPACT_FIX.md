# R5.3 — corrección de dirección y sidebar compacta

Base: `785ddf4`; defectos reproducidos en Galaxy en `R5_3_DEVICE_USABILITY_REVIEW.md`.
Implementación aislada en `assistant/archium-r5-3-omnibox-split`.

## Causas demostradas

DEVICE-01: `LocationBarMediator.beginOrResumeInput`, callback de `session.activate`,
vaciaba `initialInput`, texto y preview siempre que existía un popup Arc. No distinguía editar URL de Ctrl+T.
DEVICE-02: `LocationBarMediator.loadUrl` copiaba los parámetros nativos con `setOpenInNewTab(true)`
para todo popup Arc. Esto explica la pestaña adicional y la salida del visor dividido observadas en el dispositivo.
DEVICE-03: `TabVerticalViewBinder.updateIcons` resolvía el modo compacto con `DeviceInfo.isDesktop()`.
Un teléfono en ventana Arc/DeX puede devolver false y mantener X visible en lugar del favicon.

## Cambio mínimo

- `ArcCommandBar` distingue edición de dirección de Ctrl+T y acciones; sólo expone el modo mientras está abierto.
- `ArcDesktopCoordinator` publica ese modo en `LocationBarLayout` antes de empezar el input nativo.
- `LocationBarLayout` elimina el modo al cerrar y rechaza activarlo sin popup.
- `LocationBarMediator` conserva la inicialización nativa con URL al editar, y entrega intactos los parámetros
  nativos a la navegación actual. Ctrl+T sigue vacío y crea nueva pestaña. Acciones no cargan URLs.
- El binder compacto reconoce ventana Arc además del tipo de dispositivo: favicon sin hover,
  cierre en hover. Se conservan móvil, fila expandida y pestañas fijadas.

No se sustituye autocomplete, editor ni resolución de URLs; se conservan POST, headers, callbacks,
disposición explícita a otra ventana/background y el TabModel activo. No se toca el compositor ni GPU.
No hay recreaciones de Activity, Tab o WebContents.

## RED/GREEN y gates

La prueba `tests/test_r53_address_semantics.py` ejecuta fragmentos exactos de producción en Java,
con límites nativos explícitos. RED: 4 fallos de 6 casos en el código anterior. GREEN: 6/6.
Cubre URL preservada, navegación actual con identidad de parámetros, Ctrl+T, disposiciones explícitas,
acciones y política de cierre compacto. No equivale a ejecutar una APK Android.

También se añaden regresiones al `LocationBarMediatorUnitTest` real de Chromium y
`TabVerticalViewBinderUnitTest`; se añade el filtro `LocationBarMediatorUnitTest.testArc*` al gate,
con su prueba de cobertura, conservando todos los filtros anteriores.
El test de popup con vistas reales comprueba el modo de edición y su limpieza al cerrar/reabrir Ctrl+T.

Resultados locales y sus hashes se registran en el informe privado de gates antes del despacho.
Pruebas JVM realizadas: puente nativo/Fusebox 18 PASS, popup 18 PASS, split 86 PASS, helpers 50 PASS;
preparación API37 PASS. Son JVM/Robolectric con adaptadores, no QEMU ni GPU real.
La suite completa host pasó 371/371 tests (694.799s); actionlint, sintaxis Python/shell y diff check PASS. El runner completo
Chromium/GN/JNI y la nueva APK se verifican en CI.

## Build y monitor

Checkpoint origen: `archium-checkpoint-39370769321-1`, commit `8d26b0cf7a5a55701a58ff7d14b59fdd479aa4ca`.
El run exitoso 39379198808 no publicó otro checkpoint. Se verificaron otra vez inventario,
identidad/digests de artefactos y manifiesto: cuatro grupos, 25 partes.
SHA256 del manifiesto `e9d0c6d6060e234b836ce90b3684473c4946b352fe0744cb9bcef6ea44b05da7`.
Chromium pin, GN args, toolchain y package permanecen iguales. Restauración íntegra,
capacidad del runner y hashes de cada parte quedan como gates CI; no se afirma restauración local.
Sin clean build, purga ni borrado de outputs/checkpoints.

Usuario autoriza nueva ventana de hasta 10 horas; se conservan contadores históricos,
se registra un único despacho manual adicional y QEMU continúa desactivado.
Se conserva monitor único, refresco 600s y actualización ADB condicionada a gates/APK/firma/version/hash
instalado. RUN_ID, SHA y prueba de sesión independiente quedan en el estado privado del handoff.

## Aceptación pendiente

No hay GREEN visual de estas correcciones hasta instalar una APK que las contenga.
Repetir: copiar URL actual, editar y Enter en ambos paneles sin crear pestaña ni perder split,
Ctrl+T creando nueva pestaña, cancelar sin navegar, POST/selecciones/autocomplete y compacta con mouse/toque.
Mantener pruebas pendientes de estabilidad, transición por frames y UA móvil efectiva.
Amazon sigue UNRESOLVED_GRAPHICS_BLOCKER y no se reabre su investigación.
